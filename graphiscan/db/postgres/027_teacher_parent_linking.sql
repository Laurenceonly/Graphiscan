-- Owner migration after 026. No student, account, assignment or consent rows seeded.
-- Teachers may link an existing active parent only on students they own, within
-- their existing school/grade scope. Parent discovery requires an exact login email.
BEGIN;

CREATE OR REPLACE FUNCTION public.graphiscan_teacher_parent_options(subject_id uuid,provider_session_id uuid,
    school bigint,grade smallint,parent_email text)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
WITH actor AS MATERIALIZED (
    SELECT p.role,public.graphiscan_read_directory(subject_id,provider_session_id,'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' AS code
    FROM (SELECT 1) seed LEFT JOIN public.user_profiles p ON p.user_id=subject_id
), gate AS MATERIALIZED (
    SELECT CASE WHEN actor.code IS NOT NULL THEN actor.code
        WHEN school IS NULL OR school<=0 OR grade IS NULL OR grade NOT BETWEEN 1 AND 3
            OR parent_email IS NULL OR length(parent_email)>254
            OR parent_email<>lower(btrim(parent_email))
            OR parent_email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' THEN 'INVALID_QUERY'
        WHEN actor.role IS DISTINCT FROM 'teacher' OR NOT public.graphiscan_grade_allowed(subject_id,school,grade)
            THEN 'FORBIDDEN' ELSE NULL END AS code FROM actor
), matches AS MATERIALIZED (
    SELECT p.user_id,p.full_name,p.role,p.created_at FROM public.user_profiles p
    JOIN auth.users u ON u.id=p.user_id CROSS JOIN gate
    WHERE gate.code IS NULL AND lower(u.email)=parent_email
        AND p.role='parent' AND p.account_status='active' AND NOT p.credential_update_pending
    LIMIT 2
)
SELECT jsonb_build_object('code',gate.code,'rows',CASE WHEN (SELECT count(*) FROM matches)=1 THEN
    (SELECT jsonb_agg(jsonb_build_object('data',jsonb_build_object('user_id',user_id::text,
        'full_name',full_name,'role',role),'created_at',created_at)) FROM matches)
    ELSE '[]'::jsonb END) FROM gate;
$$;
REVOKE ALL ON FUNCTION public.graphiscan_teacher_parent_options(uuid,uuid,bigint,smallint,text)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_admin_writer,graphiscan_password_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_teacher_parent_options(uuid,uuid,bigint,smallint,text) TO graphiscan_api_reader;

-- Retain the existing transaction's current session/onboarding, ownership,
-- school/grade, active-parent, revision, idempotency and audit checks.
DO $patch$
DECLARE body text; old_text text:=$old$        IF actor.role='teacher' AND parent IS DISTINCT FROM st.parent_id THEN
            RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
$old$;
BEGIN
    -- SQL editors can convert the pasted dollar-quoted literal to CRLF too.
    -- Normalize both sides before the exact, single-match source guard.
    old_text:=replace(old_text,E'\r\n',E'\n');
    body:=replace(pg_get_functiondef('public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)'::regprocedure),E'\r\n',E'\n');
    IF position('-- teacher parent linking027' IN body)>0 THEN RETURN; END IF;
    IF (length(body)-length(replace(body,old_text,'')))/length(old_text)<>1
        THEN RAISE EXCEPTION 'Teacher parent migration: unexpected directory writer body'; END IF;
    EXECUTE replace(body,old_text,E'        -- teacher parent linking027: existing scope and active-parent checks apply.\n');
END $patch$;
COMMIT;
