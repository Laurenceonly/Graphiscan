-- Apply once after019 as schema owner. No accounts, grants or eligibility seeded.
BEGIN;

CREATE FUNCTION public.graphiscan_assignment_access_gate(subject_id uuid,provider_session_id uuid,
    candidate uuid,acting uuid,school bigint)
RETURNS text LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text;
BEGIN
    code:=public.graphiscan_admin_account_gate(subject_id,provider_session_id);
    IF code IS NOT NULL THEN RETURN code; END IF;
    IF candidate IS NULL OR acting IS NULL OR school IS NULL OR school<=0 THEN RETURN 'INVALID_INPUT'; END IF;
    IF NOT public.graphiscan_directory_grant(subject_id,'assignments.manage',school) THEN RETURN 'FORBIDDEN'; END IF;
    IF NOT EXISTS(SELECT 1 FROM public.schools WHERE school_id=school)
        OR NOT EXISTS(SELECT 1 FROM public.user_profiles WHERE user_id=candidate)
        OR NOT EXISTS(SELECT 1 FROM public.user_profiles WHERE user_id=acting) THEN RETURN 'NOT_FOUND'; END IF;
    IF (SELECT role FROM public.user_profiles WHERE user_id=subject_id)<>'admin'
        AND acting<>subject_id AND (SELECT role FROM public.user_profiles WHERE user_id=acting) IN ('admin','researcher')
        THEN RETURN 'FORBIDDEN'; END IF;
    RETURN NULL;
END;
$$;

CREATE FUNCTION public.graphiscan_assignment_access_snapshot(candidate uuid,acting uuid,school bigint)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
WITH state AS (
    SELECT p.user_id,p.role,p.revision,
        p.account_status='active' AND NOT p.credential_update_pending
        AND a.account_status='active' AND NOT a.credential_update_pending
        AND p.role IN ('teacher','parent','expert')
        AND (p.role='parent' OR EXISTS(SELECT 1 FROM public.school_memberships m
            WHERE m.user_id=p.user_id AND m.school_id=school))
        AND ((a.role='teacher' AND p.role='parent' AND EXISTS(SELECT 1 FROM public.school_memberships m
                WHERE m.user_id=a.user_id AND m.school_id=school))
            OR (a.role IN ('admin','researcher') AND public.graphiscan_directory_grant(a.user_id,'assignments.manage',school)))
        AS can_grant
    FROM public.user_profiles p CROSS JOIN public.user_profiles a WHERE p.user_id=candidate AND a.user_id=acting
)
SELECT jsonb_build_object('candidate_id',candidate::text,'actor_id',acting::text,'school_id',school::text,
    'revision',s.revision,'candidate_role',s.role,'can_grant',s.can_grant,
    'eligible',EXISTS(SELECT 1 FROM public.assignment_eligibilities e
        WHERE e.actor_id=acting AND e.candidate_id=candidate AND e.school_id=school),
    'effective',s.can_grant AND EXISTS(SELECT 1 FROM public.assignment_eligibilities e
        WHERE e.actor_id=acting AND e.candidate_id=candidate AND e.school_id=school AND e.assignment_role=s.role))
FROM state s;
$$;

CREATE FUNCTION public.graphiscan_get_assignment_access(subject_id uuid,provider_session_id uuid,
    candidate uuid,acting uuid,school bigint)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text;
BEGIN
    code:=public.graphiscan_assignment_access_gate(subject_id,provider_session_id,candidate,acting,school);
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    RETURN jsonb_build_object('code',NULL,'data',public.graphiscan_assignment_access_snapshot(candidate,acting,school));
END;
$$;

CREATE FUNCTION public.graphiscan_set_assignment_access(subject_id uuid,provider_session_id uuid,
    candidate uuid,acting uuid,school bigint,expected_revision bigint,enabled boolean,request uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text; p public.user_profiles%ROWTYPE; state jsonb; changes integer; added integer;
BEGIN
    IF expected_revision IS NULL OR expected_revision<1 OR expected_revision>9223372036854775806
        OR enabled IS NULL OR request IS NULL THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    -- Assignment writers share-lock these profiles. Serialize revocation with
    -- their scope checks, including expert assignment's eligibility EXISTS.
    PERFORM user_id FROM public.user_profiles WHERE user_id IN(subject_id,candidate,acting) ORDER BY user_id FOR UPDATE;
    PERFORM version FROM public.privacy_agreements WHERE is_current FOR SHARE;
    code:=public.graphiscan_assignment_access_gate(subject_id,provider_session_id,candidate,acting,school);
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    SELECT * INTO p FROM public.user_profiles WHERE user_id=candidate;
    IF p.credential_update_pending THEN RETURN jsonb_build_object('code','ACCOUNT_OPERATION_PENDING'); END IF;
    IF p.revision<>expected_revision THEN RETURN jsonb_build_object('code','REVISION_CONFLICT'); END IF;
    state:=public.graphiscan_assignment_access_snapshot(candidate,acting,school);
    IF enabled AND NOT (state->>'can_grant')::boolean THEN RETURN jsonb_build_object('code','INVALID_ASSIGNMENT'); END IF;
    DELETE FROM public.assignment_eligibilities e WHERE e.actor_id=acting AND e.candidate_id=candidate
        AND e.school_id=school AND (NOT enabled OR e.assignment_role<>p.role);
    GET DIAGNOSTICS changes=ROW_COUNT;
    IF enabled THEN
        INSERT INTO public.assignment_eligibilities(actor_id,candidate_id,school_id,assignment_role,granted_by)
        VALUES(acting,candidate,school,p.role,subject_id) ON CONFLICT DO NOTHING;
        GET DIAGNOSTICS added=ROW_COUNT;
        changes:=changes+added;
    END IF;
    IF changes>0 THEN
        UPDATE public.user_profiles SET revision=revision WHERE user_id=candidate;
        INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
        VALUES(subject_id,CASE WHEN enabled THEN 'assignments.eligibility.granted' ELSE 'assignments.eligibility.revoked' END,
            'assignment_eligibility',acting::text||'/'||candidate::text||'/'||school::text,request::text);
    END IF;
    RETURN jsonb_build_object('code',NULL,'data',public.graphiscan_assignment_access_snapshot(candidate,acting,school));
END;
$$;

REVOKE ALL ON FUNCTION public.graphiscan_assignment_access_gate(uuid,uuid,uuid,uuid,bigint),
    public.graphiscan_assignment_access_snapshot(uuid,uuid,bigint),
    public.graphiscan_get_assignment_access(uuid,uuid,uuid,uuid,bigint),
    public.graphiscan_set_assignment_access(uuid,uuid,uuid,uuid,bigint,bigint,boolean,uuid)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_password_writer,graphiscan_admin_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_get_assignment_access(uuid,uuid,uuid,uuid,bigint) TO graphiscan_api_reader;
GRANT EXECUTE ON FUNCTION public.graphiscan_set_assignment_access(uuid,uuid,uuid,uuid,bigint,bigint,boolean,uuid) TO graphiscan_admin_writer;
COMMIT;
