-- Owner migration after 024. Current school/grade scopes define expert responsibility.

-- Existing and future students/results follow current scope; no per-screening backfill.

-- Keeps session, privacy, role, ownership, review revisions, audit and idempotency gates.

-- Does not add memberships, pick an expert, or change historical review authorship.

BEGIN;

DO $patch$ DECLARE body text; old_text text:=$old$(a.role = 'expert' AND EXISTS (
            SELECT 1 FROM public.handwriting_samples h
            JOIN public.screening_results r ON r.sample_id = h.sample_id
            JOIN public.screening_expert_assignments e ON e.result_id = r.result_id
            WHERE h.student_id = s.student_id AND e.assigned_expert_id = subject_id AND public.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level)))$old$; BEGIN
    old_text:=replace(old_text, E'\r\n', E'\n');
    body:=replace(pg_get_functiondef('public.graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)'::regprocedure), E'\r\n', E'\n');
    -- An already-installed predicate is a successful no-op on owner reruns.
    IF position(old_text IN body)=0 AND position($already$(a.role='expert' AND public.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level))$already$ IN body)>0 THEN RETURN; END IF;
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Grade expert migration: unexpected function body public.graphiscan_read_directory'; END IF;
    EXECUTE replace(body,old_text,$new$(a.role='expert' AND public.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level))$new$);
END $patch$;

DO $patch$ DECLARE body text; old_text text:=$old$(a.role='expert' AND EXISTS (SELECT 1 FROM public.handwriting_samples h
            JOIN public.screening_results r ON r.sample_id=h.sample_id
            JOIN public.screening_expert_assignments e ON e.result_id=r.result_id
            WHERE h.student_id=s.student_id AND e.assigned_expert_id=subject_id AND public.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level)))$old$; BEGIN
    old_text:=replace(old_text, E'\r\n', E'\n');
    body:=replace(pg_get_functiondef('public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)'::regprocedure), E'\r\n', E'\n');
    -- An already-installed predicate is a successful no-op on owner reruns.
    IF position(old_text IN body)=0 AND position($already$(a.role='expert' AND public.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level))$already$ IN body)>0 THEN RETURN; END IF;
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Grade expert migration: unexpected function body public.graphiscan_read_screenings'; END IF;
    EXECUTE replace(body,old_text,$new$(a.role='expert' AND public.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level))$new$);
END $patch$;

DO $patch$ DECLARE body text; old_text text:=$old$(a.role = 'expert' AND e.assigned_expert_id = subject_id)$old$; BEGIN
    old_text:=replace(old_text, E'\r\n', E'\n');
    body:=replace(pg_get_functiondef('public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)'::regprocedure), E'\r\n', E'\n');
    -- An already-installed predicate is a successful no-op on owner reruns.
    IF position(old_text IN body)=0 AND position($already$(a.role = 'expert' AND public.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level))$already$ IN body)>0 THEN RETURN; END IF;
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Grade expert migration: unexpected function body public.graphiscan_read_screenings'; END IF;
    EXECUTE replace(body,old_text,$new$(a.role = 'expert' AND public.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level))$new$);
END $patch$;

DO $patch$ DECLARE body text; old_text text:=$old$IF assigned IS DISTINCT FROM subject_id OR NOT public.graphiscan_grade_allowed(subject_id,st.school_id,st.grade_level) THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;$old$; BEGIN
    old_text:=replace(old_text, E'\r\n', E'\n');
    body:=replace(pg_get_functiondef('public.graphiscan_write_review(uuid,uuid,bigint,jsonb,text,uuid)'::regprocedure), E'\r\n', E'\n');
    -- An already-installed predicate is a successful no-op on owner reruns.
    IF position(old_text IN body)=0 AND position($already$IF NOT public.graphiscan_grade_allowed(subject_id,st.school_id,st.grade_level) THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;$already$ IN body)>0 THEN RETURN; END IF;
    IF position(old_text IN body)=0 OR (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Grade expert migration: unexpected function body public.graphiscan_write_review'; END IF;
    EXECUTE replace(body,old_text,$new$IF NOT public.graphiscan_grade_allowed(subject_id,st.school_id,st.grade_level) THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;$new$);
END $patch$;

COMMIT;
