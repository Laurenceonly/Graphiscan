-- Prepared migration. Apply once after 001-012 as reviewed schema owner.
-- No accounts, grants to users, records, buckets or model defaults are seeded.
BEGIN;

CREATE FUNCTION public.graphiscan_write_review(
    subject_id uuid, provider_session_id uuid, target_id bigint,
    payload jsonb, request_key text, request uuid
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text; actor public.user_profiles%ROWTYPE; st public.students%ROWTYPE;
    result public.screening_results%ROWTYPE; review public.expert_validations%ROWTYPE;
    existing public.api_requests%ROWTYPE; digest text; assigned uuid;
BEGIN
    PERFORM 1 FROM public.user_profiles WHERE user_id=subject_id FOR SHARE;
    PERFORM 1 FROM public.privacy_agreements WHERE is_current FOR SHARE;
    SELECT public.graphiscan_read_directory(subject_id,provider_session_id,'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' INTO code;
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    SELECT * INTO actor FROM public.user_profiles WHERE user_id=subject_id;
    IF actor.role<>'expert' THEN RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    IF target_id IS NULL OR target_id<=0 OR request IS NULL
        OR request_key IS NULL OR request_key !~ '^[A-Za-z0-9_-]{16,128}$'
        OR jsonb_typeof(payload) IS DISTINCT FROM 'object'
        OR NOT payload ?& ARRAY['status','remarks','follow_up_needed','expected_revision']
        OR payload - ARRAY['status','remarks','expert_recommendation','follow_up_needed','expected_revision'] <> '{}'::jsonb
        OR payload->>'status' NOT IN ('Validated','Flagged')
        OR jsonb_typeof(payload->'remarks') IS DISTINCT FROM 'string'
        OR length(btrim(payload->>'remarks')) NOT BETWEEN 1 AND 10000
        OR jsonb_typeof(payload->'follow_up_needed') IS DISTINCT FROM 'boolean'
        OR jsonb_typeof(payload->'expected_revision') IS DISTINCT FROM 'number'
        OR coalesce(payload->>'expected_revision','') !~ '^[1-9][0-9]{0,18}$'
        OR (payload->>'expected_revision')::numeric>9223372036854775806
        OR (payload ? 'expert_recommendation' AND payload->'expert_recommendation'<>'null'::jsonb AND
            (jsonb_typeof(payload->'expert_recommendation') IS DISTINCT FROM 'string'
             OR length(btrim(payload->>'expert_recommendation')) NOT BETWEEN 1 AND 10000))
        THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(subject_id::text||':review:'||request_key,0));
    SELECT * INTO result FROM public.screening_results WHERE result_id=target_id FOR UPDATE;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    SELECT s.* INTO st FROM public.students s JOIN public.handwriting_samples h ON h.student_id=s.student_id
        WHERE h.sample_id=result.sample_id FOR SHARE OF s;
    SELECT assigned_expert_id INTO assigned FROM public.screening_expert_assignments WHERE result_id=target_id;
    IF assigned IS DISTINCT FROM subject_id THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    SELECT * INTO review FROM public.expert_validations WHERE result_id=target_id FOR UPDATE;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    digest:=public.graphiscan_directory_digest(jsonb_build_object('operation','screenings.review','result_id',target_id,'body',payload));
    SELECT * INTO existing FROM public.api_requests WHERE actor_id=subject_id
        AND operation='screenings.review' AND idempotency_key=request_key FOR UPDATE;
    IF FOUND THEN
        IF existing.request_digest<>digest THEN RETURN jsonb_build_object('code','IDEMPOTENCY_CONFLICT'); END IF;
        IF existing.state<>'completed' THEN RETURN jsonb_build_object('code','REQUEST_IN_PROGRESS'); END IF;
        IF review.revision<>(payload->>'expected_revision')::bigint+1 THEN
            RETURN jsonb_build_object('code','REVISION_CONFLICT'); END IF;
    ELSE
        IF review.revision<>(payload->>'expected_revision')::bigint THEN
            RETURN jsonb_build_object('code','REVISION_CONFLICT'); END IF;
        UPDATE public.expert_validations SET status=payload->>'status',expert_id=subject_id,
            remarks=btrim(payload->>'remarks'),expert_recommendation=btrim(payload->>'expert_recommendation'),
            follow_up_needed=(payload->>'follow_up_needed')::boolean,
            validation_date=clock_timestamp(),provenance='verified' WHERE result_id=target_id;
        INSERT INTO public.api_requests(actor_id,operation,idempotency_key,request_digest,state,resource_type,resource_id)
            VALUES(subject_id,'screenings.review',request_key,digest,'completed','review',target_id::text);
        INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
            VALUES(subject_id,'screenings.review','screening',target_id::text,request::text);
    END IF;
    RETURN jsonb_build_object('code',NULL,'data',public.graphiscan_read_screenings(
        subject_id,provider_session_id,'screening','{}',NULL,NULL,1,target_id,false)->'rows'->0->'review');
END;
$$;

CREATE FUNCTION public.graphiscan_assign_expert(
    subject_id uuid, provider_session_id uuid, target_id bigint, payload jsonb, request uuid
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text; actor public.user_profiles%ROWTYPE; st public.students%ROWTYPE;
    result public.screening_results%ROWTYPE; candidate uuid; old_candidate uuid;
BEGIN
    IF jsonb_typeof(payload) IS DISTINCT FROM 'object' OR request IS NULL
        OR NOT payload ?& ARRAY['assigned_expert_id','expected_revision']
        OR payload - ARRAY['assigned_expert_id','expected_revision']<>'{}'::jsonb
        OR (payload->'assigned_expert_id'<>'null'::jsonb AND
            (jsonb_typeof(payload->'assigned_expert_id') IS DISTINCT FROM 'string' OR
             payload->>'assigned_expert_id' !~ '^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$'))
        OR jsonb_typeof(payload->'expected_revision') IS DISTINCT FROM 'number'
        OR coalesce(payload->>'expected_revision','') !~ '^[1-9][0-9]{0,18}$'
        OR (payload->>'expected_revision')::numeric>9223372036854775807
        THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    candidate:=(payload->>'assigned_expert_id')::uuid;
    PERFORM 1 FROM public.user_profiles WHERE user_id=subject_id OR user_id=candidate ORDER BY user_id FOR SHARE;
    PERFORM 1 FROM public.privacy_agreements WHERE is_current FOR SHARE;
    SELECT public.graphiscan_read_directory(subject_id,provider_session_id,'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' INTO code;
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    SELECT * INTO actor FROM public.user_profiles WHERE user_id=subject_id;
    IF actor.role NOT IN ('admin','researcher') THEN RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    SELECT * INTO result FROM public.screening_results WHERE result_id=target_id FOR UPDATE;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    SELECT s.* INTO st FROM public.students s JOIN public.handwriting_samples h ON h.student_id=s.student_id
        WHERE h.sample_id=result.sample_id FOR SHARE OF s;
    IF NOT public.graphiscan_directory_grant(subject_id,'assignments.manage',st.school_id) THEN
        RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    IF result.revision<>(payload->>'expected_revision')::bigint THEN RETURN jsonb_build_object('code','REVISION_CONFLICT'); END IF;
    IF candidate IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.user_profiles p JOIN public.school_memberships m ON m.user_id=p.user_id
        JOIN public.assignment_eligibilities e ON e.candidate_id=p.user_id AND e.school_id=m.school_id
        WHERE p.user_id=candidate AND p.role='expert' AND p.account_status='active'
        AND m.school_id=st.school_id AND e.actor_id=subject_id AND e.assignment_role='expert'
    ) THEN RETURN jsonb_build_object('code','INVALID_ASSIGNMENT'); END IF;
    SELECT assigned_expert_id INTO old_candidate FROM public.screening_expert_assignments WHERE result_id=target_id;
    IF old_candidate IS DISTINCT FROM candidate THEN
        INSERT INTO public.screening_expert_assignments(result_id,assigned_expert_id,assigned_by)
            VALUES(target_id,candidate,subject_id) ON CONFLICT(result_id) DO UPDATE
            SET assigned_expert_id=EXCLUDED.assigned_expert_id,assigned_by=subject_id,assigned_at=clock_timestamp();
        INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
            VALUES(subject_id,'screenings.expert_assignment','screening',target_id::text,request::text);
    END IF;
    RETURN jsonb_build_object('code',NULL,'data',public.graphiscan_read_screenings(
        subject_id,provider_session_id,'screening','{}',NULL,NULL,1,target_id,false)->'rows'->0);
END;
$$;

REVOKE ALL ON FUNCTION public.graphiscan_write_review(uuid,uuid,bigint,jsonb,text,uuid),
    public.graphiscan_assign_expert(uuid,uuid,bigint,jsonb,uuid)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader;
GRANT EXECUTE ON FUNCTION public.graphiscan_write_review(uuid,uuid,bigint,jsonb,text,uuid),
    public.graphiscan_assign_expert(uuid,uuid,bigint,jsonb,uuid) TO graphiscan_password_writer;
COMMIT;
