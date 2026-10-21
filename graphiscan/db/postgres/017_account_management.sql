-- Apply once after 016 as the reviewed schema owner.
-- Adds bounded account updates for the Flask v1 API. Does not create Auth users
-- or reset credentials. Those cross-provider operations need a separate saga.
BEGIN;

CREATE ROLE graphiscan_admin_writer NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB
    NOCREATEROLE NOREPLICATION NOBYPASSRLS;
GRANT USAGE ON SCHEMA public TO graphiscan_admin_writer;

CREATE FUNCTION public.graphiscan_update_account(
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
    IF payload ? 'school_ids' THEN
        DELETE FROM public.school_memberships m WHERE m.user_id=target_id
            AND NOT (m.school_id = ANY(desired_schools));
        INSERT INTO public.school_memberships(user_id,school_id,created_by)
        SELECT target_id,s,subject_id FROM unnest(desired_schools) s
        ON CONFLICT (user_id,school_id) DO NOTHING;
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
CREATE OR REPLACE FUNCTION public.graphiscan_read_admin(
    subject_id uuid, provider_session_id uuid, resource text, search_text text,
    filter_role text, filter_status text, after_time timestamptz,
    after_user uuid, after_log bigint, page_limit integer
) RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
WITH base AS MATERIALIZED (
    SELECT public.graphiscan_read_directory(subject_id,provider_session_id,
        'schools','',NULL,NULL,NULL,NULL,1,NULL)->>'code' AS code
), gate AS MATERIALIZED (
    SELECT CASE
        WHEN base.code IS NOT NULL THEN base.code
        WHEN p.role NOT IN ('admin','researcher') THEN 'FORBIDDEN'
        WHEN resource NOT IN ('accounts','audit') OR resource IS NULL
            OR search_text IS NULL OR length(search_text)>120
            OR page_limit IS NULL OR page_limit NOT BETWEEN 1 AND 100
            OR ((after_time IS NULL) <> (CASE WHEN resource='accounts' THEN after_user IS NULL ELSE after_log IS NULL END))
            OR (resource='accounts' AND (after_log IS NOT NULL
                OR (filter_role IS NOT NULL AND filter_role NOT IN ('admin','researcher','teacher','parent','expert','guest'))
                OR (filter_status IS NOT NULL AND filter_status NOT IN ('active','pending','disabled','rejected'))))
            OR (resource='audit' AND (after_user IS NOT NULL OR filter_status IS NOT NULL
                OR (filter_role IS NOT NULL AND filter_role NOT IN ('admin','researcher','teacher','parent','expert','guest'))))
            THEN 'INVALID_QUERY'
        WHEN NOT EXISTS (SELECT 1 FROM public.user_permission_grants g
            WHERE g.user_id=subject_id AND g.school_id IS NULL
                AND g.permission_key=CASE resource WHEN 'accounts' THEN 'accounts.manage' ELSE 'audit.read' END)
            THEN 'FORBIDDEN'
        ELSE NULL END AS code
    FROM base LEFT JOIN public.user_profiles p ON p.user_id=subject_id
), account_page AS MATERIALIZED (
    SELECT p.created_at AS sort_time,p.user_id AS sort_user,
        jsonb_build_object('user_id',p.user_id::text,'full_name',p.full_name,
            'email',u.email,'role',p.role,'account_status',p.account_status,
            'revision',p.revision,'created_at',p.created_at) AS row_data
    FROM public.user_profiles p JOIN auth.users u ON u.id=p.user_id CROSS JOIN gate g
    WHERE g.code IS NULL AND resource='accounts'
        AND (filter_role IS NULL OR p.role=filter_role)
        AND (filter_status IS NULL OR p.account_status=filter_status)
        AND (search_text='' OR strpos(lower(p.full_name),lower(search_text))>0
            OR strpos(lower(coalesce(u.email,'')),lower(search_text))>0)
        AND (after_time IS NULL OR (p.created_at,p.user_id)<(after_time,after_user))
    ORDER BY p.created_at DESC,p.user_id DESC
    LIMIT least(greatest(coalesce(page_limit,1),1),100)+1
), audit_page AS MATERIALIZED (
    SELECT a.created_at AS sort_time,a.log_id AS sort_id,
        jsonb_build_object('log_id',a.log_id::text,'actor_id',a.actor_id::text,
            'full_name',p.full_name,'role',p.role,'action',a.action,'created_at',a.created_at) AS row_data
    FROM public.audit_logs a LEFT JOIN public.user_profiles p ON p.user_id=a.actor_id CROSS JOIN gate g
    WHERE g.code IS NULL AND resource='audit'
        AND (filter_role IS NULL OR p.role=filter_role)
        AND (search_text='' OR strpos(lower(a.action),lower(search_text))>0
            OR strpos(lower(coalesce(p.full_name,'')),lower(search_text))>0)
        AND (after_time IS NULL OR (a.created_at,a.log_id)<(after_time,after_log))
    ORDER BY a.created_at DESC,a.log_id DESC
    LIMIT least(greatest(coalesce(page_limit,1),1),100)+1
)
SELECT jsonb_build_object('code',(SELECT code FROM gate),'rows',CASE resource
    WHEN 'accounts' THEN coalesce((SELECT jsonb_agg(row_data ORDER BY sort_time DESC,sort_user DESC) FROM account_page),'[]'::jsonb)
    WHEN 'audit' THEN coalesce((SELECT jsonb_agg(row_data ORDER BY sort_time DESC,sort_id DESC) FROM audit_page),'[]'::jsonb)
    ELSE '[]'::jsonb END);
$$;

REVOKE ALL ON FUNCTION public.graphiscan_read_admin(uuid,uuid,text,text,text,text,timestamptz,uuid,bigint,integer)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_password_writer,graphiscan_admin_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_read_admin(uuid,uuid,text,text,text,text,timestamptz,uuid,bigint,integer)
    TO graphiscan_api_reader;

REVOKE ALL ON FUNCTION public.graphiscan_update_account(uuid,uuid,uuid,jsonb,uuid)
    FROM PUBLIC,anon,authenticated,service_role,graphiscan_api_reader,graphiscan_password_writer;
GRANT EXECUTE ON FUNCTION public.graphiscan_update_account(uuid,uuid,uuid,jsonb,uuid)
    TO graphiscan_admin_writer;
ALTER ROLE graphiscan_admin_writer SET statement_timeout='5s';
ALTER ROLE graphiscan_admin_writer SET lock_timeout='3s';

COMMIT;
