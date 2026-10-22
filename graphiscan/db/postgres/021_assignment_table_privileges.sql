-- Apply after020 as schema owner. Removes leftover Supabase default privileges.
-- No records, policies, functions, credentials or eligibility entries change.
BEGIN;
REVOKE TRUNCATE, REFERENCES, TRIGGER ON TABLE public.assignment_eligibilities
    FROM anon, authenticated, service_role;
COMMIT;
