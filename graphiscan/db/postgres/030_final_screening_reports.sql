-- Owner migration after 029. No application records or user grants are seeded.
-- Append-only expert conclusions; current access is rechecked on every read.
BEGIN;
CREATE TABLE public.final_screening_reports (
    final_report_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id bigint NOT NULL REFERENCES public.students(student_id) ON DELETE RESTRICT,
    revision bigint NOT NULL CHECK (revision > 0),
    expert_id uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    expert_name text NOT NULL,
    summary text NOT NULL CHECK (length(btrim(summary)) BETWEEN 1 AND 10000),
    conclusion text NOT NULL CHECK (length(btrim(conclusion)) BETWEEN 1 AND 10000),
    next_steps text NOT NULL CHECK (length(btrim(next_steps)) BETWEEN 1 AND 10000),
    history_fingerprint text NOT NULL CHECK (history_fingerprint ~ '^[0-9a-f]{64}$'),
    screenings jsonb NOT NULL CHECK (jsonb_typeof(screenings)='array'),
    request_key text NOT NULL CHECK (request_key ~ '^[A-Za-z0-9_-]{16,128}$'),
    request_digest text NOT NULL,
    finalized_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE(student_id,revision), UNIQUE(expert_id,request_key)
);
ALTER TABLE public.final_screening_reports ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.final_screening_reports FROM PUBLIC,anon,authenticated,service_role,
    graphiscan_api_reader,graphiscan_password_writer,graphiscan_admin_writer;
REVOKE ALL ON SEQUENCE public.final_screening_reports_final_report_id_seq FROM PUBLIC,anon,authenticated,service_role,
    graphiscan_api_reader,graphiscan_password_writer,graphiscan_admin_writer;
CREATE TRIGGER final_screening_reports_immutable BEFORE UPDATE OR DELETE
    ON public.final_screening_reports FOR EACH ROW EXECUTE FUNCTION public.prevent_history_change();

-- Internal only. Reuse the installed directory/history scope and onboarding gates.
-- Compare against the complete official history so a partial expert/parent view
-- cannot silently become a whole-student final report. Never return storage paths.
CREATE FUNCTION public.graphiscan_final_context(subject_id uuid, provider_session_id uuid, target_id bigint)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE page jsonb; directory jsonb; rows jsonb:='[]'; chunk jsonb; last_row jsonb;
    stamp timestamptz; last_id bigint; total bigint; fingerprint text; actor_role text;
    student_revision bigint;
BEGIN
    directory:=public.graphiscan_read_directory(subject_id,provider_session_id,'student','',NULL,NULL,NULL,NULL,1,target_id);
    IF directory->>'code' IS NOT NULL THEN RETURN jsonb_build_object('code',directory->>'code'); END IF;
    IF jsonb_array_length(directory->'rows')<>1 THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    SELECT role INTO actor_role FROM public.user_profiles WHERE user_id=subject_id;
    LOOP
        page:=public.graphiscan_read_screenings(subject_id,provider_session_id,'history','{}',stamp,last_id,100,target_id,true);
        IF page->>'code' IS NOT NULL THEN RETURN jsonb_build_object('code',page->>'code'); END IF;
        IF NOT coalesce((page->>'found')::boolean,false) THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
        -- Reader returns limit+1 for pagination. Include only the first 100.
        SELECT coalesce(jsonb_agg(value ORDER BY ord),'[]'::jsonb) INTO chunk
            FROM jsonb_array_elements(page->'rows') WITH ORDINALITY t(value,ord) WHERE ord<=100;
        rows:=rows||chunk;
        EXIT WHEN jsonb_array_length(page->'rows')<=100;
        last_row:=chunk->99; stamp:=(last_row->>'date_generated')::timestamptz;
        last_id:=(last_row->>'result_id')::bigint;
    END LOOP;
    SELECT count(*) INTO total FROM public.screening_results r
        JOIN public.handwriting_samples h ON h.sample_id=r.sample_id WHERE h.student_id=target_id;
    IF total<>jsonb_array_length(rows) THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    SELECT revision INTO student_revision FROM public.students WHERE student_id=target_id;
    -- Names can change independently; exclude display-only names from the digest.
    SELECT encode(sha256(convert_to(jsonb_build_object('student_revision',student_revision,
        'rows',coalesce(jsonb_agg(value #- '{review,expert_name}' ORDER BY ord),'[]'::jsonb))::text,'UTF8')),'hex')
        INTO fingerprint FROM jsonb_array_elements(rows) WITH ORDINALITY t(value,ord);
    RETURN jsonb_build_object('code',NULL,'student',directory->'rows'->0,'screenings',rows,
        'fingerprint',fingerprint,'role',actor_role);
END;
$$;

CREATE FUNCTION public.graphiscan_read_final_report(subject_id uuid, provider_session_id uuid, target_id bigint)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE context jsonb; saved public.final_screening_reports%ROWTYPE; ready boolean; reason text;
    current_report jsonb;
BEGIN
    context:=public.graphiscan_final_context(subject_id,provider_session_id,target_id);
    IF context->>'code' IS NOT NULL THEN RETURN jsonb_build_object('code',context->>'code'); END IF;
    SELECT * INTO saved FROM public.final_screening_reports WHERE student_id=target_id ORDER BY revision DESC LIMIT 1;
    IF saved.history_fingerprint=context->>'fingerprint' THEN
        current_report:=jsonb_build_object('final_report_id',saved.final_report_id::text,
            'revision',saved.revision,'expert_id',saved.expert_id,'expert_name',saved.expert_name,
            'summary',saved.summary,'conclusion',saved.conclusion,'next_steps',saved.next_steps,
            'finalized_at',saved.finalized_at,'screenings',saved.screenings);
    END IF;
    IF context->>'role'='parent' AND current_report IS NULL THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    ready:=context->>'role'='expert' AND current_report IS NULL;
    IF jsonb_array_length(context->'screenings')<1
        OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(context->'screenings') r WHERE r->'report'->>'report_type'='Initial Screening') THEN
        ready:=false; reason:='Complete the initial screening before writing the final conclusion.';
    ELSIF EXISTS(SELECT 1 FROM jsonb_array_elements(context->'screenings') r
        WHERE r->'review'->>'status' NOT IN ('Validated','Flagged') OR r->'review'->>'expert_id' IS NULL) THEN
        ready:=false; reason:='Review every screening before writing the final conclusion.';
    ELSIF (context->'screenings'->-1->'review'->>'follow_up_needed')::boolean IS DISTINCT FROM false THEN
        ready:=false; reason:='The latest review requests a follow-up. Update that review to No when monitoring can conclude.';
    END IF;
    RETURN jsonb_build_object('code',NULL,'data',jsonb_build_object('student',context->'student',
        'state',CASE WHEN current_report IS NOT NULL THEN 'Finalized' ELSE 'Monitoring' END,
        'revision',coalesce(saved.revision,0),'history_fingerprint',context->>'fingerprint',
        'can_finalize',ready,'reason',reason,'final_report',current_report,
        'screenings',context->'screenings'));
END;
$$;

CREATE FUNCTION public.graphiscan_finalize_report(subject_id uuid, provider_session_id uuid,
    target_id bigint, payload jsonb, request_key text, request uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE context jsonb; actor public.user_profiles%ROWTYPE; saved public.final_screening_reports%ROWTYPE;
    latest bigint; digest text; field text; gate jsonb;
BEGIN
    PERFORM 1 FROM public.user_profiles WHERE user_id=subject_id FOR SHARE;
    PERFORM 1 FROM public.privacy_agreements WHERE is_current FOR SHARE;
    gate:=public.graphiscan_read_directory(subject_id,provider_session_id,'schools','',NULL,NULL,NULL,NULL,1,NULL);
    IF gate->>'code' IS NOT NULL THEN RETURN jsonb_build_object('code',gate->>'code'); END IF;
    SELECT * INTO actor FROM public.user_profiles WHERE user_id=subject_id;
    IF actor.role<>'expert' THEN RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    IF target_id IS NULL OR target_id<=0 OR request IS NULL OR request_key IS NULL
        OR request_key !~ '^[A-Za-z0-9_-]{16,128}$' OR jsonb_typeof(payload) IS DISTINCT FROM 'object'
        OR NOT payload ?& ARRAY['summary','conclusion','next_steps','history_fingerprint','expected_revision']
        OR payload-ARRAY['summary','conclusion','next_steps','history_fingerprint','expected_revision']<>'{}'::jsonb
        OR jsonb_typeof(payload->'expected_revision') IS DISTINCT FROM 'number'
        OR coalesce(payload->>'expected_revision','') !~ '^(0|[1-9][0-9]{0,18})$'
        OR (payload->>'expected_revision')::numeric>9223372036854775806
        OR jsonb_typeof(payload->'history_fingerprint') IS DISTINCT FROM 'string'
        OR payload->>'history_fingerprint' !~ '^[0-9a-f]{64}$'
        THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    FOREACH field IN ARRAY ARRAY['summary','conclusion','next_steps'] LOOP
        IF jsonb_typeof(payload->field) IS DISTINCT FROM 'string' OR length(btrim(payload->>field)) NOT BETWEEN 1 AND 10000
            THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    END LOOP;
    PERFORM pg_advisory_xact_lock(hashtextextended(subject_id::text||':final-report:'||request_key,0));
    -- Match review/assignment lock order: results before the student. Student lock
    -- serializes upload completion and directory changes while the snapshot saves.
    PERFORM r.result_id FROM public.screening_results r JOIN public.handwriting_samples h ON h.sample_id=r.sample_id
        WHERE h.student_id=target_id ORDER BY r.result_id FOR SHARE OF r;
    PERFORM 1 FROM public.students WHERE student_id=target_id FOR UPDATE;
    context:=public.graphiscan_read_final_report(subject_id,provider_session_id,target_id);
    IF context->>'code' IS NOT NULL THEN RETURN jsonb_build_object('code',context->>'code'); END IF;
    digest:=public.graphiscan_directory_digest(jsonb_build_object('operation','reports.finalize','student_id',target_id,'body',payload));
    SELECT * INTO saved FROM public.final_screening_reports f WHERE f.expert_id=subject_id AND f.request_key=graphiscan_finalize_report.request_key;
    IF FOUND THEN
        IF saved.request_digest<>digest THEN RETURN jsonb_build_object('code','IDEMPOTENCY_CONFLICT'); END IF;
        IF saved.revision<>(context->'data'->>'revision')::bigint
            OR saved.history_fingerprint IS DISTINCT FROM context->'data'->>'history_fingerprint'
            OR saved.final_report_id::text IS DISTINCT FROM context->'data'->'final_report'->>'final_report_id'
            THEN RETURN jsonb_build_object('code','REVISION_CONFLICT'); END IF;
        RETURN context;
    END IF;
    latest:=(context->'data'->>'revision')::bigint;
    IF latest<>(payload->>'expected_revision')::bigint
        OR payload->>'history_fingerprint' IS DISTINCT FROM context->'data'->>'history_fingerprint'
        THEN RETURN jsonb_build_object('code','REVISION_CONFLICT'); END IF;
    IF NOT (context->'data'->>'can_finalize')::boolean THEN RETURN jsonb_build_object('code','FINAL_REPORT_NOT_READY'); END IF;
    INSERT INTO public.final_screening_reports(student_id,revision,expert_id,expert_name,summary,conclusion,next_steps,
        history_fingerprint,screenings,request_key,request_digest)
        VALUES(target_id,latest+1,subject_id,actor.full_name,btrim(payload->>'summary'),btrim(payload->>'conclusion'),
            btrim(payload->>'next_steps'),payload->>'history_fingerprint',context->'data'->'screenings',request_key,digest);
    INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
        VALUES(subject_id,'reports.finalize','student',target_id::text,request::text);
    RETURN public.graphiscan_read_final_report(subject_id,provider_session_id,target_id);
END;
$$;
REVOKE ALL ON FUNCTION public.graphiscan_final_context(uuid,uuid,bigint),
    public.graphiscan_read_final_report(uuid,uuid,bigint),
    public.graphiscan_finalize_report(uuid,uuid,bigint,jsonb,text,uuid)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_password_writer,graphiscan_admin_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_read_final_report(uuid,uuid,bigint) TO graphiscan_api_reader;
GRANT EXECUTE ON FUNCTION public.graphiscan_finalize_report(uuid,uuid,bigint,jsonb,text,uuid) TO graphiscan_password_writer;
COMMIT;
