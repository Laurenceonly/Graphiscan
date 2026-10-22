// Used inside the existing isolated admin transaction; no provider connection.
const assert=require('assert/strict');
module.exports=async({db,U,A,R,T,B,school,sessions,fresh,revision,reader,writer,validateRow})=>{
  let checks=0;const check=(ok,message)=>{assert(ok,message);checks++;};
  const q=(sql,args=[])=>db.query(sql,args),P=U(47001),E=U(47002);
  for(const [id,role]of [[P,'parent'],[E,'expert']]){
    await q('INSERT INTO auth.users(id) VALUES($1)',[id]);
    await q('INSERT INTO user_profiles(user_id,full_name,role,created_by,must_change_password) VALUES($1,$2,$3,$4,false)',[id,'Fictional '+role,role,A]);
  }
  const get=(operator,candidate,actor=operator,s=school,session=sessions[operator])=>reader('SELECT graphiscan_get_assignment_access($1,$2,$3,$4,$5) result',[operator,session,candidate,actor,s]);
  const set=async(operator,candidate,actor,enabled,s=school,rev)=>writer('SELECT graphiscan_set_assignment_access($1,$2,$3,$4,$5,$6,$7,$8) result',
    [operator,sessions[operator],candidate,actor,s,rev??await revision(candidate),enabled,U(47999)]);
  const options=async(actor)=>(await reader('SELECT graphiscan_assignment_options($1,$2,$3,NULL,NULL,100) result',[actor,sessions[actor],school])).rows.map(row=>row.data.user_id);
  let current=(await get(A,T)).data;
  check(validateRow('AssignmentAccess',current).ok,'SQL eligibility projection violates OpenAPI');
  check(current.can_grant&&!current.eligible&&!current.effective,'Initial eligible state incorrect');
  check((await get(R,T)).code==='FORBIDDEN','Account management implied school assignment authority');
  check((await get(T,P)).code==='FORBIDDEN','Teacher provisioned own eligible parents');
  check((await get(A,T,A,school,U(47998))).code==='AUTHENTICATION_REQUIRED','Missing session read eligibility');
  const other=String((await q("INSERT INTO schools(name) VALUES('Other fictional access school') RETURNING school_id")).rows[0].school_id);
  check((await set(A,T,A,true,other)).code==='FORBIDDEN','Operator school scope escaped');
  const before=await revision(T);
  current=(await set(A,T,A,true)).data;
  check(current.eligible&&current.effective&&current.revision>before,'Teacher eligibility not granted/revisioned');
  check((await options(A)).includes(T),'Granted teacher unavailable to assignment choices');
  check((await set(A,T,A,false,school,before)).code==='REVISION_CONFLICT','Stale eligibility update overwrote access');
  const auditBefore=(await q("SELECT count(*)::int n FROM audit_logs WHERE action LIKE 'assignments.eligibility.%'")).rows[0].n;
  const noChange=await set(A,T,A,true);
  check(noChange.data.revision===current.revision,'No-op eligibility save changed revision');
  check((await q("SELECT count(*)::int n FROM audit_logs WHERE action LIKE 'assignments.eligibility.%'")).rows[0].n===auditBefore,'No-op eligibility save duplicated audit');
  const student=(await q("INSERT INTO students(full_name,school_id,grade_level,teacher_id) VALUES('Fictional access child',$1,1,$2) RETURNING student_id",[school,T])).rows[0].student_id;
  check((await set(A,T,A,false)).data.eligible===false,'Teacher eligibility not revoked');
  check(!(await options(A)).includes(T),'Revoked teacher remained in choices');
  check((await q('SELECT teacher_id FROM students WHERE student_id=$1',[student])).rows[0].teacher_id===T,'Eligibility revocation rewrote existing student assignment');
  check((await set(A,E,A,true)).code==='INVALID_ASSIGNMENT','Expert without membership became eligible');
  await q('INSERT INTO school_memberships(user_id,school_id,created_by) VALUES($1,$2,$3)',[E,school,A]);
  check((await set(A,E,A,true)).data.effective===true,'Expert with membership not eligible');
  check((await set(A,P,T,true)).data.effective===true,'Explicit teacher-parent eligibility unavailable');
  check((await options(T)).includes(P),'Teacher could not choose explicitly allowed parent');
  check((await set(A,E,T,true)).code==='INVALID_ASSIGNMENT','Teacher received expert assignment capability');
  check((await set(A,T,T,true)).code==='INVALID_ASSIGNMENT','Teacher received arbitrary teacher-selection capability');
  check((await set(A,P,R,true)).code==='INVALID_ASSIGNMENT','Researcher actor without school authority received candidate');
  await q("INSERT INTO user_permission_grants(user_id,permission_key,school_id,granted_by) VALUES($1,'assignments.manage',$2,$3)",[R,school,A]);await fresh(R);
  check((await set(R,P,R,true)).data.effective===true,'Scoped researcher could not manage own candidates');
  check((await set(R,P,A,true)).code==='FORBIDDEN','Researcher changed protected actor eligibility');
  await q('DELETE FROM school_memberships WHERE user_id=$1 AND school_id=$2',[T,school]);
  current=(await get(A,P,T)).data;
  check(current.eligible&&!current.effective&&!current.can_grant,'Removed actor membership left effective eligibility');
  check((await set(A,P,T,false)).data.eligible===false,'Invalid historical eligibility could not be revoked');
  await q("UPDATE user_profiles SET account_status='disabled' WHERE user_id=$1",[E]);
  check((await set(A,E,A,true)).code==='INVALID_ASSIGNMENT','Disabled candidate granted eligibility');
  check((await set(A,E,A,false)).data.eligible===false,'Disabled candidate eligibility could not be revoked');
  await q('UPDATE user_profiles SET credential_update_pending=true WHERE user_id=$1',[P]);
  check((await set(A,P,R,false)).code==='ACCOUNT_OPERATION_PENDING','Eligibility write interfered with locked credential operation');
  await q('UPDATE user_profiles SET credential_update_pending=false WHERE user_id=$1',[P]);
  // Role changes may leave older rows; the operation must remove all obsolete roles.
  await q("INSERT INTO assignment_eligibilities(actor_id,candidate_id,school_id,assignment_role,granted_by) VALUES($1,$2,$3,'expert',$1)",[A,P,school]);
  check((await set(A,P,A,true)).data.effective===true,'Current role grant failed to replace stale role');
  check((await q('SELECT assignment_role FROM assignment_eligibilities WHERE actor_id=$1 AND candidate_id=$2 AND school_id=$3',[A,P,school])).rows.every(row=>row.assignment_role==='parent'),'Obsolete role eligibility retained');
  await set(A,P,A,false);
  const rollbackRevision=await revision(P);
  await db.exec(`CREATE FUNCTION pg_temp.reject_eligibility_audit() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'fictional audit failure'; END; $$;
    CREATE TRIGGER reject_eligibility_audit BEFORE INSERT ON audit_logs FOR EACH ROW
    WHEN (NEW.action LIKE 'assignments.eligibility.%') EXECUTE FUNCTION pg_temp.reject_eligibility_audit(); SAVEPOINT audit_failure;`);
  await assert.rejects(set(A,P,A,true));checks++;
  await db.exec('ROLLBACK TO SAVEPOINT audit_failure; RELEASE SAVEPOINT audit_failure; RESET ROLE; DROP TRIGGER reject_eligibility_audit ON audit_logs;');
  check((await get(A,P,A)).data.eligible===false&&await revision(P)===rollbackRevision,'Audit failure did not roll back eligibility/revision');
  check((await q('SELECT count(*)::int n FROM school_memberships WHERE user_id=$1',[P])).rows[0].n===0,'Parent eligibility created membership');
  check((await q('SELECT count(*)::int n FROM user_permission_grants WHERE user_id=$1',[P])).rows[0].n===0,'Eligibility created permission grant');
  check((await get(A,U(47997))).code==='NOT_FOUND','Unknown candidate exposed fabricated state');
  console.log(`Isolated assignment access SQL: PASS (${checks} checks; fictional identities only).`);
};
