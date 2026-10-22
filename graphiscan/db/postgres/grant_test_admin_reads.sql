-- DISPOSABLE TEST PROJECT ONLY. Run as schema owner after 016_admin_reads.sql.
-- Grants only the existing fictional test admin access to account/audit lists.
-- Existing school-scoped grants are preserved. Permission changes revoke old
-- sessions through the installed trigger; sign in again after this succeeds.
BEGIN;
DO $$
DECLARE
    test_admin uuid;
    added integer;
BEGIN
    IF to_regprocedure('public.graphiscan_read_admin(uuid,uuid,text,text,text,text,timestamptz,uuid,bigint,integer)') IS NULL THEN
        RAISE EXCEPTION 'Apply 016_admin_reads.sql first';
    END IF;

    SELECT p.user_id INTO STRICT test_admin
    FROM public.user_profiles p JOIN auth.users u ON u.id=p.user_id
    WHERE lower(u.email)='graphiscan.test@example.invalid'
        AND u.email_confirmed_at IS NOT NULL AND u.deleted_at IS NULL
        AND (u.banned_until IS NULL OR u.banned_until<=clock_timestamp())
        AND p.full_name='Synthetic Test Admin'
        AND p.role='admin' AND p.account_status='active'
        AND EXISTS (SELECT 1 FROM public.privacy_agreements a
            WHERE a.is_current AND a.version='graphiscan-workflow-test-v1'
                AND p.user_id=ANY(a.test_subject_ids));

    PERFORM 1 FROM public.user_profiles WHERE user_id=test_admin FOR UPDATE;
    WITH inserted AS (
        INSERT INTO public.user_permission_grants(user_id,permission_key,school_id,granted_by)
        SELECT test_admin,permission_key,NULL,test_admin
        FROM (VALUES ('accounts.manage'),('audit.read')) wanted(permission_key)
        ON CONFLICT (user_id,permission_key) WHERE school_id IS NULL DO NOTHING
        RETURNING grant_id
    ) SELECT count(*) INTO added FROM inserted;

    IF added>0 THEN
        INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id)
        VALUES(test_admin,'test_fixture.admin_read_permissions_added','user_profile',test_admin::text);
    END IF;
EXCEPTION
    WHEN no_data_found OR too_many_rows THEN
        RAISE EXCEPTION 'Expected the single active fictional admin in the installed test audience; no grants were added';
END;
$$;
COMMIT;
