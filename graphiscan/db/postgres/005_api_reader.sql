-- Apply once, after 001-004, as the reviewed schema owner in the test project.
-- Creates a server-only role with NOLOGIN and no password; private login setup
-- is a separate step. Does not import data or grant access to client API roles.
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles
                   WHERE rolname = current_user AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'Run this setup as the reviewed schema owner with Auth RLS access';
    END IF;
END;
$$;

CREATE ROLE graphiscan_api_reader NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB
    NOCREATEROLE NOREPLICATION NOBYPASSRLS;

-- Supabase owns/protects Auth tables. Expose only the requested subject/session
-- pair's ID and times; no Auth grants or policy changes are made for the reader.
CREATE FUNCTION public.graphiscan_session_state(subject_id uuid, provider_session_id uuid)
RETURNS TABLE (id uuid, created_at timestamptz, not_after timestamptz)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
    SELECT s.id, s.created_at, s.not_after
    FROM auth.sessions s
    WHERE s.user_id = subject_id AND s.id = provider_session_id;
$$;
REVOKE ALL ON FUNCTION public.graphiscan_session_state(uuid, uuid) FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.graphiscan_session_state(uuid, uuid) TO graphiscan_api_reader;

-- Credential/security writes must revoke existing Auth session IDs even when
-- the future writer has no direct access to Supabase's protected session table.
ALTER FUNCTION public.invalidate_profile_sessions() SECURITY DEFINER;
ALTER FUNCTION public.invalidate_profile_sessions() SET search_path = pg_catalog;
REVOKE ALL ON FUNCTION public.invalidate_profile_sessions() FROM PUBLIC, anon, authenticated, service_role;

GRANT USAGE ON SCHEMA public, auth TO graphiscan_api_reader;
GRANT SELECT ON public.user_profiles, public.app_session_revocations,
    public.privacy_agreements, public.privacy_agreement_acceptances,
    public.user_permission_grants, public.school_memberships TO graphiscan_api_reader;

-- These SELECT policies apply only to the private server role. Flask enforces
-- identity, gates and record scope. No policies target anon or authenticated.
CREATE POLICY graphiscan_reader_select ON public.user_profiles
    FOR SELECT TO graphiscan_api_reader USING (true);
CREATE POLICY graphiscan_reader_select ON public.app_session_revocations
    FOR SELECT TO graphiscan_api_reader USING (true);
CREATE POLICY graphiscan_reader_select ON public.privacy_agreements
    FOR SELECT TO graphiscan_api_reader USING (true);
CREATE POLICY graphiscan_reader_select ON public.privacy_agreement_acceptances
    FOR SELECT TO graphiscan_api_reader USING (true);
CREATE POLICY graphiscan_reader_select ON public.user_permission_grants
    FOR SELECT TO graphiscan_api_reader USING (true);
CREATE POLICY graphiscan_reader_select ON public.school_memberships
    FOR SELECT TO graphiscan_api_reader USING (true);

ALTER ROLE graphiscan_api_reader SET default_transaction_read_only = on;
ALTER ROLE graphiscan_api_reader SET statement_timeout = '5s';
COMMIT;
