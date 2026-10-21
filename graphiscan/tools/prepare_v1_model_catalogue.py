"""Stage evaluated local binary artifacts and prepare reviewed registry SQL; never connects."""
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v1_models import ARCHITECTURES
from v1_uploads import PREPROCESSING_KEY,RULE,file_digest


def prepare():
    evidence=ROOT/'training_results/hosted_runtime_evaluation.local.json'
    report=json.loads(evidence.read_text(encoding='utf-8'))
    if report['status']!='evaluation-complete' or report['preprocessing_key']!=PREPROCESSING_KEY:
        raise ValueError('Missing evaluated preprocessing')
    for field,path in [('runtime_source_sha256','predict.py'),('class_names_sha256','model/class_names.json')]:
        if report[field]!=file_digest(ROOT/path):raise ValueError('Evaluation source mismatch')
    if report['class_counts']!={'normal':70,'high_potential':66} or report['matrix_order']!=['normal','high_potential']:
        raise ValueError('Unexpected evaluated split')
    models=report['models']
    if len(models)!=3 or {m['model'] for m in models}!=set(ARCHITECTURES.values()):raise ValueError('Missing comparison')
    manifest={'schema_version':2,'runtime_source_sha256':file_digest(ROOT/'predict.py'),
        'normalizer_source_sha256':file_digest(ROOT/'v1_uploads.py'),
        'adapter_source_sha256':file_digest(ROOT/'v1_models.py'),
        'class_names_sha256':file_digest(ROOT/'model/class_names.json'),'models':[]}
    entries=[]
    for key,name in ARCHITECTURES.items():
        model=next(m for m in models if m['model']==name)
        artifact=ROOT/'training_results/models'/f'{name}_best.keras'
        digest=file_digest(artifact)
        if digest!=model['artifact_sha256']:raise ValueError('Evaluation artifact mismatch')
        measured=model['thresholds']['0.75']; matrix=measured['confusion_matrix']
        if len(matrix)!=2 or any(len(r)!=2 for r in matrix) or any(type(v) is not int or v<0 for r in matrix for v in r):
            raise ValueError('Invalid matrix')
        if [sum(r) for r in matrix]!=[70,66] or measured['sample_count']!=136:
            raise ValueError('Invalid evaluated counts')
        accuracy=(matrix[0][0]+matrix[1][1])/136
        if abs(accuracy-measured['accuracy'])>1e-12:raise ValueError('Invalid accuracy')
        entry={'model_key':key,'model_version':'binary-'+digest[:12]+'-hosted-v1',
            'artifact_sha256':digest,'preprocessing_key':PREPROCESSING_KEY,'decision_rule':RULE}
        manifest['models'].append(entry)
        entries.append((entry,name,accuracy,artifact))
    best=max(entries,key=lambda item:item[2])
    if sum(item[2]==best[2] for item in entries)!=1:raise ValueError('Default choice required for tie')
    evidence_reference='sha256:'+file_digest(evidence)
    dataset_version='sha256:'+report['dataset_sha256']
    # All interpolated strings are generated identifiers/hashes, never configuration,
    # user names, credentials, paths or raw model result text.
    def literal(value):return "'"+value.replace("'","''")+"'"
    sql=["-- Prepared from executed local binary hosted-path evaluation; inspect MODEL_EVIDENCE.md.",
        "-- Optional data publication after 013+014, not a schema migration or account seed.",
        "-- Image split only; writer separation is NOT verified. Existing defaults are not replaced.",
        "BEGIN;", "DO $publication$", "DECLARE evaluation bigint; selected public.model_registry%ROWTYPE;", "BEGIN",
        "PERFORM pg_advisory_xact_lock(hashtextextended('graphiscan.binary.hosted-evaluation-v1',0));",
        f"SELECT evaluation_id INTO evaluation FROM public.model_evaluations WHERE evidence_reference={literal(evidence_reference)};",
        "IF evaluation IS NULL THEN",
        "INSERT INTO public.model_evaluations(task_type,dataset_key,dataset_version,split_key,split_unit,writer_separation_verified,evidence_reference)",
        f"VALUES ('binary','existing-binary-dataset',{literal(dataset_version)},'test-hosted-normalized-threshold-075','image',false,{literal(evidence_reference)}) RETURNING evaluation_id INTO evaluation;",
        "END IF;",
        f"IF NOT EXISTS(SELECT 1 FROM public.model_evaluations WHERE evaluation_id=evaluation AND task_type='binary' AND dataset_key='existing-binary-dataset' AND dataset_version={literal(dataset_version)} AND split_key='test-hosted-normalized-threshold-075' AND split_unit='image' AND NOT writer_separation_verified) THEN RAISE EXCEPTION 'Evaluation metadata conflict'; END IF;"]
    for entry,name,accuracy,_ in entries:
        key,version=literal(entry['model_key']),literal(entry['model_version'])
        accuracy_sql=f'{accuracy:.5f}'
        sql += ["INSERT INTO public.model_registry(model_key,model_version,architecture,task_type,test_accuracy,is_selectable,is_default,evaluation_id,preprocessing_key,class_labels,decision_rule,provenance)",
            f"VALUES ({key},{version},{literal(name)},'binary',{accuracy_sql},true,false,evaluation,{literal(PREPROCESSING_KEY)},'[\"Normal\",\"High Potential\"]'::jsonb,'{json.dumps(RULE)}'::jsonb,'verified') ON CONFLICT(model_key,model_version) DO NOTHING;",
            f"SELECT * INTO STRICT selected FROM public.model_registry WHERE model_key={key} AND model_version={version};",
            f"IF selected.architecture<>{literal(name)} OR selected.task_type<>'binary' OR selected.test_accuracy IS DISTINCT FROM {accuracy_sql}::numeric OR selected.evaluation_id IS DISTINCT FROM evaluation OR selected.preprocessing_key IS DISTINCT FROM {literal(PREPROCESSING_KEY)} OR selected.class_labels IS DISTINCT FROM '[\"Normal\",\"High Potential\"]'::jsonb OR selected.decision_rule IS DISTINCT FROM '{json.dumps(RULE)}'::jsonb OR selected.provenance<>'verified' OR NOT selected.is_selectable THEN RAISE EXCEPTION 'Published model metadata conflict'; END IF;"]
    default=best[0]
    sql += [f"IF EXISTS(SELECT 1 FROM public.model_registry WHERE task_type='binary' AND is_default AND (model_key<>{literal(default['model_key'])} OR model_version<>{literal(default['model_version'])})) THEN RAISE EXCEPTION 'Existing default requires explicit version review'; END IF;",
        f"UPDATE public.model_registry SET is_default=true WHERE model_key={literal(default['model_key'])} AND model_version={literal(default['model_version'])};",
        "END;", "$publication$;", "COMMIT;", ""]
    destination=ROOT/'model/deployment.local.json'
    serialized=json.dumps(manifest,indent=2)+'\n'
    if destination.exists() and destination.read_text(encoding='utf-8')!=serialized:
        raise ValueError('Existing manifest differs; review before replacement')
    versions=ROOT/'model/versions';versions.mkdir(exist_ok=True)
    for entry,_,_,source in entries:
        target=versions/f"{entry['model_key']}-{entry['artifact_sha256']}.keras"
        if target.exists():
            if file_digest(target)!=entry['artifact_sha256']:raise ValueError('Existing staged artifact differs')
        else:
            shutil.copyfile(source,target)
            if file_digest(target)!=entry['artifact_sha256']:raise ValueError('Staged artifact mismatch')
    destination.write_text(serialized,encoding='utf-8')
    publication=ROOT/'db/postgres/publish_binary_models.sql'
    publication.write_text('\n'.join(sql),encoding='utf-8')
    from v1_models import VersionedBinaryRuntime
    runtime=VersionedBinaryRuntime(destination)
    from dotenv import set_key
    set_key(str(ROOT/'.env'),'GRAPHISCAN_V1_MODEL_MANIFEST',destination.as_posix())
    print(json.dumps({'status':'model-catalogue-prepared','installed_models':len(runtime.entries),
        'prepared_default':default['model_key'],'publication_sql':'db/postgres/publish_binary_models.sql',
        'database_changed':False,'legacy_artifact_changed':False}))


if __name__=='__main__':
    try:prepare()
    except Exception:
        print(json.dumps({'status':'model-catalogue-not-confirmed','private_error_omitted':True}));sys.exit(1)
