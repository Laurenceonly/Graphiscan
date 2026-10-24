-- Optional model-data rollback, not a schema migration. No student/result rows are changed.
-- Generated from api/litert-linux-evaluation.json; preserve historical model rows.
BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
DO $catalogue$
DECLARE config jsonb := '[{"model_key":"efficientnetb0","architecture":"EfficientNetB0","previous_version":"binary-0c7951d1114c-hosted-v1","model_version":"binary-bdc6e8dd7006-litert-fp32-v1","test_accuracy":0.72794},{"model_key":"mobilenetv2","architecture":"MobileNetV2","previous_version":"binary-ecad77ab7de3-hosted-v1","model_version":"binary-3abdc7ee4b2b-litert-fp32-v1","test_accuracy":0.85294},{"model_key":"resnet50","architecture":"ResNet50","previous_version":"binary-9c6e2cd5b031-hosted-v1","model_version":"binary-e141366a992c-litert-fp32-v1","test_accuracy":0.72794}]'::jsonb;
        spec jsonb; selected public.model_registry%ROWTYPE; evaluation bigint; matches integer;
BEGIN
PERFORM pg_advisory_xact_lock(hashtextextended('graphiscan.model-registry-publication',0));
IF NOT EXISTS(SELECT 1 FROM public.model_registry WHERE task_type='binary' AND is_default
    AND model_key='mobilenetv2' AND model_version IN ('binary-ecad77ab7de3-hosted-v1','binary-3abdc7ee4b2b-litert-fp32-v1'))
OR EXISTS(SELECT 1 FROM public.model_registry WHERE task_type='binary' AND is_default
    AND (model_key<>'mobilenetv2' OR model_version NOT IN ('binary-ecad77ab7de3-hosted-v1','binary-3abdc7ee4b2b-litert-fp32-v1')))
THEN RAISE EXCEPTION 'Unexpected current default; review before cutover'; END IF;
FOR spec IN SELECT value FROM jsonb_array_elements(config) LOOP
  SELECT * INTO STRICT selected FROM public.model_registry
    WHERE model_key=spec->>'model_key' AND model_version=spec->>'previous_version' FOR UPDATE;
  IF selected.architecture IS DISTINCT FROM spec->>'architecture' OR selected.task_type<>'binary'
    OR selected.test_accuracy IS DISTINCT FROM (spec->>'test_accuracy')::numeric
    OR selected.preprocessing_key IS DISTINCT FROM 'graphiscan-rgb224-raw-normalized-png-v1'
    OR selected.class_labels IS DISTINCT FROM '["Normal","High Potential"]'::jsonb OR selected.decision_rule IS DISTINCT FROM '{"kind":"high_potential_threshold","threshold":0.75}'::jsonb
    OR selected.provenance<>'verified' OR NOT EXISTS(SELECT 1 FROM public.model_evaluations e
      WHERE e.evaluation_id=selected.evaluation_id AND e.task_type='binary' AND e.dataset_key='existing-binary-dataset'
      AND e.dataset_version='sha256:29c3bb42a09a733eacc43489dcb9214d2b526aa1866e61114a93db943b744549' AND e.split_key='test-hosted-normalized-threshold-075'
      AND e.split_unit='image' AND NOT e.writer_separation_verified)
  THEN RAISE EXCEPTION 'Previous model metadata conflict'; END IF;
END LOOP;
UPDATE public.model_registry m SET is_default=false,is_selectable=false FROM jsonb_array_elements(config) s
  WHERE m.model_key=s->>'model_key' AND m.model_version=s->>'model_version';
UPDATE public.model_registry m SET is_default=false,is_selectable=true FROM jsonb_array_elements(config) s
  WHERE m.model_key=s->>'model_key' AND m.model_version=s->>'previous_version';
UPDATE public.model_registry SET is_default=true WHERE model_key='mobilenetv2' AND model_version='binary-ecad77ab7de3-hosted-v1';
END;
$catalogue$;
COMMIT;
