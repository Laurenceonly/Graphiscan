-- Read-only function metadata; no account or screening rows returned.
WITH reader AS (SELECT p.*,pg_get_functiondef(p.oid) body FROM pg_proc p
    WHERE p.oid=to_regprocedure('public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)'))
SELECT
    EXISTS(SELECT 1 FROM reader WHERE strpos(body,'-- review expert name029')>0) AS expert_name_installed,
    EXISTS(SELECT 1 FROM reader WHERE prosecdef AND proconfig @> ARRAY['search_path=pg_catalog']) AS pinned_reader_definer,
    EXISTS(SELECT 1 FROM reader WHERE strpos(body,'reviewer.user_id=page.expert_id')>0) AS name_bound_to_review_author,
    coalesce(has_function_privilege('graphiscan_api_reader',to_regprocedure('public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)'),'EXECUTE'),false)
        AND NOT EXISTS(SELECT 1 FROM unnest(ARRAY['anon','authenticated','service_role','graphiscan_password_writer','graphiscan_admin_writer']) r
            WHERE coalesce(has_function_privilege(r,to_regprocedure('public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)'),'EXECUTE'),false)) AS reader_roles_retained;
