-- Change only the default among the verified, currently selectable models.
BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
DO $default$
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended('graphiscan.model-registry-publication', 0));
  IF (SELECT count(*) FROM public.model_registry WHERE task_type='binary' AND is_default
      AND (model_key, model_version) IN (('mobilenetv2','binary-3abdc7ee4b2b-litert-fp32-v1'),
                                       ('resnet50','binary-55e0844c9896-litert-fp32-v1'))) <> 1
     OR (SELECT count(*) FROM public.model_registry WHERE task_type='binary' AND is_default) <> 1
     OR NOT EXISTS (SELECT 1 FROM public.model_registry WHERE model_key='resnet50'
       AND model_version='binary-55e0844c9896-litert-fp32-v1' AND task_type='binary'
       AND is_selectable AND provenance='verified' AND test_accuracy=0.86765)
     OR EXISTS (SELECT 1 FROM public.model_registry WHERE task_type='binary' AND is_selectable
       AND (test_accuracy IS NULL OR test_accuracy > 0.86765))
  THEN RAISE EXCEPTION 'Model catalogue differs from expected selected versions'; END IF;
  UPDATE public.model_registry SET is_default=false WHERE task_type='binary' AND is_default;
  UPDATE public.model_registry SET is_default=true WHERE model_key='resnet50'
    AND model_version='binary-55e0844c9896-litert-fp32-v1';
END;
$default$;
COMMIT;
