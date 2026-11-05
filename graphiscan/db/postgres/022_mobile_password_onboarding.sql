-- New/confirmed-reset mobile accounts use temporary passwords.
-- Admin/researcher credentials are permanent from issuance/reset.
-- Existing flags and in-flight operations are not cleared by this migration.
BEGIN;

CREATE OR REPLACE FUNCTION public.graphiscan_complete_account_issuance(
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
    VALUES(target,issuance.full_name,issuance.role,'active',
        issuance.role IN ('teacher','expert','parent'),subject_id);
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

CREATE OR REPLACE FUNCTION public.graphiscan_complete_admin_account_operation(subject_id uuid,provider_session_id uuid,
    operation uuid,request uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE
    code text; pending public.admin_account_operations%ROWTYPE;
    p public.user_profiles%ROWTYPE; result jsonb;
BEGIN
    PERFORM user_id FROM public.user_profiles WHERE user_id=subject_id FOR SHARE;
    PERFORM version FROM public.privacy_agreements WHERE is_current FOR SHARE;
    code:=public.graphiscan_admin_account_gate(subject_id,provider_session_id);
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    SELECT * INTO pending FROM public.admin_account_operations WHERE operation_id=operation FOR UPDATE;
    IF NOT FOUND OR pending.actor_id<>subject_id OR request IS NULL THEN
        RETURN jsonb_build_object('code','ISSUANCE_CONFLICT'); END IF;
    IF pending.completed_at IS NOT NULL THEN RETURN jsonb_build_object('code',NULL,'data',pending.response_data); END IF;
    IF pending.action='delete' THEN
        IF EXISTS (SELECT 1 FROM auth.users WHERE id=pending.target_id) OR EXISTS (
            SELECT 1 FROM public.user_profiles WHERE user_id=pending.target_id) THEN
            RETURN jsonb_build_object('code','ACCOUNT_OPERATION_PENDING'); END IF;
        result:=jsonb_build_object('user_id',pending.target_id::text,'deleted',true);
    ELSE
        SELECT * INTO p FROM public.user_profiles WHERE user_id=pending.target_id FOR UPDATE;
        IF NOT FOUND OR NOT p.credential_update_pending OR p.revision<>pending.locked_revision THEN
            RETURN jsonb_build_object('code','ACCOUNT_OPERATION_PENDING'); END IF;
        IF (SELECT role FROM public.user_profiles WHERE user_id=subject_id)<>'admin' AND p.role IN ('admin','researcher') THEN
            RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
        UPDATE public.user_profiles SET must_change_password=(role IN ('teacher','expert','parent')),credential_update_pending=false,
            password_changed_at=CASE WHEN role IN ('teacher','expert','parent') THEN NULL ELSE clock_timestamp() END,
            security_version=security_version+1 WHERE user_id=pending.target_id;
        result:=public.graphiscan_admin_account_snapshot(pending.target_id);
    END IF;
    UPDATE public.admin_account_operations SET completed_at=clock_timestamp(),response_data=result
    WHERE operation_id=operation;
    INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
    VALUES(subject_id,'accounts.'||pending.action||'.completed','account',pending.target_id::text,request::text);
    RETURN jsonb_build_object('code',NULL,'data',result);
END;
$$;

REVOKE ALL ON FUNCTION public.graphiscan_complete_account_issuance(uuid,uuid,uuid,uuid,uuid),
    public.graphiscan_complete_admin_account_operation(uuid,uuid,uuid,uuid)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_password_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_complete_account_issuance(uuid,uuid,uuid,uuid,uuid),
    public.graphiscan_complete_admin_account_operation(uuid,uuid,uuid,uuid) TO graphiscan_admin_writer;

COMMIT;
