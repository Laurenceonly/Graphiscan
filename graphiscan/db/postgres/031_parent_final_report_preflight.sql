-- Read-only installation checks; no student data.
SELECT
  to_regprocedure('public.graphiscan_final_history_read(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)') IS NOT NULL AS internal_reader_exists,
  coalesce(position('graphiscan_final_history_read' IN pg_get_functiondef(to_regprocedure('public.graphiscan_final_context(uuid,uuid,bigint)')))>0,false) AS final_context_uses_internal_reader,
  NOT EXISTS (SELECT 1 FROM unnest(ARRAY['anon','authenticated','service_role','graphiscan_api_reader','graphiscan_password_writer','graphiscan_admin_writer']) role_name
    WHERE coalesce(has_function_privilege(role_name,to_regprocedure('public.graphiscan_final_history_read(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)'),'EXECUTE'),true)) AS application_roles_cannot_call_internal_reader;
