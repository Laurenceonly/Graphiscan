-- Target GraphiScan data model for Supabase PostgreSQL.
-- Apply after 001_identity.sql. This defines new tables only; it does not import
-- private MySQL rows or install model artifacts. Server API access only.

BEGIN;

CREATE TABLE public.schools (
    school_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL CHECK (length(btrim(name)) > 0),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX schools_name_idx ON public.schools (lower(name));

CREATE TABLE public.students (
    student_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name text NOT NULL CHECK (length(btrim(full_name)) > 0),
    age smallint CHECK (age > 0),
    school_id bigint NOT NULL REFERENCES public.schools(school_id),
    grade_level smallint NOT NULL CHECK (grade_level BETWEEN 1 AND 3),
    teacher_id uuid REFERENCES public.user_profiles(user_id) ON DELETE SET NULL,
    parent_id uuid REFERENCES public.user_profiles(user_id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX students_school_grade_idx ON public.students (school_id, grade_level);
CREATE INDEX students_teacher_idx ON public.students (teacher_id);
CREATE INDEX students_parent_idx ON public.students (parent_id);

CREATE TABLE public.model_registry (
    model_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_key text NOT NULL CHECK (length(btrim(model_key)) > 0),
    model_version text NOT NULL CHECK (length(btrim(model_version)) > 0),
    architecture text NOT NULL,
    task_type text NOT NULL CHECK (task_type IN ('binary', 'three_class')),
    test_accuracy numeric(6,5) CHECK (test_accuracy BETWEEN 0 AND 1),
    is_selectable boolean NOT NULL DEFAULT false,
    is_default boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (model_key, model_version),
    UNIQUE (model_id, task_type),
    CHECK (NOT is_default OR is_selectable)
);

CREATE UNIQUE INDEX model_registry_one_default_per_task_idx
    ON public.model_registry (task_type) WHERE is_default;

CREATE TABLE public.handwriting_samples (
    sample_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id bigint NOT NULL REFERENCES public.students(student_id) ON DELETE RESTRICT,
    teacher_id uuid REFERENCES public.user_profiles(user_id) ON DELETE SET NULL,
    storage_path text NOT NULL CHECK (length(btrim(storage_path)) > 0),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX handwriting_samples_student_date_idx
    ON public.handwriting_samples (student_id, created_at DESC);

CREATE TABLE public.screening_results (
    result_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sample_id bigint NOT NULL UNIQUE
        REFERENCES public.handwriting_samples(sample_id) ON DELETE RESTRICT,
    model_id bigint NOT NULL,
    task_type text NOT NULL CHECK (task_type IN ('binary', 'three_class')),
    FOREIGN KEY (model_id, task_type)
        REFERENCES public.model_registry(model_id, task_type),
    classification text NOT NULL,
    class_probabilities jsonb,
    confidence_score numeric(6,5) CHECK (confidence_score BETWEEN 0 AND 1),
    analysis_summary text,
    date_generated timestamptz NOT NULL DEFAULT now(),
    CHECK (
        (task_type = 'binary' AND classification IN ('Normal', 'High Potential'))
        OR (task_type = 'three_class'
            AND classification IN ('Normal', 'Low Potential', 'High Potential'))
    )
);

CREATE TABLE public.expert_validations (
    validation_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    result_id bigint NOT NULL UNIQUE
        REFERENCES public.screening_results(result_id) ON DELETE RESTRICT,
    status text NOT NULL DEFAULT 'Pending'
        CHECK (status IN ('Pending', 'Validated', 'Flagged')),
    expert_id uuid REFERENCES public.user_profiles(user_id) ON DELETE SET NULL,
    remarks text,
    expert_recommendation text,
    follow_up_needed boolean NOT NULL DEFAULT false,
    validation_date timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.screening_reports (
    report_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id bigint NOT NULL REFERENCES public.students(student_id) ON DELETE RESTRICT,
    result_id bigint NOT NULL UNIQUE
        REFERENCES public.screening_results(result_id) ON DELETE RESTRICT,
    report_type text NOT NULL CHECK (report_type IN ('Initial Screening', 'Follow-up Screening')),
    report_status text NOT NULL DEFAULT 'Generated',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX screening_reports_one_initial_per_student_idx
    ON public.screening_reports (student_id)
    WHERE report_type = 'Initial Screening';
CREATE INDEX screening_reports_student_date_idx
    ON public.screening_reports (student_id, created_at DESC);

CREATE TABLE public.audit_logs (
    log_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_id uuid REFERENCES public.user_profiles(user_id) ON DELETE SET NULL,
    action text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX audit_logs_actor_date_idx ON public.audit_logs (actor_id, created_at DESC);

ALTER TABLE public.schools ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.students ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.handwriting_samples ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.screening_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.expert_validations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.screening_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

COMMIT;
