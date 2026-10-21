-- Apply once after the installed 015 bundle as the reviewed schema owner.
-- Read-only hosted admin lists. No data, credentials, grants or account actions.
BEGIN;

CREATE INDEX user_profiles_admin_page_idx ON public.user_profiles (created_at DESC, user_id DESC);
CREATE INDEX audit_logs_admin_page_idx ON public.audit_logs (created_at DESC, log_id DESC);

CREATE FUNCTION public.graphiscan_read_admin(
    subject_id uuid, provider_session_id uuid, resource text, search_text text,
    filter_role text, filter_status text, after_time timestamptz,
    after_user uuid, after_log bigint, page_limit integer
) RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
WITH base AS MATERIALIZED (
    -- Reuse the installed current-session, account, password and privacy gate.
    SELECT public.graphiscan_read_directory(subject_id, provider_session_id,
        'schools', '', NULL, NULL, NULL, NULL, 1, NULL)->>'code' AS code
), gate AS MATERIALIZED (
    SELECT CASE
        WHEN base.code IS NOT NULL THEN base.code
        WHEN p.role NOT IN ('admin', 'researcher') THEN 'FORBIDDEN'
        WHEN resource NOT IN ('accounts', 'audit') OR resource IS NULL
            OR search_text IS NULL OR length(search_text) > 120
            OR page_limit IS NULL OR page_limit NOT BETWEEN 1 AND 100
            OR ((after_time IS NULL) <> (CASE WHEN resource = 'accounts' THEN after_user IS NULL ELSE after_log IS NULL END))
            OR (resource = 'accounts' AND (after_log IS NOT NULL
                OR (filter_role IS NOT NULL AND filter_role NOT IN ('admin','researcher','teacher','parent','expert','guest'))
                OR (filter_status IS NOT NULL AND filter_status NOT IN ('active','pending','disabled','rejected'))))
            OR (resource = 'audit' AND (after_user IS NOT NULL OR filter_status IS NOT NULL
                OR (filter_role IS NOT NULL AND filter_role NOT IN ('admin','researcher','teacher','parent','expert','guest'))))
            THEN 'INVALID_QUERY'
        WHEN NOT EXISTS (
            SELECT 1 FROM public.user_permission_grants g
            WHERE g.user_id = subject_id AND g.school_id IS NULL
                AND g.permission_key = CASE resource WHEN 'accounts' THEN 'accounts.manage' ELSE 'audit.read' END
        ) THEN 'FORBIDDEN'
        ELSE NULL END AS code
    FROM base LEFT JOIN public.user_profiles p ON p.user_id = subject_id
), account_page AS MATERIALIZED (
    SELECT p.created_at AS sort_time, p.user_id AS sort_user,
        jsonb_build_object('user_id',p.user_id::text,'full_name',p.full_name,
            'email',u.email,'role',p.role,'account_status',p.account_status,
            'created_at',p.created_at) AS row_data
    FROM public.user_profiles p JOIN auth.users u ON u.id = p.user_id CROSS JOIN gate g
    WHERE g.code IS NULL AND resource = 'accounts'
        AND (filter_role IS NULL OR p.role = filter_role)
        AND (filter_status IS NULL OR p.account_status = filter_status)
        AND (search_text = '' OR strpos(lower(p.full_name),lower(search_text)) > 0
            OR strpos(lower(coalesce(u.email,'')),lower(search_text)) > 0)
        AND (after_time IS NULL OR (p.created_at,p.user_id) < (after_time,after_user))
    ORDER BY p.created_at DESC,p.user_id DESC LIMIT least(greatest(coalesce(page_limit,1),1),100)+1
), audit_page AS MATERIALIZED (
    SELECT a.created_at AS sort_time, a.log_id AS sort_id,
        jsonb_build_object('log_id',a.log_id::text,'actor_id',a.actor_id::text,
            'full_name',p.full_name,'role',p.role,'action',a.action,
            'created_at',a.created_at) AS row_data
    FROM public.audit_logs a LEFT JOIN public.user_profiles p ON p.user_id = a.actor_id
    CROSS JOIN gate g
    WHERE g.code IS NULL AND resource = 'audit'
        AND (filter_role IS NULL OR p.role = filter_role)
        AND (search_text = '' OR strpos(lower(a.action),lower(search_text)) > 0
            OR strpos(lower(coalesce(p.full_name,'')),lower(search_text)) > 0)
        AND (after_time IS NULL OR (a.created_at,a.log_id) < (after_time,after_log))
    ORDER BY a.created_at DESC,a.log_id DESC LIMIT least(greatest(coalesce(page_limit,1),1),100)+1
)
SELECT jsonb_build_object('code',(SELECT code FROM gate),'rows',
    CASE resource
        WHEN 'accounts' THEN coalesce((SELECT jsonb_agg(row_data ORDER BY sort_time DESC,sort_user DESC) FROM account_page),'[]'::jsonb)
        WHEN 'audit' THEN coalesce((SELECT jsonb_agg(row_data ORDER BY sort_time DESC,sort_id DESC) FROM audit_page),'[]'::jsonb)
        ELSE '[]'::jsonb END);
$$;

REVOKE ALL ON FUNCTION public.graphiscan_read_admin(uuid,uuid,text,text,text,text,timestamptz,uuid,bigint,integer)
    FROM PUBLIC, anon, authenticated, service_role, graphiscan_password_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_read_admin(uuid,uuid,text,text,text,text,timestamptz,uuid,bigint,integer)
    TO graphiscan_api_reader;
COMMIT;
