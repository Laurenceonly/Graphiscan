-- Reviewed owner migration after 021 (022 is independent). Never run as an app user.
-- Existing staff school memberships retain Grades 1-3 on migration; new memberships
-- receive no grade eligibility until explicitly configured. No people, consent,
-- actor-specific eligibility, credentials or individual review assignments seeded.
BEGIN;

CREATE TABLE public.user_school_grades (
    user_id uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE CASCADE,
    school_id bigint NOT NULL REFERENCES public.schools(school_id) ON DELETE RESTRICT,
    grade_level smallint NOT NULL CHECK (grade_level BETWEEN 1 AND 3),
    created_by uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id,school_id,grade_level)
);
ALTER TABLE public.user_school_grades ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.user_school_grades FROM PUBLIC,anon,authenticated,service_role,
    graphiscan_api_reader,graphiscan_admin_writer,graphiscan_password_writer;

-- Refuse to silently expand membership to reconcile inconsistent legacy records.
DO $$ BEGIN
    IF EXISTS(SELECT 1 FROM public.students s JOIN public.user_profiles p ON p.user_id=s.teacher_id
        WHERE p.role='teacher' AND p.account_status='active' AND NOT p.must_change_password
        AND NOT EXISTS(SELECT 1 FROM public.school_memberships m WHERE m.user_id=p.user_id AND m.school_id=s.school_id))
    OR EXISTS(SELECT 1 FROM public.screening_expert_assignments a
        JOIN public.user_profiles p ON p.user_id=a.assigned_expert_id
        JOIN public.screening_results r ON r.result_id=a.result_id
        JOIN public.handwriting_samples h ON h.sample_id=r.sample_id
        JOIN public.students s ON s.student_id=h.student_id
        WHERE p.role='expert' AND p.account_status='active' AND NOT p.must_change_password
        AND NOT EXISTS(SELECT 1 FROM public.school_memberships m WHERE m.user_id=p.user_id AND m.school_id=s.school_id))
    THEN RAISE EXCEPTION 'Review existing staff ownership without school membership before installing grade assignments'; END IF;
END $$;
INSERT INTO public.user_school_grades(user_id,school_id,grade_level,created_by)
SELECT m.user_id,m.school_id,g::smallint,m.created_by FROM public.school_memberships m
JOIN public.user_profiles p ON p.user_id=m.user_id CROSS JOIN generate_series(1,3) g
WHERE p.role IN ('teacher','expert');
CREATE TRIGGER grade_scope_revision AFTER INSERT OR UPDATE OR DELETE ON public.user_school_grades
    FOR EACH ROW EXECUTE FUNCTION public.touch_account_scope_revision();

CREATE FUNCTION public.graphiscan_grade_allowed(candidate uuid,school bigint,grade smallint)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
SELECT EXISTS(SELECT 1 FROM public.user_school_grades g
    JOIN public.school_memberships m ON m.user_id=g.user_id AND m.school_id=g.school_id
    JOIN public.user_profiles p ON p.user_id=g.user_id
    WHERE g.user_id=candidate AND g.school_id=school AND g.grade_level=grade
        AND p.role IN ('teacher','expert') AND p.account_status='active' AND NOT p.credential_update_pending);
$$;
REVOKE ALL ON FUNCTION public.graphiscan_grade_allowed(uuid,bigint,smallint)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_admin_writer,graphiscan_password_writer;

CREATE FUNCTION public.graphiscan_get_role_assignments(subject_id uuid,provider_session_id uuid,target_id uuid)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text; target public.user_profiles%ROWTYPE;
BEGIN
    code:=public.graphiscan_admin_account_gate(subject_id,provider_session_id);
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    SELECT * INTO target FROM public.user_profiles WHERE user_id=target_id;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    IF target.role NOT IN ('teacher','expert','parent') OR target_id=subject_id THEN RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    RETURN jsonb_build_object('code',NULL,'data',jsonb_build_object(
        'user_id',target_id::text,'role',target.role,'revision',target.revision,
        'school_grades',coalesce((SELECT jsonb_agg(jsonb_build_object('school_id',g.school_id::text,
            'school_name',s.name,'grade_level',g.grade_level) ORDER BY g.school_id,g.grade_level)
            FROM public.user_school_grades g JOIN public.schools s ON s.school_id=g.school_id
            WHERE g.user_id=target_id AND target.role IN ('teacher','expert')),'[]'::jsonb),
        'students',coalesce((SELECT jsonb_agg(jsonb_build_object('student_id',s.student_id::text,
            'full_name',s.full_name,'school_id',s.school_id::text,'school_name',school.name,
            'grade_level',s.grade_level,'revision',s.revision,'parent_id',s.parent_id::text) ORDER BY s.school_id,s.grade_level,s.student_id)
            FROM public.students s JOIN public.schools school ON school.school_id=s.school_id
            WHERE target.role='parent' AND s.parent_id=target_id
                AND public.graphiscan_directory_grant(subject_id,'assignments.manage',s.school_id)),'[]'::jsonb)));
END;
$$;

CREATE FUNCTION public.graphiscan_set_role_assignments(subject_id uuid,provider_session_id uuid,target_id uuid,
    payload jsonb,request uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text; target public.user_profiles%ROWTYPE; item jsonb; st public.students%ROWTYPE;
    selected_schools bigint[]; student_ids bigint[]; old_parents uuid[]; changed integer:=0; affected integer;
BEGIN
    IF jsonb_typeof(payload) IS DISTINCT FROM 'object' OR request IS NULL
        OR NOT payload ? 'expected_revision' OR jsonb_typeof(payload->'expected_revision') IS DISTINCT FROM 'number'
        OR coalesce(payload->>'expected_revision','') !~ '^[1-9][0-9]{0,18}$'
        OR (payload->>'expected_revision')::numeric>9223372036854775806
        OR NOT (payload ? 'school_grades' OR payload ? 'student_links')
        OR payload - ARRAY['expected_revision','school_grades','student_links']<>'{}'::jsonb
        OR (payload ? 'school_grades' AND payload ? 'student_links') THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    IF payload ? 'school_grades' THEN
        IF jsonb_typeof(payload->'school_grades') IS DISTINCT FROM 'array' OR jsonb_array_length(payload->'school_grades')>384
            THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
        FOR item IN SELECT value FROM jsonb_array_elements(payload->'school_grades') LOOP
            IF jsonb_typeof(item) IS DISTINCT FROM 'object' OR NOT item ?& ARRAY['school_id','grade_level']
                OR item - ARRAY['school_id','grade_level']<>'{}'::jsonb
                OR jsonb_typeof(item->'school_id') IS DISTINCT FROM 'string'
                OR coalesce(item->>'school_id','') !~ '^[1-9][0-9]{0,18}$'
                OR (item->>'school_id')::numeric>9223372036854775807
                OR jsonb_typeof(item->'grade_level') IS DISTINCT FROM 'number'
                OR item->>'grade_level' NOT IN ('1','2','3') THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
        END LOOP;
        IF EXISTS(SELECT 1 FROM jsonb_array_elements(payload->'school_grades') e GROUP BY e->>'school_id',e->>'grade_level' HAVING count(*)>1)
            THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
        SELECT coalesce(array_agg(DISTINCT (e->>'school_id')::bigint),'{}'::bigint[]) INTO selected_schools FROM jsonb_array_elements(payload->'school_grades') e;
        IF EXISTS(SELECT 1 FROM unnest(selected_schools) n LEFT JOIN public.schools s ON s.school_id=n WHERE s.school_id IS NULL)
            THEN RETURN jsonb_build_object('code','INVALID_ASSIGNMENT'); END IF;
    ELSE
        IF jsonb_typeof(payload->'student_links') IS DISTINCT FROM 'array' OR jsonb_array_length(payload->'student_links') NOT BETWEEN 1 AND 128
            THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
        FOR item IN SELECT value FROM jsonb_array_elements(payload->'student_links') LOOP
            IF jsonb_typeof(item) IS DISTINCT FROM 'object' OR NOT item ?& ARRAY['student_id','expected_revision','linked']
                OR item - ARRAY['student_id','expected_revision','linked']<>'{}'::jsonb
                OR jsonb_typeof(item->'student_id') IS DISTINCT FROM 'string'
                OR coalesce(item->>'student_id','') !~ '^[1-9][0-9]{0,18}$'
                OR (item->>'student_id')::numeric>9223372036854775807
                OR jsonb_typeof(item->'expected_revision') IS DISTINCT FROM 'number'
                OR coalesce(item->>'expected_revision','') !~ '^[1-9][0-9]{0,18}$'
                OR (item->>'expected_revision')::numeric>9223372036854775806
                OR jsonb_typeof(item->'linked') IS DISTINCT FROM 'boolean' THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
        END LOOP;
        IF EXISTS(SELECT 1 FROM jsonb_array_elements(payload->'student_links') e GROUP BY e->>'student_id' HAVING count(*)>1)
            THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
        SELECT array_agg((e->>'student_id')::bigint) INTO student_ids FROM jsonb_array_elements(payload->'student_links') e;
    END IF;
    -- Shared ordering with student writers; expected student revisions reject a concurrent transfer.
    PERFORM user_id FROM public.user_profiles WHERE user_id IN(subject_id,target_id)
        OR user_id IN(SELECT parent_id FROM public.students WHERE student_id=ANY(student_ids)) ORDER BY user_id FOR UPDATE;
    PERFORM version FROM public.privacy_agreements WHERE is_current FOR SHARE;
    code:=public.graphiscan_admin_account_gate(subject_id,provider_session_id);
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    SELECT * INTO target FROM public.user_profiles WHERE user_id=target_id;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    IF target_id=subject_id OR target.role NOT IN ('teacher','expert','parent') THEN RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    IF target.credential_update_pending THEN RETURN jsonb_build_object('code','ACCOUNT_OPERATION_PENDING'); END IF;
    IF target.revision<>(payload->>'expected_revision')::bigint THEN RETURN jsonb_build_object('code','REVISION_CONFLICT'); END IF;
    IF (target.role='parent') IS DISTINCT FROM (payload ? 'student_links') THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    IF target.role IN ('teacher','expert') THEN
        DELETE FROM public.user_school_grades g WHERE g.user_id=target_id AND NOT EXISTS(
            SELECT 1 FROM jsonb_array_elements(payload->'school_grades') e WHERE (e->>'school_id')::bigint=g.school_id AND (e->>'grade_level')::smallint=g.grade_level);
        GET DIAGNOSTICS affected=ROW_COUNT;changed:=changed+affected;
        DELETE FROM public.school_memberships m WHERE m.user_id=target_id AND NOT(m.school_id=ANY(selected_schools));
        GET DIAGNOSTICS affected=ROW_COUNT;changed:=changed+affected;
        INSERT INTO public.school_memberships(user_id,school_id,created_by)
            SELECT target_id,n,subject_id FROM unnest(selected_schools) n ON CONFLICT DO NOTHING;
        GET DIAGNOSTICS affected=ROW_COUNT;changed:=changed+affected;
        INSERT INTO public.user_school_grades(user_id,school_id,grade_level,created_by)
            SELECT target_id,(e->>'school_id')::bigint,(e->>'grade_level')::smallint,subject_id FROM jsonb_array_elements(payload->'school_grades') e ON CONFLICT DO NOTHING;
        GET DIAGNOSTICS affected=ROW_COUNT;changed:=changed+affected;
    ELSE
        PERFORM student_id FROM public.students WHERE student_id=ANY(student_ids) ORDER BY student_id FOR UPDATE;
        -- Validate every delta before changing any link, including removals.
        FOR item IN SELECT value FROM jsonb_array_elements(payload->'student_links') LOOP
            SELECT * INTO st FROM public.students WHERE student_id=(item->>'student_id')::bigint;
            IF NOT FOUND OR NOT public.graphiscan_directory_grant(subject_id,'assignments.manage',st.school_id)
                THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
            IF st.revision<>(item->>'expected_revision')::bigint OR (NOT(item->>'linked')::boolean AND st.parent_id IS DISTINCT FROM target_id)
                THEN RETURN jsonb_build_object('code','REVISION_CONFLICT'); END IF;
        END LOOP;
        SELECT array_agg(DISTINCT parent_id) INTO old_parents FROM public.students WHERE student_id=ANY(student_ids) AND parent_id IS NOT NULL;
        FOR item IN SELECT value FROM jsonb_array_elements(payload->'student_links') LOOP
            UPDATE public.students SET parent_id=CASE WHEN (item->>'linked')::boolean THEN target_id ELSE NULL END
                WHERE student_id=(item->>'student_id')::bigint AND parent_id IS DISTINCT FROM CASE WHEN (item->>'linked')::boolean THEN target_id ELSE NULL::uuid END;
            GET DIAGNOSTICS affected=ROW_COUNT;changed:=changed+affected;
        END LOOP;
        IF changed>0 THEN
            UPDATE public.user_profiles SET security_version=security_version+1 WHERE role='parent' AND (user_id=target_id OR user_id=ANY(old_parents));
        END IF;
    END IF;
    IF changed>0 THEN INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
        VALUES(subject_id,'accounts.assignments.updated','account',target_id::text,request::text); END IF;
    RETURN public.graphiscan_get_role_assignments(subject_id,provider_session_id,target_id);
END;
$$;
REVOKE ALL ON FUNCTION public.graphiscan_get_role_assignments(uuid,uuid,uuid),public.graphiscan_set_role_assignments(uuid,uuid,uuid,jsonb,uuid)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_admin_writer,graphiscan_password_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_get_role_assignments(uuid,uuid,uuid) TO graphiscan_api_reader;
GRANT EXECUTE ON FUNCTION public.graphiscan_set_role_assignments(uuid,uuid,uuid,jsonb,uuid) TO graphiscan_admin_writer;

-- Runtime grade/ownership integration follows below. All changes are atomic.
CREATE FUNCTION public.graphiscan_assignment_options_by_grade(subject_id uuid,provider_session_id uuid,
    school bigint,grade smallint,after_time timestamptz,after_user uuid,page_limit integer)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
WITH actor AS MATERIALIZED (
    SELECT p.role,public.graphiscan_read_directory(subject_id,provider_session_id,'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' AS code
    FROM (SELECT 1) seed LEFT JOIN public.user_profiles p ON p.user_id=subject_id
), gate AS MATERIALIZED (
    SELECT actor.role,CASE WHEN actor.code IS NOT NULL THEN actor.code
        WHEN school IS NULL OR school<=0 OR page_limit IS NULL OR page_limit NOT BETWEEN 1 AND 100
            OR (grade IS NOT NULL AND grade NOT BETWEEN 1 AND 3) OR ((after_time IS NULL)<>(after_user IS NULL)) THEN 'INVALID_QUERY'
        WHEN NOT ((role='teacher' AND EXISTS(SELECT 1 FROM public.school_memberships m WHERE m.user_id=subject_id AND m.school_id=school))
            OR public.graphiscan_directory_grant(subject_id,'assignments.manage',school)) THEN 'FORBIDDEN'
        WHEN NOT EXISTS(SELECT 1 FROM public.schools s WHERE s.school_id=school) THEN 'NOT_FOUND' ELSE NULL END AS code FROM actor
), candidates AS MATERIALIZED (
    SELECT p.user_id,p.full_name,p.role,p.created_at,
        coalesce((SELECT jsonb_agg(g.grade_level ORDER BY g.grade_level) FROM public.user_school_grades g
            WHERE g.user_id=p.user_id AND g.school_id=school AND public.graphiscan_grade_allowed(p.user_id,school,g.grade_level)),'[]'::jsonb) AS grade_levels
    FROM public.user_profiles p CROSS JOIN gate a
    WHERE a.code IS NULL AND p.account_status='active' AND NOT p.credential_update_pending AND (
        (a.role='teacher' AND p.user_id=subject_id AND p.role='teacher' AND grade IS NULL)
        OR
        (p.role IN ('teacher','expert') AND (a.role IN ('admin','researcher') OR (a.role='teacher' AND p.user_id=subject_id AND p.role='teacher'))
            AND EXISTS(SELECT 1 FROM public.user_school_grades g WHERE g.user_id=p.user_id AND g.school_id=school
                AND (grade IS NULL OR g.grade_level=grade) AND public.graphiscan_grade_allowed(p.user_id,school,g.grade_level)))
        OR (a.role IN ('admin','researcher') AND p.role='parent' AND EXISTS(SELECT 1 FROM public.students s
            WHERE s.parent_id=p.user_id AND s.school_id=school AND (grade IS NULL OR s.grade_level=grade))))
), page AS MATERIALIZED (
    SELECT * FROM candidates WHERE after_time IS NULL OR (created_at,user_id)<(after_time,after_user)
    ORDER BY created_at DESC,user_id DESC LIMIT least(greatest(coalesce(page_limit,1),1),100)+1
)
SELECT jsonb_build_object('code',gate.code,'rows',coalesce((SELECT jsonb_agg(jsonb_build_object(
    'data',jsonb_build_object('user_id',user_id::text,'full_name',full_name,'role',role,'grade_levels',grade_levels),
    'created_at',created_at) ORDER BY created_at DESC,user_id DESC) FROM page),'[]'::jsonb)) FROM gate;
$$;
CREATE OR REPLACE FUNCTION public.graphiscan_assignment_options(subject_id uuid,provider_session_id uuid,
    school bigint,after_time timestamptz,after_user uuid,page_limit integer)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
SELECT public.graphiscan_assignment_options_by_grade(subject_id,provider_session_id,school,NULL,after_time,after_user,page_limit);
$$;
REVOKE ALL ON FUNCTION public.graphiscan_assignment_options_by_grade(uuid,uuid,bigint,smallint,timestamptz,uuid,integer)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_admin_writer,graphiscan_password_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_assignment_options_by_grade(uuid,uuid,bigint,smallint,timestamptz,uuid,integer) TO graphiscan_api_reader;
-- BEGIN VERIFIED RUNTIME PATCHES
-- Refuse unknown function bodies; preserve every existing session/privacy/ownership gate.
DO $patch$ DECLARE body text; old_text text:=$old$(a.role = 'teacher' AND s.teacher_id = subject_id)$old$; BEGIN
    body:=pg_get_functiondef('public.graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)'::regprocedure);
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Role assignment migration: unexpected function body public.graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)'; END IF;
    EXECUTE replace(body,old_text,$new$(a.role = 'teacher' AND s.teacher_id = subject_id AND public.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level))$new$);
END $patch$;
DO $patch$ DECLARE body text; old_text text:=$old$WHERE h.student_id = s.student_id AND e.assigned_expert_id = subject_id))$old$; BEGIN
    body:=pg_get_functiondef('public.graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)'::regprocedure);
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Role assignment migration: unexpected function body public.graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)'; END IF;
    EXECUTE replace(body,old_text,$new$WHERE h.student_id = s.student_id AND e.assigned_expert_id = subject_id AND public.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level)))$new$);
END $patch$;
DO $patch$ DECLARE body text; old_text text:=$old$(a.role='teacher' AND s.teacher_id=subject_id)$old$; BEGIN
    body:=pg_get_functiondef('public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)'::regprocedure);
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Role assignment migration: unexpected function body public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)'; END IF;
    EXECUTE replace(body,old_text,$new$(a.role='teacher' AND s.teacher_id=subject_id AND public.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level))$new$);
END $patch$;
DO $patch$ DECLARE body text; old_text text:=$old$WHERE h.student_id=s.student_id AND e.assigned_expert_id=subject_id))$old$; BEGIN
    body:=pg_get_functiondef('public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)'::regprocedure);
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Role assignment migration: unexpected function body public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)'; END IF;
    EXECUTE replace(body,old_text,$new$WHERE h.student_id=s.student_id AND e.assigned_expert_id=subject_id AND public.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level)))$new$);
END $patch$;
DO $patch$ DECLARE body text; old_text text:=$old$(actor.role='teacher' AND st.teacher_id=subject_id)$old$; BEGIN
    body:=pg_get_functiondef('public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)'::regprocedure);
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Role assignment migration: unexpected function body public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)'; END IF;
    EXECUTE replace(body,old_text,$new$(actor.role='teacher' AND st.teacher_id=subject_id AND public.graphiscan_grade_allowed(subject_id,st.school_id,st.grade_level))$new$);
END $patch$;
DO $patch$ DECLARE body text; old_text text:=$old$        IF teacher IS NOT NULL AND NOT EXISTS(SELECT 1 FROM public.user_profiles p
            JOIN public.school_memberships m ON m.user_id=p.user_id AND m.school_id=school
            WHERE p.user_id=teacher AND p.role='teacher' AND p.account_status='active') THEN
            RETURN jsonb_build_object('code','INVALID_ASSIGNMENT'); END IF;
        IF teacher IS NOT NULL AND actor.role<>'teacher' THEN
            PERFORM e.actor_id FROM public.assignment_eligibilities e WHERE e.actor_id=subject_id
                AND e.candidate_id=teacher AND e.school_id=school AND e.assignment_role='teacher' FOR SHARE;
            IF NOT FOUND THEN RETURN jsonb_build_object('code','INVALID_ASSIGNMENT'); END IF;
        END IF;
        IF parent IS NOT NULL THEN
            PERFORM e.actor_id FROM public.assignment_eligibilities e
                JOIN public.user_profiles p ON p.user_id=e.candidate_id
                WHERE e.actor_id=subject_id AND e.candidate_id=parent AND e.school_id=school
                AND e.assignment_role='parent' AND p.role='parent' AND p.account_status='active' FOR SHARE OF e,p;
            IF NOT FOUND THEN RETURN jsonb_build_object('code','INVALID_ASSIGNMENT'); END IF;
        END IF;
$old$; BEGIN
    body:=pg_get_functiondef('public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)'::regprocedure);
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Role assignment migration: unexpected function body public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)'; END IF;
    EXECUTE replace(body,old_text,$new$        IF teacher IS NOT NULL AND NOT EXISTS(SELECT 1 FROM public.user_profiles p
            WHERE p.user_id=teacher AND p.role='teacher' AND p.account_status='active'
            AND public.graphiscan_grade_allowed(teacher,school,CASE WHEN payload ? 'grade_level' THEN (payload->>'grade_level')::smallint ELSE st.grade_level END)) THEN
            RETURN jsonb_build_object('code','INVALID_ASSIGNMENT'); END IF;
        IF actor.role='teacher' AND parent IS DISTINCT FROM st.parent_id THEN
            RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
        IF parent IS NOT NULL AND NOT EXISTS(SELECT 1 FROM public.user_profiles p
            WHERE p.user_id=parent AND p.role='parent' AND p.account_status='active' AND NOT p.credential_update_pending) THEN
            RETURN jsonb_build_object('code','INVALID_ASSIGNMENT'); END IF;
$new$);
END $patch$;
DO $patch$ DECLARE body text; old_text text:=$old$    IF candidate IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.user_profiles p JOIN public.school_memberships m ON m.user_id=p.user_id
        JOIN public.assignment_eligibilities e ON e.candidate_id=p.user_id AND e.school_id=m.school_id
        WHERE p.user_id=candidate AND p.role='expert' AND p.account_status='active'
        AND m.school_id=st.school_id AND e.actor_id=subject_id AND e.assignment_role='expert'
    ) THEN RETURN jsonb_build_object('code','INVALID_ASSIGNMENT'); END IF;
$old$; BEGIN
    body:=pg_get_functiondef('public.graphiscan_assign_expert(uuid,uuid,bigint,jsonb,uuid)'::regprocedure);
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Role assignment migration: unexpected function body public.graphiscan_assign_expert(uuid,uuid,bigint,jsonb,uuid)'; END IF;
    EXECUTE replace(body,old_text,$new$    IF candidate IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.user_profiles p WHERE p.user_id=candidate AND p.role='expert'
        AND public.graphiscan_grade_allowed(candidate,st.school_id,st.grade_level)
    ) THEN RETURN jsonb_build_object('code','INVALID_ASSIGNMENT'); END IF;
$new$);
END $patch$;
DO $patch$ DECLARE body text; old_text text:=$old$IF assigned IS DISTINCT FROM subject_id THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;$old$; BEGIN
    body:=pg_get_functiondef('public.graphiscan_write_review(uuid,uuid,bigint,jsonb,text,uuid)'::regprocedure);
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Role assignment migration: unexpected function body public.graphiscan_write_review(uuid,uuid,bigint,jsonb,text,uuid)'; END IF;
    EXECUTE replace(body,old_text,$new$IF assigned IS DISTINCT FROM subject_id OR NOT public.graphiscan_grade_allowed(subject_id,st.school_id,st.grade_level) THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;$new$);
END $patch$;
DO $patch$ DECLARE body text; old_text text:=$old$IF NOT FOUND OR st.teacher_id IS DISTINCT FROM subject_id THEN$old$; BEGIN
    body:=pg_get_functiondef('public.graphiscan_reserve_screening(uuid,uuid,jsonb,text,jsonb,text,uuid)'::regprocedure);
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Role assignment migration: unexpected function body public.graphiscan_reserve_screening(uuid,uuid,jsonb,text,jsonb,text,uuid)'; END IF;
    EXECUTE replace(body,old_text,$new$IF NOT FOUND OR st.teacher_id IS DISTINCT FROM subject_id OR NOT public.graphiscan_grade_allowed(subject_id,st.school_id,st.grade_level) THEN$new$);
END $patch$;
DO $patch$ DECLARE body text; old_text text:=$old$IF st.teacher_id IS DISTINCT FROM subject_id THEN$old$; BEGIN
    body:=pg_get_functiondef('public.graphiscan_complete_screening(uuid,uuid,text,jsonb,uuid)'::regprocedure);
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Role assignment migration: unexpected function body public.graphiscan_complete_screening(uuid,uuid,text,jsonb,uuid)'; END IF;
    EXECUTE replace(body,old_text,$new$IF st.teacher_id IS DISTINCT FROM subject_id OR NOT public.graphiscan_grade_allowed(subject_id,st.school_id,st.grade_level) THEN$new$);
END $patch$;
DO $patch$ DECLARE body text; old_text text:=$old$SELECT 1 FROM public.students WHERE student_id=job.student_id AND teacher_id=subject_id$old$; BEGIN
    body:=pg_get_functiondef('public.graphiscan_screening_request(uuid,uuid,text)'::regprocedure);
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Role assignment migration: unexpected function body public.graphiscan_screening_request(uuid,uuid,text)'; END IF;
    EXECUTE replace(body,old_text,$new$SELECT 1 FROM public.students WHERE student_id=job.student_id AND teacher_id=subject_id AND public.graphiscan_grade_allowed(subject_id,school_id,grade_level)$new$);
END $patch$;
COMMIT;
