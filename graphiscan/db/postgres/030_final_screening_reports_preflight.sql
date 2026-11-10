-- Read-only metadata, no accounts/student/report data.
WITH functions AS (
    SELECT p.* FROM pg_proc p WHERE p.oid IN (
        to_regprocedure('public.graphiscan_final_context(uuid,uuid,bigint)'),
        to_regprocedure('public.graphiscan_read_final_report(uuid,uuid,bigint)'),
        to_regprocedure('public.graphiscan_finalize_report(uuid,uuid,bigint,jsonb,text,uuid)'))
)
SELECT
    (SELECT count(*)=3 AND bool_and(prosecdef AND proconfig @> ARRAY['search_path=pg_catalog']) FROM functions) AS pinned_definers,
    EXISTS(SELECT 1 FROM pg_class WHERE oid=to_regclass('public.final_screening_reports') AND relrowsecurity) AS final_report_rls,
    EXISTS(SELECT 1 FROM pg_trigger WHERE tgrelid=to_regclass('public.final_screening_reports') AND tgname='final_screening_reports_immutable' AND tgenabled='O') AS immutable_snapshot,
    coalesce(has_function_privilege('graphiscan_api_reader',to_regprocedure('public.graphiscan_read_final_report(uuid,uuid,bigint)'),'EXECUTE'),false)
        AND coalesce(has_function_privilege('graphiscan_password_writer',to_regprocedure('public.graphiscan_finalize_report(uuid,uuid,bigint,jsonb,text,uuid)'),'EXECUTE'),false) AS capability_grants,
    NOT EXISTS(SELECT 1 FROM functions f CROSS JOIN unnest(ARRAY['anon','authenticated','service_role','graphiscan_api_reader','graphiscan_password_writer','graphiscan_admin_writer']) r
        WHERE has_function_privilege(r,f.oid,'EXECUTE') AND NOT (
            (r='graphiscan_api_reader' AND f.proname='graphiscan_read_final_report')
            OR (r='graphiscan_password_writer' AND f.proname='graphiscan_finalize_report'))) AS capability_separation,
    NOT EXISTS(SELECT 1 FROM unnest(ARRAY['anon','authenticated','service_role','graphiscan_api_reader','graphiscan_password_writer','graphiscan_admin_writer']) r
        WHERE coalesce(has_table_privilege(r,to_regclass('public.final_screening_reports'),'SELECT,INSERT,UPDATE,DELETE'),false)) AS no_direct_table_access;
