// Called only in the contract checker's disposable fictional PGlite database.
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
module.exports = async ({db, root, U}) => {
  let checks = 0;
  const check = (value, message) => {assert(value, message); checks++;};
  const query = (sql, params=[]) => db.query(sql, params);
  const denied = async sql => {
    await db.exec('BEGIN');
    let code;
    try {await db.exec(sql);} catch (error) {code=error.code;}
    await db.exec('ROLLBACK');
    check(code==='42501', 'Unauthorized SQL was accepted: '+sql);
  };
  await db.exec(fs.readFileSync(path.join(root,'graphiscan/db/postgres/006_password_change.sql'),'utf8'));
  for (const role of ['anon','authenticated','service_role','graphiscan_api_reader']) {
    const row = (await query(`SELECT has_function_privilege($1,'public.graphiscan_begin_password(uuid,uuid,uuid,uuid)','EXECUTE') AS begin,
      has_function_privilege($1,'public.graphiscan_complete_password(uuid,uuid,uuid)','EXECUTE') AS finish`,[role])).rows[0];
    check(!row.begin && !row.finish, role+' can execute password mutation functions');
  }
  const flags=(await query("SELECT rolcanlogin,rolsuper,rolbypassrls,rolcreaterole FROM pg_roles WHERE rolname='graphiscan_password_writer'")).rows[0];
  check(Object.values(flags).every(v=>v===false), 'Writer was created with excessive privileges');
  const user=U(7), session=U(701), operation=U(702), request=U(703), during=U(704);
  await query('INSERT INTO auth.sessions(id,user_id) VALUES ($1,$2)',[session,user]);
  const begin = async (subject=user, sid=session, op=operation) => (await query(
    'SELECT graphiscan_begin_password($1,$2,$3,$4) AS ok',[subject,sid,op,request])).rows[0].ok;
  const finish = async (subject=user, op=operation) => (await query(
    'SELECT graphiscan_complete_password($1,$2,$3) AS ok',[subject,op,request])).rows[0].ok;
  await db.exec('SET ROLE graphiscan_password_writer');
  check(await begin(user,U(799))===false, 'Missing session can start password change');
  check(await begin(U(1),session)===false, 'Other subject session can start password change');
  for (const sql of ["SELECT * FROM public.user_profiles", "SELECT * FROM auth.sessions",
    "UPDATE public.user_profiles SET must_change_password=false",
    "SELECT * FROM public.password_change_operations", "DELETE FROM public.app_session_revocations"]) await denied(sql);
  check(await begin()===true, 'Restricted function-only writer cannot begin');
  check(await begin(user,session,U(705))===false, 'Duplicate pending attempt accepted');
  check(await finish(U(1))===false, 'Wrong subject completed an operation');
  check(await finish(user,U(799))===false, 'Unknown operation completed');
  await db.exec('RESET ROLE');
  let profile=(await query('SELECT * FROM user_profiles WHERE user_id=$1',[user])).rows[0];
  check(profile.credential_update_pending && profile.must_change_password, 'Begin cleared onboarding prematurely');
  check((await query('SELECT count(*)::int AS n FROM app_session_revocations WHERE session_id=$1',[session])).rows[0].n===1,
    'Begin did not durably revoke original session');
  await query('INSERT INTO auth.sessions(id,user_id) VALUES ($1,$2)',[during,user]);
  const snapshotSql=fs.readFileSync(path.join(root,'graphiscan/db/postgres/access_snapshot.sql'),'utf8')
    .replaceAll('%(user_id)s','$1').replaceAll('%(session_id)s','$2');
  check(!(await query(snapshotSql,[user,during])).rows[0].session_valid, 'Pending admits fresh sign-in');
  // A racing profile/security edit must prevent stale completion.
  await db.exec('BEGIN');
  await query('UPDATE user_profiles SET security_version=security_version+1 WHERE user_id=$1',[user]);
  check(await finish()===false, 'Concurrent security change overwritten by finish');
  await db.exec('ROLLBACK');
  await db.exec('SET ROLE graphiscan_password_writer');
  check(await finish()===true, 'Confirmed operation cannot finish');
  check(await finish()===false, 'Completed operation replay accepted');
  await db.exec('RESET ROLE');
  profile=(await query('SELECT * FROM user_profiles WHERE user_id=$1',[user])).rows[0];
  check(!profile.credential_update_pending && !profile.must_change_password && !!profile.password_changed_at,
    'Completion did not clear gate/set timestamp');
  check(!(await query(snapshotSql,[user,session])).rows[0].session_valid, 'Original session resurrected');
  check(!(await query(snapshotSql,[user,during])).rows[0].session_valid, 'Session created while pending resurrected');
  await query('INSERT INTO auth.sessions(id,user_id) VALUES ($1,$2)',[U(706),user]);
  check((await query(snapshotSql,[user,U(706)])).rows[0].session_valid, 'Fresh sign-in locked out');
  const audit=(await query("SELECT count(*)::int AS n FROM audit_logs WHERE actor_id=$1 AND action IN ('password_change.started','password_change.completed')",[user])).rows[0].n;
  check(audit===2, 'Transactional password audits missing/duplicated');
  check((await query("SELECT relrowsecurity FROM pg_class WHERE oid='public.password_change_operations'::regclass")).rows[0].relrowsecurity,
    'Operation table lacks RLS');
  // Execute the exact new writer inspector SQL in the same fictional database.
  const inspector = fs.readFileSync(path.join(root,'graphiscan/tools/check_v1_password_writer.py'),'utf8');
  const inspectorSql = name => {
    const match = inspector.match(new RegExp(name + ' = """([\\s\\S]*?)"""'));
    assert(match, 'Missing writer inspector SQL '+name);
    return match[1];
  };
  await db.exec("BEGIN; SET LOCAL ROLE graphiscan_password_writer; SET LOCAL TIME ZONE 'UTC'; SET LOCAL statement_timeout='5s'; SET LOCAL lock_timeout='3s'; SET TRANSACTION READ ONLY;");
  for (const name of ['WRITER_CONNECTION_SQL','WRITER_TABLES_SQL']) {
    const row = (await query(inspectorSql(name))).rows[0];
    check(!!row && Object.values(row).every(v=>v===true), 'Writer inspector rejected restricted role: '+name);
  }
  for (const signature of ['public.graphiscan_begin_password(uuid,uuid,uuid,uuid)',
    'public.graphiscan_complete_password(uuid,uuid,uuid)']) {
    const row=(await query(inspectorSql('WRITER_FUNCTION_SQL').replace('%s','$1'),[signature])).rows[0];
    check(!!row && Object.values(row).every(v=>v===true), 'Writer inspector rejected function boundary: '+signature);
  }
  await db.exec('ROLLBACK');
  console.log(`Isolated password transaction/grant checks: PASS (${checks} checks; no provider/hosted writes).`);
};
