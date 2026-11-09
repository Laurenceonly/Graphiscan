-- Owner migration after028. Adds the actual review author's display name.
-- Existing record scope, release gates and function privileges are preserved.
BEGIN;
DO $patch$
DECLARE body text; old_text text:=$old$            'expert_id',expert_id,'remarks',remarks,'expert_recommendation',nullif(btrim(expert_recommendation),''),$old$;
new_text text:=$new$            'expert_id',expert_id,
            -- review expert name029: resolve saved authorship, never current assignment.
            'expert_name',(SELECT reviewer.full_name FROM public.user_profiles reviewer WHERE reviewer.user_id=page.expert_id),
            'remarks',remarks,'expert_recommendation',nullif(btrim(expert_recommendation),''),$new$;
BEGIN
    old_text:=replace(old_text,E'\r\n',E'\n');new_text:=replace(new_text,E'\r\n',E'\n');
    body:=replace(pg_get_functiondef('public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)'::regprocedure),E'\r\n',E'\n');
    IF position('-- review expert name029' IN body)>0 THEN RETURN; END IF;
    IF (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Review expert name migration: unexpected screening reader body'; END IF;
    EXECUTE replace(body,old_text,new_text);
END $patch$;
COMMIT;
