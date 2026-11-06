-- Owner migration after027. Adds display names to already-scoped student reads.
-- No record, permission, role, parent link or screening behavior is changed.
BEGIN;
DO $patch$
DECLARE body text; old_text text:=$old$            'teacher_id',s.teacher_id::text,'parent_id',s.parent_id::text,
$old$;
new_text text:=$new$            'teacher_id',s.teacher_id::text,'parent_id',s.parent_id::text,
            -- student display names028: only within the existing visible student projection.
            'school_name',(SELECT school.name FROM public.schools school WHERE school.school_id=s.school_id),
            'parent_name',(SELECT parent.full_name FROM public.user_profiles parent WHERE parent.user_id=s.parent_id AND parent.role='parent'),
$new$;
BEGIN
    old_text:=replace(old_text,E'\r\n',E'\n');new_text:=replace(new_text,E'\r\n',E'\n');
    body:=replace(pg_get_functiondef('public.graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)'::regprocedure),E'\r\n',E'\n');
    IF position('-- student display names028' IN body)>0 THEN RETURN; END IF;
    IF (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Student display names migration: unexpected directory reader body'; END IF;
    EXECUTE replace(body,old_text,new_text);
END $patch$;
COMMIT;
