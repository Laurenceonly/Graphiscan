// Executes real mutation SQL against fictional PGlite only.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{createHmac}=require('crypto');
module.exports=async({db,root,U})=>{
  let checks=0;const check=(ok,message)=>{assert(ok,message);checks++;};
  const q=(sql,params=[])=>db.query(sql,params);
  await db.exec(fs.readFileSync(path.join(root,'graphiscan/db/postgres/010_directory_writes.sql'),'utf8'));
  const signature='public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)';
  for(const role of ['anon','authenticated','service_role','graphiscan_api_reader'])
    check(!(await q("SELECT has_function_privilege($1,$2,'EXECUTE') AS ok",[role,signature])).rows[0].ok,'Unauthorized writer '+role);
  check((await q("SELECT has_function_privilege('graphiscan_password_writer',$1,'EXECUTE') AS ok",[signature])).rows[0].ok,'Writer execution missing');
  for(const role of ['graphiscan_password_writer','graphiscan_api_reader','anon','authenticated','service_role'])
    check(!(await q("SELECT has_table_privilege($1,'public.directory_request_keys','SELECT') AS ok",[role])).rows[0].ok,'Private key exposed');
  for(const helper of ['public.graphiscan_directory_digest(jsonb)','public.graphiscan_directory_grant(uuid,text,bigint)'])
    check(!(await q("SELECT has_function_privilege('graphiscan_password_writer',$1,'EXECUTE') AS ok",[helper])).rows[0].ok,'Writer can call private helper');
  for(const table of ['schools','students','api_requests','audit_logs'])
    check(!(await q("SELECT has_table_privilege('graphiscan_password_writer',$1,'INSERT,UPDATE,DELETE') AS ok",['public.'+table])).rows[0].ok,'Direct write privileges expanded');
  const canonical=(await q("SELECT '{\"test\":1}'::jsonb::text AS body,encode(secret,'hex') AS key,public.graphiscan_directory_digest('{\"test\":1}'::jsonb) AS digest FROM directory_request_keys")).rows[0];
  check(canonical.digest===createHmac('sha256',Buffer.from(canonical.key,'hex')).update(canonical.body).digest('hex'),'HMAC mismatch');
  await db.exec('BEGIN');
  const roles=['admin','teacher','other','parent','researcher','limited','ungranted','expert','guest'];
  const users=Object.fromEntries(roles.map((r,i)=>[r,U(2100+i)]));
  for(const role of roles){
    await q('INSERT INTO auth.users(id) VALUES ($1)',[users[role]]);
    await q('INSERT INTO user_profiles(user_id,full_name,role,created_by,must_change_password) VALUES ($1,$2,$3,$4,false)',
      [users[role],'Fictional '+role,['limited','ungranted'].includes(role)?'admin':role==='other'?'teacher':role,U(1)]);
  }
  await q('UPDATE privacy_agreements SET is_current=false');
  await q("INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current) VALUES ('directory-write-fictional','Fictional','Fictional',encode(sha256(convert_to('Fictional','UTF8')),'hex'),$1,now(),now(),true)",[users.admin]);
  for(const user of Object.values(users))await q("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES ($1,'directory-write-fictional')",[user]);
  const schools=[];for(const name of ['Write Alpha','Write Beta'])schools.push(String((await q('INSERT INTO schools(name) VALUES ($1) RETURNING school_id',[name])).rows[0].school_id));
  for(const teacher of ['teacher','other'])for(const school of schools){
    await q('INSERT INTO school_memberships(user_id,school_id,created_by) VALUES ($1,$2,$3)',[users[teacher],school,users.admin]);
    for(const actor of ['admin','researcher'])await q("INSERT INTO assignment_eligibilities(actor_id,candidate_id,school_id,assignment_role,granted_by) VALUES ($1,$2,$3,'teacher',$4)",[users[actor],users[teacher],school,users.admin]);
  }
  for(const actor of ['admin','researcher','teacher'])await q("INSERT INTO assignment_eligibilities(actor_id,candidate_id,school_id,assignment_role,granted_by) VALUES ($1,$2,$3,'parent',$4)",[users[actor],users.parent,schools[0],users.admin]);
  for(const permission of ['schools.manage','assignments.manage'])await q('INSERT INTO user_permission_grants(user_id,permission_key,granted_by) VALUES ($1,$2,$1)',[users.admin,permission]);
  await q("INSERT INTO user_permission_grants(user_id,permission_key,school_id,granted_by) VALUES ($1,'assignments.manage',$2,$3),($4,'schools.manage',$2,$3)",[users.researcher,schools[0],users.admin,users.limited]);
  let sequence=2200;const sessions={};
  const fresh=async role=>{sessions[role]=U(sequence++);await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES ($1,$2,clock_timestamp())',[sessions[role],users[role]]);};
  for(const role of roles)await fresh(role);
  const write=async(role,op,body,target=null,key='fictional_create_key_0001')=>(await q('SELECT public.graphiscan_write_directory($1,$2,$3,$4::bigint,$5::jsonb,$6,$7) AS result',
    [users[role],sessions[role],op,target,JSON.stringify(body),key,U(2999)])).rows[0].result;
  const base={full_name:'Fictional Child',age:8,school_id:schools[0],grade_level:1};
  await db.exec('SET LOCAL ROLE graphiscan_password_writer');
  for(const role of ['parent','expert','guest','ungranted'])check((await write(role,'students.create',base)).code==='FORBIDDEN','Unprivileged student write '+role);
  check((await write('teacher','schools.create',{name:'Forbidden'})).code==='FORBIDDEN','Teacher created school');
  check((await write('limited','schools.create',{name:'Forbidden'})).code==='FORBIDDEN','Scoped grant created school');
  check((await write('teacher','students.create',{...base,teacher_id:users.other})).code==='FORBIDDEN','Teacher forged assignment');
  check((await write('teacher','students.create',{...base,parent_id:users.other})).code==='INVALID_ASSIGNMENT','Wrong parent role accepted');
  check((await write('admin','students.create',base)).code==='INVALID_ASSIGNMENT','Admin missing teacher accepted');
  check((await write('researcher','students.create',{...base,school_id:schools[1],teacher_id:users.teacher})).code==='FORBIDDEN','Researcher crossed school scope');
  check((await write('teacher','students.create',base,null,'short')).code==='INVALID_INPUT','Bad request key accepted');
  const created=await write('teacher','students.create',{...base,parent_id:users.parent});
  check(created.code===null&&created.data.teacher_id===users.teacher&&created.data.parent_id===users.parent,'Teacher-derived ownership failed');
  const id=created.data.student_id;
  check(typeof id==='string'&&created.data.revision===1,'Create projection invalid');
  const replay=await write('teacher','students.create',{...base,parent_id:users.parent});
  check(replay.data.student_id===id,'Retry duplicated student');
  check((await write('teacher','students.create',{...base,age:9})).code==='IDEMPOTENCY_CONFLICT','Changed payload reused key');
  const hidden=await write('other','students.create',base,null,'fictional_other_create_01');
  check(hidden.code===null&&hidden.warnings.length===0,'Duplicate warning leaked other teacher student');
  const duplicate=await write('teacher','students.create',{...base,full_name:'FICTIONAL  CHILD'},null,'fictional_duplicate_0001');
  check(duplicate.warnings.join()==='duplicate_name'&&duplicate.data.student_id!==id,'Duplicate warning/merge failed');
  check((await write('teacher','students.update',{full_name:'Changed',expected_revision:99},id)).code==='REVISION_CONFLICT','Stale update overwritten');
  check((await write('other','students.update',{age:9,expected_revision:1},id)).code==='NOT_FOUND','Other teacher edited student');
  check((await write('teacher','students.update',{school_id:schools[1],expected_revision:1},id)).code==='FORBIDDEN','Teacher moved school');
  const updated=await write('teacher','students.update',{age:9,parent_id:null,expected_revision:1},id);
  check(updated.data.age===9&&updated.data.parent_id===null&&updated.data.revision===2,'Student edit/revision failed');
  const refreshed=await write('teacher','students.create',{...base,parent_id:users.parent});
  check(refreshed.data.age===9&&refreshed.data.parent_id===null,'Replay returned stale metadata');
  const moved=await write('admin','students.update',{teacher_id:users.other,school_id:schools[1],expected_revision:2},id);
  check(moved.code===null&&moved.data.school_id===schools[1]&&moved.data.revision===3,'Authorized reassignment failed');
  check((await write('teacher','students.create',{...base,parent_id:users.parent})).code==='NOT_FOUND','Replay bypassed ownership');
  check((await write('researcher','students.update',{age:10,expected_revision:3},id)).code==='NOT_FOUND','Researcher edited moved student');
  const school=await write('admin','schools.create',{name:' Write Alpha '});
  check(school.code===null&&school.warnings.join()==='duplicate_name','School duplicate handling failed');
  check((await write('admin','schools.update',{name:'Updated',expected_revision:999},school.data.school_id)).code==='REVISION_CONFLICT','Stale school update succeeded');
  const changed=await write('admin','schools.update',{name:'Updated',expected_revision:1},school.data.school_id);
  check(changed.data.revision===2&&changed.data.name==='Updated','School update failed');
  check((await write('limited','schools.update',{name:'Forbidden',expected_revision:1},schools[1])).code==='FORBIDDEN','Scoped school edit crossed scope');
  await db.exec('RESET ROLE');
  check((await q("SELECT count(*)::int AS n FROM audit_logs WHERE actor_id=$1 AND action='students.create'",[users.teacher])).rows[0].n===2,'Replay duplicated audit');
  const request=(await q("SELECT request_digest,resource_id FROM api_requests WHERE actor_id=$1 AND idempotency_key='fictional_create_key_0001'",[users.teacher])).rows[0];
  check(/^[a-f0-9]{64}$/.test(request.request_digest)&&request.resource_id===id,'Request binding missing');
  await q('DELETE FROM assignment_eligibilities WHERE actor_id=$1 AND candidate_id=$2',[users.teacher,users.parent]);
  check((await write('teacher','students.create',{...base,parent_id:users.parent},null,'fictional_missing_link01')).code==='INVALID_ASSIGNMENT','Removed eligibility still allowed');
  await q("UPDATE user_profiles SET account_status='disabled' WHERE user_id=$1",[users.other]);
  check((await write('admin','students.create',{...base,teacher_id:users.other},null,'fictional_disabled_001')).code==='INVALID_ASSIGNMENT','Disabled candidate accepted');
  await q("INSERT INTO app_session_revocations(session_id,user_id,reason) VALUES ($1,$2,'logout')",[sessions.teacher,users.teacher]);
  check((await write('teacher','students.create',base)).code==='AUTHENTICATION_REQUIRED','Revoked actor wrote records');
  await fresh('teacher');
  await q("DELETE FROM privacy_agreement_acceptances WHERE user_id=$1 AND agreement_version='directory-write-fictional'",[users.teacher]);
  check((await write('teacher','students.create',base)).code==='PRIVACY_ACCEPTANCE_REQUIRED','Missing acceptance wrote records');
  await db.exec("CREATE FUNCTION public.directory_fixture_fail() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Fictional audit failure'; END; $$; CREATE TRIGGER directory_fixture_fail BEFORE INSERT ON public.audit_logs FOR EACH ROW EXECUTE FUNCTION public.directory_fixture_fail(); SAVEPOINT atomic_case;");
  let failed=false;try{await write('admin','students.create',{...base,teacher_id:users.teacher},null,'fictional_atomic_fail01');}catch{failed=true;}
  await db.exec('ROLLBACK TO SAVEPOINT atomic_case');
  check(failed,'Audit failure ignored');
  check((await q("SELECT count(*)::int AS n FROM api_requests WHERE idempotency_key='fictional_atomic_fail01'")).rows[0].n===0,'Failed audit retained request');
  check((await q("SELECT count(*)::int AS n FROM students WHERE teacher_id=$1",[users.teacher])).rows[0].n===1,'Failed audit left partial student');
  await db.exec('ROLLBACK');
  console.log('Isolated directory mutation checks: PASS ('+checks+' checks; fictional records only).');
};
