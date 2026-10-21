const fs=require('fs'),path=require('path'),assert=require('assert/strict');
module.exports=async({db,root,U})=>{
  let checks=0;const check=(ok,message)=>{assert(ok,message);checks++;};
  const q=(sql,params=[])=>db.query(sql,params);
  await db.exec(fs.readFileSync(path.join(root,'graphiscan/db/postgres/011_assignment_options.sql'),'utf8'));
  const signature='public.graphiscan_assignment_options(uuid,uuid,bigint,timestamptz,uuid,integer)';
  for(const role of ['anon','authenticated','service_role','graphiscan_password_writer'])
    check(!(await q("SELECT has_function_privilege($1,$2,'EXECUTE') AS ok",[role,signature])).rows[0].ok,'Option directory exposed to '+role);
  check((await q("SELECT prosecdef AND provolatile='s' AND proconfig @> ARRAY['search_path=pg_catalog'] AS ok FROM pg_proc WHERE oid=$1::regprocedure",[signature])).rows[0].ok,'Option definer settings');
  await db.exec('BEGIN');
  const roles=['admin','teacher','parent','expert','other','disabled','researcher'];
  const users=Object.fromEntries(roles.map((role,i)=>[role,U(3100+i)]));
  for(const role of roles){
    await q('INSERT INTO auth.users(id) VALUES ($1)',[users[role]]);
    await q("INSERT INTO user_profiles(user_id,full_name,role,created_by,must_change_password,account_status) VALUES ($1,$2,$3,$4,false,$5)",
      [users[role],'Fictional '+role,role==='other'?'teacher':role==='disabled'?'parent':role,U(1),role==='disabled'?'disabled':'active']);
  }
  await q('UPDATE privacy_agreements SET is_current=false');
  await q("INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current) VALUES ('option-fictional','Fictional','Fictional',encode(sha256(convert_to('Fictional','UTF8')),'hex'),$1,now(),now(),true)",[users.admin]);
  for(const user of Object.values(users))await q("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES ($1,'option-fictional')",[user]);
  const school=String((await q("INSERT INTO schools(name) VALUES ('Options fictional') RETURNING school_id")).rows[0].school_id);
  const otherSchool=String((await q("INSERT INTO schools(name) VALUES ('Other options fictional') RETURNING school_id")).rows[0].school_id);
  for(const role of ['teacher','other','expert'])await q('INSERT INTO school_memberships(user_id,school_id,created_by) VALUES ($1,$2,$3)',[users[role],school,users.admin]);
  await q("INSERT INTO user_permission_grants(user_id,permission_key,school_id,granted_by) VALUES ($1,'assignments.manage',$2,$1)",[users.admin,school]);
  for(const actor of ['admin','teacher'])for(const role of ['teacher','other','parent','expert','disabled'])
    await q('INSERT INTO assignment_eligibilities(actor_id,candidate_id,school_id,assignment_role,granted_by) VALUES ($1,$2,$3,$4,$5)',
      [users[actor],users[role],school,['other'].includes(role)?'teacher':role==='disabled'?'parent':role,users.admin]);
  let index=3200;const sessions={};
  for(const role of roles){sessions[role]=U(index++);await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES ($1,$2,clock_timestamp())',[sessions[role],users[role]]);}
  const read=async(role,target=school,limit=25,time=null,user=null)=>(await q('SELECT public.graphiscan_assignment_options($1,$2,$3::bigint,$4::timestamptz,$5::uuid,$6::integer) AS result',
    [users[role],sessions[role],target,time,user,limit])).rows[0].result;
  await db.exec('SET LOCAL ROLE graphiscan_api_reader');
  const admin=await read('admin'),teacher=await read('teacher');
  check(admin.code===null&&admin.rows.length===4,'Administrative eligible people projection');
  check(teacher.rows.length===2&&teacher.rows.every(r=>r.data.user_id===users.teacher||r.data.user_id===users.parent),'Teacher enumerated other teachers/experts');
  check(admin.rows.every(r=>Object.keys(r.data).sort().join()==='full_name,role,user_id'),'Option exposed nonminimal profile');
  check(!JSON.stringify(admin.rows).includes(users.disabled),'Disabled candidate exposed');
  check((await read('teacher',otherSchool)).code==='FORBIDDEN','Membership scope bypassed');
  check((await read('researcher')).code==='FORBIDDEN','Researcher role acquired implicit assignment authority');
  check((await read('parent')).code==='FORBIDDEN','Parent enumerated people');
  check((await read('expert')).code==='FORBIDDEN','Expert enumerated people');
  const page=await read('admin',school,1);
  check(page.rows.length===2,'Missing option lookahead');
  const next=await read('admin',school,1,page.rows[0].created_at,page.rows[0].data.user_id);
  check(next.rows[0].data.user_id===admin.rows[1].data.user_id,'Option timestamp/UUID keyset incorrect');
  check((await read('admin',school,101)).code==='INVALID_QUERY','Unbounded option list accepted');
  await db.exec('RESET ROLE');
  await q("DELETE FROM assignment_eligibilities WHERE actor_id=$1 AND candidate_id=$2",[users.admin,users.parent]);
  check(!(await read('admin')).rows.some(r=>r.data.user_id===users.parent),'Removed eligibility still exposed');
  await q("INSERT INTO app_session_revocations(session_id,user_id,reason) VALUES ($1,$2,'logout')",[sessions.admin,users.admin]);
  check((await read('admin')).code==='AUTHENTICATION_REQUIRED','Revoked actor enumerated options');
  await q("DELETE FROM privacy_agreement_acceptances WHERE user_id=$1",[users.teacher]);
  check((await read('teacher')).code==='PRIVACY_ACCEPTANCE_REQUIRED','Unaccepted actor enumerated options');
  await db.exec('ROLLBACK');
  console.log('Isolated assignment option checks: PASS ('+checks+' checks; fictional people only).');
};
