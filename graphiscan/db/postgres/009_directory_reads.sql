-- Apply once after 001-008 as the reviewed schema owner. No data import or writes.
-- The existing private reader gets one bounded read capability, no table grants.
BEGIN;

CREATE FUNCTION public.graphiscan_read_directory(
    subject_id uuid, provider_session_id uuid, resource text, search_text text,
    filter_school bigint, filter_grade smallint, after_time timestamptz,
    after_id bigint, page_limit integer, target_id bigint
) RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
WITH actor AS MATERIALIZED (
    SELECT p.*, s.id AS provider_id, s.created_at AS session_created,
        s.not_after AS session_expires,
        a.version AS agreement_version
    FROM (SELECT 1) seed
    LEFT JOIN public.user_profiles p ON p.user_id = subject_id
    LEFT JOIN public.graphiscan_session_state(subject_id, provider_session_id) s ON true
    LEFT JOIN public.privacy_agreements a ON a.is_current
        AND (a.test_subject_id IS NULL OR a.test_subject_id = p.user_id)
        AND a.approved_by IS NOT NULL AND a.approved_at <= statement_timestamp()
        AND a.published_at <= statement_timestamp()
        AND a.content_sha256 = encode(sha256(convert_to(a.content, 'UTF8')), 'hex')
), gate AS MATERIALIZED (
    SELECT actor.*, CASE
        WHEN provider_id IS NULL OR session_expires <= statement_timestamp()
            OR coalesce(credential_update_pending, false)
            OR session_created < sessions_valid_after
            OR EXISTS (SELECT 1 FROM public.app_session_revocations r
                       WHERE r.session_id = provider_session_id) THEN 'AUTHENTICATION_REQUIRED'
        WHEN user_id IS NULL OR account_status <> 'active' THEN 'ACCOUNT_UNAVAILABLE'
        WHEN must_change_password THEN 'PASSWORD_CHANGE_REQUIRED'
        WHEN agreement_version IS NULL THEN 'AGREEMENT_NOT_CONFIGURED'
        WHEN NOT EXISTS (SELECT 1 FROM public.privacy_agreement_acceptances a
            WHERE a.user_id = subject_id AND a.agreement_version = actor.agreement_version)
            THEN 'PRIVACY_ACCEPTANCE_REQUIRED'
        WHEN role NOT IN ('admin','researcher','teacher','parent','expert') THEN 'FORBIDDEN'
        WHEN resource NOT IN ('schools','students','student') OR resource IS NULL
            OR page_limit IS NULL OR page_limit NOT BETWEEN 1 AND 100
            OR search_text IS NULL OR length(search_text) > 120
            OR (filter_school IS NOT NULL AND filter_school <= 0)
            OR (filter_grade IS NOT NULL AND filter_grade NOT BETWEEN 1 AND 3)
            OR ((after_time IS NULL) <> (after_id IS NULL))
            OR (after_id IS NOT NULL AND after_id <= 0)
            OR (resource = 'student' AND (target_id IS NULL OR target_id <= 0))
            THEN 'INVALID_QUERY'
        ELSE NULL END AS code FROM actor
), visible_students AS MATERIALIZED (
    SELECT s.* FROM public.students s CROSS JOIN gate a
    WHERE a.code IS NULL AND (
        (a.role = 'teacher' AND s.teacher_id = subject_id)
        OR (a.role = 'parent' AND s.parent_id = subject_id)
        OR (a.role = 'expert' AND EXISTS (
            SELECT 1 FROM public.handwriting_samples h
            JOIN public.screening_results r ON r.sample_id = h.sample_id
            JOIN public.screening_expert_assignments e ON e.result_id = r.result_id
            WHERE h.student_id = s.student_id AND e.assigned_expert_id = subject_id))
        OR (a.role IN ('admin','researcher') AND EXISTS (
            SELECT 1 FROM public.user_permission_grants g WHERE g.user_id = subject_id
            AND g.permission_key = 'assignments.manage'
            AND (g.school_id IS NULL OR g.school_id = s.school_id)))
    )
), visible_schools AS MATERIALIZED (
    SELECT s.* FROM public.schools s CROSS JOIN gate a
    WHERE a.code IS NULL AND (
        (a.role IN ('teacher','parent','expert') AND EXISTS (
            SELECT 1 FROM visible_students v WHERE v.school_id = s.school_id))
        OR (a.role = 'teacher' AND EXISTS (SELECT 1 FROM public.school_memberships m
            WHERE m.user_id = subject_id AND m.school_id = s.school_id))
        OR (a.role IN ('admin','researcher') AND EXISTS (
            SELECT 1 FROM public.user_permission_grants g WHERE g.user_id = subject_id
            AND g.permission_key IN ('accounts.manage','schools.manage','assignments.manage')
            AND (g.school_id IS NULL OR g.school_id = s.school_id)))
    )
), filtered AS MATERIALIZED (
    SELECT s.school_id AS id, s.created_at AS sort_time,
        jsonb_build_object('school_id',s.school_id::text,'name',s.name,
            'revision',s.revision,'created_at',s.created_at) AS data
    FROM visible_schools s WHERE resource = 'schools'
        AND (search_text = '' OR strpos(lower(s.name),lower(search_text)) > 0)
    UNION ALL
    SELECT s.student_id, s.created_at,
        jsonb_build_object('student_id',s.student_id::text,'full_name',s.full_name,
            'age',s.age,'school_id',s.school_id::text,'grade_level',s.grade_level,
            'teacher_id',s.teacher_id::text,'parent_id',s.parent_id::text,
            'revision',s.revision,'created_at',s.created_at,'updated_at',s.updated_at)
    FROM visible_students s WHERE resource IN ('students','student')
        AND (resource <> 'student' OR s.student_id = target_id)
        AND (filter_school IS NULL OR s.school_id = filter_school)
        AND (filter_grade IS NULL OR s.grade_level = filter_grade)
        AND (search_text = '' OR strpos(lower(s.full_name),lower(search_text)) > 0)
), page AS MATERIALIZED (
    SELECT * FROM filtered WHERE after_time IS NULL OR (sort_time,id) < (after_time,after_id)
    ORDER BY sort_time DESC, id DESC LIMIT least(greatest(coalesce(page_limit,1),1),100) + 1
)
SELECT jsonb_build_object('code',gate.code,
    'rows',coalesce((SELECT jsonb_agg(data ORDER BY sort_time DESC,id DESC)
        FROM page),'[]'::jsonb)) FROM gate;
$$;

REVOKE ALL ON FUNCTION public.graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)
    FROM PUBLIC, anon, authenticated, service_role, graphiscan_password_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)
    TO graphiscan_api_reader;
COMMIT;
