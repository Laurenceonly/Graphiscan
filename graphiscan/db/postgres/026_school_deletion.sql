-- Owner migration after025. Admin-only, unused-school deletion; no cascades.
BEGIN;
CREATE FUNCTION public.graphiscan_school_deletion(subject_id uuid,provider_session_id uuid,
 operation text,target_id bigint,payload jsonb,idem_key text,request uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE actor public.user_profiles%ROWTYPE; school public.schools%ROWTYPE;
 code text; ref record; n bigint; total bigint:=0; student_count bigint;
 teacher_count bigint; expert_count bigint; summary jsonb;
BEGIN
 SELECT * INTO actor FROM public.user_profiles WHERE user_id=subject_id FOR SHARE;
 SELECT public.graphiscan_read_directory(subject_id,provider_session_id,'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' INTO code;
 IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
 IF actor.role IS DISTINCT FROM 'admin' OR NOT public.graphiscan_directory_grant(subject_id,'schools.manage',target_id)
 THEN RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
 IF operation IS NULL OR operation NOT IN ('schools.delete_check','schools.delete') OR request IS NULL
 OR jsonb_typeof(payload) IS DISTINCT FROM 'object' THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
 SELECT * INTO school FROM public.schools WHERE school_id=target_id FOR UPDATE;
 IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
 IF operation='schools.delete' THEN
  IF NOT payload ?& ARRAY['expected_revision','confirmation']
   OR payload - ARRAY['expected_revision','confirmation'] <> '{}'::jsonb
   OR payload->>'confirmation' IS DISTINCT FROM 'DELETE'
   OR jsonb_typeof(payload->'expected_revision') IS DISTINCT FROM 'number'
   OR payload->>'expected_revision' !~ '^[1-9][0-9]{0,18}$'
   OR (payload->>'expected_revision')::numeric>9223372036854775807
  THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
  IF school.revision<>(payload->>'expected_revision')::bigint THEN RETURN jsonb_build_object('code','REVISION_CONFLICT'); END IF;
 ELSIF payload<>'{}'::jsonb THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
 SELECT count(*) INTO student_count FROM public.students WHERE school_id=target_id;
 SELECT count(*) FILTER(WHERE p.role='teacher'),count(*) FILTER(WHERE p.role='expert')
 INTO teacher_count,expert_count FROM public.school_memberships m
 JOIN public.user_profiles p ON p.user_id=m.user_id WHERE m.school_id=target_id;
 -- Count all live FK references, including grants/grade assignments and future tables.
 FOR ref IN SELECT ns.nspname,c.relname,a.attname FROM pg_constraint fk
 JOIN pg_class c ON c.oid=fk.conrelid JOIN pg_namespace ns ON ns.oid=c.relnamespace
 JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum=fk.conkey[1]
 WHERE fk.contype='f' AND fk.confrelid='public.schools'::regclass AND cardinality(fk.conkey)=1 LOOP
  EXECUTE format('SELECT count(*) FROM %I.%I WHERE %I=$1',ref.nspname,ref.relname,ref.attname) INTO n USING target_id;
  total:=total+n;
 END LOOP;
 summary:=jsonb_build_object('school_id',school.school_id::text,'name',school.name,'revision',school.revision,
  'students',student_count,'teachers',teacher_count,'experts',expert_count,'linked_records',total,'can_delete',total=0);
 IF operation='schools.delete_check' THEN RETURN jsonb_build_object('code',NULL,'data',summary,'warnings','[]'::jsonb); END IF;
 IF total>0 THEN RETURN jsonb_build_object('code','SCHOOL_IN_USE'); END IF;
 BEGIN
  DELETE FROM public.schools WHERE school_id=target_id;
 EXCEPTION WHEN foreign_key_violation THEN RETURN jsonb_build_object('code','SCHOOL_IN_USE'); END;
 INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
 VALUES(subject_id,'schools.delete','school',target_id::text,request::text);
 RETURN jsonb_build_object('code',NULL,'data',jsonb_build_object('school_id',target_id::text,'deleted',true),'warnings','[]'::jsonb);
END $$;
REVOKE ALL ON FUNCTION public.graphiscan_school_deletion(uuid,uuid,text,bigint,jsonb,text,uuid)
 FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_admin_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_school_deletion(uuid,uuid,text,bigint,jsonb,text,uuid) TO graphiscan_password_writer;
COMMIT;
