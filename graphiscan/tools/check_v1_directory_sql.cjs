// Real authorization SQL in fictional PGlite only; no hosted connection.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
module.exports=async({db,root,U})=>{
  let checks=0;const check=(ok,message)=>{assert(ok,message);checks++;};
  const q=(sql,params=[])=>db.query(sql,params);
  await db.exec(fs.readFileSync(path.join(root,'graphiscan/db/postgres/009_directory_reads.sql'),'utf8'));
  const signature='public.graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)';
  for(const role of ['anon','authenticated','service_role','graphiscan_password_writer'])
    check(!(await q('SELECT has_function_privilege($1,$2,\'EXECUTE\') AS ok',[role,signature])).rows[0].ok,role+' gained directory execution');
  check((await q("SELECT has_function_privilege('graphiscan_api_reader',$1,'EXECUTE') AS ok",[signature])).rows[0].ok,'Reader missing function');
  for(const table of ['schools','students','screening_results','screening_expert_assignments'])
    check(!(await q("SELECT has_table_privilege('graphiscan_api_reader',$1,'SELECT') AS ok",['public.'+table])).rows[0].ok,'Reader gained direct '+table);
  check((await q("SELECT prosecdef AND proconfig @> ARRAY['search_path=pg_catalog'] AS ok FROM pg_proc WHERE oid=$1::regprocedure",[signature])).rows[0].ok,'Unsafe definer settings');
  await db.exec('BEGIN');
  const ids={admin:U(1101),teacher:U(1102),parent:U(1103),expert:U(1104),researcher:U(1105),guest:U(1106),other:U(1107)};
  for(const [role,user] of Object.entries(ids)){
    await q('INSERT INTO auth.users(id) VALUES ($1)',[user]);
    await q('INSERT INTO user_profiles(user_id,full_name,role,created_by,must_change_password) VALUES ($1,$2,$3,$4,false)',
      [user,'Fictional '+role,role==='other'?'teacher':role,U(1)]);
  }
  await q('UPDATE privacy_agreements SET is_current=false');
  await q(`INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current)
    VALUES ('directory-fictional','Fictional','Fictional',encode(sha256(convert_to('Fictional','UTF8')),'hex'),$1,now(),now(),true)`,[ids.admin]);
  for(const user of Object.values(ids))
    await q("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES ($1,'directory-fictional')",[user]);
  const schools=[];
  for(const name of ['Directory Alpha','Directory Beta','Empty membership school'])
    schools.push(String((await q('INSERT INTO schools(name) VALUES ($1) RETURNING school_id',[name])).rows[0].school_id));
  await q('INSERT INTO school_memberships(user_id,school_id,created_by) VALUES ($1,$2,$4),($1,$3,$4)',[ids.teacher,schools[1],schools[2],ids.admin]);
  for(const role of ['parent','expert','researcher'])
    await q('INSERT INTO school_memberships(user_id,school_id,created_by) VALUES ($1,$2,$3)',[ids[role],schools[2],ids.admin]);
  await q("INSERT INTO user_permission_grants(user_id,permission_key,school_id,granted_by) VALUES ($1,'assignments.manage',$2,$3)",[ids.researcher,schools[0],ids.admin]);
  await q("INSERT INTO user_permission_grants(user_id,permission_key,granted_by) VALUES ($1,'schools.manage',$1)",[ids.admin]);
  const students=[];
  for(const [name,school,teacher,parent,grade] of [
    ['Directory one',schools[0],ids.teacher,ids.parent,1],
    ['Directory two',schools[0],ids.other,null,2],
    ['Directory three',schools[1],ids.other,null,3],
    ['Literal %_ name',schools[0],ids.teacher,null,1]])
    students.push(String((await q(`INSERT INTO students(full_name,school_id,teacher_id,parent_id,grade_level,age,created_at)
      VALUES ($1,$2,$3,$4,$5,8,'2026-01-01T00:00:00Z') RETURNING student_id`,[name,school,teacher,parent,grade])).rows[0].student_id));
  // Reuse an isolated synthetic model; create only expert context, no review release.
  const model=(await q('SELECT model_id FROM model_registry LIMIT 1')).rows[0].model_id;
  const sample=(await q("INSERT INTO handwriting_samples(student_id,teacher_id,storage_path) VALUES ($1,$2,'private/fictional-directory') RETURNING sample_id",[students[2],ids.other])).rows[0].sample_id;
  const result=(await q(`INSERT INTO screening_results(sample_id,model_id,task_type,classification,provenance)
    VALUES ($1,$2,'binary','Normal','legacy_unverified') RETURNING result_id`,[sample,model])).rows[0].result_id;
  await q('INSERT INTO screening_expert_assignments(result_id,assigned_expert_id,assigned_by) VALUES ($1,$2,$3)',[result,ids.expert,ids.admin]);
  let nextSession=1200;const sessions={};
  const fresh=async role=>{
    const sid=U(nextSession++);sessions[role]=sid;
    await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES ($1,$2,clock_timestamp())',[sid,ids[role]]);return sid;
  };
  for(const role of Object.keys(ids))await fresh(role);
  const read=async(role,resource='students',options={})=>(await q(
    'SELECT public.graphiscan_read_directory($1,$2,$3,$4,$5::bigint,$6::smallint,$7::timestamptz,$8::bigint,$9::integer,$10::bigint) AS result',
    [ids[role],sessions[role],resource,options.q??'',options.school??null,options.grade??null,options.time??null,options.after??null,options.limit??25,options.target??null])).rows[0].result;
  const list=async(role,resource='students',options={})=>(await read(role,resource,options)).rows;
  await db.exec('SET LOCAL ROLE graphiscan_api_reader');
  check((await list('teacher')).map(s=>s.student_id).join()===`${students[3]},${students[0]}`,'Teacher saw membership-only/unowned students');
  check((await list('parent')).map(s=>s.student_id).join()===students[0],'Parent linked-child projection wrong');
  check((await list('expert')).map(s=>s.student_id).join()===students[2],'Expert saw unassigned student context');
  check((await list('researcher')).length===3,'Researcher scoped grant not enforced');
  check((await list('admin')).length===0,'School management granted student access');
  check((await read('guest')).code==='FORBIDDEN','Guest reached private directory');
  check((await list('teacher','students',{school:schools[1]})).length===0,'School filter widened teacher scope');
  check((await list('teacher','students',{grade:2})).length===0,'Grade filter widened scope');
  check((await list('teacher','students',{q:'%_'})).length===1,'Search wildcard was interpreted');
  check((await list('teacher','students',{q:'DIRECTORY'})).length===1,'Case-insensitive search failed');
  check((await read('teacher','student',{target:students[1]})).rows.length===0,'Foreign detail leaked');
  check((await read('teacher','student',{target:'9223372036854775807'})).rows.length===0,'Missing detail not empty');
  const owned=(await read('teacher','student',{target:students[0]})).rows[0];
  check(typeof owned.student_id==='string'&&typeof owned.school_id==='string'&&owned.age===8,'Bigint projection wrong');
  check(!('classification'in owned)&&!('storage_path'in owned),'Student context leaked screening/image data');
  const schoolRows=await list('teacher','schools');
  check(schoolRows.length===3,'Teacher membership/owned school directory wrong');
  check((await list('parent','schools')).length===1,'Parent school directory exceeded linked children');
  check((await list('expert','schools')).map(s=>s.school_id).join()===schools[1],'Expert school scope wrong');
  check((await list('researcher','schools')).length===1,'Researcher school membership/grant scope wrong');
  const page=await list('teacher','students',{limit:1});
  check(page.length===2,'Missing lookahead row');
  const next=await list('teacher','students',{limit:1,time:page[0].created_at,after:page[0].student_id});
  check(next.length===1&&next[0].student_id===students[0],'Same-timestamp keyset skipped/duplicated boundary');
  for(const options of [{limit:101},{grade:4},{school:-1},{time:'2026-01-01Z'}])
    check((await read('teacher','students',options)).code==='INVALID_QUERY','Function accepted invalid bounded query');
  await db.exec('RESET ROLE');
  // Ownership and assignment changes must take effect without a new client login.
  await q('UPDATE students SET teacher_id=$1,parent_id=NULL WHERE student_id=$2',[ids.other,students[0]]);
  check((await list('teacher')).length===1&&(await list('parent')).length===0,'Reassignment left former teacher/parent access');
  await q('UPDATE screening_expert_assignments SET assigned_expert_id=NULL WHERE result_id=$1',[result]);
  check((await list('expert')).length===0,'Expert reassignment left access');
  await q("INSERT INTO user_permission_grants(user_id,permission_key,granted_by) VALUES ($1,'assignments.manage',$1)",[ids.admin]);
  check((await read('admin')).code==='AUTHENTICATION_REQUIRED','Grant change did not invalidate old session');
  await fresh('admin');
  check((await list('admin')).length>=4,'Global assignment grant failed');
  await q("INSERT INTO app_session_revocations(session_id,user_id,reason) VALUES ($1,$2,'logout')",[sessions.teacher,ids.teacher]);
  check((await read('teacher')).code==='AUTHENTICATION_REQUIRED','Revoked session read directory');
  await fresh('teacher');
  await q("UPDATE auth.sessions SET not_after=clock_timestamp()-interval '1 second' WHERE id=$1",[sessions.teacher]);
  check((await read('teacher')).code==='AUTHENTICATION_REQUIRED','Expired session read directory');
  for(const [update,code] of [["account_status='disabled'",'ACCOUNT_UNAVAILABLE'],['must_change_password=true','PASSWORD_CHANGE_REQUIRED'],['credential_update_pending=true','AUTHENTICATION_REQUIRED']]){
    await db.exec('SAVEPOINT gate_case');
    await q('UPDATE user_profiles SET '+update+' WHERE user_id=$1',[ids.teacher]);await fresh('teacher');
    check((await read('teacher')).code===code,'Fresh database gate not enforced: '+code);
    await db.exec('ROLLBACK TO SAVEPOINT gate_case');
  }
  await fresh('teacher');
  await q("DELETE FROM privacy_agreement_acceptances WHERE user_id=$1 AND agreement_version='directory-fictional'",[ids.teacher]);
  check((await read('teacher')).code==='PRIVACY_ACCEPTANCE_REQUIRED','Missing acceptance read records');
  await q("UPDATE privacy_agreements SET is_current=false WHERE version='directory-fictional'");
  await q(`INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current,test_subject_id)
    VALUES ('directory-scoped','Fictional','Fictional',encode(sha256(convert_to('Fictional','UTF8')),'hex'),$1,now(),now(),true,$1)`,[ids.admin]);
  check((await read('teacher')).code==='AGREEMENT_NOT_CONFIGURED','Another subject test notice enabled data access');
  await db.exec('ROLLBACK');
  console.log(`Isolated directory read checks: PASS (${checks} checks; fictional records only).`);
};
