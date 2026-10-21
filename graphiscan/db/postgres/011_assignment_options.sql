-- Apply once after 001-010. Read capability only, no eligibility/grant seeding.
BEGIN;
CREATE FUNCTION public.graphiscan_assignment_options(subject_id uuid, provider_session_id uuid,
    school bigint, after_time timestamptz, after_user uuid, page_limit integer)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
WITH actor AS MATERIALIZED (
    SELECT p.role, public.graphiscan_read_directory(subject_id,provider_session_id,
        'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' AS code
    FROM (SELECT 1) seed LEFT JOIN public.user_profiles p ON p.user_id=subject_id
), gate AS MATERIALIZED (
    SELECT actor.role, CASE WHEN actor.code IS NOT NULL THEN actor.code
        WHEN school IS NULL OR school<=0 OR page_limit IS NULL OR page_limit NOT BETWEEN 1 AND 100
            OR ((after_time IS NULL)<>(after_user IS NULL)) THEN 'INVALID_QUERY'
        WHEN NOT ((role='teacher' AND EXISTS(SELECT 1 FROM public.school_memberships m
            WHERE m.user_id=subject_id AND m.school_id=school))
            OR public.graphiscan_directory_grant(subject_id,'assignments.manage',school)) THEN 'FORBIDDEN'
        WHEN NOT EXISTS(SELECT 1 FROM public.schools s WHERE s.school_id=school) THEN 'NOT_FOUND'
        ELSE NULL END AS code FROM actor
), candidates AS MATERIALIZED (
    SELECT p.user_id,p.full_name,p.role,p.created_at FROM public.user_profiles p CROSS JOIN gate g
    WHERE g.code IS NULL AND p.account_status='active' AND (
        (g.role='teacher' AND p.user_id=subject_id AND p.role='teacher')
        OR (EXISTS(SELECT 1 FROM public.assignment_eligibilities e
            WHERE e.actor_id=subject_id AND e.candidate_id=p.user_id AND e.school_id=school
            AND e.assignment_role=p.role) AND (
            (p.role='parent') OR (g.role IN ('admin','researcher') AND p.role IN ('teacher','expert')
            AND EXISTS(SELECT 1 FROM public.school_memberships m
                WHERE m.user_id=p.user_id AND m.school_id=school)))))
), page AS MATERIALIZED (
    SELECT * FROM candidates WHERE after_time IS NULL OR (created_at,user_id)<(after_time,after_user)
    ORDER BY created_at DESC,user_id DESC LIMIT least(greatest(coalesce(page_limit,1),1),100)+1
)
SELECT jsonb_build_object('code',gate.code,'rows',coalesce((SELECT jsonb_agg(
    jsonb_build_object('data',jsonb_build_object('user_id',user_id::text,'full_name',full_name,'role',role),
        'created_at',created_at) ORDER BY created_at DESC,user_id DESC) FROM page),'[]'::jsonb)) FROM gate;
$$;
REVOKE ALL ON FUNCTION public.graphiscan_assignment_options(uuid,uuid,bigint,timestamptz,uuid,integer)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_password_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_assignment_options(uuid,uuid,bigint,timestamptz,uuid,integer)
    TO graphiscan_api_reader;
COMMIT;
