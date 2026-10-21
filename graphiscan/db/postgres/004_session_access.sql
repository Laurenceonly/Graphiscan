-- UNAPPLIED target extension. Requires reviewed 001/002/003 and Supabase Auth.
-- Does not seed profiles, publish privacy text or modify provider sessions.
-- Requires SELECT on auth.sessions and INSERT on app_session_revocations for
-- the server role performing profile/security changes (function is invoker).
BEGIN;

ALTER TABLE public.user_profiles ADD COLUMN sessions_valid_after timestamptz
    NOT NULL DEFAULT '-infinity';

CREATE FUNCTION public.invalidate_profile_sessions() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
    -- Grants/membership changes already advance security_version through 003.
    -- Retain the floor after restoration so old sessions cannot become valid again.
    IF NEW.security_version IS DISTINCT FROM OLD.security_version
       OR NEW.role IS DISTINCT FROM OLD.role
       OR NEW.account_status IS DISTINCT FROM OLD.account_status
       OR NEW.credential_update_pending IS DISTINCT FROM OLD.credential_update_pending
       OR NEW.password_changed_at IS DISTINCT FROM OLD.password_changed_at
       OR NEW.must_change_password IS DISTINCT FROM OLD.must_change_password THEN
        NEW.sessions_valid_after := greatest(OLD.sessions_valid_after, clock_timestamp());
        -- Session IDs, rather than rounded JWT iat timestamps, make same-tick
        -- reauthentication possible without resurrecting an existing session.
        INSERT INTO public.app_session_revocations(session_id,user_id,reason)
            SELECT id, NEW.user_id, 'account_change' FROM auth.sessions
            WHERE user_id = NEW.user_id
            ON CONFLICT (session_id) DO NOTHING;
    ELSE
        NEW.sessions_valid_after := greatest(OLD.sessions_valid_after, NEW.sessions_valid_after);
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER profile_session_invalidation BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW EXECUTE FUNCTION public.invalidate_profile_sessions();

COMMIT;
