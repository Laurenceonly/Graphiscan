-- DISPOSABLE TEST PROJECT ONLY, after 001-005 and the manually created,
-- auto-confirmed Auth account graphiscan.test@example.invalid.
-- Creates one fictional bootstrap profile and an audit row. No passwords,
-- permission grants, privacy acceptances, student records or model defaults.con
-- Run once as the reviewed schema owner; existing profiles are never overwritten.
BEGIN;

DO $$
DECLARE test_user_id uuid;
BEGIN
    SELECT id INTO STRICT test_user_id FROM auth.users
        WHERE lower(email) = 'graphiscan.test@example.invalid';
    IF EXISTS (SELECT 1 FROM public.user_profiles WHERE user_id = test_user_id) THEN
        RAISE EXCEPTION 'Test profile already exists; this script will not overwrite it';
    END IF;

    INSERT INTO public.user_profiles
        (user_id, full_name, role, account_status, must_change_password, created_by)
    VALUES (test_user_id, 'Synthetic Test Admin', 'admin', 'active', true, NULL);

    INSERT INTO public.audit_logs
        (actor_id, action, resource_type, resource_id)
    VALUES (test_user_id, 'test_fixture.profile_created', 'user_profile', test_user_id::text);
EXCEPTION
    WHEN no_data_found THEN
        RAISE EXCEPTION 'Create the fictional Auth account in the test project first';
    WHEN too_many_rows THEN
        RAISE EXCEPTION 'Expected exactly one fictional Auth account; inspect before continuing';
END;
$$;

COMMIT;
