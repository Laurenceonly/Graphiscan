-- GraphiScan target identity schema for Supabase PostgreSQL.
-- Apply only during the PostgreSQL migration, after reviewing existing user data.
-- The GraphiScan server owns these tables. Clients use Auth to sign in and the
-- Flask API to access protected records; no direct client RLS policies are added.

BEGIN;

CREATE TABLE public.user_profiles (
    user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name text NOT NULL CHECK (length(btrim(full_name)) > 0),
    role text NOT NULL CHECK (role IN ('admin', 'researcher', 'teacher', 'parent', 'expert', 'guest')),
    account_status text NOT NULL DEFAULT 'active'
        CHECK (account_status IN ('active', 'pending', 'disabled', 'rejected')),
    must_change_password boolean NOT NULL DEFAULT true,
    created_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    password_changed_at timestamptz,
    CONSTRAINT temporary_account_has_issuer
        CHECK (created_by IS NOT NULL OR role = 'admin')
);

CREATE INDEX user_profiles_role_status_idx
    ON public.user_profiles (role, account_status);

CREATE TABLE public.privacy_agreement_acceptances (
    acceptance_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    agreement_version text NOT NULL CHECK (length(btrim(agreement_version)) > 0),
    accepted_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, agreement_version)
);

CREATE INDEX privacy_agreement_acceptances_user_idx
    ON public.privacy_agreement_acceptances (user_id, accepted_at DESC);

ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.privacy_agreement_acceptances ENABLE ROW LEVEL SECURITY;

COMMIT;
