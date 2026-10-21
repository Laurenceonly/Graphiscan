// Executed by check_api_contract.cjs, exclusively inside its fictional PGlite DB.
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const {createHash} = require('crypto');

module.exports = async function ({db, root, U}) {
  let checks = 0, nextSession = 100;
  const check = (ok, message) => { assert(ok, message); checks++; };
  const query = (sql, params=[]) => db.query(sql, params);
  await db.exec('ALTER TABLE auth.sessions ENABLE ROW LEVEL SECURITY');
  const sql = fs.readFileSync(path.join(root, 'graphiscan/db/postgres/access_snapshot.sql'), 'utf8')
    .replaceAll('%(user_id)s', '$1').replaceAll('%(session_id)s', '$2');
  const snapshot = async (user, session) => (await query(sql, [user, session])).rows[0];
  // Only the Auth fields actually queried are stubbed by the caller.
  const sessionFor = async user => {
    const session = U(nextSession++);
    await query('INSERT INTO auth.sessions(id,user_id) VALUES ($1,$2)', [session,user]);
    return session;
  };
  await query('UPDATE user_profiles SET must_change_password=false WHERE user_id=$1', [U(2)]);
  const teacherSession = await sessionFor(U(2));
  let row = await snapshot(U(2), teacherSession);
  check(row.session_valid && row.user_id===U(2) && row.role==='teacher', 'Fresh session/profile not read');
  check(row.must_change_password===false, 'Password state not read from profile');
  check(!row.required_agreement_version, 'Agreement with incorrect content hash was trusted');
  check(row.accepted_agreement_version==='synthetic-v1', 'Historical acceptance lost');
  check(!((await snapshot(U(2), U(999))).session_valid), 'Missing provider session accepted');
  check(!((await snapshot(U(3), teacherSession)).session_valid), 'Other user session accepted');
  await query('INSERT INTO auth.users(id) VALUES ($1)', [U(6)]);
  const unissuedSession = await sessionFor(U(6));
  row = await snapshot(U(6), unissuedSession);
  check(row.session_valid && row.user_id===null, 'Unissued identity fabricated a profile');
  await query("UPDATE auth.sessions SET not_after=clock_timestamp()-interval '1 second' WHERE id=$1", [teacherSession]);
  check(!(await snapshot(U(2), teacherSession)).session_valid, 'Expired provider session accepted');
  await query('UPDATE auth.sessions SET not_after=NULL WHERE id=$1', [teacherSession]);
  await query("INSERT INTO app_session_revocations(session_id,user_id,reason) VALUES ($1,$2,'logout')", [teacherSession,U(2)]);
  check(!(await snapshot(U(2), teacherSession)).session_valid, 'Durably revoked session accepted');
  await query('DELETE FROM auth.sessions WHERE id=$1', [teacherSession]);
  check(!(await snapshot(U(2), teacherSession)).session_valid, 'Provider sign-out deletion accepted');

  let current = await sessionFor(U(2));
  await query('UPDATE privacy_agreements SET is_current=false');
  const content = 'Synthetic adapter agreement; not approved real privacy wording.';
  const digest = createHash('sha256').update(content).digest('hex');
  await query(`INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current)
    VALUES ('synthetic-adapter-v2','Synthetic',$1,$2,$3,now(),now(),true)`, [content,digest,U(1)]);
  row = await snapshot(U(2), current);
  check(row.required_agreement_version==='synthetic-adapter-v2', 'Approved hashed current agreement not loaded');
  check(row.accepted_agreement_version==='synthetic-v1', 'Old acceptance silently promoted');
  await query("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES ($1,'synthetic-adapter-v2')", [U(2)]);
  check((await snapshot(U(2), current)).accepted_agreement_version==='synthetic-adapter-v2', 'Current acceptance not selected');
  // A historical row with a later time must not hide an accepted current version.
  await query("UPDATE privacy_agreement_acceptances SET accepted_at=now()+interval '1 day' WHERE user_id=$1 AND agreement_version='synthetic-v1'", [U(2)]);
  check((await snapshot(U(2), current)).accepted_agreement_version==='synthetic-adapter-v2', 'Historical timestamp hid current acceptance');
  await query('BEGIN');
  await query('UPDATE privacy_agreements SET is_current=false');
  await query(`INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current)
    VALUES ('synthetic-future','Synthetic',$1,$2,$3,now(),now()+interval '1 day',true)`, [content,digest,U(1)]);
  check((await snapshot(U(2), current)).required_agreement_version===null, 'Future publication trusted');
  await query('ROLLBACK');

  await query('UPDATE user_profiles SET credential_update_pending=true WHERE user_id=$1', [U(2)]);
  check(!(await snapshot(U(2), current)).session_valid, 'Pending credential change accepted old session');
  current = await sessionFor(U(2));
  check(!(await snapshot(U(2), current)).session_valid, 'Pending credential change accepted new session');
  await query('UPDATE user_profiles SET credential_update_pending=false,password_changed_at=clock_timestamp() WHERE user_id=$1', [U(2)]);
  check(!(await snapshot(U(2), current)).session_valid, 'Completed credential change resurrected session');
  current = await sessionFor(U(2));
  check((await snapshot(U(2), current)).session_valid, 'Fresh reauthentication after credential change denied');
  await query('UPDATE user_profiles SET security_version=security_version+1 WHERE user_id=$1', [U(2)]);
  check(!(await snapshot(U(2), current)).session_valid, 'Security version did not invalidate existing sessions');
  await query('UPDATE auth.sessions SET created_at=(SELECT sessions_valid_after FROM user_profiles WHERE user_id=$2) WHERE id=$1', [current,U(2)]);
  check(!(await snapshot(U(2), current)).session_valid, 'Revoked old session at exact cutoff was accepted');
  current = await sessionFor(U(2));
  await query('UPDATE auth.sessions SET created_at=(SELECT sessions_valid_after FROM user_profiles WHERE user_id=$2) WHERE id=$1', [current,U(2)]);
  check((await snapshot(U(2), current)).session_valid, 'Fresh same-tick reauthentication incorrectly denied');
  await query("UPDATE auth.sessions SET created_at=(SELECT sessions_valid_after-interval '1 microsecond' FROM user_profiles WHERE user_id=$2) WHERE id=$1", [current,U(2)]);
  check(!(await snapshot(U(2), current)).session_valid, 'Backdated unregistered session bypassed floor');
  await query("UPDATE user_profiles SET account_status='disabled' WHERE user_id=$1", [U(2)]);
  check(!(await snapshot(U(2), current)).session_valid, 'Account disable did not invalidate prior session');
  await query("UPDATE user_profiles SET account_status='active',sessions_valid_after='-infinity' WHERE user_id=$1", [U(2)]);
  check(!(await snapshot(U(2), current)).session_valid, 'Restoration or floor reduction resurrected old session');

  const adminSession = await sessionFor(U(1));
  row = await snapshot(U(1), adminSession);
  check(row.grants.some(g=>g.permission==='accounts.manage' && g.school_id===null), 'Global explicit grant not projected');
  await query('INSERT INTO school_memberships(user_id,school_id,created_by) SELECT $1,school_id,$1 FROM schools LIMIT 1', [U(1)]);
  check(!(await snapshot(U(1), adminSession)).session_valid, 'Membership change failed to invalidate prior session');
  const freshAdmin = await sessionFor(U(1));
  row = await snapshot(U(1), freshAdmin);
  check(row.school_ids.length===1 && typeof row.school_ids[0]==='string', 'Membership IDs not canonical strings');
  await query("DELETE FROM user_permission_grants WHERE user_id=$1 AND permission_key='accounts.manage'", [U(1)]);
  check(!(await snapshot(U(1), freshAdmin)).session_valid, 'Grant change failed to invalidate prior session');
  const finalAdmin = await sessionFor(U(1));
  check((await snapshot(U(1), finalAdmin)).grants.length===0, 'Removed grant survived new access read');

  // Use the exact 005 role/policies. Auth RLS stays enabled; the reader has no
  // direct Auth SELECT or BYPASSRLS and calls only the narrow definer function.
  await db.exec("BEGIN; SET LOCAL ROLE graphiscan_api_reader; SET LOCAL TIME ZONE 'UTC';");
  check((await snapshot(U(1), finalAdmin)).session_valid, 'Server SELECT grants insufficient for snapshot');
  check(!(await snapshot(U(2), finalAdmin)).session_valid, 'Session function failed subject binding');
  check((await query("SELECT NOT rolsuper AND NOT rolbypassrls AND NOT rolcanlogin AND NOT rolcreaterole AND NOT rolcreatedb AS restricted FROM pg_roles WHERE rolname=current_user")).rows[0].restricted,
    'Setup role should start NOLOGIN without administrative flags');
  check((await query("SELECT NOT has_table_privilege(current_user,'auth.sessions','SELECT') AS restricted")).rows[0].restricted,
    'Reader unexpectedly has direct Auth table SELECT');
  const denied = async statement => {
    await query('SAVEPOINT access_denial'); let code;
    try { await query(statement); } catch(error) { code=error.code; }
    await query('ROLLBACK TO SAVEPOINT access_denial');
    check(code==='42501', 'Reader unexpectedly allowed operation: '+statement);
  };
  await denied('SELECT * FROM auth.sessions');
  await denied('SELECT * FROM public.students');
  await denied("UPDATE public.user_profiles SET full_name='tamper'");
  await db.exec('ROLLBACK');
  await db.exec('BEGIN; SET LOCAL ROLE anon;');
  let anonCode;
  try { await query('SELECT * FROM public.graphiscan_session_state($1,$2)',[U(1),finalAdmin]); } catch(error) { anonCode=error.code; }
  await db.exec('ROLLBACK');
  check(anonCode==='42501', 'Client anon role can execute server session function');
  // Future profile writers must also revoke real session IDs while Auth RLS is
  // enabled, without acquiring direct Auth SELECT or RLS bypass themselves.
  await db.exec(`CREATE ROLE fixture_profile_writer NOINHERIT NOBYPASSRLS;
    GRANT USAGE ON SCHEMA public,auth TO fixture_profile_writer;
    GRANT SELECT,UPDATE ON public.user_profiles TO fixture_profile_writer;
    CREATE POLICY fixture_writer_select ON public.user_profiles FOR SELECT TO fixture_profile_writer USING (true);
    CREATE POLICY fixture_writer_update ON public.user_profiles FOR UPDATE TO fixture_profile_writer USING (true) WITH CHECK (true);`);
  await db.exec('BEGIN; SET LOCAL ROLE fixture_profile_writer;');
  check((await query("SELECT NOT has_table_privilege(current_user,'auth.sessions','SELECT') AS restricted")).rows[0].restricted,
    'Test writer should lack direct Auth SELECT');
  await query('UPDATE public.user_profiles SET security_version=security_version+1 WHERE user_id=$1',[U(1)]);
  await db.exec('RESET ROLE');
  check(!(await snapshot(U(1),finalAdmin)).session_valid, 'Definer trigger failed to revoke Auth session for restricted writer');
  await db.exec('ROLLBACK');
  console.log(`Isolated v1 access snapshot/security checks: PASS (${checks} checks; fictional Auth sessions only).`);

  // Exercise the hosted runner's exact catalog SQL against PostgreSQL, not just
  // driver mocks. Extract plain triple-quoted constants; no Python is executed.
  const preflightSource = fs.readFileSync(path.join(root, 'graphiscan/tools/check_v1_hosted.py'), 'utf8');
  const preflightSql = name => {
    const match = preflightSource.match(new RegExp(name + ' = """([\\s\\S]*?)"""'));
    assert(match, `Missing preflight SQL constant ${name}`);
    return match[1];
  };
  let preflightChecks = 0;
  const preflightCheck = (ok, message) => {assert(ok, message); preflightChecks++;};
  // Hosted reader has no Auth schema usage; metadata checks must inspect table
  // privileges by catalog OID instead of resolving a protected schema name.
  await db.exec('REVOKE USAGE ON SCHEMA auth FROM graphiscan_api_reader');
  await db.exec("BEGIN; SET LOCAL ROLE graphiscan_api_reader; SET LOCAL TIME ZONE 'UTC'; SET LOCAL statement_timeout='5s'; SET TRANSACTION READ ONLY;");
  preflightCheck((await query("SELECT NOT has_schema_privilege(current_user,oid,'USAGE') AS restricted FROM pg_namespace WHERE nspname='auth'")).rows[0].restricted,
    'Preflight regression fixture must lack Auth schema usage');
  const connectionInfo = (await query(preflightSql('CONNECTION_SQL'))).rows[0];
  preflightCheck(Object.values(connectionInfo).every(v=>v===true), 'Preflight connection settings rejected dedicated read-only role');
  for (const table of ['public.user_profiles', 'public.app_session_revocations',
    'public.privacy_agreements', 'public.privacy_agreement_acceptances', 'public.user_permission_grants', 'public.school_memberships']) {
    const access = (await query(preflightSql('TABLE_ACCESS_SQL').replace('%s','$1'), [table])).rows[0];
    preflightCheck(access.schema_usage && access.can_select && !access.can_write && !access.owns_table &&
      access.rls, `Preflight grants failed for ${table}`);
  }
  preflightCheck((await query(preflightSql('TRIGGER_SQL'))).rows[0].installed===true, 'Preflight failed to recognize real session trigger');
  const functionAccess = (await query(preflightSql('SESSION_FUNCTION_SQL'))).rows[0];
  preflightCheck(functionAccess.installed && functionAccess.auth_table_restricted, 'Preflight did not validate restricted session function');
  const zero = U(0).replace('4000-8000', '0000-0000');
  const absent = await snapshot(zero,zero);
  preflightCheck(absent.session_valid===false && absent.user_id===null, 'Preflight zero identity query allowed access');
  await db.exec('ROLLBACK');
  const schemaStatus = (await query(fs.readFileSync(path.join(root, 'graphiscan/db/postgres/verify_schema.sql'), 'utf8'))).rows[0];
  preflightCheck(Number(schemaStatus.graphiscan_tables)===20 && Number(schemaStatus.tables_with_rls)===20 &&
    schemaStatus.session_trigger_ready===true, 'User-assisted schema verification query failed');
  console.log(`Isolated hosted-preflight catalog checks: PASS (${preflightChecks} checks; no hosted project contacted).`);

  // Validate the optional manual test-profile seed; no hosted mutation occurs.
  let fixtureChecks = 0;
  const fixtureCheck = (ok, message) => {assert(ok, message); fixtureChecks++;};
  const seedSql = fs.readFileSync(path.join(root,'graphiscan/db/postgres/seed_test_profile.sql'),'utf8');
  await db.exec('ALTER TABLE auth.users ADD COLUMN email text');
  const seedDenied = async () => {
    let code;
    try { await db.exec(seedSql); } catch(error) { code=error.code; }
    await db.exec('ROLLBACK');
    return code==='P0001';
  };
  fixtureCheck(await seedDenied(), 'Seed accepted a missing fictional Auth account');
  await query("INSERT INTO auth.users(id,email) VALUES ($1,'graphiscan.test@example.invalid')",[U(7)]);
  await db.exec(seedSql);
  const profile=(await query('SELECT role,account_status,must_change_password,created_by FROM public.user_profiles WHERE user_id=$1',[U(7)])).rows[0];
  fixtureCheck(profile.role==='admin' && profile.account_status==='active' && profile.created_by===null, 'Seed profile identity/role mismatch');
  fixtureCheck(profile.must_change_password===true, 'Seed bypassed forced-password onboarding');
  const untouched=(await query(`SELECT
    (SELECT count(*) FROM public.user_permission_grants WHERE user_id=$1)::int AS grants,
    (SELECT count(*) FROM public.privacy_agreement_acceptances WHERE user_id=$1)::int AS acceptances,
    (SELECT count(*) FROM public.audit_logs WHERE actor_id=$1 AND action='test_fixture.profile_created')::int AS audits`,[U(7)])).rows[0];
  fixtureCheck(untouched.grants===0 && untouched.acceptances===0, 'Seed added grants or consent');
  fixtureCheck(untouched.audits===1, 'Seed profile/audit transaction missing');
  await query("UPDATE public.user_profiles SET full_name='Synthetic preserve fixture' WHERE user_id=$1",[U(7)]);
  fixtureCheck(await seedDenied(), 'Seed overwrote an existing profile');
  fixtureCheck((await query('SELECT full_name FROM public.user_profiles WHERE user_id=$1',[U(7)])).rows[0].full_name==='Synthetic preserve fixture', 'Rerun mutated existing profile');
  console.log(`Isolated fictional-profile seed checks: PASS (${fixtureChecks} checks; no hosted writes performed).`);
};
