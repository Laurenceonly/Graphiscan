// Execute the actual capability against fictional PostgreSQL in PGlite only.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
module.exports=async({db,root,U,validateRow})=>{
  let checks=0;const check=(ok,msg)=>{assert(ok,msg);checks++};
  const q=(sql,args=[])=>db.query(sql,args);
  await db.exec(fs.readFileSync(path.join(root,'graphiscan/db/postgres/012_screening_reads.sql'),'utf8'));
  // Storage schema fixture belongs only to this disposable PostgreSQL test.
  await db.exec("CREATE SCHEMA storage; CREATE TABLE storage.buckets(id text PRIMARY KEY,public boolean NOT NULL); INSERT INTO storage.buckets VALUES ('fictional-private',false),('fictional-public',true)");
  const bundle=fs.readFileSync(path.join(root,'graphiscan/db/postgres/013_014_screening_writes.sql'),'utf8');
  const expected=['013_screening_writes.sql','014_screening_uploads.sql'].map(p=>fs.readFileSync(path.join(root,'graphiscan/db/postgres',p),'utf8').replace(/^BEGIN;\r?$/gm,'').replace(/^COMMIT;\r?$/gm,'').trim()).join('\n\n');
  check(bundle==='-- Atomic bundle of 013 + 014. Apply ONLY this bundle once after 012.\nBEGIN;\n'+expected+'\nCOMMIT;\n','Atomic migration bundle drift');
  await db.exec(bundle);
  const sig='public.graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)';
  for(const role of ['anon','authenticated','service_role','graphiscan_password_writer'])
    check(!(await q('SELECT has_function_privilege($1,$2,\'EXECUTE\') ok',[role,sig])).rows[0].ok,'Unexpected execution '+role);
  check((await q("SELECT has_function_privilege('graphiscan_api_reader',$1,'EXECUTE') ok",[sig])).rows[0].ok,'Missing reader capability');
  check((await q("SELECT prosecdef AND proconfig @> ARRAY['search_path=pg_catalog'] ok FROM pg_proc WHERE oid=$1::regprocedure",[sig])).rows[0].ok,'Unsafe function settings');
  for(const table of ['screening_results','screening_reports','expert_validations','handwriting_samples'])
    check(!(await q("SELECT has_table_privilege('graphiscan_api_reader',$1,'SELECT') ok",[table])).rows[0].ok,'Reader got table access');
  await db.exec('BEGIN');
  const ids={},sessions={};let next=15000;
  for(const role of ['admin','researcher','teacher','other','parent','expert','guest']){
    const id=ids[role]=U(next++);sessions[role]=U(next++);
    await q('INSERT INTO auth.users(id) VALUES ($1)',[id]);
    await q('INSERT INTO user_profiles(user_id,full_name,role,created_by,must_change_password) VALUES ($1,$2,$3,$4,false)',[id,'Fictional '+role,role==='other'?'teacher':role,U(1)]);
    await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES ($1,$2,clock_timestamp())',[sessions[role],id]);
  }
  await q('UPDATE privacy_agreements SET is_current=false');
  await q(`INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current)
    VALUES ('screening-fixture','Fictional','Fictional',encode(sha256(convert_to('Fictional','UTF8')),'hex'),$1,now(),now(),true)`,[ids.admin]);
  for(const id of Object.values(ids))await q("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES ($1,'screening-fixture')",[id]);
  const schools=[];for(const name of ['Screenings Alpha','Screenings Beta'])schools.push(String((await q('INSERT INTO schools(name) VALUES ($1) RETURNING school_id',[name])).rows[0].school_id));
  const students=[];for(const [i,teacher,parent] of [[0,ids.teacher,ids.parent],[1,ids.other,null],[0,ids.teacher,ids.parent]])
    students.push(String((await q('INSERT INTO students(full_name,school_id,grade_level,teacher_id,parent_id) VALUES ($1,$2,1,$3,$4) RETURNING student_id',['Fictional child',schools[i],teacher,parent])).rows[0].student_id));
  await q("INSERT INTO user_permission_grants(user_id,permission_key,school_id,granted_by) VALUES ($1,'assignments.manage',$2,$3)",[ids.researcher,schools[0],ids.admin]);
  await q("INSERT INTO user_permission_grants(user_id,permission_key,granted_by) VALUES ($1,'schools.manage',$1)",[ids.admin]);
  const model=(await q('SELECT model_id FROM model_registry LIMIT 1')).rows[0].model_id;
  const results=[],reports=[];
  for(const [index,student,status] of [[0,students[0],'Pending'],[1,students[0],'Validated'],[2,students[1],'Validated']]){
    const sample=(await q("INSERT INTO handwriting_samples(student_id,teacher_id,storage_path) VALUES ($1,$2,'private/never-return-this') RETURNING sample_id",[student,index===2?ids.other:ids.teacher])).rows[0].sample_id;
    const r=(await q(`INSERT INTO screening_results(sample_id,model_id,task_type,classification,confidence_score,class_probabilities,decision_rule,model_snapshot,provenance,date_generated)
      VALUES ($1,$2,'binary','Normal',0.9,'{"normal":0.9,"high_potential":0.1}','{"kind":"argmax"}',
      '{"model_key":"frozen-key","model_version":"frozen-version","architecture":"Fictional","preprocessing_key":"frozen-input"}',$3,'2026-01-01T00:00:00Z') RETURNING result_id`,[sample,model,index===1?'verified':'legacy_unverified'])).rows[0].result_id;
    results.push(String(r));
    await q('INSERT INTO expert_validations(result_id,status,expert_id,remarks,validation_date) VALUES ($1,$2,$3,$4,now())',[r,status,status==='Pending'?null:ids.expert,status==='Pending'?null:'Fictional review']);
    reports.push(String((await q(`INSERT INTO screening_reports(student_id,result_id,report_type,school_context)
      VALUES ($1,$2,$3,jsonb_build_object('school_id',$4::text,'school_name','Fictional school','grade_level',1,'private_extra','never-return-this')) RETURNING report_id`,[student,r,index===1?'Follow-up Screening':'Initial Screening',schools[index===2?1:0]])).rows[0].report_id));
  }
  for(const result of [results[0],results[2]])await q('INSERT INTO screening_expert_assignments(result_id,assigned_expert_id,assigned_by) VALUES ($1,$2,$3)',[result,ids.expert,ids.admin]);
  // Grants invalidate earlier sessions; fixtures sign in after setup, as real users must.
  for(const role of Object.keys(sessions)){
    sessions[role]=U(next++);
    await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES ($1,$2,clock_timestamp())',[sessions[role],ids[role]]);
  }
  const read=async(role,resource='screenings',options={})=>(await q('SELECT public.graphiscan_read_screenings($1,$2,$3,$4::jsonb,$5::timestamptz,$6::bigint,$7::integer,$8::bigint,$9::boolean) result',
    [ids[role],sessions[role],resource,JSON.stringify(options.filters??{}),options.time??null,options.after??null,options.limit??25,options.target??null,options.oldest??false])).rows[0].result;
  await db.exec('SET LOCAL ROLE graphiscan_api_reader');
  let r=await read('teacher');check(r.rows.length===2,'Teacher crossed current link');
  for(const row of r.rows){const valid=validateRow('Screening',row);check(valid.ok,'SQL screening/schema mismatch: '+JSON.stringify(valid.errors));}
  check(r.rows[0].result_id===results[1],'Equal timestamp numeric ordering wrong');
  check(!JSON.stringify(r).includes('never-return-this'),'Private storage path leaked');
  check(r.rows[0].model.model_key==='frozen-key','Frozen snapshot lost');
  check(r.rows[1].model.model_key===null,'Unverified legacy model asserted');
  check(r.rows[0].class_scores.normal===0.9 && r.rows[0].predicted_class_score===0.9,'Fraction scores changed');
  r=await read('parent');check(r.rows.length===1 && r.rows[0].result_id===results[1],'Parent release filtering leaked');
  r=await read('parent','history',{target:students[0],oldest:true});check(r.rows[0].report.report_type==='Follow-up Screening','Parent first-visible relabeled');
  check((await read('parent','history',{target:students[2]})).found===true,'Linked empty history lost');
  check((await read('parent','history',{target:students[1]})).found===false,'Foreign child history found');
  check((await read('parent','screening',{target:results[0]})).rows.length===0,'Parent opened Pending detail');
  check((await read('parent','report',{target:reports[0]})).rows.length===0,'Parent opened Pending report');
  r=await read('parent','report',{target:reports[1]});check(r.rows[0].report_type==='Follow-up Screening' && !('sample_id' in r.rows[0]),'Report projection wrong');
  {const valid=validateRow('Report',r.rows[0]);check(valid.ok,'SQL report/schema mismatch: '+JSON.stringify(valid.errors));}
  check((await read('expert')).rows.length===2,'Expert current assignment scope wrong');
  check((await read('expert','screening',{target:results[1]})).rows.length===0,'Expert opened unassigned sibling result');
  r=await read('researcher');check(r.code===null && r.rows.length===2,'Scoped researcher read: '+JSON.stringify(r));
  check((await read('admin')).rows.length===0,'School management granted screenings');
  check((await read('guest')).code==='FORBIDDEN','Guest read screenings');
  check((await read('teacher','screenings',{filters:{school_id:schools[1]}})).rows.length===0,'Filter widened scope');
  check((await read('parent','screenings',{filters:{validation_status:'Pending'}})).rows.length===0,'Parent status filter widened release');
  r=await read('teacher','history',{target:students[0],oldest:true,limit:1});check(r.rows[0].result_id===results[0] && r.rows.length===2,'Oldest keyset order wrong');
  r=await read('teacher','history',{target:students[0],oldest:true,limit:1,time:r.rows[0].date_generated,after:results[0]});check(r.rows.length===1 && r.rows[0].result_id===results[1],'Oldest continuation wrong');
  await db.exec('RESET ROLE');
  await require('./check_v1_screening_writes_sql.cjs')({db,U,ids,sessions,results,schools});
  await require('./check_v1_screening_uploads_sql.cjs')({db,U,ids,sessions,students,model,validateRow});
  r=await read('parent','report',{target:reports[1]});check(r.rows[0].school_context.school_name==='Fictional school' && !JSON.stringify(r).includes('never-return-this'),'School snapshot extra fields leaked');
  await q("UPDATE expert_validations SET status='Flagged' WHERE result_id=$1",[results[1]]);
  check((await read('parent')).rows.length===0,'Review withdrawal did not revoke release');
  await q('UPDATE students SET teacher_id=$1,parent_id=NULL WHERE student_id=$2',[ids.other,students[0]]);
  check((await read('teacher')).rows.length===0,'Teacher reassignment retained access');
  check((await read('parent','history',{target:students[0]})).found===false,'Parent unlink retained history');
  await q('UPDATE screening_expert_assignments SET assigned_expert_id=NULL WHERE result_id=$1',[results[0]]);
  check((await read('expert','screening',{target:results[0]})).rows.length===0,'Expert unassignment retained detail');
  await q('UPDATE user_profiles SET must_change_password=true WHERE user_id=$1',[ids.other]);
  sessions.other=U(next++);await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES ($1,$2,clock_timestamp())',[sessions.other,ids.other]);
  check((await read('other')).code==='PASSWORD_CHANGE_REQUIRED','Password gate bypass');
  await q('UPDATE user_profiles SET must_change_password=false,credential_update_pending=true WHERE user_id=$1',[ids.other]);
  check((await read('other')).code==='AUTHENTICATION_REQUIRED','Pending credentials gate bypass');
  await q('UPDATE user_profiles SET credential_update_pending=false WHERE user_id=$1',[ids.other]);
  sessions.other=U(next++);await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES ($1,$2,clock_timestamp())',[sessions.other,ids.other]);
  await q('DELETE FROM privacy_agreement_acceptances WHERE user_id=$1',[ids.other]);
  check((await read('other')).code==='PRIVACY_ACCEPTANCE_REQUIRED','Notice gate bypass');
  await q('DELETE FROM auth.sessions WHERE id=$1',[sessions.expert]);
  check((await read('expert')).code==='AUTHENTICATION_REQUIRED','Removed provider session read');
  await db.exec('ROLLBACK');
  console.log(`Isolated screening read SQL: PASS (${checks} checks; fictional records only).`);
};
