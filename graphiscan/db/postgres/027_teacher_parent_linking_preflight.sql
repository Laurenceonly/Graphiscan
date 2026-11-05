-- Read-only installation verification. Returns metadata flags only, no accounts.
WITH lookup AS (
    SELECT p.* FROM pg_proc p WHERE p.oid=to_regprocedure('public.graphiscan_teacher_parent_options(uuid,uuid,bigint,smallint,text)')
), writer AS (
    SELECT pg_get_functiondef(p.oid) body FROM pg_proc p
    WHERE p.oid=to_regprocedure('public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)')
)
SELECT
    EXISTS(SELECT 1 FROM lookup WHERE prosecdef AND proconfig @> ARRAY['search_path=pg_catalog']) AS lookup_definer_ready,
    coalesce(has_function_privilege('graphiscan_api_reader',to_regprocedure('public.graphiscan_teacher_parent_options(uuid,uuid,bigint,smallint,text)'),'EXECUTE'),false) AS reader_lookup_ready,
    EXISTS(SELECT 1 FROM lookup WHERE NOT EXISTS(SELECT 1 FROM aclexplode(coalesce(proacl,acldefault('f',proowner))) a WHERE a.grantee=0 AND a.privilege_type='EXECUTE')) AS lookup_public_denied,
    NOT EXISTS(SELECT 1 FROM unnest(ARRAY['anon','authenticated','service_role','graphiscan_admin_writer','graphiscan_password_writer']) role_name
        WHERE coalesce(has_function_privilege(role_name,to_regprocedure('public.graphiscan_teacher_parent_options(uuid,uuid,bigint,smallint,text)'),'EXECUTE'),false)) AS other_lookup_roles_denied,
    EXISTS(SELECT 1 FROM writer WHERE strpos(body,'-- teacher parent linking027')>0
        AND strpos(body,'actor.role=''teacher'' AND parent IS DISTINCT FROM st.parent_id')=0) AS teacher_parent_changes_enabled,
    EXISTS(SELECT 1 FROM writer WHERE strpos(body,'st.teacher_id=subject_id AND public.graphiscan_grade_allowed')>0
        AND strpos(body,'p.role=''parent'' AND p.account_status=''active'' AND NOT p.credential_update_pending')>0) AS ownership_grade_parent_checks_retained,
    coalesce(has_function_privilege('graphiscan_password_writer',to_regprocedure('public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)'),'EXECUTE'),false)
        AND NOT EXISTS(SELECT 1 FROM unnest(ARRAY['anon','authenticated','service_role','graphiscan_api_reader','graphiscan_admin_writer']) role_name
            WHERE coalesce(has_function_privilege(role_name,to_regprocedure('public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)'),'EXECUTE'),false)) AS writer_roles_retained;
