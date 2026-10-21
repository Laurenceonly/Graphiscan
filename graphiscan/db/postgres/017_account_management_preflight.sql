-- Read-only catalog checks; returns booleans only, no application records.
WITH writer AS (
    SELECT * FROM pg_catalog.pg_roles WHERE rolname='graphiscan_admin_writer'
), updater AS (
    SELECT * FROM pg_catalog.pg_proc
    WHERE oid=to_regprocedure('public.graphiscan_update_account(uuid,uuid,uuid,jsonb,uuid)')
)
SELECT
    NOT (w.rolsuper OR w.rolcreaterole OR w.rolcreatedb OR w.rolreplication
        OR w.rolbypassrls OR w.rolinherit) AS restricted_role,
    NOT EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members WHERE member=w.oid) AS no_role_memberships,
    has_schema_privilege(w.oid,'public','USAGE')
        AND NOT has_schema_privilege(w.oid,'public','CREATE') AS bounded_schema_access,
    NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname IN ('public','auth') AND c.relkind IN ('r','p','v','m','f')
            AND (c.relowner=w.oid OR has_table_privilege(w.oid,c.oid,
                'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER'))
    ) AS no_direct_table_access,
    NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname IN ('public','auth') AND c.relkind='S'
            AND (c.relowner=w.oid OR has_sequence_privilege(w.oid,c.oid,'SELECT,USAGE,UPDATE'))
    ) AS no_direct_sequence_access,
    p.prosecdef AND p.provolatile='v' AND p.proconfig @> ARRAY['search_path=pg_catalog']
        AND p.proowner<>w.oid AS guarded_update_function,
    has_function_privilege(w.oid,p.oid,'EXECUTE') AS writer_can_update,
    NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_roles r
        WHERE r.rolname IN ('anon','authenticated','service_role',
            'graphiscan_api_reader','graphiscan_password_writer')
            AND has_function_privilege(r.oid,p.oid,'EXECUTE')
    ) AS other_runtime_roles_denied,
    NOT EXISTS (
        SELECT 1 FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
        WHERE a.grantee=0 AND a.privilege_type='EXECUTE'
    ) AS public_denied,
    NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_proc other JOIN pg_catalog.pg_namespace n ON n.oid=other.pronamespace
        WHERE n.nspname='public' AND other.proname LIKE 'graphiscan\_%' ESCAPE '\'
            AND other.oid<>p.oid AND other.prokind='f' AND other.prorettype<>'trigger'::regtype
            AND has_function_privilege(w.oid,other.oid,'EXECUTE')
    ) AS other_application_functions_denied
FROM writer w CROSS JOIN updater p;
