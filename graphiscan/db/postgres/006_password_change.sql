-- UNAPPLIED. Review/test locally, then apply once as the owner after 001-005.
-- Separate server writer; reader remains SELECT-only. No credentials are seeded.
BEGIN;

CREATE ROLE graphiscan_password_writer NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB
    NOCREATEROLE NOREPLICATION NOBYPASSRLS;
GRANT USAGE ON SCHEMA public TO graphiscan_password_writer;

CREATE TABLE public.password_change_operations (
    operation_id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    profile_revision bigint NOT NULL,
    state text NOT NULL CHECK (state IN ('pending', 'completed')),
    request_id uuid NOT NULL,
    started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    completed_at timestamptz,
    CHECK ((state = 'completed') = (completed_at IS NOT NULL))
);
CREATE UNIQUE INDEX password_change_one_pending ON public.password_change_operations(user_id)
    WHERE state = 'pending';
ALTER TABLE public.password_change_operations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.password_change_operations FROM PUBLIC, anon, authenticated, service_role,
    graphiscan_api_reader, graphiscan_password_writer;

CREATE FUNCTION public.graphiscan_begin_password(subject_id uuid, provider_session_id uuid,
                                                operation uuid, request uuid)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE p public.user_profiles%ROWTYPE;
BEGIN
    -- Lock serializes competing attempts; recheck after taking it. No remote call
    -- occurs while this transaction holds a lock.
    SELECT * INTO p FROM public.user_profiles WHERE user_id = subject_id FOR UPDATE;
    IF NOT FOUND OR p.account_status <> 'active' OR p.credential_update_pending
       OR NOT EXISTS (
           SELECT 1 FROM public.graphiscan_session_state(subject_id, provider_session_id) s
           WHERE (s.not_after IS NULL OR s.not_after > clock_timestamp())
             AND s.created_at >= p.sessions_valid_after
             AND NOT EXISTS (SELECT 1 FROM public.app_session_revocations r WHERE r.session_id = s.id)
       ) THEN RETURN false; END IF;
    UPDATE public.user_profiles SET credential_update_pending = true
        WHERE user_id = subject_id RETURNING * INTO p;
    INSERT INTO public.password_change_operations(operation_id,user_id,profile_revision,state,request_id)
        VALUES (operation,subject_id,p.revision,'pending',request);
    INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
        VALUES (subject_id,'password_change.started','account',subject_id::text,request::text);
    RETURN true;
END;
$$;

CREATE FUNCTION public.graphiscan_complete_password(subject_id uuid, operation uuid, request uuid)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE p public.user_profiles%ROWTYPE; change public.password_change_operations%ROWTYPE;
BEGIN
    SELECT * INTO p FROM public.user_profiles WHERE user_id = subject_id FOR UPDATE;
    IF NOT FOUND THEN RETURN false; END IF;
    SELECT * INTO change FROM public.password_change_operations
        WHERE operation_id = operation AND user_id = subject_id FOR UPDATE;
    IF NOT FOUND OR change.state <> 'pending' OR NOT p.credential_update_pending
       OR p.account_status <> 'active' OR p.revision <> change.profile_revision
       THEN RETURN false; END IF;
    -- Caller only reaches here after confirmed provider update AND global logout.
    -- Trigger also revokes sessions created during the pending interval.
    UPDATE public.user_profiles SET must_change_password = false,
        credential_update_pending = false, password_changed_at = clock_timestamp(),
        security_version = security_version + 1 WHERE user_id = subject_id;
    UPDATE public.password_change_operations SET state = 'completed', completed_at = clock_timestamp()
        WHERE operation_id = operation;
    INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
        VALUES (subject_id,'password_change.completed','account',subject_id::text,request::text);
    RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION public.graphiscan_begin_password(uuid,uuid,uuid,uuid),
    public.graphiscan_complete_password(uuid,uuid,uuid)
    FROM PUBLIC, anon, authenticated, service_role, graphiscan_api_reader;
GRANT EXECUTE ON FUNCTION public.graphiscan_begin_password(uuid,uuid,uuid,uuid),
    public.graphiscan_complete_password(uuid,uuid,uuid) TO graphiscan_password_writer;
ALTER ROLE graphiscan_password_writer SET statement_timeout = '5s';
COMMIT;
