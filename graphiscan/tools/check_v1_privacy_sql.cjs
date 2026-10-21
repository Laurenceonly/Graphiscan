// Actual SQL against only the contract checker's fictional in-memory database.
const fs=require('fs'), path=require('path'), assert=require('assert/strict');
module.exports=async ({db,root,U})=>{
  let checks=0;
  const check=(ok,message)=>{assert(ok,message);checks++;};
  const query=(sql,params=[])=>db.query(sql,params);
  await db.exec(fs.readFileSync(path.join(root,'graphiscan/db/postgres/007_privacy_acceptance.sql'),'utf8'));
  const seed=fs.readFileSync(path.join(root,'graphiscan/db/postgres/seed_test_agreement.sql'),'utf8');
  const notice=fs.readFileSync(path.join(root,'graphiscan/api/test-notice-v1.txt'),'utf8').replace(/\r\n/g,'\n');
  check(seed.split('$notice$')[1]===notice,'Seed/canonical test notice text drift');
  const user=U(7),session=U(706),request=U(801),version='graphiscan-test-v1';
  const accept=async (subject=user,sid=session,v=version)=>(await query(
    'SELECT * FROM graphiscan_accept_privacy($1,$2,$3,$4)',[subject,sid,v,request])).rows[0];
  const snapshot=fs.readFileSync(path.join(root,'graphiscan/db/postgres/access_snapshot.sql'),'utf8')
    .replaceAll('%(user_id)s','$1').replaceAll('%(session_id)s','$2');
  const rejectSeed=async()=>{
    let code;try{await db.exec(seed);}catch(error){code=error.code;}
    await db.exec('ROLLBACK');return !!code;
  };
  check(await rejectSeed(),'Seed replaced existing current notice');
  await query('UPDATE privacy_agreements SET is_current=false');
  await query("UPDATE user_profiles SET full_name='Synthetic Test Admin' WHERE user_id=$1",[user]);
  await db.exec(seed);
  const row=(await query('SELECT * FROM privacy_agreements WHERE version=$1',[version])).rows[0];
  check(row.test_subject_id===user && row.content===notice,'Seed not scoped to canonical fixture');
  check((await query('SELECT count(*)::int AS n FROM privacy_agreement_acceptances WHERE user_id=$1',[user])).rows[0].n===0,
    'Publication silently accepted notice');
  check(await rejectSeed(),'Seed overwrote published version');
  for(const role of ['anon','authenticated','service_role','graphiscan_api_reader']){
    check(!(await query("SELECT has_function_privilege($1,'public.graphiscan_accept_privacy(uuid,uuid,text,uuid)','EXECUTE') AS allowed",[role])).rows[0].allowed,
      role+' can execute acceptance function');
  }
  await db.exec('SET ROLE graphiscan_password_writer');
  check((await accept(user,U(999))).outcome==='invalid_session','Missing session accepted');
  check((await accept(U(1),session)).outcome==='invalid_session','Cross-subject session accepted');
  check((await accept(user,session,'stale-v0')).outcome==='agreement_changed','Stale version accepted');
  const first=await accept();
  const repeated=await accept();
  check(first.outcome==='accepted' && repeated.outcome==='accepted' && first.accepted_at.getTime()===repeated.accepted_at.getTime(),
    'Repeated acceptance changed timestamp or failed');
  await db.exec('RESET ROLE');
  await db.exec('BEGIN');
  await query("UPDATE auth.sessions SET not_after=clock_timestamp()-interval '1 second' WHERE id=$1",[session]);
  check((await accept()).outcome==='invalid_session','Expired provider session accepted notice');
  await db.exec('ROLLBACK');
  await db.exec('BEGIN');
  await query("INSERT INTO app_session_revocations(session_id,user_id,reason) VALUES ($1,$2,'logout')",[session,user]);
  check((await accept()).outcome==='invalid_session','Durably revoked session accepted notice');
  await db.exec('ROLLBACK');
  check((await query("SELECT count(*)::int AS n FROM audit_logs WHERE actor_id=$1 AND action='privacy.accepted'",[user])).rows[0].n===1,
    'Acceptance audit missing or duplicated');
  check((await query(snapshot,[user,session])).rows[0].required_agreement_version===version,'Fixture notice absent from bootstrap');
  check((await query(snapshot,[user,session])).rows[0].accepted_agreement_version===version,'Acceptance not projected');
  // Other active issued identities cannot use the temporary notice.
  await query('INSERT INTO auth.sessions(id,user_id) VALUES ($1,$2)',[U(802),U(1)]);
  check((await query(snapshot,[U(1),U(802)])).rows[0].required_agreement_version===null,'Test notice exposed to another account');
  // Satisfy password gate for this test without persisting the mutation.
  await db.exec('BEGIN');
  await query('UPDATE user_profiles SET must_change_password=false WHERE user_id=$1',[U(1)]);
  await query('INSERT INTO auth.sessions(id,user_id) VALUES ($1,$2)',[U(803),U(1)]);
  check((await accept(U(1),U(803))).outcome==='agreement_unavailable','Other account accepted scoped notice');
  await db.exec('ROLLBACK');
  for(const [update,expected] of [
    ["must_change_password=true",'password_required'],["account_status='disabled'",'account_unavailable'],
    ["credential_update_pending=true",'invalid_session']]){
    await db.exec('BEGIN');
    await query('UPDATE user_profiles SET '+update+' WHERE user_id=$1',[user]);
    await query('INSERT INTO auth.sessions(id,user_id) VALUES ($1,$2)',[U(804),user]);
    check((await accept(user,U(804))).outcome===expected,'Fresh state not enforced: '+expected);
    await db.exec('ROLLBACK');
  }
  await db.exec('BEGIN');
  await query('UPDATE privacy_agreements SET is_current=false');
  check((await accept()).outcome==='agreement_unavailable','Missing notice did not fail closed');
  // New immutable version makes prior acceptance insufficient.
  await query(`INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current,test_subject_id)
    SELECT 'graphiscan-test-v2',title,content,content_sha256,approved_by,clock_timestamp(),clock_timestamp(),true,test_subject_id
    FROM privacy_agreements WHERE version=$1`,[version]);
  check((await accept()).outcome==='agreement_changed','Superseded version accepted');
  const changed=(await query(snapshot,[user,session])).rows[0];
  check(changed.required_agreement_version==='graphiscan-test-v2' && changed.accepted_agreement_version===version,'New version inherited old consent');
  await db.exec(`CREATE FUNCTION public.fixture_reject_privacy_audit() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'Fictional audit failure'; END; $$;
    CREATE TRIGGER fixture_reject_privacy_audit BEFORE INSERT ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION public.fixture_reject_privacy_audit();`);
  let auditError;
  try{await accept(user,session,'graphiscan-test-v2');}catch(error){auditError=error.code;}
  await db.exec('ROLLBACK');
  check(auditError==='P0001' && (await query("SELECT count(*)::int AS n FROM privacy_agreement_acceptances WHERE agreement_version='graphiscan-test-v2'")).rows[0].n===0,
    'Failed audit left a partial acceptance');
  // Server reader executes the exact projection SQL without exposing seed metadata.
  const source=fs.readFileSync(path.join(root,'graphiscan/v1_privacy.py'),'utf8');
  const sql=source.match(/AGREEMENT_SQL = """([\s\S]*?)"""/)[1].replace('%s','$1');
  await db.exec('SET ROLE graphiscan_api_reader');
  check((await query(sql,[user])).rows.length===1 && (await query(sql,[U(1)])).rows.length===0,'Reader notice scope failed');
  await db.exec('RESET ROLE');
  console.log(`Isolated privacy notice/acceptance checks: PASS (${checks} checks; fictional Auth only).`);
};
