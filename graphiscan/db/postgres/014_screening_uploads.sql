-- Prepared migration. Apply once after 013; no bucket/model/user records seeded.
BEGIN;
CREATE TABLE public.screening_upload_jobs (
    actor_id uuid NOT NULL, operation text NOT NULL DEFAULT 'screenings.create' CHECK(operation='screenings.create'),
    idempotency_key text NOT NULL, student_id bigint NOT NULL REFERENCES public.students(student_id),
    model_id bigint NOT NULL REFERENCES public.model_registry(model_id),
    model_snapshot jsonb NOT NULL, decision_rule jsonb NOT NULL,
    bucket_id text NOT NULL, object_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(actor_id,idempotency_key),
    FOREIGN KEY(actor_id,operation,idempotency_key) REFERENCES public.api_requests(actor_id,operation,idempotency_key)
);
ALTER TABLE public.screening_upload_jobs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.screening_upload_jobs FROM PUBLIC,anon,authenticated,service_role,
    graphiscan_api_reader,graphiscan_password_writer;

CREATE FUNCTION public.graphiscan_model_catalogue(subject_id uuid,provider_session_id uuid,
    after_id bigint,page_limit integer) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text; rows jsonb;
BEGIN
    SELECT public.graphiscan_read_directory(subject_id,provider_session_id,'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' INTO code;
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    IF page_limit IS NULL OR page_limit NOT BETWEEN 1 AND 100 OR after_id<0 THEN
        RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    SELECT coalesce(jsonb_agg(data ORDER BY id),'[]'::jsonb) INTO rows FROM (
        SELECT m.model_id AS id,jsonb_build_object('model_id',m.model_id::text,
            'model_key',CASE WHEN m.provenance='verified' THEN m.model_key END,
            'model_version',CASE WHEN m.provenance='verified' THEN m.model_version END,
            'architecture',CASE WHEN m.provenance='verified' THEN m.architecture END,
            'task_type',m.task_type,'class_labels',coalesce(m.class_labels,CASE WHEN m.task_type='binary'
                THEN '["Normal","High Potential"]'::jsonb ELSE '["Normal","Low Potential","High Potential"]'::jsonb END),
            'preprocessing_key',m.preprocessing_key,'decision_rule',m.decision_rule,'provenance',m.provenance,
            'is_selectable',m.is_selectable,'is_default',m.is_default AND NOT EXISTS(
                SELECT 1 FROM public.model_registry peer WHERE peer.task_type=m.task_type
                AND peer.evaluation_id=m.evaluation_id AND peer.is_selectable
                AND peer.provenance='verified' AND peer.test_accuracy>m.test_accuracy),
            'evaluation',CASE WHEN e.evaluation_id IS NOT NULL AND m.test_accuracy IS NOT NULL THEN jsonb_build_object(
                'evaluation_id',e.evaluation_id::text,'task_type',e.task_type,'split_key',e.split_key,
                'split_unit',e.split_unit,'writer_separation_verified',e.writer_separation_verified,
                'test_accuracy',m.test_accuracy) END) AS data
        FROM public.model_registry m LEFT JOIN public.model_evaluations e ON e.evaluation_id=m.evaluation_id
        WHERE after_id IS NULL OR m.model_id>after_id ORDER BY m.model_id LIMIT page_limit+1
    ) selected;
    RETURN jsonb_build_object('code',NULL,'rows',rows);
END;
$$;

CREATE FUNCTION public.graphiscan_reserve_screening(subject_id uuid,provider_session_id uuid,
    payload jsonb,request_key text,runtime_identity jsonb,bucket text,request uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text; st public.students%ROWTYPE; model public.model_registry%ROWTYPE;
    actor public.user_profiles%ROWTYPE; job public.screening_upload_jobs%ROWTYPE;
    previous public.api_requests%ROWTYPE; digest text; snapshot jsonb;
BEGIN
    PERFORM 1 FROM public.user_profiles WHERE user_id=subject_id FOR SHARE;
    PERFORM 1 FROM public.privacy_agreements WHERE is_current FOR SHARE;
    SELECT public.graphiscan_read_directory(subject_id,provider_session_id,'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' INTO code;
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    SELECT * INTO actor FROM public.user_profiles WHERE user_id=subject_id;
    IF actor.role<>'teacher' THEN RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    IF request IS NULL OR request_key IS NULL OR request_key !~ '^[A-Za-z0-9_-]{16,128}$'
        OR jsonb_typeof(payload) IS DISTINCT FROM 'object'
        OR NOT payload ?& ARRAY['student_id','image_sha256']
        OR payload - ARRAY['student_id','image_sha256','model_id']<>'{}'::jsonb
        OR coalesce(payload->>'student_id','') !~ '^[1-9][0-9]{0,18}$'
        OR (payload->>'student_id')::numeric>9223372036854775807
        OR coalesce(payload->>'image_sha256','') !~ '^[a-f0-9]{64}$'
        THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    SELECT * INTO st FROM public.students WHERE student_id=(payload->>'student_id')::bigint FOR SHARE;
    IF NOT FOUND OR st.teacher_id IS DISTINCT FROM subject_id THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(subject_id::text||':screenings.create:'||request_key,0));
    digest:=public.graphiscan_directory_digest(jsonb_build_object('operation','screenings.create','body',payload));
    SELECT * INTO previous FROM public.api_requests WHERE actor_id=subject_id
        AND operation='screenings.create' AND idempotency_key=request_key FOR UPDATE;
    IF FOUND THEN
        IF previous.request_digest<>digest THEN RETURN jsonb_build_object('code','IDEMPOTENCY_CONFLICT'); END IF;
        IF previous.state='completed' THEN
            IF jsonb_array_length(public.graphiscan_read_screenings(subject_id,provider_session_id,'screening','{}',NULL,NULL,1,previous.result_id,false)->'rows')=0 THEN
                RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
            RETURN jsonb_build_object('code',NULL,'state','completed','result_id',previous.result_id::text);
        END IF;
        RETURN jsonb_build_object('code',NULL,'state',previous.state,'error_code',previous.error_code);
    END IF;
    IF payload ? 'model_id' AND payload->'model_id'<>'null'::jsonb THEN
        IF coalesce(payload->>'model_id','') !~ '^[1-9][0-9]{0,18}$' OR (payload->>'model_id')::numeric>9223372036854775807 THEN
            RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
        SELECT * INTO model FROM public.model_registry WHERE model_id=(payload->>'model_id')::bigint FOR SHARE;
    ELSE
        SELECT * INTO model FROM public.model_registry WHERE task_type='binary' AND is_default FOR SHARE;
    END IF;
    IF model.model_id IS NULL OR NOT model.is_selectable OR model.provenance<>'verified'
        OR model.evaluation_id IS NULL OR model.task_type<>'binary'
        OR runtime_identity IS NULL OR runtime_identity->>'model_key' IS DISTINCT FROM model.model_key
        OR runtime_identity->>'model_version' IS DISTINCT FROM model.model_version
        OR runtime_identity->>'preprocessing_key' IS DISTINCT FROM model.preprocessing_key
        OR runtime_identity->'decision_rule' IS DISTINCT FROM model.decision_rule
        OR (payload->>'model_id' IS NULL AND EXISTS(SELECT 1 FROM public.model_registry peer
            WHERE peer.task_type=model.task_type AND peer.evaluation_id=model.evaluation_id
            AND peer.is_selectable AND peer.provenance='verified' AND peer.test_accuracy>model.test_accuracy))
        OR coalesce(runtime_identity->>'artifact_sha256','') !~ '^[a-f0-9]{64}$'
        THEN RETURN jsonb_build_object('code','MODEL_UNAVAILABLE'); END IF;
    -- Use the Storage API/UI to create the bucket, not direct object-table writes.
    IF bucket IS NULL OR bucket !~ '^[a-z0-9][a-z0-9_-]{0,62}$' OR NOT EXISTS (
        SELECT 1 FROM storage.buckets b WHERE b.id=bucket AND b.public=false
    ) THEN RETURN jsonb_build_object('code','STORAGE_UNAVAILABLE'); END IF;
    snapshot:=jsonb_build_object('model_id',model.model_id::text,'model_key',model.model_key,
        'model_version',model.model_version,'architecture',model.architecture,'task_type',model.task_type,
        'class_labels',model.class_labels,'preprocessing_key',model.preprocessing_key,
        'decision_rule',model.decision_rule,'artifact_sha256',runtime_identity->>'artifact_sha256');
    INSERT INTO public.api_requests(actor_id,operation,idempotency_key,request_digest,state)
        VALUES(subject_id,'screenings.create',request_key,digest,'processing');
    INSERT INTO public.screening_upload_jobs(actor_id,idempotency_key,student_id,model_id,model_snapshot,decision_rule,bucket_id,object_key)
        VALUES(subject_id,request_key,st.student_id,model.model_id,snapshot,model.decision_rule,bucket,'screenings/'||gen_random_uuid()::text||'.png') RETURNING * INTO job;
    RETURN jsonb_build_object('code',NULL,'state','reserved','model',snapshot,'bucket_id',job.bucket_id,'object_key',job.object_key);
END;
$$;

CREATE FUNCTION public.graphiscan_complete_screening(subject_id uuid,provider_session_id uuid,
    request_key text,prediction jsonb,request uuid) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text; st public.students%ROWTYPE; job public.screening_upload_jobs%ROWTYPE;
    previous public.api_requests%ROWTYPE; model public.model_registry%ROWTYPE;
    sample bigint; result bigint; kind text; school_name text;
BEGIN
    PERFORM 1 FROM public.user_profiles WHERE user_id=subject_id FOR SHARE;
    PERFORM 1 FROM public.privacy_agreements WHERE is_current FOR SHARE;
    SELECT public.graphiscan_read_directory(subject_id,provider_session_id,'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' INTO code;
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    IF NOT EXISTS(SELECT 1 FROM public.user_profiles WHERE user_id=subject_id AND role='teacher') THEN
        RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(subject_id::text||':screenings.create:'||request_key,0));
    SELECT * INTO previous FROM public.api_requests WHERE actor_id=subject_id
        AND operation='screenings.create' AND idempotency_key=request_key FOR UPDATE;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    SELECT * INTO job FROM public.screening_upload_jobs WHERE actor_id=subject_id AND idempotency_key=request_key;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    -- Lock the authoritative student before counting completed reports. This
    -- serializes two different request keys completing for the same student.
    SELECT * INTO st FROM public.students WHERE student_id=job.student_id FOR UPDATE;
    IF st.teacher_id IS DISTINCT FROM subject_id THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    IF previous.state='completed' THEN RETURN jsonb_build_object('code',NULL,'result_id',previous.result_id::text); END IF;
    IF previous.state<>'processing' THEN RETURN jsonb_build_object('code','REQUEST_IN_PROGRESS'); END IF;
    SELECT * INTO model FROM public.model_registry WHERE model_id=job.model_id FOR SHARE;
    IF NOT model.is_selectable OR model.provenance<>'verified' OR
        jsonb_build_object('model_id',model.model_id::text,'model_key',model.model_key,
            'model_version',model.model_version,'architecture',model.architecture,'task_type',model.task_type,
            'class_labels',model.class_labels,'preprocessing_key',model.preprocessing_key,'decision_rule',model.decision_rule)
        IS DISTINCT FROM (job.model_snapshot-'artifact_sha256')
        THEN RETURN jsonb_build_object('code','MODEL_UNAVAILABLE'); END IF;
    IF NOT EXISTS(SELECT 1 FROM storage.buckets b WHERE b.id=job.bucket_id AND b.public=false) THEN
        RETURN jsonb_build_object('code','STORAGE_UNAVAILABLE'); END IF;
    IF request IS NULL OR jsonb_typeof(prediction) IS DISTINCT FROM 'object'
        OR NOT prediction ?& ARRAY['classification','class_scores','predicted_class_score']
        OR prediction - ARRAY['classification','class_scores','predicted_class_score']<>'{}'::jsonb
        OR prediction->>'classification' NOT IN ('Normal','High Potential')
        OR NOT public.valid_class_scores(prediction->'class_scores','binary')
        OR prediction->'class_scores'='null'::jsonb
        OR jsonb_typeof(prediction->'predicted_class_score') IS DISTINCT FROM 'number'
        THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    IF (job.decision_rule->>'kind')<>'high_potential_threshold' OR
        prediction->>'classification' IS DISTINCT FROM (CASE
            WHEN (prediction->'class_scores'->>'high_potential')::numeric >= (job.decision_rule->>'threshold')::numeric
            THEN 'High Potential' ELSE 'Normal' END) THEN
        RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    INSERT INTO public.handwriting_samples(student_id,teacher_id,storage_path)
        VALUES(st.student_id,subject_id,job.bucket_id||'/'||job.object_key) RETURNING sample_id INTO sample;
    INSERT INTO public.screening_results(sample_id,model_id,task_type,classification,class_probabilities,
        confidence_score,model_snapshot,decision_rule,provenance)
        VALUES(sample,job.model_id,'binary',prediction->>'classification',prediction->'class_scores',
            (prediction->>'predicted_class_score')::numeric,job.model_snapshot,job.decision_rule,'verified') RETURNING result_id INTO result;
    INSERT INTO public.expert_validations(result_id,status,provenance) VALUES(result,'Pending','verified');
    kind:=CASE WHEN EXISTS(SELECT 1 FROM public.screening_reports WHERE student_id=st.student_id)
        THEN 'Follow-up Screening' ELSE 'Initial Screening' END;
    SELECT name INTO school_name FROM public.schools WHERE school_id=st.school_id FOR SHARE;
    INSERT INTO public.screening_reports(student_id,result_id,report_type,school_context)
        VALUES(st.student_id,result,kind,jsonb_build_object('school_id',st.school_id::text,'school_name',school_name,'grade_level',st.grade_level));
    UPDATE public.api_requests SET state='completed',result_id=result,resource_type='screening',resource_id=result::text,updated_at=clock_timestamp()
        WHERE actor_id=subject_id AND operation='screenings.create' AND idempotency_key=request_key;
    INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
        VALUES(subject_id,'screenings.create','screening',result::text,request::text);
    RETURN jsonb_build_object('code',NULL,'result_id',result::text);
END;
$$;

-- A failed or uncertain external operation cannot delete a completed image.
-- Cleanup intent remains durable, even if provider deletion is unavailable.
CREATE FUNCTION public.graphiscan_fail_screening(subject_id uuid,request_key text,reason text)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE previous public.api_requests%ROWTYPE; job public.screening_upload_jobs%ROWTYPE;
BEGIN
    PERFORM pg_advisory_xact_lock(hashtextextended(subject_id::text||':screenings.create:'||request_key,0));
    SELECT * INTO previous FROM public.api_requests WHERE actor_id=subject_id AND operation='screenings.create'
        AND idempotency_key=request_key FOR UPDATE;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    IF previous.state='completed' THEN RETURN jsonb_build_object('code',NULL,'state','completed'); END IF;
    IF previous.state='processing' THEN
        SELECT * INTO job FROM public.screening_upload_jobs WHERE actor_id=subject_id AND idempotency_key=request_key;
        UPDATE public.api_requests SET state='failed',error_code='SCREENING_FAILED',updated_at=clock_timestamp()
            WHERE actor_id=subject_id AND operation='screenings.create' AND idempotency_key=request_key;
        INSERT INTO public.storage_cleanup_jobs(storage_path,reason)
            VALUES(job.bucket_id||'/'||job.object_key,CASE WHEN reason='upload_failed' THEN 'upload_failed' ELSE 'commit_failed' END);
    END IF;
    RETURN jsonb_build_object('code',NULL,'state','failed');
END;
$$;

CREATE FUNCTION public.graphiscan_screening_request(subject_id uuid,provider_session_id uuid,request_key text)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text; previous public.api_requests%ROWTYPE; job public.screening_upload_jobs%ROWTYPE;
BEGIN
    SELECT public.graphiscan_read_directory(subject_id,provider_session_id,'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' INTO code;
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    IF NOT EXISTS(SELECT 1 FROM public.user_profiles WHERE user_id=subject_id AND role='teacher') THEN
        RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    SELECT * INTO previous FROM public.api_requests WHERE actor_id=subject_id AND operation='screenings.create' AND idempotency_key=request_key;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    SELECT * INTO job FROM public.screening_upload_jobs WHERE actor_id=subject_id AND idempotency_key=request_key;
    IF NOT EXISTS(SELECT 1 FROM public.students WHERE student_id=job.student_id AND teacher_id=subject_id) THEN
        RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    IF previous.state='completed' AND jsonb_array_length(public.graphiscan_read_screenings(
        subject_id,provider_session_id,'screening','{}',NULL,NULL,1,previous.result_id,false)->'rows')=0 THEN
        RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    RETURN jsonb_build_object('code',NULL,'data',jsonb_build_object('state',previous.state,
        'result_id',previous.result_id::text,'error_code',previous.error_code));
END;
$$;

CREATE FUNCTION public.graphiscan_screening_image(subject_id uuid,provider_session_id uuid,target_id bigint)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE result jsonb; location text;
BEGIN
    result:=public.graphiscan_read_screenings(subject_id,provider_session_id,'screening','{}',NULL,NULL,1,target_id,false);
    IF result->>'code' IS NOT NULL THEN RETURN jsonb_build_object('code',result->>'code'); END IF;
    IF jsonb_array_length(result->'rows')=0 THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    SELECT h.storage_path INTO location FROM public.handwriting_samples h JOIN public.screening_results r ON r.sample_id=h.sample_id WHERE r.result_id=target_id;
    IF NOT EXISTS(SELECT 1 FROM storage.buckets b WHERE b.id=split_part(location,'/',1) AND b.public=false) THEN
        RETURN jsonb_build_object('code','STORAGE_UNAVAILABLE'); END IF;
    RETURN jsonb_build_object('code',NULL,'storage_path',location);
END;
$$;

CREATE FUNCTION public.graphiscan_screening_cleanup(mode text,target_id bigint,successful boolean)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE item record; job public.storage_cleanup_jobs%ROWTYPE; rows jsonb;
BEGIN
    IF mode='list' THEN
        -- Expire abandoned work before cleanup. All finalization paths take the
        -- same advisory lock and refuse a failed request; no official row can
        -- be created later for an expired request, even by a slow old worker.
        FOR item IN SELECT j.* FROM public.screening_upload_jobs j JOIN public.api_requests r
            ON r.actor_id=j.actor_id AND r.operation=j.operation AND r.idempotency_key=j.idempotency_key
            WHERE r.state='processing' AND j.created_at<clock_timestamp()-interval '20 minutes'
            ORDER BY j.created_at LIMIT 25
        LOOP
            IF pg_try_advisory_xact_lock(hashtextextended(item.actor_id::text||':screenings.create:'||item.idempotency_key,0)) THEN
                UPDATE public.api_requests SET state='failed',error_code='SCREENING_EXPIRED',updated_at=clock_timestamp()
                    WHERE actor_id=item.actor_id AND operation='screenings.create' AND idempotency_key=item.idempotency_key AND state='processing';
                IF FOUND THEN INSERT INTO public.storage_cleanup_jobs(storage_path,reason)
                    VALUES(item.bucket_id||'/'||item.object_key,'commit_failed'); END IF;
            END IF;
        END LOOP;
        SELECT coalesce(jsonb_agg(jsonb_build_object('cleanup_id',cleanup_id::text,'storage_path',storage_path)),'[]') INTO rows FROM (
            SELECT c.* FROM public.storage_cleanup_jobs c WHERE c.next_attempt_at<=clock_timestamp()
                AND NOT EXISTS(SELECT 1 FROM public.handwriting_samples h WHERE h.storage_path=c.storage_path)
                AND EXISTS(SELECT 1 FROM public.screening_upload_jobs j JOIN public.api_requests r
                    ON r.actor_id=j.actor_id AND r.operation=j.operation AND r.idempotency_key=j.idempotency_key
                    WHERE r.state='failed' AND j.bucket_id||'/'||j.object_key=c.storage_path)
            ORDER BY c.cleanup_id LIMIT 25
        ) selected;
        RETURN jsonb_build_object('code',NULL,'rows',rows);
    ELSIF mode='ack' AND successful IS NOT NULL THEN
        SELECT * INTO job FROM public.storage_cleanup_jobs WHERE cleanup_id=target_id FOR UPDATE;
        IF FOUND AND NOT EXISTS(SELECT 1 FROM public.handwriting_samples WHERE storage_path=job.storage_path)
            AND EXISTS(SELECT 1 FROM public.screening_upload_jobs j JOIN public.api_requests r
                ON r.actor_id=j.actor_id AND r.operation=j.operation AND r.idempotency_key=j.idempotency_key
                WHERE r.state='failed' AND j.bucket_id||'/'||j.object_key=job.storage_path) THEN
            IF successful THEN DELETE FROM public.storage_cleanup_jobs WHERE cleanup_id=target_id;
            ELSE UPDATE public.storage_cleanup_jobs SET attempts=attempts+1,last_error_code='PROVIDER_UNAVAILABLE',next_attempt_at=clock_timestamp()+interval '1 hour' WHERE cleanup_id=target_id; END IF;
        END IF;
        RETURN jsonb_build_object('code',NULL);
    END IF;
    RETURN jsonb_build_object('code','INVALID_INPUT');
END;
$$;

REVOKE ALL ON FUNCTION public.graphiscan_screening_cleanup(text,bigint,boolean)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader;
GRANT EXECUTE ON FUNCTION public.graphiscan_screening_cleanup(text,bigint,boolean) TO graphiscan_password_writer;

REVOKE ALL ON FUNCTION public.graphiscan_model_catalogue(uuid,uuid,bigint,integer),
    public.graphiscan_screening_request(uuid,uuid,text),public.graphiscan_screening_image(uuid,uuid,bigint)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_password_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_model_catalogue(uuid,uuid,bigint,integer),
    public.graphiscan_screening_request(uuid,uuid,text),public.graphiscan_screening_image(uuid,uuid,bigint) TO graphiscan_api_reader;
REVOKE ALL ON FUNCTION public.graphiscan_reserve_screening(uuid,uuid,jsonb,text,jsonb,text,uuid),
    public.graphiscan_complete_screening(uuid,uuid,text,jsonb,uuid),public.graphiscan_fail_screening(uuid,text,text)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader;
GRANT EXECUTE ON FUNCTION public.graphiscan_reserve_screening(uuid,uuid,jsonb,text,jsonb,text,uuid),
    public.graphiscan_complete_screening(uuid,uuid,text,jsonb,uuid),public.graphiscan_fail_screening(uuid,text,text) TO graphiscan_password_writer;
COMMIT;
