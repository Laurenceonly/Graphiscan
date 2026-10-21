-- Unapplied after 001-007. Adds durable local-session sign-out only.
-- No new role/password/table grant and no hosted session is changed by migration.
BEGIN;
CREATE FUNCTION public.graphiscan_revoke_session(subject_id uuid, provider_session_id uuid, request uuid)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE profile_id uuid; inserted_id uuid;
BEGIN
    IF EXISTS (SELECT 1 FROM public.app_session_revocations r
               WHERE r.session_id=provider_session_id AND r.user_id=subject_id) THEN
        RETURN true;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.graphiscan_session_state(subject_id,provider_session_id)) THEN
        RETURN false;
    END IF;
    -- Sign-out is allowed even for disabled/onboarding/pending accounts.
    SELECT user_id INTO profile_id FROM public.user_profiles WHERE user_id=subject_id FOR UPDATE;
    IF profile_id IS NULL THEN RETURN true; END IF;
    INSERT INTO public.app_session_revocations AS revocation(session_id,user_id,reason)
        VALUES(provider_session_id,subject_id,'logout') ON CONFLICT(session_id) DO NOTHING
        RETURNING revocation.session_id INTO inserted_id;
    IF inserted_id IS NOT NULL THEN
        INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
            VALUES(subject_id,'session.logout','session',provider_session_id::text,request::text);
    END IF;
    RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION public.graphiscan_revoke_session(uuid,uuid,uuid)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader;
GRANT EXECUTE ON FUNCTION public.graphiscan_revoke_session(uuid,uuid,uuid)
    TO graphiscan_password_writer;
COMMIT;
