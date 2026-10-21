-- Apply once after 001-011 as the reviewed schema owner. Read capability only.
-- No rows, assignments, model defaults, table grants or credentials are created.
BEGIN;
CREATE FUNCTION public.graphiscan_read_screenings(
    subject_id uuid, provider_session_id uuid, resource text, filters jsonb,
    after_time timestamptz, after_id bigint, page_limit integer, target_id bigint,
    oldest_first boolean
) RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
WITH actor AS MATERIALIZED (
    SELECT p.*, s.id AS provider_id, s.created_at AS session_created,
        s.not_after AS session_expires, a.version AS agreement_version
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
            OR coalesce(credential_update_pending, false) OR session_created < sessions_valid_after
            OR EXISTS (SELECT 1 FROM public.app_session_revocations r WHERE r.session_id = provider_session_id)
            THEN 'AUTHENTICATION_REQUIRED'
        WHEN user_id IS NULL OR account_status <> 'active' THEN 'ACCOUNT_UNAVAILABLE'
        WHEN must_change_password THEN 'PASSWORD_CHANGE_REQUIRED'
        WHEN agreement_version IS NULL THEN 'AGREEMENT_NOT_CONFIGURED'
        WHEN NOT EXISTS (SELECT 1 FROM public.privacy_agreement_acceptances a
            WHERE a.user_id = subject_id AND a.agreement_version = actor.agreement_version)
            THEN 'PRIVACY_ACCEPTANCE_REQUIRED'
        WHEN role NOT IN ('admin','researcher','teacher','parent','expert') THEN 'FORBIDDEN'
        WHEN resource IS NULL OR resource NOT IN ('screenings','screening','history','report')
            OR page_limit IS NULL OR page_limit NOT BETWEEN 1 AND 100
            OR oldest_first IS NULL OR (oldest_first AND resource <> 'history')
            OR filters IS NULL OR jsonb_typeof(filters) <> 'object'
            OR filters - ARRAY['student_id','school_id','grade_level','validation_status','model_id','task_type','from','to'] <> '{}'::jsonb
            OR ((after_time IS NULL) <> (after_id IS NULL)) OR after_id <= 0
            OR (resource <> 'screenings' AND (target_id IS NULL OR target_id <= 0))
            THEN 'INVALID_QUERY'
        ELSE NULL END AS code FROM actor
), student_context AS MATERIALIZED (
    SELECT s.* FROM public.students s CROSS JOIN gate a WHERE a.code IS NULL AND (
        (a.role='teacher' AND s.teacher_id=subject_id)
        OR (a.role='parent' AND s.parent_id=subject_id)
        OR (a.role='expert' AND EXISTS (SELECT 1 FROM public.handwriting_samples h
            JOIN public.screening_results r ON r.sample_id=h.sample_id
            JOIN public.screening_expert_assignments e ON e.result_id=r.result_id
            WHERE h.student_id=s.student_id AND e.assigned_expert_id=subject_id))
        OR (a.role IN ('admin','researcher') AND EXISTS (
            SELECT 1 FROM public.user_permission_grants g WHERE g.user_id=subject_id
            AND g.permission_key='assignments.manage' AND (g.school_id IS NULL OR g.school_id=s.school_id)))
    )
), visible AS MATERIALIZED (
    SELECT r.*, h.student_id, s.school_id, s.grade_level,
        v.status AS review_status, v.expert_id, v.remarks, v.expert_recommendation,
        v.follow_up_needed, v.validation_date, v.revision AS review_revision,
        v.provenance AS review_provenance, e.assigned_expert_id,
        p.report_id, p.report_type, p.school_context
    FROM public.screening_results r
    JOIN public.handwriting_samples h ON h.sample_id = r.sample_id
    JOIN student_context s ON s.student_id = h.student_id
    JOIN public.expert_validations v ON v.result_id = r.result_id
    JOIN public.screening_reports p ON p.result_id = r.result_id AND p.student_id = h.student_id
    LEFT JOIN public.screening_expert_assignments e ON e.result_id = r.result_id
    CROSS JOIN gate a
    WHERE a.code IS NULL AND (
        (a.role = 'teacher')
        OR (a.role = 'parent' AND s.parent_id = subject_id AND v.status = 'Validated')
        OR (a.role = 'expert' AND e.assigned_expert_id = subject_id)
        OR (a.role IN ('admin','researcher'))
    )
), filtered AS MATERIALIZED (
    SELECT * FROM visible r WHERE
        (resource <> 'screening' OR r.result_id = target_id)
        AND (resource <> 'report' OR r.report_id = target_id)
        AND (resource <> 'history' OR r.student_id = target_id)
        AND (NOT filters ? 'student_id' OR r.student_id = (filters->>'student_id')::bigint)
        AND (NOT filters ? 'school_id' OR r.school_id = (filters->>'school_id')::bigint)
        AND (NOT filters ? 'grade_level' OR r.grade_level = (filters->>'grade_level')::smallint)
        AND (NOT filters ? 'model_id' OR r.model_id = (filters->>'model_id')::bigint)
        AND (NOT filters ? 'validation_status' OR r.review_status = filters->>'validation_status')
        AND (NOT filters ? 'task_type' OR r.task_type = filters->>'task_type')
        AND (NOT filters ? 'from' OR r.date_generated >= (filters->>'from')::timestamptz)
        AND (NOT filters ? 'to' OR r.date_generated <= (filters->>'to')::timestamptz)
), page AS MATERIALIZED (
    SELECT * FROM filtered r WHERE after_time IS NULL
        OR (NOT oldest_first AND (r.date_generated,r.result_id) < (after_time,after_id))
        OR (oldest_first AND (r.date_generated,r.result_id) > (after_time,after_id))
    ORDER BY CASE WHEN oldest_first THEN r.date_generated END ASC,
        CASE WHEN oldest_first THEN r.result_id END ASC,
        CASE WHEN NOT oldest_first THEN r.date_generated END DESC,
        CASE WHEN NOT oldest_first THEN r.result_id END DESC
    LIMIT least(greatest(coalesce(page_limit,1),1),100) + 1
), projected AS (
    SELECT date_generated, result_id, jsonb_build_object(
        'result_id',result_id::text,'student_id',student_id::text,'sample_id',sample_id::text,
        'revision',revision,'task_type',task_type,'classification',classification,
        'class_scores',class_probabilities,'predicted_class_score',confidence_score,
        'decision_rule',decision_rule,'date_generated',date_generated,'provenance',provenance,
        'model',jsonb_build_object('model_id',model_id::text,
            'model_key',CASE WHEN provenance = 'verified' THEN model_snapshot->>'model_key' END,
            'model_version',CASE WHEN provenance = 'verified' THEN model_snapshot->>'model_version' END,
            'architecture',CASE WHEN provenance = 'verified' THEN model_snapshot->>'architecture' END,
            'task_type',task_type,
            'class_labels',CASE WHEN task_type='binary' THEN '["Normal","High Potential"]'::jsonb
                ELSE '["Normal","Low Potential","High Potential"]'::jsonb END,
            'preprocessing_key',CASE WHEN provenance='verified' THEN model_snapshot->>'preprocessing_key' END,
            'decision_rule',decision_rule,'provenance',provenance,
            'is_selectable',false,'is_default',false,'evaluation',NULL),
        'report',jsonb_build_object('report_id',report_id::text,'report_type',report_type),
        'review',jsonb_build_object('status',review_status,'assigned_expert_id',assigned_expert_id,
            'expert_id',expert_id,'remarks',remarks,'expert_recommendation',nullif(btrim(expert_recommendation),''),
            'follow_up_needed',follow_up_needed,'validation_date',validation_date,
            'revision',review_revision,'provenance',review_provenance)
        ) AS data, report_id,report_type,
        CASE WHEN jsonb_typeof(school_context)='object'
            AND school_context->>'school_id' ~ '^[1-9][0-9]{0,18}$'
            AND jsonb_typeof(school_context->'school_name')='string'
            AND length(btrim(school_context->>'school_name'))>0
            AND school_context->'grade_level' IN ('1'::jsonb,'2'::jsonb,'3'::jsonb)
        THEN jsonb_build_object('school_id',school_context->>'school_id',
            'school_name',school_context->>'school_name','grade_level',school_context->'grade_level')
        ELSE NULL END AS school_context FROM page
), response_rows AS (
    SELECT date_generated,result_id,CASE WHEN resource='report' THEN
        (data - ARRAY['sample_id','revision','decision_rule','report']) || jsonb_build_object(
            'report_id',report_id::text,'report_type',report_type,'school_context',school_context)
        ELSE data END AS data FROM projected
)
SELECT jsonb_build_object('code',gate.code,
    'found',resource <> 'history' OR EXISTS (SELECT 1 FROM student_context WHERE student_id=target_id),
    'rows',coalesce((SELECT jsonb_agg(data ORDER BY
    CASE WHEN oldest_first THEN date_generated END ASC, CASE WHEN oldest_first THEN result_id END ASC,
    CASE WHEN NOT oldest_first THEN date_generated END DESC, CASE WHEN NOT oldest_first THEN result_id END DESC)
    FROM response_rows),'[]'::jsonb)) FROM gate;
$$;
REVOKE ALL ON FUNCTION public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)
    FROM PUBLIC, anon, authenticated, service_role, graphiscan_password_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)
    TO graphiscan_api_reader;
COMMIT;
