-- Apply after 030 as schema owner. Final-report context only; individual
-- screening/report access remains unchanged. No direct table grants.
BEGIN;
DO $migration$
DECLARE body text; old_name text := 'public.graphiscan_read_screenings('; new_name text := 'public.graphiscan_final_history_read('; gate text := '(a.role = ''parent'' AND s.parent_id = subject_id AND v.status = ''Validated'')';
BEGIN
  body:=replace(pg_get_functiondef('public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)'::regprocedure), E'\r\n', E'\n');
  IF position(old_name IN body)=0 OR position(gate IN body)=0 OR position(new_name IN body)>0 THEN
    RAISE EXCEPTION 'Unexpected screening reader; parent final report migration stopped';
  END IF;
  body:=replace(body,old_name,new_name);
  body:=replace(body,gate,'(a.role = ''parent'' AND s.parent_id = subject_id)');
  EXECUTE body;
END
$migration$;
REVOKE ALL ON FUNCTION public.graphiscan_final_history_read(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)
  FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_password_writer,graphiscan_admin_writer;
DO $migration$
DECLARE body text; old_call text := 'page:=public.graphiscan_read_screenings(subject_id,provider_session_id,''history'',''{}'',stamp,last_id,100,target_id,true);';
BEGIN
  body:=replace(pg_get_functiondef('public.graphiscan_final_context(uuid,uuid,bigint)'::regprocedure), E'\r\n', E'\n');
  IF position(old_call IN body)=0 THEN RAISE EXCEPTION 'Unexpected final context; migration stopped'; END IF;
  body:=replace(body,old_call, 'IF actor_role=''parent'' THEN page:=public.graphiscan_final_history_read(subject_id,provider_session_id,''history'',''{}'',stamp,last_id,100,target_id,true); ELSE ' || old_call || ' END IF;');
  EXECUTE body;
END
$migration$;
COMMIT;
