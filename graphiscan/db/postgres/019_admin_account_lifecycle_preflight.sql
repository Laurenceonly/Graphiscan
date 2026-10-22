-- Catalog booleans only; no account data or mutations.
WITH expected(signature,allowed_role) AS (VALUES
    ('public.graphiscan_admin_account_gate(uuid,uuid)',NULL::text),
    ('public.graphiscan_admin_account_snapshot(uuid)',NULL::text),
    ('public.graphiscan_get_admin_account(uuid,uuid,uuid)','graphiscan_api_reader'),
    ('public.graphiscan_read_admin_account_operation(uuid,uuid,uuid)','graphiscan_api_reader'),
    ('public.graphiscan_begin_admin_account_operation(uuid,uuid,uuid,uuid,text,bigint,uuid)','graphiscan_admin_writer'),
    ('public.graphiscan_complete_admin_account_operation(uuid,uuid,uuid,uuid)','graphiscan_admin_writer')
), functions AS (
    SELECT e.*,p.* FROM expected e LEFT JOIN pg_proc p ON p.oid=to_regprocedure(e.signature)
)
SELECT (SELECT count(oid)=6 FROM functions) AS lifecycle_functions_installed,
    (SELECT count(oid)=6 AND bool_and(prosecdef AND proconfig @> ARRAY['search_path=pg_catalog']
        AND proowner NOT IN (SELECT oid FROM pg_roles WHERE rolname IN ('graphiscan_api_reader','graphiscan_admin_writer')))
        FROM functions) AS guarded_lifecycle_functions,
    NOT EXISTS (SELECT 1 FROM functions f CROSS JOIN pg_roles r WHERE
        r.rolname IN ('anon','authenticated','service_role','graphiscan_api_reader','graphiscan_password_writer','graphiscan_admin_writer')
        AND has_function_privilege(r.oid,f.oid,'EXECUTE') IS DISTINCT FROM (r.rolname IS NOT DISTINCT FROM f.allowed_role)) AS lifecycle_exact_runtime_grants,
    NOT EXISTS (SELECT 1 FROM functions f,LATERAL aclexplode(coalesce(f.proacl,acldefault('f',f.proowner))) a
        WHERE a.grantee=0 AND a.privilege_type='EXECUTE') AS lifecycle_public_denied,
    coalesce((SELECT relrowsecurity FROM pg_class WHERE oid=to_regclass('public.admin_account_operations')),false)
        AND NOT EXISTS (SELECT 1 FROM pg_roles r WHERE r.rolname IN
            ('anon','authenticated','service_role','graphiscan_api_reader','graphiscan_password_writer','graphiscan_admin_writer')
            AND has_table_privilege(r.oid,to_regclass('public.admin_account_operations'),
                'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')) AS lifecycle_table_protected;
