-- Prepared from executed local binary hosted-path evaluation; inspect MODEL_EVIDENCE.md.
-- Optional data publication after 013+014, not a schema migration or account seed.
-- Image split only; writer separation is NOT verified. Existing defaults are not replaced.
BEGIN;
DO $publication$
DECLARE evaluation bigint; selected public.model_registry%ROWTYPE;
BEGIN
PERFORM pg_advisory_xact_lock(hashtextextended('graphiscan.binary.hosted-evaluation-v1',0));
SELECT evaluation_id INTO evaluation FROM public.model_evaluations WHERE evidence_reference='sha256:71184e7c2be2a5efcb36fbc28e8b3429880d4257db799579b38be9397459acd0';
IF evaluation IS NULL THEN
INSERT INTO public.model_evaluations(task_type,dataset_key,dataset_version,split_key,split_unit,writer_separation_verified,evidence_reference)
VALUES ('binary','existing-binary-dataset','sha256:29c3bb42a09a733eacc43489dcb9214d2b526aa1866e61114a93db943b744549','test-hosted-normalized-threshold-075','image',false,'sha256:71184e7c2be2a5efcb36fbc28e8b3429880d4257db799579b38be9397459acd0') RETURNING evaluation_id INTO evaluation;
END IF;
IF NOT EXISTS(SELECT 1 FROM public.model_evaluations WHERE evaluation_id=evaluation AND task_type='binary' AND dataset_key='existing-binary-dataset' AND dataset_version='sha256:29c3bb42a09a733eacc43489dcb9214d2b526aa1866e61114a93db943b744549' AND split_key='test-hosted-normalized-threshold-075' AND split_unit='image' AND NOT writer_separation_verified) THEN RAISE EXCEPTION 'Evaluation metadata conflict'; END IF;
INSERT INTO public.model_registry(model_key,model_version,architecture,task_type,test_accuracy,is_selectable,is_default,evaluation_id,preprocessing_key,class_labels,decision_rule,provenance)
VALUES ('resnet50','binary-9c6e2cd5b031-hosted-v1','ResNet50','binary',0.72794,true,false,evaluation,'graphiscan-rgb224-raw-normalized-png-v1','["Normal","High Potential"]'::jsonb,'{"kind": "high_potential_threshold", "threshold": 0.75}'::jsonb,'verified') ON CONFLICT(model_key,model_version) DO NOTHING;
SELECT * INTO STRICT selected FROM public.model_registry WHERE model_key='resnet50' AND model_version='binary-9c6e2cd5b031-hosted-v1';
IF selected.architecture<>'ResNet50' OR selected.task_type<>'binary' OR selected.test_accuracy IS DISTINCT FROM 0.72794::numeric OR selected.evaluation_id IS DISTINCT FROM evaluation OR selected.preprocessing_key IS DISTINCT FROM 'graphiscan-rgb224-raw-normalized-png-v1' OR selected.class_labels IS DISTINCT FROM '["Normal","High Potential"]'::jsonb OR selected.decision_rule IS DISTINCT FROM '{"kind": "high_potential_threshold", "threshold": 0.75}'::jsonb OR selected.provenance<>'verified' OR NOT selected.is_selectable THEN RAISE EXCEPTION 'Published model metadata conflict'; END IF;
INSERT INTO public.model_registry(model_key,model_version,architecture,task_type,test_accuracy,is_selectable,is_default,evaluation_id,preprocessing_key,class_labels,decision_rule,provenance)
VALUES ('efficientnetb0','binary-0c7951d1114c-hosted-v1','EfficientNetB0','binary',0.72794,true,false,evaluation,'graphiscan-rgb224-raw-normalized-png-v1','["Normal","High Potential"]'::jsonb,'{"kind": "high_potential_threshold", "threshold": 0.75}'::jsonb,'verified') ON CONFLICT(model_key,model_version) DO NOTHING;
SELECT * INTO STRICT selected FROM public.model_registry WHERE model_key='efficientnetb0' AND model_version='binary-0c7951d1114c-hosted-v1';
IF selected.architecture<>'EfficientNetB0' OR selected.task_type<>'binary' OR selected.test_accuracy IS DISTINCT FROM 0.72794::numeric OR selected.evaluation_id IS DISTINCT FROM evaluation OR selected.preprocessing_key IS DISTINCT FROM 'graphiscan-rgb224-raw-normalized-png-v1' OR selected.class_labels IS DISTINCT FROM '["Normal","High Potential"]'::jsonb OR selected.decision_rule IS DISTINCT FROM '{"kind": "high_potential_threshold", "threshold": 0.75}'::jsonb OR selected.provenance<>'verified' OR NOT selected.is_selectable THEN RAISE EXCEPTION 'Published model metadata conflict'; END IF;
INSERT INTO public.model_registry(model_key,model_version,architecture,task_type,test_accuracy,is_selectable,is_default,evaluation_id,preprocessing_key,class_labels,decision_rule,provenance)
VALUES ('mobilenetv2','binary-ecad77ab7de3-hosted-v1','MobileNetV2','binary',0.85294,true,false,evaluation,'graphiscan-rgb224-raw-normalized-png-v1','["Normal","High Potential"]'::jsonb,'{"kind": "high_potential_threshold", "threshold": 0.75}'::jsonb,'verified') ON CONFLICT(model_key,model_version) DO NOTHING;
SELECT * INTO STRICT selected FROM public.model_registry WHERE model_key='mobilenetv2' AND model_version='binary-ecad77ab7de3-hosted-v1';
IF selected.architecture<>'MobileNetV2' OR selected.task_type<>'binary' OR selected.test_accuracy IS DISTINCT FROM 0.85294::numeric OR selected.evaluation_id IS DISTINCT FROM evaluation OR selected.preprocessing_key IS DISTINCT FROM 'graphiscan-rgb224-raw-normalized-png-v1' OR selected.class_labels IS DISTINCT FROM '["Normal","High Potential"]'::jsonb OR selected.decision_rule IS DISTINCT FROM '{"kind": "high_potential_threshold", "threshold": 0.75}'::jsonb OR selected.provenance<>'verified' OR NOT selected.is_selectable THEN RAISE EXCEPTION 'Published model metadata conflict'; END IF;
IF EXISTS(SELECT 1 FROM public.model_registry WHERE task_type='binary' AND is_default AND (model_key<>'mobilenetv2' OR model_version<>'binary-ecad77ab7de3-hosted-v1')) THEN RAISE EXCEPTION 'Existing default requires explicit version review'; END IF;
UPDATE public.model_registry SET is_default=true WHERE model_key='mobilenetv2' AND model_version='binary-ecad77ab7de3-hosted-v1';
END;
$publication$;
COMMIT;
