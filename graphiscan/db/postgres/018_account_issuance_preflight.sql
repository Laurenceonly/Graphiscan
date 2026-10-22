-- Catalog only. No account records or provider credentials are read.
WITH functions AS (
    SELECT p.* FROM pg_proc p WHERE p.oid IN (
        to_regprocedure('public.graphiscan_begin_account_issuance(uuid,uuid,uuid,jsonb)'),
        to_regprocedure('public.graphiscan_complete_account_issuance(uuid,uuid,uuid,uuid,uuid)'))
), writer AS (SELECT oid FROM pg_roles WHERE rolname='graphiscan_admin_writer')
SELECT (SELECT count(*)=2 FROM functions) AS issuance_functions_installed,
    (SELECT count(*)=2 AND bool_and(prosecdef AND provolatile='v'
        AND proconfig @> ARRAY['search_path=pg_catalog'] AND proowner<>(SELECT oid FROM writer))
        FROM functions) AS guarded_issuance_functions,
    (SELECT count(*)=2 AND bool_and(has_function_privilege((SELECT oid FROM writer),oid,'EXECUTE'))
        FROM functions) AS writer_can_issue,
    NOT EXISTS (SELECT 1 FROM functions f CROSS JOIN pg_roles r
        WHERE r.rolname IN ('anon','authenticated','service_role','graphiscan_api_reader','graphiscan_password_writer')
        AND has_function_privilege(r.oid,f.oid,'EXECUTE')) AS issuance_other_roles_denied,
    NOT EXISTS (SELECT 1 FROM functions f,
        LATERAL aclexplode(coalesce(f.proacl,acldefault('f',f.proowner))) a
        WHERE a.grantee=0 AND a.privilege_type='EXECUTE') AS issuance_public_denied,
    coalesce((SELECT relrowsecurity AND relowner<>(SELECT oid FROM writer)
        FROM pg_class WHERE oid=to_regclass('public.account_issuance_requests')),false)
        AND NOT EXISTS (SELECT 1 FROM pg_roles r
            WHERE r.rolname IN ('anon','authenticated','service_role','graphiscan_api_reader',
                'graphiscan_password_writer','graphiscan_admin_writer')
            AND has_table_privilege(r.oid,to_regclass('public.account_issuance_requests'),
                'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')) AS issuance_table_protected;
