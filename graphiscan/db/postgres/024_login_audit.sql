-- Apply after 023 and BEFORE restarting/deploying the login-audit server change.
-- No historical sign-ins are fabricated. Runtime roles get function access only.
BEGIN;
CREATE FUNCTION public.graphiscan_record_login(subject_id uuid, provider_session_id uuid, request uuid)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE profile_id uuid;
BEGIN
    IF request IS NULL THEN RETURN false; END IF;
    -- Serialize duplicates for this account without adding any client table grants.
    SELECT user_id INTO profile_id FROM public.user_profiles
        WHERE user_id=subject_id AND account_status='active' AND NOT credential_update_pending FOR UPDATE;
    IF profile_id IS NULL OR NOT EXISTS (
        SELECT 1 FROM public.graphiscan_session_state(subject_id,provider_session_id) s
        WHERE (s.not_after IS NULL OR s.not_after>clock_timestamp())
          AND s.created_at >= (SELECT sessions_valid_after FROM public.user_profiles WHERE user_id=subject_id)
          AND NOT EXISTS (SELECT 1 FROM public.app_session_revocations r WHERE r.session_id=s.id)
    ) THEN RETURN false; END IF;
    -- Onboarding may still be pending: this event means sign-in, not workspace access.
    IF NOT EXISTS (SELECT 1 FROM public.audit_logs WHERE actor_id=subject_id
        AND action='session.login' AND resource_type='session'
        AND resource_id=provider_session_id::text) THEN
        INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
        VALUES(subject_id,'session.login','session',provider_session_id::text,request::text);
    END IF;
    RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION public.graphiscan_record_login(uuid,uuid,uuid)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader;
GRANT EXECUTE ON FUNCTION public.graphiscan_record_login(uuid,uuid,uuid)
    TO graphiscan_password_writer;
COMMIT;
