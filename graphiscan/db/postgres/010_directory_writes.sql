-- Apply once after 001-009 as the reviewed owner. No application records/grants seeded.
-- Reuses the function-only writer; reader retains no write capability.
BEGIN;
CREATE TABLE public.directory_request_keys (
    singleton boolean PRIMARY KEY CHECK (singleton), secret bytea NOT NULL CHECK (octet_length(secret)=32)
);
INSERT INTO public.directory_request_keys VALUES
    (true,sha256(convert_to(gen_random_uuid()::text || gen_random_uuid()::text,'UTF8')));
ALTER TABLE public.directory_request_keys ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.directory_request_keys FROM PUBLIC,anon,authenticated,service_role,
    graphiscan_api_reader,graphiscan_password_writer;

-- Native SHA-256 HMAC, without an extension dependency. Never expose the key.
CREATE FUNCTION public.graphiscan_directory_digest(payload jsonb) RETURNS text
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE k bytea; inner_pad bytea:=decode(repeat('36',64),'hex');
    outer_pad bytea:=decode(repeat('5c',64),'hex'); i integer;
BEGIN
    SELECT secret INTO STRICT k FROM public.directory_request_keys WHERE singleton;
    FOR i IN 0..31 LOOP
        inner_pad:=set_byte(inner_pad,i,get_byte(inner_pad,i) # get_byte(k,i));
        outer_pad:=set_byte(outer_pad,i,get_byte(outer_pad,i) # get_byte(k,i));
    END LOOP;
    RETURN encode(sha256(outer_pad || sha256(inner_pad || convert_to(payload::text,'UTF8'))),'hex');
END;
$$;

CREATE FUNCTION public.graphiscan_directory_grant(actor uuid, permission text, school bigint)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
    SELECT EXISTS (SELECT 1 FROM public.user_profiles p
        JOIN public.user_permission_grants g ON g.user_id=p.user_id
        WHERE p.user_id=actor AND p.account_status='active' AND p.role IN ('admin','researcher')
        AND g.permission_key=permission AND (g.school_id IS NULL OR g.school_id=school));
$$;

CREATE FUNCTION public.graphiscan_write_directory(subject_id uuid, provider_session_id uuid,
    operation text, target_id bigint, payload jsonb, idem_key text, request uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE actor public.user_profiles%ROWTYPE; st public.students%ROWTYPE;
    sch public.schools%ROWTYPE; previous public.api_requests%ROWTYPE;
    code text; school bigint; teacher uuid; parent uuid; digest text;
    duplicate boolean:=false; replay boolean:=false; fields text[];
BEGIN
    -- Profile SHARE locks block credential/grant/membership invalidation commits.
    -- Candidate locks use deterministic order before taking a student row lock.
    PERFORM p.user_id FROM public.user_profiles p
        WHERE p.user_id IN (subject_id,CASE WHEN payload->>'teacher_id' ~ '^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$'
            THEN (payload->>'teacher_id')::uuid END,CASE WHEN payload->>'parent_id' ~ '^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$'
            THEN (payload->>'parent_id')::uuid END)
        ORDER BY p.user_id FOR SHARE;
    PERFORM a.version FROM public.privacy_agreements a WHERE a.is_current FOR SHARE;
    SELECT * INTO actor FROM public.user_profiles WHERE user_id=subject_id;
    SELECT public.graphiscan_read_directory(subject_id,provider_session_id,'schools','',
        NULL,NULL,NULL,NULL,1,NULL)->>'code' INTO code;
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    IF actor.role NOT IN ('admin','researcher','teacher') THEN
        RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    IF operation IS NULL OR operation NOT IN ('schools.create','schools.update','students.create','students.update')
        OR jsonb_typeof(payload) IS DISTINCT FROM 'object' OR request IS NULL THEN
        RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    SELECT array_agg(key) INTO fields FROM jsonb_object_keys(payload) key;
    IF operation LIKE 'schools.%' THEN
        IF actor.role='teacher' OR NOT public.graphiscan_directory_grant(subject_id,'schools.manage',
            CASE WHEN operation='schools.update' THEN target_id END) THEN
            RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
        IF fields IS NULL OR NOT fields <@ (CASE WHEN operation='schools.create' THEN ARRAY['name']
                ELSE ARRAY['name','expected_revision'] END)
            OR jsonb_typeof(payload->'name') IS DISTINCT FROM 'string'
            OR length(btrim(payload->>'name')) NOT BETWEEN 1 AND 200
            OR (payload->>'name') ~ '[[:cntrl:]]' THEN
            RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
        IF operation='schools.update' THEN
            IF (payload->>'expected_revision') IS NULL OR (payload->>'expected_revision') !~ '^[1-9][0-9]{0,18}$'
                OR (payload->>'expected_revision')::numeric>9223372036854775807 THEN
                RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
            SELECT * INTO sch FROM public.schools WHERE school_id=target_id FOR UPDATE;
            IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
            IF sch.revision<>(payload->>'expected_revision')::bigint THEN
                RETURN jsonb_build_object('code','REVISION_CONFLICT'); END IF;
        END IF;
        SELECT EXISTS(SELECT 1 FROM public.schools s WHERE s.school_id<>coalesce(target_id,0)
            AND public.graphiscan_directory_grant(subject_id,'schools.manage',s.school_id)
            AND lower(regexp_replace(btrim(s.name),'[[:space:]]+',' ','g'))=
                lower(regexp_replace(btrim(payload->>'name'),'[[:space:]]+',' ','g'))) INTO duplicate;
        IF operation='schools.create' THEN
            INSERT INTO public.schools(name) VALUES(btrim(payload->>'name')) RETURNING * INTO sch;
        ELSE
            UPDATE public.schools SET name=btrim(payload->>'name') WHERE school_id=target_id RETURNING * INTO sch;
        END IF;
        INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
            VALUES(subject_id,operation,'school',sch.school_id::text,request::text);
        RETURN jsonb_build_object('code',NULL,'data',jsonb_build_object('school_id',sch.school_id::text,
            'name',sch.name,'revision',sch.revision,'created_at',sch.created_at),
            'warnings',CASE WHEN duplicate THEN '["duplicate_name"]'::jsonb ELSE '[]'::jsonb END);
    END IF;
    IF fields IS NULL OR NOT fields <@ ARRAY['full_name','age','school_id','grade_level','teacher_id','parent_id','expected_revision']
        OR (operation='students.create' AND (payload ? 'expected_revision' OR
            NOT payload ?& ARRAY['full_name','age','school_id','grade_level']))
        OR (operation='students.update' AND (NOT payload ? 'expected_revision' OR cardinality(fields)<2))
        OR (payload ? 'full_name' AND (jsonb_typeof(payload->'full_name') IS DISTINCT FROM 'string'
            OR length(btrim(payload->>'full_name')) NOT BETWEEN 1 AND 200 OR payload->>'full_name' ~ '[[:cntrl:]]'))
        OR (payload ? 'age' AND (jsonb_typeof(payload->'age') IS DISTINCT FROM 'number'
            OR payload->>'age' !~ '^[1-9][0-9]{0,4}$' OR (payload->>'age')::numeric>32767))
        OR (payload ? 'grade_level' AND (jsonb_typeof(payload->'grade_level') IS DISTINCT FROM 'number'
            OR payload->>'grade_level' NOT IN ('1','2','3')))
        OR (payload ? 'school_id' AND (jsonb_typeof(payload->'school_id') IS DISTINCT FROM 'string'
            OR payload->>'school_id' !~ '^[1-9][0-9]{0,18}$' OR (payload->>'school_id')::numeric>9223372036854775807))
        OR (payload ? 'teacher_id' AND (jsonb_typeof(payload->'teacher_id') IS DISTINCT FROM 'string'
            OR payload->>'teacher_id' !~ '^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$'))
        OR (payload ? 'parent_id' AND payload->'parent_id'<>'null'::jsonb AND
            (jsonb_typeof(payload->'parent_id') IS DISTINCT FROM 'string'
            OR payload->>'parent_id' !~ '^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$')) THEN
        RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    IF operation='students.create' THEN
        IF idem_key IS NULL OR idem_key !~ '^[A-Za-z0-9_-]{16,128}$' THEN
            RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
        digest:=public.graphiscan_directory_digest(payload);
        PERFORM pg_advisory_xact_lock(hashtextextended(subject_id::text || ':students.create:' || idem_key,0));
        SELECT * INTO previous FROM public.api_requests WHERE actor_id=subject_id
            AND api_requests.operation='students.create' AND idempotency_key=idem_key;
        IF FOUND THEN
            IF previous.request_digest<>digest OR previous.state<>'completed' THEN
                RETURN jsonb_build_object('code','IDEMPOTENCY_CONFLICT'); END IF;
            target_id:=previous.resource_id::bigint; replay:=true;
        END IF;
    END IF;
    IF operation='students.update' OR replay THEN
        SELECT * INTO st FROM public.students WHERE student_id=target_id FOR UPDATE;
        IF NOT FOUND OR NOT ((actor.role='teacher' AND st.teacher_id=subject_id)
            OR public.graphiscan_directory_grant(subject_id,'assignments.manage',st.school_id)) THEN
            RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
        IF NOT replay THEN
            IF payload->>'expected_revision' IS NULL OR payload->>'expected_revision' !~ '^[1-9][0-9]{0,18}$'
                OR (payload->>'expected_revision')::numeric>9223372036854775807 THEN
                RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
            IF st.revision<>(payload->>'expected_revision')::bigint THEN
                RETURN jsonb_build_object('code','REVISION_CONFLICT'); END IF;
        END IF;
    END IF;
    IF NOT replay THEN
        school:=CASE WHEN payload ? 'school_id' THEN (payload->>'school_id')::bigint ELSE st.school_id END;
        teacher:=CASE WHEN payload ? 'teacher_id' THEN (payload->>'teacher_id')::uuid
            WHEN operation='students.create' AND actor.role='teacher' THEN subject_id ELSE st.teacher_id END;
        parent:=CASE WHEN payload ? 'parent_id' THEN (payload->>'parent_id')::uuid ELSE st.parent_id END;
        IF actor.role='teacher' THEN
            IF teacher IS DISTINCT FROM subject_id OR (operation='students.update' AND school<>st.school_id)
                OR NOT EXISTS(SELECT 1 FROM public.school_memberships m
                    WHERE m.user_id=subject_id AND m.school_id=school) THEN
                RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
        ELSIF NOT public.graphiscan_directory_grant(subject_id,'assignments.manage',school) THEN
            RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
        PERFORM s.school_id FROM public.schools s WHERE s.school_id=school FOR SHARE;
        IF NOT FOUND THEN RETURN jsonb_build_object('code','INVALID_ASSIGNMENT'); END IF;
        PERFORM p.user_id FROM public.user_profiles p WHERE p.user_id IN (teacher,parent)
            ORDER BY p.user_id FOR SHARE;
        IF teacher IS NULL AND operation='students.create' THEN
            RETURN jsonb_build_object('code','INVALID_ASSIGNMENT'); END IF;
        IF teacher IS NOT NULL AND NOT EXISTS(SELECT 1 FROM public.user_profiles p
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
        IF operation='students.create' THEN
            INSERT INTO public.students(full_name,age,school_id,grade_level,teacher_id,parent_id)
                VALUES(btrim(payload->>'full_name'),(payload->>'age')::smallint,school,
                    (payload->>'grade_level')::smallint,teacher,parent) RETURNING * INTO st;
            INSERT INTO public.api_requests(actor_id,operation,idempotency_key,request_digest,state,resource_type,resource_id)
                VALUES(subject_id,'students.create',idem_key,digest,'completed','student',st.student_id::text);
        ELSE
            UPDATE public.students SET full_name=CASE WHEN payload ? 'full_name' THEN btrim(payload->>'full_name') ELSE full_name END,
                age=CASE WHEN payload ? 'age' THEN (payload->>'age')::smallint ELSE age END,
                grade_level=CASE WHEN payload ? 'grade_level' THEN (payload->>'grade_level')::smallint ELSE grade_level END,
                school_id=school,teacher_id=teacher,parent_id=parent WHERE student_id=target_id RETURNING * INTO st;
        END IF;
        INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
            VALUES(subject_id,operation,'student',st.student_id::text,request::text);
    END IF;
    SELECT EXISTS(SELECT 1 FROM public.students s WHERE s.student_id<>st.student_id
        AND s.school_id=st.school_id AND s.grade_level=st.grade_level
        AND (s.teacher_id=subject_id OR public.graphiscan_directory_grant(subject_id,'assignments.manage',s.school_id))
        AND lower(regexp_replace(btrim(s.full_name),'[[:space:]]+',' ','g'))=
            lower(regexp_replace(btrim(st.full_name),'[[:space:]]+',' ','g'))) INTO duplicate;
    RETURN jsonb_build_object('code',NULL,'data',jsonb_build_object('student_id',st.student_id::text,
        'full_name',st.full_name,'age',st.age,'school_id',st.school_id::text,'grade_level',st.grade_level,
        'teacher_id',st.teacher_id::text,'parent_id',st.parent_id::text,'revision',st.revision,
        'created_at',st.created_at,'updated_at',st.updated_at),
        'warnings',CASE WHEN duplicate THEN '["duplicate_name"]'::jsonb ELSE '[]'::jsonb END);
END;
$$;
REVOKE ALL ON FUNCTION public.graphiscan_directory_digest(jsonb),
    public.graphiscan_directory_grant(uuid,text,bigint),
    public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_password_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)
    TO graphiscan_password_writer;
COMMIT;
