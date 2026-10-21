"""Fictional uploads/reviews: no provider, configured database or real model."""
from contextlib import contextmanager
from io import BytesIO
import json
import unittest
from unittest.mock import Mock,patch
from tempfile import TemporaryDirectory
from pathlib import Path
from types import SimpleNamespace
from flask import Flask
from PIL import Image
from werkzeug.datastructures import MultiDict
from api_v1 import AccessState, BackendUnavailable, Identity, install_api_v1
from v1_screening_writes import ScreeningWriteService, validate_write
from v1_uploads import ScreeningUploadService, normalize_image,ActiveBinaryRuntime,PREPROCESSING_KEY,RULE,MAX_BYTES
from v1_storage import PrivateS3Storage

USER='00000000-0000-4000-8000-000000000001'
SESSION='00000000-0000-4000-8000-000000000002'
KEY='fictional-upload-key-0001'
OBJECT='screenings/00000000-0000-4000-8000-000000000003.png'
def png():
    data=BytesIO();Image.new('RGB',(8,8),'white').save(data,format='PNG');return data.getvalue()

class ScreeningWritesTests(unittest.TestCase):
    def setUp(self):
        self.events=[];self.state=AccessState(USER,'Fictional','teacher','active',False,'test','test')
        self.repository=Mock();self.runtime=Mock();self.storage=Mock()
        self.runtime.identity={'model_key':'fictional'};self.storage.bucket='fictional-private'
        self.runtime.infer.side_effect=lambda *args:self.events.append('infer') or {'classification':'Normal'}
        self.storage.put.side_effect=lambda *args:self.events.append('storage')
        self.read_result={'code':None,'data':{'state':'processing','result_id':None,'error_code':None}}
        @contextmanager
        def connect():
            cursor=Mock();cursor.fetchone.side_effect=lambda:{'result':self.read_result}
            connection=Mock();connection.cursor.return_value.__enter__=Mock(return_value=cursor)
            connection.cursor.return_value.__exit__=Mock(return_value=False);yield connection
        self.service=ScreeningUploadService(connect,self.repository,self.runtime,self.storage)
        self.repository.execute.side_effect=self.execute
        self.backend=Mock();self.backend.authenticate.return_value=Identity(USER,SESSION)
        self.backend.load_access.side_effect=lambda identity:self.state
        self.backend.screening_upload_service=self.service
        self.backend.screening_write_service=ScreeningWriteService(self.repository)
        self.backend.screening_read_service.read.return_value={'data':{'result_id':'9'}}
        app=Flask(__name__);install_api_v1(app,self.backend);self.client=app.test_client()
        self.headers={'Authorization':'Bearer fictional','Idempotency-Key':KEY}
    def execute(self,sql,params):
        if 'reserve_screening' in sql:
            self.events.append('reserve');return {'result':{'code':None,'state':'reserved','bucket_id':'fictional-private','object_key':OBJECT,'model':{'model_key':'fictional'}}}
        if 'complete_screening' in sql:self.events.append('complete');return {'result':{'code':None,'result_id':'9'}}
        if 'fail_screening' in sql:self.events.append('fail');return {'result':{'code':None,'state':'failed'}}
        return {'result':{'code':None,'data':{'status':'Validated','revision':2}}}
    def upload(self,data=None,headers=None):
        return self.client.post('/api/v1/screenings',headers=self.headers if headers is None else headers,
            data=data or {'student_id':'1','handwriting_image':(BytesIO(png()),'fictional.png')},content_type='multipart/form-data')
    def test_upload_reserves_before_external_side_effects_and_returns_committed_record(self):
        response=self.upload();self.assertEqual(response.status_code,201)
        self.assertEqual(self.events,['reserve','storage','infer','complete'])
        self.assertEqual(response.headers['Location'],'/api/v1/screenings/9')
        self.assertEqual(response.headers['Cache-Control'],'no-store')
    def test_versioned_explicit_selection_and_default_pass_matching_identity_to_reserve(self):
        from v1_models import VersionedBinaryRuntime
        runtime=object.__new__(VersionedBinaryRuntime)
        entries=[{'model_key':key,'model_version':'v1','artifact_sha256':letter*64,
                  'preprocessing_key':PREPROCESSING_KEY,'decision_rule':RULE}
                 for key,letter in [('resnet50','a'),('mobilenetv2','b')]]
        runtime.entries={entry['model_key']:(entry,Path('unused')) for entry in entries}
        runtime.infer=Mock(return_value={'classification':'Normal'})
        self.service.runtime=runtime
        self.read_result={'code':None,'rows':[{**entry,'model_id':str(i+1),'task_type':'binary','is_default':i==1}
                                              for i,entry in enumerate(entries)]}
        for selected,expected in [('1',entries[0]),(None,entries[1])]:
            data={'student_id':'1','handwriting_image':(BytesIO(png()),'fictional.png')}
            if selected is not None:data['model_id']=selected
            self.assertEqual(self.upload(data).status_code,201)
            call=next(call for call in reversed(self.repository.execute.call_args_list) if 'reserve_screening' in call.args[0])
            self.assertEqual(json.loads(call.args[1][4]),expected)
    def test_versioned_completed_retry_survives_withdrawn_model_catalogue(self):
        from v1_models import VersionedBinaryRuntime
        runtime=object.__new__(VersionedBinaryRuntime);runtime.entries={};runtime.infer=Mock()
        self.service.runtime=runtime;self.read_result={'code':None,'rows':[]}
        self.repository.execute.side_effect=lambda *args:{'result':{'code':None,'state':'completed','result_id':'9'}}
        self.assertEqual(self.upload().status_code,201)
        self.storage.put.assert_not_called();runtime.infer.assert_not_called()
    def test_processing_or_completed_retry_never_repeats_storage_or_inference(self):
        for state,status in [('processing',409),('completed',201),('failed',409)]:
            self.repository.execute.side_effect=lambda *args:{'result':{'code':None,'state':state,'result_id':'9'}}
            self.assertEqual(self.upload().status_code,status)
        self.storage.put.assert_not_called();self.runtime.infer.assert_not_called()
    def test_inference_failure_queues_reconciliation_without_exposing_exception(self):
        self.runtime.infer.side_effect=RuntimeError('private provider token/path')
        response=self.upload();self.assertEqual(response.status_code,503)
        self.assertEqual(self.events,['reserve','storage','fail'])
        self.assertNotIn('private provider',response.get_data(as_text=True))
        self.storage.delete.assert_not_called()
    def test_uncertain_commit_never_deletes_an_object(self):
        def execute(sql,params):
            if 'complete_screening' in sql:raise BackendUnavailable()
            return self.execute(sql,params)
        self.repository.execute.side_effect=execute
        self.assertEqual(self.upload().json['error']['code'],'SCREENING_RECOVERY_REQUIRED')
        self.assertIn('fail',self.events);self.storage.delete.assert_not_called()
    def test_uncertain_reservation_does_not_start_external_side_effects(self):
        self.repository.execute.side_effect=BackendUnavailable()
        self.assertEqual(self.upload().status_code,503)
        self.storage.put.assert_not_called();self.runtime.infer.assert_not_called()
    def test_invalid_images_duplicate_fields_and_missing_keys_do_not_write(self):
        for data in [{'student_id':'1','handwriting_image':(BytesIO(b'not an image'),'looks-valid.png')},MultiDict([('student_id','1'),('student_id','2'),('handwriting_image',(BytesIO(png()),'a.png'))])]:
            self.assertEqual(self.upload(data).status_code,422)
        self.assertEqual(self.upload(headers={'Authorization':'Bearer fictional'}).status_code,422)
        self.repository.execute.assert_not_called()
    def test_missing_runtime_or_storage_fails_closed(self):
        self.service.runtime=None
        self.assertEqual(self.upload().json['error']['code'],'SCREENING_UNAVAILABLE')
        self.repository.execute.assert_not_called()
    def test_oversized_multipart_request_is_rejected_before_database_or_storage(self):
        response=self.client.post('/api/v1/screenings',headers=self.headers,
            data=b'x',content_type='multipart/form-data; boundary=fictional',environ_overrides={'CONTENT_LENGTH':str(MAX_BYTES+65537)})
        self.assertEqual(response.status_code,413);self.repository.execute.assert_not_called()
    def test_role_and_onboarding_checks_precede_uploads(self):
        self.assertEqual(self.upload(headers={}).status_code,401)
        self.state=AccessState(USER,'Fictional','parent','active',False,'test','test')
        self.assertEqual(self.upload().status_code,403)
        self.repository.execute.assert_not_called()
    def test_request_recovery_does_not_expose_storage_metadata(self):
        response=self.client.get('/api/v1/screening-requests/'+KEY,headers=self.headers)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['data'],self.read_result['data'])
    def test_review_requires_revision_key_author_and_optional_human_recommendation(self):
        body={'status':'Validated','remarks':' Human review ','follow_up_needed':False,'expected_revision':1}
        self.state=AccessState(USER,'Fictional','expert','active',False,'test','test')
        response=self.client.patch('/api/v1/screenings/9/review',headers=self.headers,json=body)
        self.assertEqual(response.status_code,200)
        sql,args=self.repository.execute.call_args.args
        self.assertEqual(args[:3],(USER,SESSION,'9'));self.assertEqual(json.loads(args[3])['remarks'],'Human review')
        self.repository.execute.return_value={'result':{'code':'REVISION_CONFLICT'}}
        self.repository.execute.side_effect=None
        self.assertEqual(self.client.patch('/api/v1/screenings/9/review',headers=self.headers,json=body).status_code,409)
        for change in [{'remarks':' '},{'expected_revision':True},{'follow_up_needed':'Yes'},{'expert_recommendation':''},{'expert_id':USER}]:
            with self.assertRaises(Exception):validate_write('review',{**body,**change},KEY)
    def test_failed_image_authorization_never_reads_storage(self):
        self.read_result={'code':'NOT_FOUND'}
        response=self.client.get('/api/v1/screenings/9/image',headers=self.headers)
        self.assertEqual(response.status_code,404);self.storage.get.assert_not_called()
    def test_image_download_is_binary_private_and_nosniff(self):
        self.read_result={'code':None,'storage_path':'fictional-private/'+OBJECT}
        self.storage.get.return_value=(png(),'image/png')
        response=self.client.get('/api/v1/screenings/9/image',headers=self.headers)
        self.assertEqual(response.status_code,200);self.assertEqual(response.mimetype,'image/png')
        self.assertEqual(response.headers['Cache-Control'],'no-store');self.assertEqual(response.headers['X-Content-Type-Options'],'nosniff')

class ImageBoundaryTests(unittest.TestCase):
    def test_normalization_strips_metadata_and_rejects_disguised_format(self):
        data=normalize_image(BytesIO(png()))
        with Image.open(BytesIO(data)) as image:self.assertEqual(image.mode,'RGB');self.assertEqual(image.format,'PNG');self.assertEqual(image.info,{})
        gif=BytesIO();Image.new('RGB',(2,2)).save(gif,format='GIF')
        with self.assertRaises(Exception):normalize_image(BytesIO(gif.getvalue()))
    def test_s3_adapter_prevents_bucket_path_escapes_and_bounds_download(self):
        client=Mock();storage=PrivateS3Storage('fictional-private',client)
        for bucket,key in [('other',OBJECT),('fictional-private','../secret'),('fictional-private','https://elsewhere')]:
            with self.assertRaises(BackendUnavailable):storage.get(bucket,key)
        client.get_object.assert_not_called()
        stream=Mock();stream.read.return_value=png();client.get_object.return_value={'Body':stream,'ContentType':'image/png'}
        self.assertEqual(storage.get('fictional-private',OBJECT)[1],'image/png');stream.close.assert_called_once()
    def test_runtime_rejects_changed_artifacts_and_preserves_binary_threshold(self):
        manifest={'model_key':'fictional','model_version':'v1','preprocessing_key':PREPROCESSING_KEY,
                  'artifact_sha256':'a'*64,'class_names_sha256':'a'*64,'runtime_source_sha256':'a'*64}
        with TemporaryDirectory() as folder:
            target=Path(folder)/'manifest.json';target.write_text(json.dumps(manifest),encoding='utf-8')
            with patch('v1_uploads.file_digest',return_value='b'*64):
                with self.assertRaises(ValueError):ActiveBinaryRuntime(target)
            with patch('v1_uploads.file_digest',return_value='a'*64):runtime=ActiveBinaryRuntime(target)
            model={**runtime.identity,'task_type':'binary'}
            self.assertFalse(runtime.supports({**model,'model_version':'changed'}))
            predictor=SimpleNamespace(load_class_names=lambda:['high_potential','normal'],
                load_graphiscan_model=lambda:Mock(),prepare_image=lambda path:None,
                get_high_potential_probability=lambda raw:0.6,
                classify_result=lambda high:{'classification':'High Potential' if high>=0.75 else 'Normal'})
            with patch.dict('sys.modules',{'predict':predictor}):
                result=runtime.infer(png(),model)
                self.assertEqual(result['classification'],'Normal');self.assertEqual(result['predicted_class_score'],0.4)
                self.assertEqual(result['class_scores'],{'normal':0.4,'high_potential':0.6})
                predictor.get_high_potential_probability=lambda raw:float('nan')
                with self.assertRaises(BackendUnavailable):runtime.infer(png(),model)

if __name__=='__main__':unittest.main()
