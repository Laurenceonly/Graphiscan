-- Apply once after018. No provider calls, new users, credentials or grants seeded.
BEGIN;

CREATE TABLE public.admin_account_operations (
    operation_id uuid PRIMARY KEY,
    actor_id uuid NOT NULL REFERENCES public.user_profiles(user_id) ON DELETE RESTRICT,
    target_id uuid NOT NULL,
    action text NOT NULL CHECK (action IN ('reset_password','delete')),
    expected_revision bigint NOT NULL,
    locked_revision bigint NOT NULL,
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    response_data jsonb
);
CREATE UNIQUE INDEX admin_account_one_pending ON public.admin_account_operations(target_id)
    WHERE completed_at IS NULL;
ALTER TABLE public.admin_account_operations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.admin_account_operations FROM PUBLIC,anon,authenticated,service_role,
    graphiscan_api_reader,graphiscan_password_writer,graphiscan_admin_writer;

-- The receipt survives removal of an otherwise unused account.
ALTER TABLE public.account_issuance_requests DROP CONSTRAINT account_issuance_requests_target_id_fkey;
ALTER TABLE public.account_issuance_requests ADD CONSTRAINT account_issuance_requests_target_id_fkey
    FOREIGN KEY(target_id) REFERENCES auth.users(id) ON DELETE SET NULL;

CREATE FUNCTION public.graphiscan_admin_account_gate(subject_id uuid, provider_session_id uuid)
RETURNS text LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text;
BEGIN
    PERFORM user_id FROM public.user_profiles WHERE user_id=subject_id;
    IF NOT FOUND THEN RETURN 'ACCOUNT_UNAVAILABLE'; END IF;
    SELECT public.graphiscan_read_directory(subject_id,provider_session_id,
        'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' INTO code;
    IF code IS NOT NULL THEN RETURN code; END IF;
    IF NOT EXISTS (SELECT 1 FROM public.user_profiles p WHERE p.user_id=subject_id
        AND p.role IN ('admin','researcher')) OR NOT EXISTS (
        SELECT 1 FROM public.user_permission_grants WHERE user_id=subject_id
        AND permission_key='accounts.manage' AND school_id IS NULL) THEN RETURN 'FORBIDDEN'; END IF;
    RETURN NULL;
END;
$$;

CREATE FUNCTION public.graphiscan_admin_account_snapshot(target uuid)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
SELECT jsonb_build_object('user_id',p.user_id::text,'full_name',p.full_name,'email',u.email,
    'role',p.role,'account_status',p.account_status,'revision',p.revision,'created_at',p.created_at,
    'must_change_password',p.must_change_password,'credential_update_pending',p.credential_update_pending,
    'school_ids',coalesce((SELECT jsonb_agg(m.school_id::text ORDER BY m.school_id)
        FROM public.school_memberships m WHERE m.user_id=p.user_id),'[]'::jsonb),
    'permission_grants',coalesce((SELECT jsonb_agg(jsonb_build_object('permission_key',g.permission_key,
        'school_id',g.school_id::text) ORDER BY g.permission_key,g.school_id NULLS FIRST)
        FROM public.user_permission_grants g WHERE g.user_id=p.user_id),'[]'::jsonb))
FROM public.user_profiles p JOIN auth.users u ON u.id=p.user_id WHERE p.user_id=target;
$$;

CREATE FUNCTION public.graphiscan_get_admin_account(subject_id uuid,provider_session_id uuid,target uuid)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text; result jsonb;
BEGIN
    code:=public.graphiscan_admin_account_gate(subject_id,provider_session_id);
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    result:=public.graphiscan_admin_account_snapshot(target);
    IF result IS NULL THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    RETURN jsonb_build_object('code',NULL,'data',result);
END;
$$;

CREATE FUNCTION public.graphiscan_begin_admin_account_operation(subject_id uuid,provider_session_id uuid,
    operation uuid,target uuid,operation_action text,revision bigint,request uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE
    code text; actor_role text; p public.user_profiles%ROWTYPE;
    previous public.admin_account_operations%ROWTYPE;
    reference record; in_use boolean;
BEGIN
    PERFORM user_id FROM public.user_profiles WHERE user_id=subject_id FOR SHARE;
    PERFORM version FROM public.privacy_agreements WHERE is_current FOR SHARE;
    code:=public.graphiscan_admin_account_gate(subject_id,provider_session_id);
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    IF operation IS NULL OR target IS NULL OR request IS NULL OR revision IS NULL OR revision<1
        OR operation_action IS NULL OR operation_action NOT IN ('reset_password','delete') THEN
        RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    IF target=subject_id THEN RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(operation::text,820));
    SELECT * INTO previous FROM public.admin_account_operations WHERE operation_id=operation;
    IF FOUND THEN
        IF previous.actor_id<>subject_id OR previous.target_id<>target
            OR previous.action<>operation_action OR previous.expected_revision<>revision THEN
            RETURN jsonb_build_object('code','ISSUANCE_CONFLICT'); END IF;
        IF previous.completed_at IS NOT NULL THEN
            RETURN jsonb_build_object('code',NULL,'data',previous.response_data); END IF;
        RETURN jsonb_build_object('code','ACCOUNT_OPERATION_PENDING');
    END IF;
    SELECT role INTO actor_role FROM public.user_profiles WHERE user_id=subject_id;
    SELECT * INTO p FROM public.user_profiles WHERE user_id=target FOR UPDATE;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    IF actor_role<>'admin' AND p.role IN ('admin','researcher') THEN
        RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    IF p.revision<>revision THEN RETURN jsonb_build_object('code','REVISION_CONFLICT'); END IF;
    IF p.credential_update_pending OR EXISTS (SELECT 1 FROM public.admin_account_operations
        WHERE target_id=target AND completed_at IS NULL) THEN
        RETURN jsonb_build_object('code','ACCOUNT_OPERATION_PENDING'); END IF;
    IF operation_action='delete' THEN
        IF p.role='admin' AND p.account_status='active' THEN
            PERFORM pg_advisory_xact_lock(71826391042);
            IF (SELECT count(*) FROM public.user_profiles WHERE role='admin' AND account_status='active')<=1 THEN
                RETURN jsonb_build_object('code','LAST_ADMIN'); END IF;
        END IF;
        -- Only unused accounts can be removed. Never cascade through student,
        -- assignment, credential, consent, screening or audit history.
        IF EXISTS (SELECT 1 FROM auth.sessions WHERE user_id=target) THEN
            RETURN jsonb_build_object('code','ACCOUNT_IN_USE'); END IF;
        FOR reference IN
            SELECT n.nspname,c.relname,a.attname
            FROM pg_constraint fk JOIN pg_class c ON c.oid=fk.conrelid
            JOIN pg_namespace n ON n.oid=c.relnamespace
            JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum=fk.conkey[1]
            WHERE fk.contype='f' AND n.nspname='public' AND cardinality(fk.conkey)=1
                AND fk.confrelid IN ('auth.users'::regclass,'public.user_profiles'::regclass)
        LOOP
            IF reference.relname='user_profiles' AND reference.attname='user_id' THEN CONTINUE; END IF;
            IF reference.relname='account_issuance_requests' AND reference.attname='target_id' THEN CONTINUE; END IF;
            EXECUTE format('SELECT EXISTS (SELECT 1 FROM %I.%I WHERE %I=$1)',
                reference.nspname,reference.relname,reference.attname) INTO in_use USING target;
            IF in_use THEN RETURN jsonb_build_object('code','ACCOUNT_IN_USE'); END IF;
        END LOOP;
    END IF;
    UPDATE public.user_profiles SET credential_update_pending=true,
        account_status=CASE WHEN operation_action='delete' THEN 'disabled' ELSE account_status END
        WHERE user_id=target RETURNING * INTO p;
    INSERT INTO public.admin_account_operations(operation_id,actor_id,target_id,action,expected_revision,locked_revision)
    VALUES(operation,subject_id,target,operation_action,revision,p.revision);
    INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
    VALUES(subject_id,'accounts.'||operation_action||'.started','account',target::text,request::text);
    RETURN jsonb_build_object('code',NULL,'reserved',true);
END;
$$;

CREATE FUNCTION public.graphiscan_complete_admin_account_operation(subject_id uuid,provider_session_id uuid,
    operation uuid,request uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE
    code text; pending public.admin_account_operations%ROWTYPE;
    p public.user_profiles%ROWTYPE; result jsonb;
BEGIN
    PERFORM user_id FROM public.user_profiles WHERE user_id=subject_id FOR SHARE;
    PERFORM version FROM public.privacy_agreements WHERE is_current FOR SHARE;
    code:=public.graphiscan_admin_account_gate(subject_id,provider_session_id);
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    SELECT * INTO pending FROM public.admin_account_operations WHERE operation_id=operation FOR UPDATE;
    IF NOT FOUND OR pending.actor_id<>subject_id OR request IS NULL THEN
        RETURN jsonb_build_object('code','ISSUANCE_CONFLICT'); END IF;
    IF pending.completed_at IS NOT NULL THEN RETURN jsonb_build_object('code',NULL,'data',pending.response_data); END IF;
    IF pending.action='delete' THEN
        IF EXISTS (SELECT 1 FROM auth.users WHERE id=pending.target_id) OR EXISTS (
            SELECT 1 FROM public.user_profiles WHERE user_id=pending.target_id) THEN
            RETURN jsonb_build_object('code','ACCOUNT_OPERATION_PENDING'); END IF;
        result:=jsonb_build_object('user_id',pending.target_id::text,'deleted',true);
    ELSE
        SELECT * INTO p FROM public.user_profiles WHERE user_id=pending.target_id FOR UPDATE;
        IF NOT FOUND OR NOT p.credential_update_pending OR p.revision<>pending.locked_revision THEN
            RETURN jsonb_build_object('code','ACCOUNT_OPERATION_PENDING'); END IF;
        IF (SELECT role FROM public.user_profiles WHERE user_id=subject_id)<>'admin' AND p.role IN ('admin','researcher') THEN
            RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
        UPDATE public.user_profiles SET must_change_password=true,credential_update_pending=false,
            password_changed_at=NULL,security_version=security_version+1 WHERE user_id=pending.target_id;
        result:=public.graphiscan_admin_account_snapshot(pending.target_id);
    END IF;
    UPDATE public.admin_account_operations SET completed_at=clock_timestamp(),response_data=result
    WHERE operation_id=operation;
    INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
    VALUES(subject_id,'accounts.'||pending.action||'.completed','account',pending.target_id::text,request::text);
    RETURN jsonb_build_object('code',NULL,'data',result);
END;
$$;

CREATE FUNCTION public.graphiscan_read_admin_account_operation(subject_id uuid,provider_session_id uuid,operation uuid)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE code text; pending public.admin_account_operations%ROWTYPE;
BEGIN
    code:=public.graphiscan_admin_account_gate(subject_id,provider_session_id);
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    SELECT * INTO pending FROM public.admin_account_operations WHERE operation_id=operation AND actor_id=subject_id;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    RETURN jsonb_build_object('code',NULL,'data',jsonb_build_object('operation_id',operation::text,
        'state',CASE WHEN pending.completed_at IS NULL THEN 'pending' ELSE 'completed' END,
        'action',pending.action,'target_id',pending.target_id::text,'result',pending.response_data));
END;
$$;

REVOKE ALL ON FUNCTION public.graphiscan_admin_account_gate(uuid,uuid),
    public.graphiscan_admin_account_snapshot(uuid),public.graphiscan_get_admin_account(uuid,uuid,uuid),
    public.graphiscan_begin_admin_account_operation(uuid,uuid,uuid,uuid,text,bigint,uuid),
    public.graphiscan_complete_admin_account_operation(uuid,uuid,uuid,uuid),
    public.graphiscan_read_admin_account_operation(uuid,uuid,uuid)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_password_writer,graphiscan_admin_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_get_admin_account(uuid,uuid,uuid),
    public.graphiscan_read_admin_account_operation(uuid,uuid,uuid) TO graphiscan_api_reader;
GRANT EXECUTE ON FUNCTION public.graphiscan_begin_admin_account_operation(uuid,uuid,uuid,uuid,text,bigint,uuid),
    public.graphiscan_complete_admin_account_operation(uuid,uuid,uuid,uuid) TO graphiscan_admin_writer;

CREATE OR REPLACE FUNCTION public.graphiscan_update_account(
    subject_id uuid, provider_session_id uuid, target_id uuid,
    payload jsonb, request uuid
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE
    actor public.user_profiles%ROWTYPE;
    target public.user_profiles%ROWTYPE;
    code text;
    fields text[];
    new_role text;
    new_status text;
    new_name text;
    desired_schools bigint[];
    desired_grants jsonb;
    grant_item jsonb;
    grant_key text;
    grant_school bigint;
    grant_count integer;
    active_admins bigint;
    response_data jsonb;
BEGIN
    SELECT * INTO actor FROM public.user_profiles WHERE user_id=subject_id FOR SHARE;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','ACCOUNT_UNAVAILABLE'); END IF;
    PERFORM version FROM public.privacy_agreements WHERE is_current FOR SHARE;
    SELECT public.graphiscan_read_directory(subject_id,provider_session_id,
        'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' INTO code;
    IF code IS NOT NULL THEN RETURN jsonb_build_object('code',code); END IF;
    IF actor.role NOT IN ('admin','researcher') OR NOT EXISTS (
        SELECT 1 FROM public.user_permission_grants g
        WHERE g.user_id=subject_id AND g.permission_key='accounts.manage' AND g.school_id IS NULL
    ) THEN RETURN jsonb_build_object('code','FORBIDDEN'); END IF;
    IF target_id IS NULL OR payload IS NULL OR jsonb_typeof(payload) IS DISTINCT FROM 'object'
        OR request IS NULL THEN RETURN jsonb_build_object('code','INVALID_INPUT'); END IF;
    SELECT array_agg(key) INTO fields FROM jsonb_object_keys(payload) key;
    IF fields IS NULL OR NOT fields <@ ARRAY['expected_revision','full_name','role',
        'account_status','school_ids','permission_grants']::text[]
        OR jsonb_typeof(payload->'expected_revision') IS DISTINCT FROM 'number'
        OR (payload->>'expected_revision') !~ '^[1-9][0-9]{0,18}$'
        OR (payload->>'expected_revision')::numeric > 9223372036854775806
        OR cardinality(fields) < 2 THEN
        RETURN jsonb_build_object('code','INVALID_INPUT');
    END IF;
    IF payload ? 'full_name' THEN
        IF jsonb_typeof(payload->'full_name') IS DISTINCT FROM 'string'
            OR length(btrim(payload->>'full_name')) NOT BETWEEN 1 AND 200
            OR (payload->>'full_name') ~ '[[:cntrl:]]' THEN
            RETURN jsonb_build_object('code','INVALID_INPUT');
        END IF;
        new_name := btrim(payload->>'full_name');
    END IF;
    IF payload ? 'role' THEN
        new_role := payload->>'role';
        IF jsonb_typeof(payload->'role') IS DISTINCT FROM 'string'
            OR new_role NOT IN ('admin','researcher','teacher','parent','expert','guest') THEN
            RETURN jsonb_build_object('code','INVALID_INPUT');
        END IF;
        IF actor.role <> 'admin' AND new_role IN ('admin','researcher') THEN
            RETURN jsonb_build_object('code','FORBIDDEN');
        END IF;
    END IF;
    IF payload ? 'account_status' THEN
        new_status := payload->>'account_status';
        IF jsonb_typeof(payload->'account_status') IS DISTINCT FROM 'string'
            OR new_status NOT IN ('active','pending','disabled','rejected') THEN
            RETURN jsonb_build_object('code','INVALID_INPUT');
        END IF;
    END IF;
    IF payload ? 'school_ids' THEN
        IF jsonb_typeof(payload->'school_ids') IS DISTINCT FROM 'array' THEN
            RETURN jsonb_build_object('code','INVALID_INPUT');
        END IF;
        IF jsonb_array_length(payload->'school_ids') > 128 THEN
            RETURN jsonb_build_object('code','INVALID_INPUT');
        END IF;
        IF EXISTS (SELECT 1 FROM jsonb_array_elements(payload->'school_ids') e
            WHERE jsonb_typeof(e) IS DISTINCT FROM 'string'
                OR e #>> '{}' !~ '^[1-9][0-9]{0,18}$') THEN
            RETURN jsonb_build_object('code','INVALID_INPUT');
        END IF;
        IF EXISTS (SELECT 1 FROM jsonb_array_elements_text(payload->'school_ids') e
            GROUP BY e HAVING count(*) > 1) THEN
            RETURN jsonb_build_object('code','INVALID_INPUT');
        END IF;
        BEGIN
            SELECT coalesce(array_agg(value::bigint ORDER BY value::bigint),'{}'::bigint[])
                INTO desired_schools FROM jsonb_array_elements_text(payload->'school_ids') e(value);
        EXCEPTION WHEN numeric_value_out_of_range THEN
            RETURN jsonb_build_object('code','INVALID_INPUT');
        END;
        IF EXISTS (SELECT 1 FROM unnest(desired_schools) s
            LEFT JOIN public.schools known ON known.school_id=s WHERE known.school_id IS NULL) THEN
            RETURN jsonb_build_object('code','INVALID_ASSIGNMENT');
        END IF;
    END IF;
    IF payload ? 'permission_grants' THEN
        IF jsonb_typeof(payload->'permission_grants') IS DISTINCT FROM 'array' THEN
            RETURN jsonb_build_object('code','INVALID_INPUT');
        END IF;
        IF jsonb_array_length(payload->'permission_grants') > 128 THEN
            RETURN jsonb_build_object('code','INVALID_INPUT');
        END IF;
        desired_grants := payload->'permission_grants';
        FOR grant_item IN SELECT value FROM jsonb_array_elements(desired_grants) LOOP
            IF jsonb_typeof(grant_item) IS DISTINCT FROM 'object'
                OR (SELECT count(*) FROM jsonb_object_keys(grant_item)) <> 2
                OR NOT (grant_item ?& ARRAY['permission_key','school_id']::text[]) THEN
                RETURN jsonb_build_object('code','INVALID_INPUT');
            END IF;
            grant_key := grant_item->>'permission_key';
            IF jsonb_typeof(grant_item->'permission_key') IS DISTINCT FROM 'string'
                OR grant_key NOT IN ('accounts.manage','permissions.manage','schools.manage',
                    'assignments.manage','audit.read') THEN
                RETURN jsonb_build_object('code','INVALID_INPUT');
            END IF;
            IF jsonb_typeof(grant_item->'school_id')='null' THEN
                grant_school := NULL;
            ELSIF jsonb_typeof(grant_item->'school_id')='string'
                AND grant_item->>'school_id' ~ '^[1-9][0-9]{0,18}$' THEN
                BEGIN grant_school := (grant_item->>'school_id')::bigint;
                EXCEPTION WHEN numeric_value_out_of_range THEN
                    RETURN jsonb_build_object('code','INVALID_INPUT');
                END;
            ELSE
                RETURN jsonb_build_object('code','INVALID_INPUT');
            END IF;
            IF grant_key IN ('accounts.manage','permissions.manage','audit.read')
                AND grant_school IS NOT NULL THEN
                RETURN jsonb_build_object('code','INVALID_INPUT');
            END IF;
            IF grant_key IN ('accounts.manage','permissions.manage') AND actor.role <> 'admin' THEN
                RETURN jsonb_build_object('code','FORBIDDEN');
            END IF;
            IF NOT public.graphiscan_directory_grant(subject_id,'permissions.manage',grant_school) THEN
                RETURN jsonb_build_object('code','FORBIDDEN');
            END IF;
            IF NOT public.graphiscan_directory_grant(subject_id,grant_key,grant_school) THEN
                RETURN jsonb_build_object('code','FORBIDDEN');
            END IF;
            IF grant_school IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM public.schools s WHERE s.school_id=grant_school) THEN
                RETURN jsonb_build_object('code','INVALID_ASSIGNMENT');
            END IF;
        END LOOP;
        SELECT count(*) INTO grant_count FROM (
            SELECT DISTINCT value->>'permission_key' AS permission_key,
                value->>'school_id' AS school_id
            FROM jsonb_array_elements(desired_grants)
        ) unique_grant;
        IF grant_count <> jsonb_array_length(desired_grants) THEN
            RETURN jsonb_build_object('code','INVALID_INPUT');
        END IF;
    END IF;
    IF target_id=subject_id AND (payload ? 'role' OR payload ? 'account_status'
        OR payload ? 'school_ids' OR payload ? 'permission_grants') THEN
        RETURN jsonb_build_object('code','FORBIDDEN');
    END IF;

    SELECT * INTO target FROM public.user_profiles WHERE user_id=target_id FOR UPDATE;
    IF NOT FOUND THEN RETURN jsonb_build_object('code','NOT_FOUND'); END IF;
    IF actor.role <> 'admin' AND target.role IN ('admin','researcher') THEN
        RETURN jsonb_build_object('code','FORBIDDEN');
    END IF;
    IF target.credential_update_pending THEN
        RETURN jsonb_build_object('code','ACCOUNT_OPERATION_PENDING');
    END IF;
    IF target.revision <> (payload->>'expected_revision')::bigint THEN
        RETURN jsonb_build_object('code','REVISION_CONFLICT');
    END IF;
    IF target.role='admin' AND target.account_status='active'
        AND (coalesce(new_role,target.role) <> 'admin'
            OR coalesce(new_status,target.account_status) <> 'active') THEN
        PERFORM pg_advisory_xact_lock(71826391042);
        SELECT count(*) INTO active_admins FROM public.user_profiles
            WHERE role='admin' AND account_status='active';
        IF active_admins <= 1 THEN RETURN jsonb_build_object('code','LAST_ADMIN'); END IF;
    END IF;
    IF payload ? 'permission_grants' THEN
        IF EXISTS (SELECT 1 FROM public.user_permission_grants old
            WHERE old.user_id=target_id AND NOT EXISTS (
                SELECT 1 FROM jsonb_array_elements(desired_grants) wanted
                WHERE wanted->>'permission_key'=old.permission_key
                    AND CASE WHEN jsonb_typeof(wanted->'school_id')='null'
                        THEN old.school_id IS NULL
                        ELSE old.school_id=(wanted->>'school_id')::bigint END)
            AND (NOT public.graphiscan_directory_grant(subject_id,'permissions.manage',old.school_id)
                OR NOT public.graphiscan_directory_grant(subject_id,old.permission_key,old.school_id))) THEN
            RETURN jsonb_build_object('code','FORBIDDEN');
        END IF;
    END IF;
    IF payload ? 'school_ids' THEN
        DELETE FROM public.school_memberships m WHERE m.user_id=target_id
            AND NOT (m.school_id = ANY(desired_schools));
        INSERT INTO public.school_memberships(user_id,school_id,created_by)
        SELECT target_id,s,subject_id FROM unnest(desired_schools) s
        ON CONFLICT (user_id,school_id) DO NOTHING;
    END IF;
    IF payload ? 'permission_grants' THEN
        DELETE FROM public.user_permission_grants old WHERE old.user_id=target_id
            AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements(desired_grants) wanted
                WHERE wanted->>'permission_key'=old.permission_key
                    AND CASE WHEN jsonb_typeof(wanted->'school_id')='null'
                        THEN old.school_id IS NULL
                        ELSE old.school_id=(wanted->>'school_id')::bigint END);
        INSERT INTO public.user_permission_grants(user_id,permission_key,school_id,granted_by)
        SELECT target_id,wanted->>'permission_key',
            CASE WHEN jsonb_typeof(wanted->'school_id')='null' THEN NULL
                ELSE (wanted->>'school_id')::bigint END,subject_id
        FROM jsonb_array_elements(desired_grants) wanted
        ON CONFLICT DO NOTHING;
    END IF;
    UPDATE public.user_profiles SET full_name=coalesce(new_name,full_name),
        role=coalesce(new_role,role),account_status=coalesce(new_status,account_status)
        WHERE user_id=target_id RETURNING * INTO target;
    INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id,request_id)
        VALUES(subject_id,'accounts.updated','account',target_id::text,request::text);
    SELECT jsonb_build_object('user_id',p.user_id::text,'full_name',p.full_name,
        'role',p.role,'account_status',p.account_status,
        'revision',p.revision,'school_ids',coalesce((SELECT jsonb_agg(m.school_id::text ORDER BY m.school_id)
            FROM public.school_memberships m WHERE m.user_id=p.user_id),'[]'::jsonb),
        'permissions',coalesce((SELECT jsonb_agg(DISTINCT g.permission_key ORDER BY g.permission_key)
            FROM public.user_permission_grants g WHERE g.user_id=p.user_id),'[]'::jsonb),
        'permission_grants',coalesce((SELECT jsonb_agg(jsonb_build_object(
            'permission_key',g.permission_key,'school_id',g.school_id::text)
            ORDER BY g.permission_key,g.school_id NULLS FIRST)
            FROM public.user_permission_grants g WHERE g.user_id=p.user_id),'[]'::jsonb),
        'created_at',p.created_at,
        'onboarding',jsonb_build_object('must_change_password',p.must_change_password,
            'required_agreement_version',a.version,'accepted_agreement_version',accepted.agreement_version,
            'next_action',CASE WHEN p.must_change_password THEN 'change_password'
                WHEN a.version IS NULL THEN 'agreement_unavailable'
                WHEN accepted.agreement_version IS DISTINCT FROM a.version THEN 'accept_privacy'
                ELSE 'ready' END))
        INTO response_data FROM public.user_profiles p
        LEFT JOIN LATERAL (SELECT agreement.version FROM public.privacy_agreements agreement
            WHERE agreement.is_current AND (agreement.test_subject_id IS NULL OR agreement.test_subject_id=p.user_id)
                AND (agreement.test_subject_ids IS NULL OR p.user_id=ANY(agreement.test_subject_ids))
                AND agreement.approved_by IS NOT NULL AND agreement.approved_at<=clock_timestamp()
                AND agreement.published_at IS NOT NULL AND agreement.published_at<=clock_timestamp()
                AND agreement.content_sha256=encode(sha256(convert_to(agreement.content,'UTF8')),'hex')
            LIMIT 1) a ON true
        LEFT JOIN LATERAL (SELECT acceptance.agreement_version
            FROM public.privacy_agreement_acceptances acceptance
            WHERE acceptance.user_id=p.user_id AND acceptance.agreement_version=a.version
            LIMIT 1) accepted ON true
        WHERE p.user_id=target_id;
    RETURN jsonb_build_object('code',NULL,'data',response_data);
END;
$$;

-- Add the account revision to list rows so a client can submit optimistic writes.

COMMIT;
