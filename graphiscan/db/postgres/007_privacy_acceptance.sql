-- Unapplied extension after 001-006. No notice is published or accepted here.
-- Existing function-only server writer gains one scoped onboarding function;
-- no additional login/password or direct table/Auth privileges are required.
BEGIN;
ALTER TABLE public.privacy_agreements ADD COLUMN test_subject_id uuid
    REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT;

CREATE FUNCTION public.graphiscan_accept_privacy(subject_id uuid, provider_session_id uuid,
                                                requested_version text, request uuid)
RETURNS TABLE(outcome text, agreement_version text, accepted_at timestamptz)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE p public.user_profiles%ROWTYPE; a public.privacy_agreements%ROWTYPE;
        inserted_id bigint; saved_at timestamptz;
BEGIN
    -- Serialize with profile/security writes and other accepts for this subject.
    SELECT * INTO p FROM public.user_profiles WHERE user_id=subject_id FOR UPDATE;
    IF NOT EXISTS (
        SELECT 1 FROM public.graphiscan_session_state(subject_id,provider_session_id) s
        WHERE (s.not_after IS NULL OR s.not_after > clock_timestamp())
          AND (p.user_id IS NULL OR s.created_at >= p.sessions_valid_after)
          AND NOT EXISTS (SELECT 1 FROM public.app_session_revocations r WHERE r.session_id=s.id)
    ) OR coalesce(p.credential_update_pending,false) THEN
        RETURN QUERY SELECT 'invalid_session'::text,NULL::text,NULL::timestamptz; RETURN;
    END IF;
    IF p.user_id IS NULL OR p.account_status <> 'active' THEN
        RETURN QUERY SELECT 'account_unavailable'::text,NULL::text,NULL::timestamptz; RETURN;
    END IF;
    IF p.must_change_password THEN
        RETURN QUERY SELECT 'password_required'::text,NULL::text,NULL::timestamptz; RETURN;
    END IF;
    -- A publisher updating is_current must wait for this row lock. If it
    -- already changed while we waited, READ COMMITTED rechecks the predicate.
    SELECT * INTO a FROM public.privacy_agreements WHERE is_current FOR SHARE;
    IF a.version IS NULL OR a.approved_by IS NULL OR a.approved_at > clock_timestamp()
       OR a.published_at IS NULL OR a.published_at > clock_timestamp()
       OR a.content_sha256 <> encode(sha256(convert_to(a.content,'UTF8')),'hex')
       OR (a.test_subject_id IS NOT NULL AND a.test_subject_id <> subject_id) THEN
        RETURN QUERY SELECT 'agreement_unavailable'::text,NULL::text,NULL::timestamptz; RETURN;
    END IF;
    IF a.version IS DISTINCT FROM requested_version THEN
        RETURN QUERY SELECT 'agreement_changed'::text,NULL::text,NULL::timestamptz; RETURN;
    END IF;
    INSERT INTO public.privacy_agreement_acceptances AS acceptance(user_id,agreement_version)
        VALUES (subject_id,a.version)
        ON CONFLICT ON CONSTRAINT privacy_agreement_acceptances_user_id_agreement_version_key DO NOTHING
        RETURNING acceptance.acceptance_id INTO inserted_id;
    IF inserted_id IS NOT NULL THEN
        INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
            VALUES(subject_id,'privacy.accepted','privacy_agreement',a.version,request::text);
    END IF;
    SELECT acceptance.accepted_at INTO saved_at FROM public.privacy_agreement_acceptances acceptance
        WHERE acceptance.user_id=subject_id AND acceptance.agreement_version=a.version;
    RETURN QUERY SELECT 'accepted'::text,a.version,saved_at;
END;
$$;
REVOKE ALL ON FUNCTION public.graphiscan_accept_privacy(uuid,uuid,text,uuid)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader;
GRANT EXECUTE ON FUNCTION public.graphiscan_accept_privacy(uuid,uuid,text,uuid)
    TO graphiscan_password_writer;
COMMIT;
