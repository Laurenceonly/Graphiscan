// Real PostgreSQL functions in disposable PGlite only. No hosted connection.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
module.exports=async({db,root,installed=false})=>{
 let checks=0;const check=(ok,message)=>{assert(ok,message);checks++},q=(sql,args=[])=>db.query(sql,args),U=n=>`00000000-0000-4000-8000-${String(n).padStart(12,'0')}`;
 if(!installed){
  const migration=fs.readFileSync(path.join(root,'graphiscan/db/postgres/023_role_assignments.sql'),'utf8');
  try{await db.exec(migration)}catch(failure){
   if(!failure.message.includes('Review existing staff ownership without school membership'))throw failure;
   await db.exec('ROLLBACK');
   check((await q("SELECT to_regclass('public.user_school_grades') missing")).rows[0].missing===null,'Rejected migration left partial schema');
   // Earlier foundational fixtures intentionally exercise ownership without membership.
   // Repair those disposable fixtures only after proving the owner migration refuses
   // to silently grant memberships. This is never run against a hosted database.
   await q(`INSERT INTO school_memberships(user_id,school_id,created_by)
    SELECT DISTINCT p.user_id,s.school_id,coalesce(p.created_by,(SELECT user_id FROM user_profiles WHERE role='admin' LIMIT 1))
    FROM user_profiles p JOIN students s ON s.teacher_id=p.user_id WHERE p.role='teacher' ON CONFLICT DO NOTHING`);
   await q(`INSERT INTO school_memberships(user_id,school_id,created_by)
    SELECT DISTINCT p.user_id,s.school_id,coalesce(p.created_by,(SELECT user_id FROM user_profiles WHERE role='admin' LIMIT 1))
    FROM user_profiles p JOIN screening_expert_assignments e ON e.assigned_expert_id=p.user_id
    JOIN screening_results r ON r.result_id=e.result_id JOIN handwriting_samples h ON h.sample_id=r.sample_id
    JOIN students s ON s.student_id=h.student_id WHERE p.role='expert' ON CONFLICT DO NOTHING`);
   await db.exec(migration);
  }
  check(!(await q(`SELECT 1 FROM school_memberships m JOIN user_profiles p USING(user_id)
   WHERE p.role IN('teacher','expert') AND (SELECT count(*) FROM user_school_grades g WHERE g.user_id=m.user_id AND g.school_id=m.school_id)<>3 LIMIT 1`)).rows.length,'Legacy membership grade compatibility not preserved');
 }
 const A=U(891001),B=U(891002),T=U(891003),E=U(891004),P=U(891005),Q=U(891006);let n=892000;
 const get=async(actor,session,target)=>(await q('SELECT public.graphiscan_get_role_assignments($1,$2,$3) r',[actor,session,target])).rows[0].r;
 const rev=async id=>Number((await q('SELECT revision FROM user_profiles WHERE user_id=$1',[id])).rows[0].revision);
 const set=async(actor,session,target,body)=>(await q('SELECT public.graphiscan_set_role_assignments($1,$2,$3,$4::jsonb,$5) r',[actor,session,target,JSON.stringify(body),U(n++)])).rows[0].r;
 const fresh=async id=>{const s=U(n++);await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES($1,$2,clock_timestamp())',[s,id]);return s};
 const directory=async(actor,session)=>(await q("SELECT public.graphiscan_read_directory($1,$2,'students','',NULL,NULL,NULL,NULL,100,NULL) r",[actor,session])).rows[0].r;
 const options=async(actor,session,school,grade)=>(await q('SELECT public.graphiscan_assignment_options_by_grade($1,$2,$3,$4::smallint,NULL,NULL,100) r',[actor,session,school,grade])).rows[0].r;
 for(const role of ['anon','authenticated','service_role','graphiscan_api_reader','graphiscan_admin_writer'])check(!(await q('SELECT has_table_privilege($1,\'public.user_school_grades\',\'SELECT,INSERT,UPDATE,DELETE\') ok',[role])).rows[0].ok,'Grade table exposed to '+role);
 check((await q("SELECT relrowsecurity FROM pg_class WHERE oid='public.user_school_grades'::regclass")).rows[0].relrowsecurity,'Grade RLS missing');
 check(!(await q("SELECT has_function_privilege('graphiscan_api_reader','public.graphiscan_set_role_assignments(uuid,uuid,uuid,jsonb,uuid)','EXECUTE') ok")).rows[0].ok,'Reader gained role assignment writes');
 check((await q("SELECT has_function_privilege('graphiscan_admin_writer','public.graphiscan_set_role_assignments(uuid,uuid,uuid,jsonb,uuid)','EXECUTE') ok")).rows[0].ok,'Writer missing capability');
 await db.exec('BEGIN');
 try{
  for(const [id,role]of [[A,'admin'],[B,'admin'],[T,'teacher'],[E,'expert'],[P,'parent'],[Q,'parent']]){
   await q('INSERT INTO auth.users(id,email,email_confirmed_at) VALUES($1,$2,now())',[id,id+'@fixture.test']);
   await q('INSERT INTO user_profiles(user_id,full_name,role,created_by,must_change_password) VALUES($1,$2,$3,$4,false)',[id,'Role fixture '+role,role,A]);
  }
  const s1=String((await q("INSERT INTO schools(name) VALUES('Role School One') RETURNING school_id")).rows[0].school_id),s2=String((await q("INSERT INTO schools(name) VALUES('Role School Two') RETURNING school_id")).rows[0].school_id);
  await q('UPDATE privacy_agreements SET is_current=false');
  await q("INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current) VALUES('role-scope-check','Synthetic notice','Synthetic notice',encode(sha256(convert_to('Synthetic notice','UTF8')),'hex'),$1,now(),now(),true)",[A]);
  for(const id of [A,B,T,E,P,Q])await q("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES($1,'role-scope-check')",[id]);
  for(const id of [A,B])await q("INSERT INTO user_permission_grants(user_id,permission_key,granted_by) VALUES($1,'accounts.manage',$2)",[id,A]);
  await q("INSERT INTO user_permission_grants(user_id,permission_key,granted_by) VALUES($1,'assignments.manage',$1)",[A]);
  await q("INSERT INTO user_permission_grants(user_id,permission_key,school_id,granted_by) VALUES($1,'assignments.manage',$2,$3)",[B,s1,A]);
  const a=await fresh(A),b=await fresh(B),oldT=await fresh(T),oldE=await fresh(E),oldP=await fresh(P),oldQ=await fresh(Q);
  let result=await set(A,a,T,{expected_revision:await rev(T),school_grades:[{school_id:s1,grade_level:1},{school_id:s2,grade_level:3}]});
  check(!result.code&&result.data.school_grades.length===2,'Teacher school/grade save failed');
  check((await q('SELECT count(*)::int n FROM school_memberships WHERE user_id=$1',[T])).rows[0].n===2,'Scopes did not establish only selected memberships');
  check((await q('SELECT count(*)::int n FROM app_session_revocations WHERE session_id=$1',[oldT])).rows[0].n===1,'Grade changes did not revoke old teacher session');
  result=await set(A,a,E,{expected_revision:await rev(E),school_grades:[{school_id:s1,grade_level:2}]});check(!result.code,'Expert grade save failed');
  check((await q('SELECT count(*)::int n FROM app_session_revocations WHERE session_id=$1',[oldE])).rows[0].n===1,'Expert old session not revoked');
  const scopesBefore=(await get(A,a,T)).data.school_grades;
  check((await set(A,a,T,{expected_revision:1,school_grades:[]})).code==='REVISION_CONFLICT','Stale profile accepted');
  for(const school_grades of [[{school_id:s1,grade_level:4}],[{school_id:s1,grade_level:1},{school_id:s1,grade_level:1}],[{school_id:'9999999',grade_level:1}]])check(!!(await set(A,a,T,{expected_revision:await rev(T),school_grades})).code,'Invalid scope accepted');
  check(JSON.stringify((await get(A,a,T)).data.school_grades)===JSON.stringify(scopesBefore),'Rejected scope changed data');
  check((await set(A,a,A,{expected_revision:await rev(A),school_grades:[]})).code==='FORBIDDEN','Admin/self assignment allowed');
  check((await get(A,U(899999),T)).code==='AUTHENTICATION_REQUIRED','Unknown session bypassed gate');
  const child=async(name,school,grade,parent=null)=>String((await q('INSERT INTO students(full_name,age,school_id,grade_level,teacher_id,parent_id) VALUES($1,8,$2,$3,$4,$5) RETURNING student_id',[name,school,grade,T,parent])).rows[0].student_id);
  const c1=await child('Role Child One',s1,1,Q),c2=await child('Role Child Two',s1,2),c3=await child('Role Child Three',s2,3);
  const studentRev=async id=>Number((await q('SELECT revision FROM students WHERE student_id=$1',[id])).rows[0].revision);
  const t=await fresh(T),e=await fresh(E);
  let visible=await directory(T,t);check(!visible.code&&visible.rows.length===2&&visible.rows.every(r=>String(r.student_id)!==c2),'Teacher reads ignore grade scope');
  const option1=await options(A,a,s1,1),option2=await options(A,a,s1,2);
  check(option1.rows.some(r=>r.data.user_id===T)&&!option1.rows.some(r=>r.data.user_id===E),'Teacher/expert grade options wrong');
  check(option2.rows.some(r=>r.data.user_id===E)&&!option2.rows.some(r=>r.data.user_id===T),'Expert grade options wrong');
  check((await options(B,b,s2,3)).code==='FORBIDDEN','Options widened operator school scope');
  check((await options(A,a,s1,4)).code==='INVALID_QUERY','Invalid grade query accepted');
  check((await q('SELECT count(*)::int n FROM assignment_eligibilities WHERE actor_id IN($1,$2)',[A,B])).rows[0].n===0,'Actor eligibility seeded');
  check((await options(T,t,s1,null)).rows.every(r=>r.data.user_id===T)&&JSON.stringify((await options(T,t,s1,null)).rows[0].data.grade_levels)==='[1]','Teacher self-discovery or parent restriction wrong');
  const writeStudent=async(id,payload)=>(await q('SELECT public.graphiscan_write_directory($1,$2,$3,$4,$5::jsonb,$6,$7) r',[T,t,id?'students.update':'students.create',id,JSON.stringify(payload),'role_grade_request_'+String(n++),U(n++)])).rows[0].r;
  check((await writeStudent(c2,{expected_revision:await studentRev(c2),grade_level:1})).code==='NOT_FOUND','Teacher moved revoked grade record into own scope');
  check((await writeStudent(null,{full_name:'Outside Grade',age:8,school_id:s1,grade_level:2})).code==='INVALID_ASSIGNMENT','Teacher created student outside grade');
  check((await writeStudent(c1,{expected_revision:await studentRev(c1),parent_id:null})).code==='FORBIDDEN','Teacher changed administrator parent link');
  check(!(await writeStudent(null,{full_name:'Allowed Grade',age:8,school_id:s1,grade_level:1})).code,'Teacher authorized grade create denied');
  result=await set(B,b,P,{expected_revision:await rev(P),student_links:[{student_id:c1,expected_revision:await studentRev(c1),linked:true},{student_id:c3,expected_revision:await studentRev(c3),linked:true}]});
  check(result.code==='NOT_FOUND'&&(await q('SELECT parent_id FROM students WHERE student_id=$1',[c1])).rows[0].parent_id===Q,'Out-of-scope delta partially applied');
  result=await set(A,a,P,{expected_revision:await rev(P),student_links:[{student_id:c1,expected_revision:await studentRev(c1),linked:true},{student_id:c3,expected_revision:await studentRev(c3),linked:true}]});
  check(!result.code&&result.data.students.length===2,'Parent specific student link failed');
  check((await q('SELECT count(*)::int n FROM app_session_revocations WHERE session_id IN($1,$2)',[oldP,oldQ])).rows[0].n===2,'Parent transfer did not revoke both old sessions');
  check((await get(B,b,P)).data.students.length===1,'Parent assignment GET exposed other school');
  const p=await fresh(P),visibleParent=await directory(P,p);check(visibleParent.rows.length===2&&visibleParent.rows.some(r=>String(r.student_id)===c3),'Parent visibility not derived from specific students');
  result=await set(B,b,P,{expected_revision:await rev(P),student_links:[{student_id:c1,expected_revision:await studentRev(c1),linked:false}]});
  check(!result.code&&(await q('SELECT parent_id FROM students WHERE student_id=$1',[c3])).rows[0].parent_id===P,'Scoped parent unlink modified hidden school link');
  const rBefore=await rev(P);result=await set(A,a,P,{expected_revision:rBefore,student_links:[{student_id:c3,expected_revision:1,linked:false}]});check(result.code==='REVISION_CONFLICT'&&await rev(P)===rBefore,'Stale student revision changed parent links');
  check((await set(P,await fresh(P),P,{expected_revision:await rev(P),student_links:[{student_id:c3,expected_revision:await studentRev(c3),linked:false}]})).code==='FORBIDDEN','Parent changed own links');
  // A promoted former parent must not revoke the acting admin while repairing a link.
  await q('UPDATE students SET parent_id=$1 WHERE student_id=$2',[A,c1]);result=await set(A,a,P,{expected_revision:await rev(P),student_links:[{student_id:c1,expected_revision:await studentRev(c1),linked:true}]});check(!result.code,'Former-parent admin link repair invalidated acting admin');
  const model=(await q("INSERT INTO model_registry(model_key,model_version,architecture,task_type) VALUES('role_fixture','v1','synthetic','binary') RETURNING model_id")).rows[0].model_id;
  const screening=async student=>{const sample=(await q("INSERT INTO handwriting_samples(student_id,teacher_id,storage_path) VALUES($1,$2,$3) RETURNING sample_id",[student,T,'fictional/'+student+'.png'])).rows[0].sample_id;const id=String((await q("INSERT INTO screening_results(sample_id,model_id,task_type,classification) VALUES($1,$2,'binary','Normal') RETURNING result_id",[sample,model])).rows[0].result_id);await q('INSERT INTO expert_validations(result_id) VALUES($1)',[id]);return id;};
  const r1=await screening(c1),r2=await screening(c2);
  await q("INSERT INTO screening_reports(student_id,result_id,report_type) VALUES($1,$2,'Initial Screening'),($3,$4,'Initial Screening')",[c1,r1,c2,r2]);
  const assign=async id=>(await q('SELECT public.graphiscan_assign_expert($1,$2,$3,$4::jsonb,$5) r',[A,a,id,JSON.stringify({assigned_expert_id:E,expected_revision:Number((await q('SELECT revision FROM screening_results WHERE result_id=$1',[id])).rows[0].revision)}),U(n++)])).rows[0].r;
  check((await assign(r1)).code==='INVALID_ASSIGNMENT','Expert assigned outside allowed grade');check(!(await assign(r2)).code,'Expert assignment requires obsolete actor eligibility');
  await q('INSERT INTO screening_expert_assignments(result_id,assigned_expert_id,assigned_by) VALUES($1,$2,$3)',[r1,E,A]);
  const screenRead=async(actor,session)=>(await q("SELECT public.graphiscan_read_screenings($1,$2,'screenings','{}'::jsonb,NULL,NULL,100,NULL,false) r",[actor,session])).rows[0].r;
  const expertRows=await screenRead(E,e);check(!expertRows.code&&expertRows.rows.length===1&&String(expertRows.rows[0].result_id)===r2,'Expert reads ignore grade despite individual assignment');
  const review=(await q('SELECT public.graphiscan_write_review($1,$2,$3,$4::jsonb,$5,$6) r',[E,e,r1,JSON.stringify({status:'Validated',remarks:'Synthetic review',follow_up_needed:false,expected_revision:1}),'role_review_check_0001',U(n++)])).rows[0].r;
  check(review.code==='NOT_FOUND','Expert reviewed outside grade');
  await q("UPDATE expert_validations SET status='Validated' WHERE result_id=$1",[r1]);const parentAfter=await fresh(P);check((await screenRead(P,parentAfter)).rows.some(r=>String(r.result_id)===r1),'Validated linked parent result unavailable');await q("UPDATE expert_validations SET status='Flagged' WHERE result_id=$1",[r1]);check(!(await screenRead(P,parentAfter)).rows.some(r=>String(r.result_id)===r1),'Flagged result exposed to parent');
  result=await set(A,a,E,{expected_revision:await rev(E),school_grades:[]});check(!result.code&&(await screenRead(E,await fresh(E))).rows.length===0,'Revoking expert grades retained read access');
  // Audit failure rolls back grades, memberships, revisions and session revocations.
  const teacherGradeChange=await set(A,a,T,{expected_revision:await rev(T),school_grades:[{school_id:s1,grade_level:2},{school_id:s2,grade_level:3}]});
  check(!teacherGradeChange.code&&(await q('SELECT count(*)::int n FROM app_session_revocations WHERE session_id=$1',[t])).rows[0].n===1,'Grade-only change did not revoke existing session');
  check((await directory(T,await fresh(T))).rows.every(r=>r.grade_level!==1),'Fresh teacher session retained revoked-grade records');
  const before=await rev(T),beforeScopes=(await get(A,a,T)).data.school_grades;
  await db.exec("CREATE FUNCTION pg_temp.reject_role_audit() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.action='accounts.assignments.updated' THEN RAISE EXCEPTION 'synthetic audit failure'; END IF; RETURN NEW; END $$;CREATE TRIGGER reject_role_audit BEFORE INSERT ON audit_logs FOR EACH ROW EXECUTE FUNCTION pg_temp.reject_role_audit();SAVEPOINT role_failure;");
  let failed=false;try{await set(A,a,T,{expected_revision:before,school_grades:[]})}catch{failed=true}await db.exec('ROLLBACK TO SAVEPOINT role_failure;');
  check(failed&&await rev(T)===before&&JSON.stringify((await get(A,a,T)).data.school_grades)===JSON.stringify(beforeScopes),'Audit failure left partial assignments');
  const parentBefore=await rev(P),otherParentBefore=await rev(Q);await db.exec('SAVEPOINT parent_role_failure');
  failed=false;try{await set(A,a,Q,{expected_revision:otherParentBefore,student_links:[{student_id:c3,expected_revision:await studentRev(c3),linked:true}]})}catch{failed=true}
  await db.exec('ROLLBACK TO SAVEPOINT parent_role_failure;DROP TRIGGER reject_role_audit ON audit_logs;');
  check(failed&&await rev(P)===parentBefore&&await rev(Q)===otherParentBefore&&(await q('SELECT parent_id FROM students WHERE student_id=$1',[c3])).rows[0].parent_id===P,'Audit failure left partial parent transfer or profile changes');
  check((await q("SELECT count(*)::int n FROM audit_logs WHERE actor_id=$1 AND action='accounts.assignments.updated'",[A])).rows[0].n>0,'Assignment changes not audited');
  await require('./check_expert_grade_sql.cjs')({db,root,q,A,E,T,P,a,s1,s2,c1,c2,c3,set,rev,fresh,U});
 }finally{await db.exec('ROLLBACK')}
 console.log('Role assignments SQL: PASS ('+checks+' checks).');return checks;
};
