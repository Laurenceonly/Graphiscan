-- Read-only metadata; no student/account records returned.
WITH reader AS (SELECT p.*,pg_get_functiondef(p.oid) body FROM pg_proc p
    WHERE p.oid=to_regprocedure('public.graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)'))
SELECT
    EXISTS(SELECT 1 FROM reader WHERE strpos(body,'-- student display names028')>0) AS display_names_installed,
    EXISTS(SELECT 1 FROM reader WHERE prosecdef AND proconfig @> ARRAY['search_path=pg_catalog']) AS pinned_reader_definer,
    EXISTS(SELECT 1 FROM reader WHERE strpos(body,'parent.user_id=s.parent_id AND parent.role=''parent''')>0
        AND strpos(body,'school.school_id=s.school_id')>0) AS names_bound_to_student_links,
    EXISTS(SELECT 1 FROM reader WHERE strpos(body,'FROM visible_students s WHERE resource IN (''students'',''student'')')>0
        AND strpos(body,'s.teacher_id = subject_id AND public.graphiscan_grade_allowed')>0
        AND strpos(body,'s.parent_id = subject_id')>0) AS student_scope_checks_retained,
    coalesce(has_function_privilege('graphiscan_api_reader',to_regprocedure('public.graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)'),'EXECUTE'),false)
        AND NOT EXISTS(SELECT 1 FROM unnest(ARRAY['anon','authenticated','service_role','graphiscan_password_writer','graphiscan_admin_writer']) r
            WHERE coalesce(has_function_privilege(r,to_regprocedure('public.graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)'),'EXECUTE'),false)) AS reader_roles_retained;
