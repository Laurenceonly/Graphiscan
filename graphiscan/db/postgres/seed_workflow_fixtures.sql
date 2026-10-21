-- SOURCE ONLY, after 015. Use the generated 015_workflow_fixtures.sql bundle.
-- Exact fictional Auth identities only. No credential or acceptance writes.
BEGIN;
DO $setup$
DECLARE administrator uuid; teacher uuid; expert uuid; parent uuid; school bigint; student bigint;
    audience uuid[]; person record; notice text := WORKFLOW_NOTICE_TEXT;
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
