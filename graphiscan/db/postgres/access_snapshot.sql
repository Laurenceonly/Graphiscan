-- One statement gives a coherent READ COMMITTED snapshot; always one row.
-- Server-only SELECT on six application tables and EXECUTE on the 005 session
-- function; no reader grants/policies on Supabase-managed Auth tables.
-- Psycopg named parameters are values, never SQL interpolation.
SELECT
    (s.id IS NOT NULL
     AND (s.not_after IS NULL OR s.not_after > statement_timestamp())
     AND NOT EXISTS (SELECT 1 FROM public.app_session_revocations r
                     WHERE r.session_id = %(session_id)s::uuid)
     AND NOT coalesce(p.credential_update_pending, false)
     AND (p.user_id IS NULL OR s.created_at >= p.sessions_valid_after)) AS session_valid,
    p.user_id::text, p.full_name, p.role, p.account_status, p.must_change_password,
    a.version AS required_agreement_version,
    (SELECT accepted.agreement_version FROM public.privacy_agreement_acceptances accepted
     WHERE accepted.user_id = p.user_id
     ORDER BY (accepted.agreement_version = a.version) DESC NULLS LAST,
              accepted.accepted_at DESC, accepted.acceptance_id DESC LIMIT 1)
        AS accepted_agreement_version,
    coalesce((SELECT jsonb_agg(jsonb_build_object(
        'permission', permission_key, 'school_id', school_id::text)
        ORDER BY permission_key, school_id NULLS FIRST)
        FROM public.user_permission_grants WHERE user_id = p.user_id), '[]'::jsonb) AS grants,
    coalesce((SELECT jsonb_agg(school_id::text ORDER BY school_id)
        FROM public.school_memberships WHERE user_id = p.user_id), '[]'::jsonb) AS school_ids
FROM (SELECT 1) seed
LEFT JOIN public.graphiscan_session_state(%(user_id)s::uuid, %(session_id)s::uuid) s ON true
LEFT JOIN public.user_profiles p ON p.user_id = %(user_id)s::uuid
LEFT JOIN public.privacy_agreements a ON a.is_current
    AND ((to_jsonb(a)->>'test_subject_id') IS NULL OR (to_jsonb(a)->>'test_subject_id') = p.user_id::text)
    AND ((to_jsonb(a)->>'test_subject_ids') IS NULL
         OR (to_jsonb(a)->'test_subject_ids') @> jsonb_build_array(p.user_id::text))
    AND a.approved_by IS NOT NULL AND a.approved_at <= statement_timestamp()
    AND a.published_at <= statement_timestamp()
    AND a.content_sha256 = encode(sha256(convert_to(a.content, 'UTF8')), 'hex');
