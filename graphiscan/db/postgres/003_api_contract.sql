-- DRAFT ONLY. Apply after 001/002 to a new, reviewed test schema first.
-- No real records, permission grants, approved privacy text or model defaults
-- are seeded. This adds storage/invariants; it does not implement authorization,
-- Auth/Storage integration, request handlers or a retention/deletion policy.
BEGIN;

ALTER TABLE public.user_profiles
    ADD COLUMN revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
    ADD COLUMN security_version bigint NOT NULL DEFAULT 1 CHECK (security_version > 0),
    ADD COLUMN credential_update_pending boolean NOT NULL DEFAULT false;
ALTER TABLE public.schools ADD COLUMN revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0);
ALTER TABLE public.students ADD COLUMN revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0);
ALTER TABLE public.screening_results
    ADD COLUMN revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
    ADD COLUMN provenance text NOT NULL DEFAULT 'legacy_unverified'
        CHECK (provenance IN ('verified', 'legacy_unverified')),
    ADD COLUMN model_snapshot jsonb,
    ADD COLUMN decision_rule jsonb;
-- Obsolete generated prose is not part of v1 and must not be imported.
ALTER TABLE public.screening_results DROP COLUMN analysis_summary;
ALTER TABLE public.expert_validations
    ADD COLUMN revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
    ADD COLUMN provenance text NOT NULL DEFAULT 'legacy_unverified'
        CHECK (provenance IN ('verified', 'legacy_unverified'));
ALTER TABLE public.screening_reports ADD COLUMN school_context jsonb;

CREATE TABLE public.user_permission_grants (
    grant_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    permission_key text NOT NULL CHECK (permission_key IN
        ('accounts.manage', 'permissions.manage', 'schools.manage', 'assignments.manage', 'audit.read')),
    school_id bigint REFERENCES public.schools(school_id) ON DELETE RESTRICT,
    granted_by uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX permission_grants_global_unique ON public.user_permission_grants(user_id, permission_key)
    WHERE school_id IS NULL;
CREATE UNIQUE INDEX permission_grants_school_unique ON public.user_permission_grants(user_id, permission_key, school_id)
    WHERE school_id IS NOT NULL;

CREATE TABLE public.school_memberships (
    user_id uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    school_id bigint NOT NULL REFERENCES public.schools(school_id) ON DELETE RESTRICT,
    created_by uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, school_id)
);
CREATE TABLE public.assignment_eligibilities (
    actor_id uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    candidate_id uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    school_id bigint NOT NULL REFERENCES public.schools(school_id) ON DELETE RESTRICT,
    assignment_role text NOT NULL CHECK (assignment_role IN ('teacher', 'parent', 'expert')),
    granted_by uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (actor_id, candidate_id, school_id, assignment_role)
);
-- Membership/eligibility is not authorization by itself. Server checks current
-- role/status, action grant, school scope AND student/result assignment.

CREATE TABLE public.privacy_agreements (
    version text PRIMARY KEY CHECK (length(btrim(version)) > 0),
    title text NOT NULL CHECK (length(btrim(title)) > 0),
    content text NOT NULL CHECK (length(btrim(content)) > 0),
    content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[a-f0-9]{64}$'),
    approved_by uuid REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    approved_at timestamptz,
    published_at timestamptz,
    is_current boolean NOT NULL DEFAULT false,
    CHECK (NOT is_current OR (approved_by IS NOT NULL AND approved_at IS NOT NULL AND published_at IS NOT NULL))
);
CREATE UNIQUE INDEX privacy_agreements_one_current ON public.privacy_agreements(is_current) WHERE is_current;
ALTER TABLE public.privacy_agreement_acceptances ADD CONSTRAINT acceptance_agreement_exists
    FOREIGN KEY (agreement_version) REFERENCES public.privacy_agreements(version) ON DELETE RESTRICT;

CREATE TABLE public.app_session_revocations (
    session_id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    revoked_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz,
    reason text NOT NULL CHECK (reason IN ('logout', 'password_change', 'temporary_reset', 'account_change')),
    CHECK (expires_at IS NULL OR expires_at >= revoked_at)
);
-- Do not FK a revoked session to auth.sessions: provider sign-out removes it.
-- The handler must verify provider session existence/revocation and register all
-- affected sessions on password/security changes; a version column alone is not
-- proof that an old, unbound JWT cannot register itself again.
CREATE INDEX session_revocations_user_idx ON public.app_session_revocations(user_id);

CREATE TABLE public.model_evaluations (
    evaluation_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    task_type text NOT NULL CHECK (task_type IN ('binary', 'three_class')),
    dataset_key text NOT NULL CHECK (length(btrim(dataset_key)) > 0),
    dataset_version text NOT NULL CHECK (length(btrim(dataset_version)) > 0),
    split_key text NOT NULL CHECK (length(btrim(split_key)) > 0),
    split_unit text NOT NULL CHECK (split_unit IN ('image', 'writer')),
    writer_separation_verified boolean NOT NULL DEFAULT false,
    evidence_reference text NOT NULL CHECK (length(btrim(evidence_reference)) > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (evaluation_id, task_type),
    CHECK (NOT writer_separation_verified OR split_unit = 'writer')
);
ALTER TABLE public.model_registry
    ADD COLUMN evaluation_id bigint,
    ADD COLUMN preprocessing_key text,
    ADD COLUMN class_labels jsonb,
    ADD COLUMN decision_rule jsonb,
    ADD COLUMN provenance text NOT NULL DEFAULT 'legacy_unverified'
        CHECK (provenance IN ('verified', 'legacy_unverified')),
    ADD CONSTRAINT model_evaluation_task_matches FOREIGN KEY (evaluation_id, task_type)
        REFERENCES public.model_evaluations(evaluation_id, task_type) ON DELETE RESTRICT,
    ADD CONSTRAINT selectable_model_has_evidence CHECK (
        NOT is_selectable OR
        (provenance = 'verified' AND evaluation_id IS NOT NULL AND test_accuracy IS NOT NULL
         AND preprocessing_key IS NOT NULL AND length(btrim(preprocessing_key)) > 0
         AND class_labels IS NOT NULL AND decision_rule IS NOT NULL)
    );

CREATE FUNCTION public.valid_class_labels(labels jsonb, task text) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SET search_path = pg_catalog, public AS $$
BEGIN
    IF labels IS NULL THEN RETURN true; END IF;
    IF jsonb_typeof(labels) <> 'array' THEN RETURN false; END IF;
    IF task = 'binary' THEN
        RETURN jsonb_array_length(labels) = 2 AND labels ?& ARRAY['Normal', 'High Potential'];
    ELSIF task = 'three_class' THEN
        RETURN jsonb_array_length(labels) = 3 AND labels ?& ARRAY['Normal', 'Low Potential', 'High Potential'];
    END IF;
    RETURN false;
END;
$$;
CREATE FUNCTION public.valid_class_scores(scores jsonb, task text) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SET search_path = pg_catalog, public AS $$
DECLARE item record; total numeric := 0; count_keys integer := 0;
BEGIN
    IF scores IS NULL THEN RETURN true; END IF;
    IF jsonb_typeof(scores) <> 'object' THEN RETURN false; END IF;
    IF task = 'binary' THEN
        IF NOT scores ?& ARRAY['normal', 'high_potential'] THEN RETURN false; END IF;
    ELSIF task = 'three_class' THEN
        IF NOT scores ?& ARRAY['normal', 'low_potential', 'high_potential'] THEN RETURN false; END IF;
    ELSE RETURN false;
    END IF;
    FOR item IN SELECT * FROM jsonb_each(scores) LOOP
        IF jsonb_typeof(item.value) <> 'number' THEN RETURN false; END IF;
        IF item.value::numeric < 0 OR item.value::numeric > 1 THEN RETURN false; END IF;
        total := total + item.value::numeric;
        count_keys := count_keys + 1;
    END LOOP;
    RETURN count_keys = CASE task WHEN 'binary' THEN 2 ELSE 3 END AND abs(total - 1) <= 0.00001;
END;
$$;
CREATE FUNCTION public.valid_decision_rule(rule jsonb, task text) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SET search_path = pg_catalog, public AS $$
BEGIN
    IF rule IS NULL THEN RETURN true; END IF;
    IF jsonb_typeof(rule) <> 'object' THEN RETURN false; END IF;
    IF rule->>'kind' = 'argmax' THEN
        RETURN rule = '{"kind":"argmax"}'::jsonb;
    END IF;
    IF task <> 'binary' OR rule->>'kind' IS DISTINCT FROM 'high_potential_threshold'
       OR jsonb_typeof(rule->'threshold') IS DISTINCT FROM 'number' THEN RETURN false; END IF;
    RETURN rule->'threshold' >= '0'::jsonb AND rule->'threshold' <= '1'::jsonb
       AND rule - 'kind' - 'threshold' = '{}'::jsonb;
END;
$$;
ALTER TABLE public.model_registry
    ADD CONSTRAINT model_class_set_valid CHECK (public.valid_class_labels(class_labels, task_type)),
    ADD CONSTRAINT model_rule_valid CHECK (public.valid_decision_rule(decision_rule, task_type));
ALTER TABLE public.screening_results
    ADD CONSTRAINT result_class_scores_valid CHECK (public.valid_class_scores(class_probabilities, task_type)),
    ADD CONSTRAINT result_rule_valid CHECK (public.valid_decision_rule(decision_rule, task_type)),
    ADD CONSTRAINT verified_result_has_snapshot CHECK (provenance <> 'verified' OR
        (model_snapshot IS NOT NULL AND jsonb_typeof(model_snapshot) = 'object'
         AND decision_rule IS NOT NULL AND class_probabilities IS NOT NULL AND confidence_score IS NOT NULL)),
    ADD CONSTRAINT reported_class_score_matches CHECK (class_probabilities IS NULL OR confidence_score IS NULL OR
        abs(confidence_score - (class_probabilities ->> CASE classification
            WHEN 'Normal' THEN 'normal' WHEN 'Low Potential' THEN 'low_potential'
            ELSE 'high_potential' END)::numeric) <= 0.00001);
ALTER TABLE public.expert_validations ADD CONSTRAINT verified_review_has_author CHECK (
    provenance <> 'verified' OR status = 'Pending' OR
    (expert_id IS NOT NULL AND validation_date IS NOT NULL AND remarks IS NOT NULL AND length(btrim(remarks)) > 0)
);

CREATE TABLE public.screening_expert_assignments (
    result_id bigint PRIMARY KEY REFERENCES public.screening_results(result_id) ON DELETE RESTRICT,
    assigned_expert_id uuid REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    assigned_by uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    assigned_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE public.expert_review_history (
    history_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    result_id bigint NOT NULL REFERENCES public.screening_results(result_id) ON DELETE RESTRICT,
    revision bigint NOT NULL CHECK (revision > 0),
    status text NOT NULL CHECK (status IN ('Pending', 'Validated', 'Flagged')),
    expert_id uuid REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    remarks text,
    expert_recommendation text,
    follow_up_needed boolean NOT NULL,
    validation_date timestamptz,
    provenance text NOT NULL CHECK (provenance IN ('verified', 'legacy_unverified')),
    recorded_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (result_id, revision)
);

CREATE TABLE public.api_requests (
    actor_id uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    operation text NOT NULL CHECK (operation IN ('screenings.create', 'students.create', 'accounts.create', 'screenings.review')),
    idempotency_key text NOT NULL CHECK (idempotency_key ~ '^[A-Za-z0-9_-]{16,128}$'),
    request_digest text NOT NULL CHECK (request_digest ~ '^[a-f0-9]{64}$'),
    state text NOT NULL CHECK (state IN ('processing', 'completed', 'failed')),
    result_id bigint REFERENCES public.screening_results(result_id) ON DELETE RESTRICT,
    resource_type text,
    resource_id text,
    error_code text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (actor_id, operation, idempotency_key),
    CHECK (operation <> 'screenings.create' OR state <> 'completed' OR result_id IS NOT NULL),
    CHECK (state = 'completed' OR result_id IS NULL),
    CHECK ((state = 'failed' AND error_code IS NOT NULL) OR (state <> 'failed' AND error_code IS NULL))
);
-- HMAC request_digest must not be a retained plaintext credential/body. Replays
-- reauthorize a stored resource; never persist an old privileged JSON response.
CREATE INDEX api_requests_result_idx ON public.api_requests(result_id) WHERE result_id IS NOT NULL;

CREATE TABLE public.storage_cleanup_jobs (
    cleanup_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    storage_path text NOT NULL CHECK (length(btrim(storage_path)) > 0),
    reason text NOT NULL CHECK (reason IN ('upload_failed', 'commit_failed', 'demo_finished')),
    attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    last_error_code text,
    next_attempt_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.audit_logs
    ADD COLUMN resource_type text,
    ADD COLUMN resource_id text,
    ADD COLUMN request_id text;
CREATE INDEX audit_logs_resource_idx ON public.audit_logs(resource_type, resource_id, created_at DESC);

CREATE FUNCTION public.bump_resource_revision() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
    NEW.revision := OLD.revision + 1;
    IF TG_TABLE_NAME IN ('students', 'expert_validations') THEN NEW.updated_at := now(); END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER user_profile_revision BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW EXECUTE FUNCTION public.bump_resource_revision();
CREATE TRIGGER school_revision BEFORE UPDATE ON public.schools
    FOR EACH ROW EXECUTE FUNCTION public.bump_resource_revision();
CREATE TRIGGER student_revision BEFORE UPDATE ON public.students
    FOR EACH ROW EXECUTE FUNCTION public.bump_resource_revision();
CREATE TRIGGER result_revision BEFORE UPDATE ON public.screening_results
    FOR EACH ROW EXECUTE FUNCTION public.bump_resource_revision();
CREATE TRIGGER validation_revision BEFORE UPDATE ON public.expert_validations
    FOR EACH ROW EXECUTE FUNCTION public.bump_resource_revision();

CREATE FUNCTION public.touch_account_scope_revision() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        UPDATE public.user_profiles SET revision = revision, security_version = security_version + 1 WHERE user_id = OLD.user_id;
    ELSE
        IF TG_OP = 'UPDATE' AND OLD.user_id IS DISTINCT FROM NEW.user_id THEN
            UPDATE public.user_profiles SET revision = revision, security_version = security_version + 1 WHERE user_id = OLD.user_id;
        END IF;
        UPDATE public.user_profiles SET revision = revision, security_version = security_version + 1 WHERE user_id = NEW.user_id;
    END IF;
    RETURN NULL;
END;
$$;
CREATE TRIGGER permission_scope_revision AFTER INSERT OR UPDATE OR DELETE ON public.user_permission_grants
    FOR EACH ROW EXECUTE FUNCTION public.touch_account_scope_revision();
CREATE TRIGGER membership_scope_revision AFTER INSERT OR UPDATE OR DELETE ON public.school_memberships
    FOR EACH ROW EXECUTE FUNCTION public.touch_account_scope_revision();

CREATE FUNCTION public.bump_expert_assignment_revisions() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
    UPDATE public.screening_results SET revision = revision WHERE result_id = NEW.result_id;
    UPDATE public.expert_validations SET revision = revision WHERE result_id = NEW.result_id;
    RETURN NEW;
END;
$$;
CREATE TRIGGER expert_assignment_revisions AFTER INSERT OR UPDATE ON public.screening_expert_assignments
    FOR EACH ROW EXECUTE FUNCTION public.bump_expert_assignment_revisions();

CREATE FUNCTION public.record_review_revision() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND
       (to_jsonb(NEW) - 'revision' - 'updated_at') = (to_jsonb(OLD) - 'revision' - 'updated_at') THEN RETURN NEW; END IF;
    INSERT INTO public.expert_review_history
        (result_id, revision, status, expert_id, remarks, expert_recommendation, follow_up_needed, validation_date, provenance)
    VALUES (NEW.result_id, NEW.revision, NEW.status, NEW.expert_id, NEW.remarks,
            NEW.expert_recommendation, NEW.follow_up_needed, NEW.validation_date, NEW.provenance);
    RETURN NEW;
END;
$$;
CREATE TRIGGER review_history AFTER INSERT OR UPDATE ON public.expert_validations
    FOR EACH ROW EXECUTE FUNCTION public.record_review_revision();

CREATE FUNCTION public.prevent_history_change() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN RAISE EXCEPTION 'Review history is append-only'; END;
$$;
CREATE TRIGGER review_history_immutable BEFORE UPDATE OR DELETE ON public.expert_review_history
    FOR EACH ROW EXECUTE FUNCTION public.prevent_history_change();

CREATE FUNCTION public.protect_published_agreement() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
    IF OLD.published_at IS NOT NULL AND
       (to_jsonb(NEW) - 'is_current') IS DISTINCT FROM (to_jsonb(OLD) - 'is_current') THEN
        RAISE EXCEPTION 'Publish a new version instead of editing an approved agreement';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER agreement_content_immutable BEFORE UPDATE ON public.privacy_agreements
    FOR EACH ROW EXECUTE FUNCTION public.protect_published_agreement();

CREATE FUNCTION public.protect_prediction_snapshot() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
    IF (to_jsonb(NEW) - 'revision') IS DISTINCT FROM (to_jsonb(OLD) - 'revision') THEN
        RAISE EXCEPTION 'Completed prediction snapshots are immutable';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER prediction_snapshot_immutable BEFORE UPDATE ON public.screening_results
    FOR EACH ROW EXECUTE FUNCTION public.protect_prediction_snapshot();

CREATE FUNCTION public.protect_model_identity() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
    IF (OLD.is_selectable OR EXISTS (SELECT 1 FROM public.screening_results WHERE model_id = OLD.model_id)) AND
       (to_jsonb(NEW) - 'is_selectable' - 'is_default') IS DISTINCT FROM
       (to_jsonb(OLD) - 'is_selectable' - 'is_default') THEN
        RAISE EXCEPTION 'Publish a new model version instead of changing published identity';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER model_identity_immutable BEFORE UPDATE ON public.model_registry
    FOR EACH ROW EXECUTE FUNCTION public.protect_model_identity();

CREATE FUNCTION public.protect_report_snapshot() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
    IF to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD) THEN
        RAISE EXCEPTION 'Completed report context is immutable';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER report_context_immutable BEFORE UPDATE ON public.screening_reports
    FOR EACH ROW EXECUTE FUNCTION public.protect_report_snapshot();

ALTER TABLE public.user_permission_grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.school_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assignment_eligibilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.privacy_agreements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_session_revocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.screening_expert_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.expert_review_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.storage_cleanup_jobs ENABLE ROW LEVEL SECURITY;
-- No client RLS policies: all data access goes through the authorized Flask API.
-- Test elevated server role/table privileges separately in a real test project.
COMMIT;
