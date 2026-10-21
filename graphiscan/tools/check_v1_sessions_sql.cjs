const fs=require('fs'),path=require('path'),assert=require('assert/strict');
module.exports=async({db,root,U})=>{
  let checks=0;const check=(ok,message)=>{assert(ok,message);checks++;};
  const q=(sql,params=[])=>db.query(sql,params);
  await db.exec(fs.readFileSync(path.join(root,'graphiscan/db/postgres/008_session_logout.sql'),'utf8'));
  const user=U(7),session=U(901),other=U(902),request=U(903);
  await q('INSERT INTO auth.sessions(id,user_id) VALUES ($1,$3),($2,$3)',[session,other,user]);
  const revoke=async(subject=user,sid=session)=>(await q('SELECT graphiscan_revoke_session($1,$2,$3) AS ok',[subject,sid,request])).rows[0].ok;
  for(const role of ['anon','authenticated','service_role','graphiscan_api_reader'])
    check(!(await q("SELECT has_function_privilege($1,'public.graphiscan_revoke_session(uuid,uuid,uuid)','EXECUTE') AS allowed",[role])).rows[0].allowed,role+' can revoke sessions');
  await db.exec('SET ROLE graphiscan_password_writer');
  check(await revoke(U(1),session)===false,'Wrong subject revoked session');
  check(await revoke(user,U(999))===false,'Missing session fabricated revocation');
  check(await revoke()===true && await revoke()===true,'Valid repeated logout failed');
  await db.exec('RESET ROLE');
  check((await q("SELECT count(*)::int AS n FROM audit_logs WHERE actor_id=$1 AND action='session.logout'",[user])).rows[0].n===1,'Logout audit duplicated/missing');
  const snapshot=fs.readFileSync(path.join(root,'graphiscan/db/postgres/access_snapshot.sql'),'utf8').replaceAll('%(user_id)s','$1').replaceAll('%(session_id)s','$2');
  check(!(await q(snapshot,[user,session])).rows[0].session_valid,'Logout did not deny token');
  check((await q(snapshot,[user,other])).rows[0].session_valid,'Local logout revoked another session');
  await q('DELETE FROM auth.sessions WHERE id=$1',[session]);
  check(await revoke()===true,'Provider deletion broke idempotent revocation');
  for(const update of ["account_status='disabled'",'must_change_password=true','credential_update_pending=true']){
    await db.exec('BEGIN');await q('UPDATE user_profiles SET '+update+' WHERE user_id=$1',[user]);
    await q('INSERT INTO auth.sessions(id,user_id) VALUES ($1,$2)',[U(904),user]);
    check(await revoke(user,U(904))===true,'Onboarding/disabled state blocked logout');
    await db.exec('ROLLBACK');
  }
  console.log(`Isolated local-session revocation checks: PASS (${checks} checks; fictional Auth only).`);
};
