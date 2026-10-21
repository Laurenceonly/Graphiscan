-- Read-only verification after 001-004 in the disposable Supabase test project.
-- Expected single row: graphiscan_tables=20, tables_with_rls=20,
-- session_trigger_ready=true. Does not read any account/student records.
SELECT
    count(*) AS graphiscan_tables,
    count(*) FILTER (WHERE c.relrowsecurity) AS tables_with_rls,
    EXISTS (
        SELECT 1 FROM pg_catalog.pg_trigger t
        JOIN pg_catalog.pg_class target ON target.oid = t.tgrelid
        JOIN pg_catalog.pg_namespace ns ON ns.oid = target.relnamespace
        JOIN pg_catalog.pg_proc p ON p.oid = t.tgfoid
        JOIN pg_catalog.pg_namespace fn_ns ON fn_ns.oid = p.pronamespace
        WHERE ns.nspname = 'public' AND target.relname = 'user_profiles'
          AND t.tgname = 'profile_session_invalidation'
          AND NOT t.tgisinternal AND t.tgenabled IN ('O', 'A') AND t.tgtype = 19
          AND fn_ns.nspname = 'public' AND p.proname = 'invalidate_profile_sessions'
    ) AS session_trigger_ready
FROM pg_catalog.pg_class c
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
  AND c.relname IN (
    'user_profiles', 'privacy_agreement_acceptances', 'schools', 'students',
    'model_registry', 'handwriting_samples', 'screening_results',
    'expert_validations', 'screening_reports', 'audit_logs',
    'user_permission_grants', 'school_memberships', 'assignment_eligibilities',
    'privacy_agreements', 'app_session_revocations', 'model_evaluations',
    'screening_expert_assignments', 'expert_review_history', 'api_requests',
    'storage_cleanup_jobs'
  );
