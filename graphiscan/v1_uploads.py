"""Private, bounded official uploads; side effects follow durable reservation."""
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import warnings

from api_v1 import ApiError, BackendUnavailable
from v1_directory import DirectoryService, invalid_query, record_id
from v1_screening_writes import checked_result, request_key

MAX_BYTES=10*1024*1024
MAX_PIXELS=16_000_000
PREPROCESSING_KEY='graphiscan-rgb224-raw-normalized-png-v1'
RULE={'kind':'high_potential_threshold','threshold':0.75}

def normalize_image(stream):
    from PIL import Image, ImageOps
    raw=stream.read(MAX_BYTES+1)
    if not raw or len(raw)>MAX_BYTES:
        raise ApiError(422,'INVALID_IMAGE','Choose a JPG or PNG image up to 10 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.format not in {'JPEG','PNG'} or image.width*image.height>MAX_PIXELS or getattr(image,'n_frames',1)!=1:
                    raise ValueError()
                image.verify()
            with Image.open(BytesIO(raw)) as image:
                normalized=ImageOps.exif_transpose(image).convert('RGB')
                output=BytesIO();normalized.save(output,format='PNG')
                data=output.getvalue()
                if len(data)>MAX_BYTES:raise ValueError()
                return data
    except Exception:
        raise ApiError(422,'INVALID_IMAGE','Use one valid JPG or PNG image, at most 16 megapixels and 10 MB after normalization.') from None

def file_digest(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()

class ActiveBinaryRuntime:
    """Only the existing trusted predictor artifact; no client paths/weights."""
    def __init__(self,manifest_path):
        root=Path(__file__).resolve().parent
        manifest=json.loads(Path(manifest_path).read_text(encoding='utf-8'))
        required={'model_key','model_version','preprocessing_key','artifact_sha256','class_names_sha256','runtime_source_sha256'}
        if not isinstance(manifest,dict) or set(manifest)!=required:raise ValueError('Invalid deployment manifest.')
        for key in required:
            if not isinstance(manifest[key],str) or not manifest[key].strip():raise ValueError('Invalid deployment manifest.')
        if manifest['preprocessing_key']!=PREPROCESSING_KEY:raise ValueError('Unsupported preprocessing.')
        for field,path in [('artifact_sha256',root/'model/graphiscan_model.keras'),('class_names_sha256',root/'model/class_names.json'),('runtime_source_sha256',root/'predict.py')]:
            if not re.fullmatch(r'[a-f0-9]{64}',manifest[field]) or file_digest(path)!=manifest[field]:raise ValueError('Deployment artifact mismatch.')
        self.identity={k:manifest[k] for k in ('model_key','model_version','preprocessing_key','artifact_sha256')}
        self.identity['decision_rule']=RULE
    def supports(self,model):
        return (model.get('task_type')=='binary' and model.get('provenance','verified')=='verified'
            and all(model.get(k)==self.identity[k] for k in ('model_key','model_version','preprocessing_key','decision_rule')))
    def infer(self,data,model):
        if not self.supports(model) or model.get('artifact_sha256')!=self.identity['artifact_sha256']:raise BackendUnavailable()
        # Reuse runtime preprocessing/class mapping without its debug-print wrapper.
        import predict
        names=predict.load_class_names()
        if len(names)!=2 or set(names)!={'normal','high_potential'}:raise BackendUnavailable()
        with TemporaryDirectory(prefix='graphiscan-inference-') as folder:
            target=Path(folder)/'sample.png';target.write_bytes(data)
            network=predict.load_graphiscan_model()
            raw=network.predict(predict.prepare_image(str(target)),verbose=0)
            high=float(predict.get_high_potential_probability(raw))
        if not math.isfinite(high) or not 0<=high<=1:raise BackendUnavailable()
        label=predict.classify_result(high)['classification']
        return {'classification':label,'class_scores':{'normal':1-high,'high_potential':high},
                'predicted_class_score':round(high if label=='High Potential' else 1-high,5)}

class ScreeningUploadService(DirectoryService):
    def __init__(self,connect,repository,runtime=None,storage=None,**options):
        super().__init__(connect,**options)
        self.repository,self.runtime,self.storage=repository,runtime,storage
    def read_function(self,sql,params):
        try:
            with self.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql,params);row=cursor.fetchone()
        except Exception:raise BackendUnavailable() from None
        return checked_result(row)
    def catalogue(self,identity,args):
        if any(k not in {'limit','cursor'} or len(args.getlist(k))!=1 for k in args):raise invalid_query()
        limit=args.get('limit','25')
        if not re.fullmatch(r'[1-9][0-9]{0,2}',limit) or int(limit)>100:raise invalid_query()
        limit=int(limit);binding=[identity.user_id,identity.session_id,'models',limit]
        after=None
        if 'cursor' in args:_,after=self.decode_cursor(args['cursor'],binding)
        result=self.read_function('SELECT public.graphiscan_model_catalogue(%s::uuid,%s::uuid,%s::bigint,%s::integer) AS result',(identity.user_id,identity.session_id,after,limit))
        rows=result.get('rows')
        if not isinstance(rows,list):raise BackendUnavailable()
        more=len(rows)>limit;rows=rows[:limit]
        for row in rows:
            installed=bool(self.runtime and self.storage and self.repository and self.runtime.supports(row))
            row['is_selectable']=row.get('is_selectable') is True and installed
            row['is_default']=row.get('is_default') is True and row['is_selectable']
        token=self.encode_cursor(binding,'2000-01-01T00:00:00+00:00',rows[-1]['model_id']) if more else None
        return {'data':rows,'page':{'next_cursor':token}}
    def request_state(self,identity,key):
        request_key(key)
        result=self.read_function('SELECT public.graphiscan_screening_request(%s::uuid,%s::uuid,%s::text) AS result',(identity.user_id,identity.session_id,key))
        if not isinstance(result.get('data'),dict):raise BackendUnavailable()
        return {'data':result['data']}
    def upload(self,identity,form,files,key,request_id):
        request_key(key)
        if any(k not in {'student_id','model_id'} or len(form.getlist(k))!=1 for k in form) or set(files)!={'handwriting_image'} or len(files.getlist('handwriting_image'))!=1:
            raise ApiError(422,'INVALID_INPUT','Select one student, model and handwriting image.')
        student=record_id(form.get('student_id'))
        model=form.get('model_id')
        if model is not None:record_id(model)
        data=normalize_image(files['handwriting_image'].stream)
        if self.repository is None or self.runtime is None or self.storage is None:
            raise ApiError(503,'SCREENING_UNAVAILABLE','Screening uploads are temporarily unavailable.')
        payload={'student_id':student,'model_id':model,'image_sha256':hashlib.sha256(data).hexdigest()}
        from v1_models import VersionedBinaryRuntime
        runtime_identity=self.runtime.identity if not isinstance(self.runtime,VersionedBinaryRuntime) else {}
        if isinstance(self.runtime,VersionedBinaryRuntime):
            after=None
            # Reauthorization and final model/default checks still run atomically
            # inside reserve. An absent/withdrawn model can still replay a completed
            # exact request, because reserve checks durable requests first.
            for _ in range(100):
                catalogue=self.read_function('SELECT public.graphiscan_model_catalogue(%s::uuid,%s::uuid,%s::bigint,%s::integer) AS result',
                    (identity.user_id,identity.session_id,after,100))
                rows=catalogue.get('rows',[])
                selected=next((row for row in rows if (str(row['model_id'])==str(model) if model is not None else row.get('is_default') is True)),None)
                if selected:
                    runtime_identity=self.runtime.identity_for(selected)
                    break
                if len(rows)<100:break
                after=rows[-1]['model_id']
        # Reservation commits before Storage/inference. A retry that finds an
        # existing processing request must never repeat those side effects.
        reserved=checked_result(self.repository.execute('''SELECT public.graphiscan_reserve_screening(
            %s::uuid,%s::uuid,%s::jsonb,%s::text,%s::jsonb,%s::text,%s::uuid) AS result''',
            (identity.user_id,identity.session_id,json.dumps(payload),key,json.dumps(runtime_identity),self.storage.bucket,request_id)))
        if reserved.get('state')=='completed':return reserved['result_id']
        if reserved.get('state')!='reserved':
            raise ApiError(409,'REQUEST_IN_PROGRESS','Check this submission status before starting another upload.')
        try:
            self.storage.put(reserved['bucket_id'],reserved['object_key'],data)
            prediction=self.runtime.infer(data,reserved['model'])
            complete=checked_result(self.repository.execute('''SELECT public.graphiscan_complete_screening(
                %s::uuid,%s::uuid,%s::text,%s::jsonb,%s::uuid) AS result''',
                (identity.user_id,identity.session_id,key,json.dumps(prediction),request_id)))
            return record_id(complete.get('result_id'))
        except Exception:
            # A commit acknowledgement may be lost. The capability checks the
            # durable state and never queues cleanup for a completed request.
            try:self.repository.execute('SELECT public.graphiscan_fail_screening(%s::uuid,%s::text,%s::text) AS result',(identity.user_id,key,'commit_failed'))
            except Exception:pass
            raise ApiError(503,'SCREENING_RECOVERY_REQUIRED','Upload completion is uncertain. Check this submission status before uploading again.') from None
    def image(self,identity,target):
        record_id(target)
        result=self.read_function('SELECT public.graphiscan_screening_image(%s::uuid,%s::uuid,%s::bigint) AS result',(identity.user_id,identity.session_id,target))
        if self.storage is None:raise BackendUnavailable()
        location=result.get('storage_path')
        if not isinstance(location,str) or '/' not in location:raise BackendUnavailable()
        bucket,key=location.split('/',1)
        return self.storage.get(bucket,key)
