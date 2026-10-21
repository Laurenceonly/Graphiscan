-- Apply ONLY this bundle once; do not also apply 015 or seed_workflow_fixtures.sql.
-- Atomic migration + four-account fictional setup. No passwords or acceptances.
-- UNAPPLIED 015, after 001-014. No notice/accounts/grants are seeded here.
-- Existing single-account and ordinary notice behavior is preserved.
BEGIN;
ALTER TABLE public.privacy_agreements ADD COLUMN test_subject_ids uuid[];
ALTER TABLE public.privacy_agreements ADD CONSTRAINT privacy_test_audience_valid CHECK (
    test_subject_ids IS NULL OR (
        test_subject_id IS NULL AND cardinality(test_subject_ids) BETWEEN 1 AND 16
        AND array_ndims(test_subject_ids)=1 AND array_position(test_subject_ids,NULL) IS NULL
    ));
CREATE OR REPLACE FUNCTION public.graphiscan_accept_privacy(subject_id uuid, provider_session_id uuid,
                                                requested_version text, request uuid)
RETURNS TABLE(outcome text, agreement_version text, accepted_at timestamptz)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE p public.user_profiles%ROWTYPE; a public.privacy_agreements%ROWTYPE;
        inserted_id bigint; saved_at timestamptz;
BEGIN
    -- Serialize with profile/security writes and other accepts for this subject.
    SELECT * INTO p FROM public.user_profiles WHERE user_id=subject_id FOR UPDATE;
    IF NOT EXISTS (
        SELECT 1 FROM public.graphiscan_session_state(subject_id,provider_session_id) s
        WHERE (s.not_after IS NULL OR s.not_after > clock_timestamp())
          AND (p.user_id IS NULL OR s.created_at >= p.sessions_valid_after)
          AND NOT EXISTS (SELECT 1 FROM public.app_session_revocations r WHERE r.session_id=s.id)
    ) OR coalesce(p.credential_update_pending,false) THEN
        RETURN QUERY SELECT 'invalid_session'::text,NULL::text,NULL::timestamptz; RETURN;
    END IF;
    IF p.user_id IS NULL OR p.account_status <> 'active' THEN
        RETURN QUERY SELECT 'account_unavailable'::text,NULL::text,NULL::timestamptz; RETURN;
    END IF;
    IF p.must_change_password THEN
        RETURN QUERY SELECT 'password_required'::text,NULL::text,NULL::timestamptz; RETURN;
    END IF;
    -- A publisher updating is_current must wait for this row lock. If it
    -- already changed while we waited, READ COMMITTED rechecks the predicate.
    SELECT * INTO a FROM public.privacy_agreements WHERE is_current FOR SHARE;
    IF a.version IS NULL OR a.approved_by IS NULL OR a.approved_at > clock_timestamp()
       OR a.published_at IS NULL OR a.published_at > clock_timestamp()
       OR a.content_sha256 <> encode(sha256(convert_to(a.content,'UTF8')),'hex')
       OR (a.test_subject_id IS NOT NULL AND a.test_subject_id <> subject_id)
       OR (a.test_subject_ids IS NOT NULL AND NOT (subject_id = ANY(a.test_subject_ids))) THEN
        RETURN QUERY SELECT 'agreement_unavailable'::text,NULL::text,NULL::timestamptz; RETURN;
    END IF;
    IF a.version IS DISTINCT FROM requested_version THEN
        RETURN QUERY SELECT 'agreement_changed'::text,NULL::text,NULL::timestamptz; RETURN;
    END IF;
    INSERT INTO public.privacy_agreement_acceptances AS acceptance(user_id,agreement_version)
        VALUES (subject_id,a.version)
        ON CONFLICT ON CONSTRAINT privacy_agreement_acceptances_user_id_agreement_version_key DO NOTHING
        RETURNING acceptance.acceptance_id INTO inserted_id;
    IF inserted_id IS NOT NULL THEN
        INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
            VALUES(subject_id,'privacy.accepted','privacy_agreement',a.version,request::text);
    END IF;
    SELECT acceptance.accepted_at INTO saved_at FROM public.privacy_agreement_acceptances acceptance
        WHERE acceptance.user_id=subject_id AND acceptance.agreement_version=a.version;
    RETURN QUERY SELECT 'accepted'::text,a.version,saved_at;
END;
$$;

CREATE OR REPLACE FUNCTION public.graphiscan_read_directory(
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
        AND (a.test_subject_ids IS NULL OR p.user_id = ANY(a.test_subject_ids))
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

CREATE OR REPLACE FUNCTION public.graphiscan_read_screenings(
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
        AND (a.test_subject_ids IS NULL OR p.user_id = ANY(a.test_subject_ids))
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

-- SOURCE ONLY, after 015. Use the generated 015_workflow_fixtures.sql bundle.
-- Exact fictional Auth identities only. No credential or acceptance writes.
DO $setup$
DECLARE administrator uuid; teacher uuid; expert uuid; parent uuid; school bigint; student bigint;
    audience uuid[]; person record; notice text := $workflow_notice$GraphiScan fictional workflow test notice
Version: graphiscan-workflow-test-v1

This is a development test for specifically issued fictional GraphiScan admin,
teacher, expert and parent accounts. The operator uses these accounts to test
different roles. They do not represent actual staff, clinicians, guardians or
children. Use only the named synthetic school/student fixture and generated
handwriting test images. Do not enter real student names, handwriting, school
records, health information or other personal records.

The test covers sign-in, mandatory first-login password change, explicit notice
acceptance, school/student links, handwriting upload, model selection, expert
assignment and review, and parent access after validation. The test records
fictional account profiles and relationships, the synthetic student's details,
normalized test images, model outputs and model identity, human-entered test
reviews and recommendations, report history, and related audit activity.

Supabase Auth manages test credentials and sessions. The application stores
test records in PostgreSQL and generated images in private Storage. The API
checks account status, onboarding, role and current record relationships.
Images are requested through the authorized API. These implemented controls
are being tested; this notice does not certify production protections.

The teacher account can submit samples for its assigned synthetic student.
The admin account can manage assignments only for the designated synthetic
school. The assigned expert can enter a test review. The linked parent can
access a result only while its current review is Validated. A later Flagged
review removes subsequent parent access through the API. Previously downloaded
copies cannot be recalled by that change. Test reviewers must label their
remarks and recommendations as fictional and must not provide advice about a
real child.

GraphiScan's current hosted models produce Normal or High Potential screening
labels. Outputs are not a diagnosis or evidence about any real person's health.
This exercise does not authorize collection of real student data, guardian
participation on behalf of a child, model training, research reuse, or production
deployment. Completing notice acceptance does not grant permissions or establish
that the workflow has passed testing.

The operator must keep passwords and session tokens private and outside chat,
screenshots, commits and reports. Test accounts start with temporary passwords
chosen and stored privately by the operator. Each new account must complete its
own password-change and explicit notice-acceptance steps; no acceptance is
inserted automatically.

You may decline by leaving the test without accepting. Questions about this
fictional exercise go to the GraphiScan project team through the existing project
contact. No real-user privacy contact, retention duration or legal approval is
asserted here. Test records and audit history may persist until the operator
performs a separately reviewed cleanup; automatic deletion is not promised.

The system records the accepted version and server timestamp. A different
published version requires a new explicit acceptance. Earlier acceptances stay
associated with their original text. Real-user purposes, participant permissions,
responsible institution, recipients, retention and request procedures require
separate review before any real-data use.
$workflow_notice$;
BEGIN
    -- Preserve the notice identity when a Windows editor changes file line endings.
    notice:=replace(notice,chr(13)||chr(10),chr(10));
    LOCK TABLE public.user_profiles,public.schools,public.students,
        public.user_permission_grants,public.school_memberships,public.assignment_eligibilities,
        public.privacy_agreements IN SHARE ROW EXCLUSIVE MODE;
    -- Do not seed against missing, unconfirmed, banned or ambiguous Auth identities.
    IF (SELECT count(*) FROM auth.users u WHERE lower(u.email) IN (
        'graphiscan.test@example.invalid','graphiscan.teacher.test@example.invalid',
        'graphiscan.expert.test@example.invalid','graphiscan.parent.test@example.invalid')) <> 4
        OR EXISTS (SELECT 1 FROM auth.users u WHERE lower(u.email) IN (
        'graphiscan.test@example.invalid','graphiscan.teacher.test@example.invalid',
        'graphiscan.expert.test@example.invalid','graphiscan.parent.test@example.invalid')
        AND (u.email_confirmed_at IS NULL OR to_jsonb(u)->>'deleted_at' IS NOT NULL
             OR (to_jsonb(u)->>'banned_until')::timestamptz > clock_timestamp())) THEN
        RAISE EXCEPTION 'Expected four distinct confirmed active fictional Auth accounts; no changes applied';
    END IF;
    SELECT id INTO STRICT administrator FROM auth.users WHERE lower(email)='graphiscan.test@example.invalid' FOR SHARE;
    SELECT id INTO STRICT teacher FROM auth.users WHERE lower(email)='graphiscan.teacher.test@example.invalid' FOR SHARE;
    SELECT id INTO STRICT expert FROM auth.users WHERE lower(email)='graphiscan.expert.test@example.invalid' FOR SHARE;
    SELECT id INTO STRICT parent FROM auth.users WHERE lower(email)='graphiscan.parent.test@example.invalid' FOR SHARE;
    audience:=ARRAY[administrator,teacher,expert,parent];
    IF NOT EXISTS (SELECT 1 FROM public.user_profiles WHERE user_id=administrator
        AND full_name='Synthetic Test Admin' AND role='admin' AND account_status='active'
        AND NOT must_change_password AND NOT credential_update_pending) THEN
        RAISE EXCEPTION 'Existing fictional admin identity/onboarding differs; review before setup';
    END IF;
    IF EXISTS (SELECT 1 FROM public.user_profiles WHERE user_id IN (teacher,expert,parent)) THEN
        RAISE EXCEPTION 'A proposed role profile already exists; no overwrite or automatic reset';
    END IF;
    IF EXISTS (SELECT 1 FROM public.user_permission_grants WHERE user_id=ANY(audience))
        OR EXISTS (SELECT 1 FROM public.school_memberships WHERE user_id=ANY(audience))
        OR EXISTS (SELECT 1 FROM public.assignment_eligibilities
                   WHERE actor_id=ANY(audience) OR candidate_id=ANY(audience)) THEN
        RAISE EXCEPTION 'Existing fixture scope requires explicit review; no privilege changes applied';
    END IF;
    IF EXISTS (SELECT 1 FROM public.schools WHERE lower(name)='graphiscan synthetic workflow school')
        OR EXISTS (SELECT 1 FROM public.students WHERE lower(full_name)='synthetic workflow student') THEN
        RAISE EXCEPTION 'A named workflow fixture already exists; no existing record will be reused';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.privacy_agreements WHERE is_current
        AND version='graphiscan-test-v1' AND test_subject_id=administrator AND test_subject_ids IS NULL
        AND approved_by=administrator AND approved_at <= clock_timestamp() AND published_at <= clock_timestamp()
        AND content_sha256=encode(sha256(convert_to(content,'UTF8')),'hex'))
        OR EXISTS (SELECT 1 FROM public.privacy_agreements WHERE version='graphiscan-workflow-test-v1') THEN
        RAISE EXCEPTION 'Notice publication state differs; preserve existing text and review';
    END IF;
    INSERT INTO public.user_profiles(user_id,full_name,role,account_status,must_change_password,created_by)
        VALUES (teacher,'Synthetic Test Teacher','teacher','active',true,administrator),
               (expert,'Synthetic Test Expert','expert','active',true,administrator),
               (parent,'Synthetic Test Parent','parent','active',true,administrator);
    INSERT INTO public.schools(name) VALUES('GraphiScan Synthetic Workflow School') RETURNING school_id INTO school;
    INSERT INTO public.students(full_name,age,school_id,grade_level,teacher_id,parent_id)
        VALUES('Synthetic Workflow Student',8,school,2,teacher,parent) RETURNING student_id INTO student;
    INSERT INTO public.user_permission_grants(user_id,permission_key,school_id,granted_by)
        VALUES(administrator,'assignments.manage',school,administrator);
    INSERT INTO public.school_memberships(user_id,school_id,created_by)
        VALUES(teacher,school,administrator),(expert,school,administrator);
    INSERT INTO public.assignment_eligibilities(actor_id,candidate_id,school_id,assignment_role,granted_by)
        VALUES(administrator,teacher,school,'teacher',administrator),
              (administrator,expert,school,'expert',administrator),
              (administrator,parent,school,'parent',administrator),
              (teacher,parent,school,'parent',administrator);
    UPDATE public.privacy_agreements SET is_current=false WHERE version='graphiscan-test-v1' AND is_current;
    INSERT INTO public.privacy_agreements(version,title,content,content_sha256,approved_by,
        approved_at,published_at,is_current,test_subject_ids)
        VALUES('graphiscan-workflow-test-v1','GraphiScan fictional workflow test notice',notice,
            encode(sha256(convert_to(notice,'UTF8')),'hex'),administrator,
            clock_timestamp(),clock_timestamp(),true,audience);
    FOR person IN SELECT unnest(ARRAY[teacher,expert,parent]) AS id LOOP
        INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id)
            VALUES(administrator,'test_fixture.profile_created','user_profile',person.id::text);
    END LOOP;
    INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id) VALUES
        (administrator,'test_fixture.school_created','school',school::text),
        (administrator,'test_fixture.student_created','student',student::text),
        (administrator,'test_fixture.scope_created','school',school::text),
        (administrator,'test_fixture.notice_published','privacy_agreement','graphiscan-workflow-test-v1');
END;
$setup$;

COMMIT;
