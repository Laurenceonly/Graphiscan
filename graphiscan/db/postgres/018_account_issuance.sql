-- Apply once after 017. Account issuance uses a durable reservation before Auth.
-- No passwords, password hashes or provider keys are stored in public tables.
BEGIN;

CREATE TABLE public.account_issuance_requests (
    operation_id uuid PRIMARY KEY,
    actor_id uuid NOT NULL REFERENCES public.user_profiles(user_id),
    email text NOT NULL UNIQUE,
    full_name text NOT NULL,
    role text NOT NULL,
    school_ids bigint[] NOT NULL,
    target_id uuid REFERENCES auth.users(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    response_data jsonb
);
ALTER TABLE public.account_issuance_requests ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.account_issuance_requests FROM PUBLIC,anon,authenticated,service_role,
    graphiscan_api_reader,graphiscan_password_writer,graphiscan_admin_writer;

CREATE FUNCTION public.graphiscan_begin_account_issuance(
    subject_id uuid, provider_session_id uuid, operation uuid, payload jsonb
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE
    actor public.user_profiles%ROWTYPE;
    previous public.account_issuance_requests%ROWTYPE;
    code text;
    schools bigint[];
    fields text[];
BEGIN
    SELECT * INTO actor FROM public.user_profiles WHERE user_id=subject_id FOR SHARE;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','ACCOUNT_UNAVAILABLE'); END IF;
    PERFORM version FROM public.privacy_agreements WHERE is_current FOR SHARE;
    SELECT public.graphiscan_read_directory(subject_id,provider_session_id,
        'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' INTO code;
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    IF actor.role NOT IN ('admin','researcher') OR NOT EXISTS (
        SELECT 1 FROM public.user_permission_grants WHERE user_id=subject_id
        AND permission_key='accounts.manage' AND school_id IS NULL
    ) THEN RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    IF operation IS NULL OR jsonb_typeof(payload) IS DISTINCT FROM 'object' THEN
        RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    SELECT array_agg(key ORDER BY key) INTO fields FROM jsonb_object_keys(payload) key;
    IF fields IS DISTINCT FROM ARRAY['email','full_name','role','school_ids']::text[]
        OR jsonb_typeof(payload->'full_name') IS DISTINCT FROM 'string'
        OR length(btrim(payload->>'full_name')) NOT BETWEEN 1 AND 200
        OR (payload->>'full_name') ~ '[[:cntrl:]]'
        OR jsonb_typeof(payload->'email') IS DISTINCT FROM 'string'
        OR length(payload->>'email') NOT BETWEEN 3 AND 254
        OR (payload->>'email') !~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$'
        OR payload->>'email' <> lower(btrim(payload->>'email'))
        OR jsonb_typeof(payload->'role') IS DISTINCT FROM 'string'
        OR payload->>'role' NOT IN ('admin','researcher','teacher','parent','expert','guest')
        OR jsonb_typeof(payload->'school_ids') IS DISTINCT FROM 'array' THEN
        RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    IF actor.role <> 'admin' AND payload->>'role' IN ('admin','researcher') THEN
        RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    IF jsonb_array_length(payload->'school_ids') > 128 OR EXISTS (
        SELECT 1 FROM jsonb_array_elements(payload->'school_ids') e
        WHERE jsonb_typeof(e) IS DISTINCT FROM 'string' OR e #>> '{}' !~ '^[1-9][0-9]{0,18}$'
    ) THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    BEGIN
        SELECT coalesce(array_agg(value::bigint ORDER BY value::bigint),'{}'::bigint[])
        INTO schools FROM jsonb_array_elements_text(payload->'school_ids');
    EXCEPTION WHEN numeric_value_out_of_range THEN
        RETURN jsonb_build_object('code','INVALID_INPUT');
    END;
    IF cardinality(schools) <> (SELECT count(DISTINCT s) FROM unnest(schools) s)
        OR EXISTS (SELECT 1 FROM unnest(schools) s LEFT JOIN public.schools known
        ON known.school_id=s WHERE known.school_id IS NULL) THEN
        RETURN jsonb_build_object('code','INVALID_ASSIGNMENT'); END IF;
    -- Serialize this operation and email before checking/inserting reservations.
    PERFORM pg_advisory_xact_lock(hashtextextended(operation::text,818));
    PERFORM pg_advisory_xact_lock(hashtextextended(payload->>'email',819));
    SELECT * INTO previous FROM public.account_issuance_requests WHERE operation_id=operation;
    IF FOUND THEN
        IF previous.actor_id<>subject_id OR previous.email<>payload->>'email'
            OR previous.full_name<>payload->>'full_name' OR previous.role<>payload->>'role'
            OR previous.school_ids<>schools THEN
            RETURN jsonb_build_object('code','ISSUANCE_CONFLICT'); END IF;
        IF previous.completed_at IS NOT NULL THEN
            RETURN jsonb_build_object('code',NULL,'data',previous.response_data); END IF;
        RETURN jsonb_build_object('code','ACCOUNT_CREATION_PENDING');
    END IF;
    IF EXISTS (SELECT 1 FROM auth.users WHERE lower(email)=payload->>'email') OR EXISTS (
        SELECT 1 FROM public.account_issuance_requests WHERE email=payload->>'email'
    ) THEN RETURN jsonb_build_object('code','EMAIL_UNAVAILABLE'); END IF;
    INSERT INTO public.account_issuance_requests(operation_id,actor_id,email,full_name,role,school_ids)
    VALUES(operation,subject_id,payload->>'email',payload->>'full_name',payload->>'role',schools);
    RETURN jsonb_build_object('code',NULL,'reserved',true);
END;
$$;

CREATE FUNCTION public.graphiscan_complete_account_issuance(
    subject_id uuid, provider_session_id uuid, operation uuid, target uuid, request uuid
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE
    issuance public.account_issuance_requests%ROWTYPE;
    actor public.user_profiles%ROWTYPE;
    code text;
    result jsonb;
BEGIN
    SELECT * INTO actor FROM public.user_profiles WHERE user_id=subject_id FOR SHARE;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','ACCOUNT_UNAVAILABLE'); END IF;
    PERFORM version FROM public.privacy_agreements WHERE is_current FOR SHARE;
    SELECT public.graphiscan_read_directory(subject_id,provider_session_id,
        'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' INTO code;
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    IF actor.role NOT IN ('admin','researcher') OR NOT EXISTS (
        SELECT 1 FROM public.user_permission_grants WHERE user_id=subject_id
        AND permission_key='accounts.manage' AND school_id IS NULL
    ) THEN RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    SELECT * INTO issuance FROM public.account_issuance_requests WHERE operation_id=operation FOR UPDATE;
    IF NOT FOUND OR issuance.actor_id<>subject_id OR target IS NULL OR request IS NULL THEN
        RETURN jsonb_build_object('code','ISSUANCE_CONFLICT'); END IF;
    IF actor.role<>'admin' AND issuance.role IN ('admin','researcher') THEN
        RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    IF issuance.completed_at IS NOT NULL THEN
        IF issuance.target_id<>target THEN RETURN jsonb_build_object('code','ISSUANCE_CONFLICT'); END IF;
        RETURN jsonb_build_object('code',NULL,'data',issuance.response_data);
    END IF;
    -- app_metadata is provider/admin controlled. Never trust user_metadata here.
    PERFORM id FROM auth.users WHERE id=target AND lower(email)=issuance.email
        AND raw_app_meta_data->>'graphiscan_issuance_id'=operation::text
        AND email_confirmed_at IS NOT NULL AND (banned_until IS NULL OR banned_until<=now())
        FOR SHARE;
    IF NOT FOUND OR EXISTS (SELECT 1 FROM public.user_profiles WHERE user_id=target) THEN
        RETURN jsonb_build_object('code','ISSUANCE_CONFLICT'); END IF;
    INSERT INTO public.user_profiles(user_id,full_name,role,account_status,must_change_password,created_by)
    VALUES(target,issuance.full_name,issuance.role,'active',true,subject_id);
    INSERT INTO public.school_memberships(user_id,school_id,created_by)
    SELECT target,s,subject_id FROM unnest(issuance.school_ids) s;
    SELECT jsonb_build_object('user_id',p.user_id::text,'full_name',p.full_name,'email',issuance.email,
        'role',p.role,'account_status',p.account_status,'revision',p.revision,
        'created_at',p.created_at,'must_change_password',p.must_change_password)
    INTO result FROM public.user_profiles p WHERE user_id=target;
    UPDATE public.account_issuance_requests SET target_id=target,completed_at=now(),response_data=result
    WHERE operation_id=operation;
    INSERT INTO public.audit_logs(actor_id,action)
    VALUES(subject_id,'account.created:'||target::text||':request:'||request::text);
    RETURN jsonb_build_object('code',NULL,'data',result);
END;
$$;

REVOKE ALL ON FUNCTION public.graphiscan_begin_account_issuance(uuid,uuid,uuid,jsonb)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_password_writer;
REVOKE ALL ON FUNCTION public.graphiscan_complete_account_issuance(uuid,uuid,uuid,uuid,uuid)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_password_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_begin_account_issuance(uuid,uuid,uuid,jsonb),
    public.graphiscan_complete_account_issuance(uuid,uuid,uuid,uuid,uuid) TO graphiscan_admin_writer;
COMMIT;
