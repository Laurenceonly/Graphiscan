BEGIN;

REVOKE TRUNCATE, REFERENCES, TRIGGER
ON TABLE public.assignment_eligibilities
FROM anon, authenticated, service_role;

COMMIT;
