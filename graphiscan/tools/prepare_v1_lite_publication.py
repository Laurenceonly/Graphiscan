"""Prepare reviewed registry cutover/rollback SQL from verified local evidence only."""
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def prepare():
    from v1_lite_models import LiteBinaryRuntime, RESNET_CPU_KERNEL
    from v1_models import ARCHITECTURES, VersionedBinaryRuntime
    from v1_uploads import PREPROCESSING_KEY, RULE, file_digest
    runtime = LiteBinaryRuntime(ROOT / 'model/deployment.litert.local.json')
    previous = VersionedBinaryRuntime(ROOT / 'model/deployment.local.json')
    evidence = ROOT / 'api/litert-linux-evaluation.json'
    report = json.loads(evidence.read_text(encoding='utf-8'))
    original = json.loads((ROOT / 'training_results/hosted_runtime_evaluation.local.json').read_text(encoding='utf-8'))
    if (report.get('status') != 'parity-passed' or report.get('platform') != 'Linux'
            or report.get('resnet_cpu_kernel') != RESNET_CPU_KERNEL or report.get('sample_count') != 136
            or report.get('decision_threshold') != .75 or report.get('quantization') != 'none-float32'
            or report.get('score_tolerance') != .0001 or len(report.get('models', [])) != 3
            or {item['model_key'] for item in report['models']} != set(ARCHITECTURES)
            or report.get('dataset_sha256') != original['dataset_sha256']):
        raise ValueError('Require the verified Linux evaluation')
    specs = []
    for key in sorted(ARCHITECTURES):
        entry, _ = runtime.entries[key]
        prior, _ = previous.entries[key]
        row = next(item for item in report['models'] if item['model_key'] == key)
        reference = next(item for item in original['models'] if item['model'] == ARCHITECTURES[key])['thresholds']['0.75']['confusion_matrix']
        error = row.get('max_absolute_score_error')
        if (row.get('parity_passed') is not True or row['classification_disagreements'] != 0
                or type(error) not in (int, float) or not math.isfinite(error) or not 0 <= error <= .0001
                or row['source_artifact_sha256'] != prior['artifact_sha256']
                or row['converted_artifact_sha256'] != entry['artifact_sha256']
                or row['reference_confusion_matrix'] != reference or row['converted_confusion_matrix'] != reference):
            raise ValueError('Registry evidence mismatch')
        accuracy = (reference[0][0]+reference[1][1])/136
        specs.append({'model_key': key, 'architecture': ARCHITECTURES[key], 'previous_version': prior['model_version'],
                      'model_version': entry['model_version'], 'test_accuracy': float(f'{accuracy:.5f}')})
    def literal(value):
        return "'" + value.replace("'", "''") + "'"
    config = literal(json.dumps(specs, separators=(',', ':')))
    mobile = next(item for item in specs if item['model_key'] == 'mobilenetv2')
    dataset = literal('sha256:'+report['dataset_sha256'])
    evidence_ref = literal('sha256:'+file_digest(evidence))
    rule = literal(json.dumps(RULE, separators=(',', ':')))
    preprocessing = literal(PREPROCESSING_KEY)
    labels = "'[\"Normal\",\"High Potential\"]'::jsonb"
    prefix = f'''-- Optional model-data cutover, not a schema migration. No student/result rows are changed.
-- Generated from api/litert-linux-evaluation.json; preserve historical model rows.
BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
DO $catalogue$
DECLARE config jsonb := {config}::jsonb;
        spec jsonb; selected public.model_registry%ROWTYPE; evaluation bigint; matches integer;
BEGIN
PERFORM pg_advisory_xact_lock(hashtextextended('graphiscan.model-registry-publication',0));
IF NOT EXISTS(SELECT 1 FROM public.model_registry WHERE task_type='binary' AND is_default
    AND model_key='mobilenetv2' AND model_version IN ({literal(mobile['previous_version'])},{literal(mobile['model_version'])}))
OR EXISTS(SELECT 1 FROM public.model_registry WHERE task_type='binary' AND is_default
    AND (model_key<>'mobilenetv2' OR model_version NOT IN ({literal(mobile['previous_version'])},{literal(mobile['model_version'])})))
THEN RAISE EXCEPTION 'Unexpected current default; review before cutover'; END IF;
FOR spec IN SELECT value FROM jsonb_array_elements(config) LOOP
  SELECT * INTO STRICT selected FROM public.model_registry
    WHERE model_key=spec->>'model_key' AND model_version=spec->>'previous_version' FOR UPDATE;
  IF selected.architecture IS DISTINCT FROM spec->>'architecture' OR selected.task_type<>'binary'
    OR selected.test_accuracy IS DISTINCT FROM (spec->>'test_accuracy')::numeric
    OR selected.preprocessing_key IS DISTINCT FROM {preprocessing}
    OR selected.class_labels IS DISTINCT FROM {labels} OR selected.decision_rule IS DISTINCT FROM {rule}::jsonb
    OR selected.provenance<>'verified' OR NOT EXISTS(SELECT 1 FROM public.model_evaluations e
      WHERE e.evaluation_id=selected.evaluation_id AND e.task_type='binary' AND e.dataset_key='existing-binary-dataset'
      AND e.dataset_version={dataset} AND e.split_key='test-hosted-normalized-threshold-075'
      AND e.split_unit='image' AND NOT e.writer_separation_verified)
  THEN RAISE EXCEPTION 'Previous model metadata conflict'; END IF;
END LOOP;
'''
    publication = prefix + f'''SELECT count(*),min(evaluation_id) INTO matches,evaluation FROM public.model_evaluations WHERE evidence_reference={evidence_ref};
IF matches>1 THEN RAISE EXCEPTION 'Ambiguous evaluation reference'; END IF;
IF matches=0 THEN
  INSERT INTO public.model_evaluations(task_type,dataset_key,dataset_version,split_key,split_unit,writer_separation_verified,evidence_reference)
  VALUES ('binary','existing-binary-dataset',{dataset},'test-hosted-litert-fp32-builtin-resnet-threshold-075','image',false,{evidence_ref})
  RETURNING evaluation_id INTO evaluation;
END IF;
IF NOT EXISTS(SELECT 1 FROM public.model_evaluations WHERE evaluation_id=evaluation AND task_type='binary'
    AND dataset_key='existing-binary-dataset' AND dataset_version={dataset}
    AND split_key='test-hosted-litert-fp32-builtin-resnet-threshold-075' AND split_unit='image' AND NOT writer_separation_verified)
THEN RAISE EXCEPTION 'Evaluation metadata conflict'; END IF;
FOR spec IN SELECT value FROM jsonb_array_elements(config) LOOP
  INSERT INTO public.model_registry(model_key,model_version,architecture,task_type,test_accuracy,is_selectable,is_default,
      evaluation_id,preprocessing_key,class_labels,decision_rule,provenance)
  VALUES (spec->>'model_key',spec->>'model_version',spec->>'architecture','binary',(spec->>'test_accuracy')::numeric,true,false,
      evaluation,{preprocessing},{labels},{rule}::jsonb,'verified') ON CONFLICT(model_key,model_version) DO NOTHING;
  SELECT * INTO STRICT selected FROM public.model_registry
    WHERE model_key=spec->>'model_key' AND model_version=spec->>'model_version' FOR UPDATE;
  IF selected.architecture IS DISTINCT FROM spec->>'architecture' OR selected.task_type<>'binary'
    OR selected.test_accuracy IS DISTINCT FROM (spec->>'test_accuracy')::numeric OR selected.evaluation_id IS DISTINCT FROM evaluation
    OR selected.preprocessing_key IS DISTINCT FROM {preprocessing} OR selected.class_labels IS DISTINCT FROM {labels}
    OR selected.decision_rule IS DISTINCT FROM {rule}::jsonb OR selected.provenance<>'verified'
  THEN RAISE EXCEPTION 'New model metadata conflict'; END IF;
END LOOP;
'''
    def flags(activate):
        inactive = 'previous_version' if activate else 'model_version'
        active = 'model_version' if activate else 'previous_version'
        default = mobile[active]
        return f'''UPDATE public.model_registry m SET is_default=false,is_selectable=false FROM jsonb_array_elements(config) s
  WHERE m.model_key=s->>'model_key' AND m.model_version=s->>'{inactive}';
UPDATE public.model_registry m SET is_default=false,is_selectable=true FROM jsonb_array_elements(config) s
  WHERE m.model_key=s->>'model_key' AND m.model_version=s->>'{active}';
UPDATE public.model_registry SET is_default=true WHERE model_key='mobilenetv2' AND model_version={literal(default)};
END;
$catalogue$;
COMMIT;
'''
    publication += flags(True)
    rollback = prefix.replace('-- Optional model-data cutover', '-- Optional model-data rollback') + flags(False)
    for name, content in [('publish_lite_binary_models.sql', publication), ('rollback_lite_binary_models.sql', rollback)]:
        (ROOT / 'db/postgres' / name).write_text(content, encoding='utf-8')
    return {'status': 'model-cutover-sql-prepared', 'models': len(specs), 'executed': False, 'evidence_reference': 'sha256:'+file_digest(evidence)}


if __name__ == '__main__':
    try:
        print(json.dumps(prepare()))
    except Exception as failure:
        print(json.dumps({'status': 'model-cutover-sql-not-prepared', 'error_type': type(failure).__name__}))
        sys.exit(1)
