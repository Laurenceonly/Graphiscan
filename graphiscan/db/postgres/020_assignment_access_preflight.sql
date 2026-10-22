-- Read-only metadata; no identities, eligibility rows or provider secrets.
WITH expected(signature,allowed_role) AS (VALUES
    ('public.graphiscan_assignment_access_gate(uuid,uuid,uuid,uuid,bigint)',NULL::text),
    ('public.graphiscan_assignment_access_snapshot(uuid,uuid,bigint)',NULL::text),
    ('public.graphiscan_get_assignment_access(uuid,uuid,uuid,uuid,bigint)','graphiscan_api_reader'),
    ('public.graphiscan_set_assignment_access(uuid,uuid,uuid,uuid,bigint,bigint,boolean,uuid)','graphiscan_admin_writer')
), functions AS (
    SELECT e.*,p.* FROM expected e LEFT JOIN pg_proc p ON p.oid=to_regprocedure(e.signature)
)
SELECT (SELECT count(oid)=4 FROM functions) AS assignment_functions_installed,
    (SELECT count(oid)=4 AND bool_and(prosecdef AND proconfig @> ARRAY['search_path=pg_catalog']
        AND proowner NOT IN (SELECT oid FROM pg_roles WHERE rolname IN ('graphiscan_api_reader','graphiscan_admin_writer')))
        FROM functions) AS assignment_guarded_functions,
    NOT EXISTS(SELECT 1 FROM functions f CROSS JOIN pg_roles r WHERE r.rolname IN
        ('anon','authenticated','service_role','graphiscan_api_reader','graphiscan_password_writer','graphiscan_admin_writer')
        AND has_function_privilege(r.oid,f.oid,'EXECUTE') IS DISTINCT FROM (r.rolname IS NOT DISTINCT FROM f.allowed_role))
        AS assignment_exact_runtime_grants,
    NOT EXISTS(SELECT 1 FROM functions f,LATERAL aclexplode(coalesce(f.proacl,acldefault('f',f.proowner))) a
        WHERE a.grantee=0 AND a.privilege_type='EXECUTE') AS assignment_public_denied,
    coalesce((SELECT relrowsecurity FROM pg_class WHERE oid=to_regclass('public.assignment_eligibilities')),false)
        AND NOT EXISTS(SELECT 1 FROM pg_roles r WHERE r.rolname IN
            ('anon','authenticated','service_role','graphiscan_api_reader','graphiscan_password_writer','graphiscan_admin_writer')
            AND has_table_privilege(r.oid,'public.assignment_eligibilities',
                'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')) AS assignment_table_protected;
