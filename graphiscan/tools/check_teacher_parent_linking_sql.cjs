// Owner migration and permission tests in disposable PGlite only.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
module.exports=async({db,root,U})=>{
 let checks=0,n=973000;const check=(ok,message)=>{assert(ok,message);checks++},q=(sql,args=[])=>db.query(sql,args);
 const migration=fs.readFileSync(path.join(root,'graphiscan/db/postgres/027_teacher_parent_linking.sql'),'utf8');
 const previousWriter=(await q("SELECT pg_get_functiondef('public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)'::regprocedure) body")).rows[0].body;
 for(const writerEnding of ['\n','\r\n'])for(const migrationEnding of ['\n','\r\n']){
  await db.exec(previousWriter.replace(/\r?\n/g,writerEnding));
  await db.exec(migration.replace(/\r?\n/g,migrationEnding));
  check((await q("SELECT strpos(prosrc,'-- teacher parent linking027')>0 ok FROM pg_proc WHERE oid='public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)'::regprocedure")).rows[0].ok,'Mixed LF/CRLF migration failed');
 }
 const unexpectedWriter=previousWriter.replace("IF actor.role='teacher' AND parent IS DISTINCT FROM st.parent_id THEN","IF actor.role='teacher' AND parent IS DISTINCT FROM st.parent_id AND true THEN");
 check(unexpectedWriter!==previousWriter,'Unexpected-body fixture was not changed');await db.exec(unexpectedWriter);
 const beforeRejected=(await q("SELECT prosrc FROM pg_proc WHERE oid='public.graphiscan_teacher_parent_options(uuid,uuid,bigint,smallint,text)'::regprocedure")).rows[0].prosrc;
 let rejected=false;try{await db.exec(migration)}catch(error){rejected=error.message.includes('unexpected directory writer body');await db.exec('ROLLBACK')}
 check(rejected,'Migration accepted an unexpected directory writer');
 check((await q("SELECT prosrc FROM pg_proc WHERE oid='public.graphiscan_teacher_parent_options(uuid,uuid,bigint,smallint,text)'::regprocedure")).rows[0].prosrc===beforeRejected,'Rejected migration partially changed lookup');
 await db.exec(previousWriter);
 await db.exec(migration);
 const signature='public.graphiscan_teacher_parent_options(uuid,uuid,bigint,smallint,text)',writer='public.graphiscan_write_directory(uuid,uuid,text,bigint,jsonb,text,uuid)';
 const writerBody=(await q('SELECT pg_get_functiondef($1::regprocedure) body',[writer])).rows[0].body;
 await db.exec(migration);check((await q('SELECT pg_get_functiondef($1::regprocedure) body',[writer])).rows[0].body===writerBody,'Migration rerun changed directory writer');
 const preflight=(await q(fs.readFileSync(path.join(root,'graphiscan/db/postgres/027_teacher_parent_linking_preflight.sql'),'utf8'))).rows[0];
 for(const [flag,value]of Object.entries(preflight))check(value===true,'Parent-link installation preflight: '+flag);
 for(const role of ['anon','authenticated','service_role','graphiscan_admin_writer','graphiscan_password_writer'])check(!(await q("SELECT has_function_privilege($1,$2,'EXECUTE') ok",[role,signature])).rows[0].ok,'Unauthorized parent lookup '+role);
 check((await q("SELECT has_function_privilege('graphiscan_api_reader',$1,'EXECUTE') ok",[signature])).rows[0].ok,'Reader parent lookup missing');
 const meta=(await q("SELECT p.prosecdef,p.proconfig FROM pg_proc p WHERE p.oid=$1::regprocedure",[signature])).rows[0];check(meta.prosecdef&&meta.proconfig.includes('search_path=pg_catalog'),'Lookup lost pinned definer');
 for(const role of ['anon','authenticated','service_role','graphiscan_api_reader','graphiscan_admin_writer'])check(!(await q("SELECT has_function_privilege($1,$2,'EXECUTE') ok",[role,writer])).rows[0].ok,'Directory writer grants expanded '+role);
 await db.exec('BEGIN');try{
 const A=U(970001),T=U(970002),O=U(970003),P=U(970004),Q=U(970005),E=U(970006);
 for(const [id,role]of [[A,'admin'],[T,'teacher'],[O,'teacher'],[P,'parent'],[Q,'parent'],[E,'expert']]){
   await q('INSERT INTO auth.users(id,email,email_confirmed_at) VALUES($1,$2,now())',[id,id+'@fixture.invalid']);
   await q('INSERT INTO user_profiles(user_id,full_name,role,created_by,must_change_password) VALUES($1,$2,$3,$4,false)',[id,'Fictional '+role,role,A]);
 }
 await q('UPDATE privacy_agreements SET is_current=false');await q("INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current) VALUES('teacher-parent-fixture','Fictional','Fictional',encode(sha256(convert_to('Fictional','UTF8')),'hex'),$1,now(),now(),true)",[A]);
 for(const id of [A,T,O,P,Q,E])await q("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES($1,'teacher-parent-fixture')",[id]);
 const school=String((await q("INSERT INTO schools(name) VALUES('Teacher Parent School') RETURNING school_id")).rows[0].school_id),otherSchool=String((await q("INSERT INTO schools(name) VALUES('Other Parent School') RETURNING school_id")).rows[0].school_id);
 for(const id of [T,O,E]){await q('INSERT INTO school_memberships(user_id,school_id,created_by) VALUES($1,$2,$3)',[id,school,A]);await q('INSERT INTO user_school_grades(user_id,school_id,grade_level,created_by) VALUES($1,$2,1,$3)',[id,school,A]);}
 const sessions={};for(const id of [A,T,O,P,Q,E]){sessions[id]=U(n++);await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES($1,$2,clock_timestamp())',[sessions[id],id]);}
 const lookup=async(actor=T,whichSchool=school,grade=1,email=P+'@fixture.invalid',session=sessions[actor])=>(await q('SELECT public.graphiscan_teacher_parent_options($1,$2,$3,$4::smallint,$5) r',[actor,session,whichSchool,grade,email])).rows[0].r;
 const result=await lookup();check(!result.code&&result.rows.length===1&&result.rows[0].data.user_id===P,'Unlinked existing parent cannot be discovered');
 check(Object.keys(result.rows[0].data).sort().join(',')==='full_name,role,user_id','Parent lookup exposed private fields');
 check((await lookup(T,school,1,'unknown@fixture.invalid')).rows.length===0,'Unknown email returned parent directory');
 check((await lookup(T,school,1,T+'@fixture.invalid')).rows.length===0,'Non-parent account returned');
 check((await lookup(T,school,1,'%')).code==='INVALID_QUERY','Broad parent query accepted');
 check((await lookup(T,school,2)).code==='FORBIDDEN','Unassigned grade lookup allowed');check((await lookup(T,otherSchool)).code==='FORBIDDEN','Unassigned school lookup allowed');
 for(const actor of [A,E,P])check((await lookup(actor)).code==='FORBIDDEN','Non-teacher parent lookup allowed');
 check((await lookup(T,school,1,P+'@fixture.invalid',U(n++))).code==='AUTHENTICATION_REQUIRED','Missing session lookup allowed');
 const student=async(teacher,grade=1)=>String((await q("INSERT INTO students(full_name,age,school_id,grade_level,teacher_id) VALUES('Fictional Child',8,$1,$2,$3) RETURNING student_id",[school,grade,teacher])).rows[0].student_id);
 const own=await student(T),other=await student(O),outside=await student(T,2);
 const rev=async id=>Number((await q('SELECT revision FROM students WHERE student_id=$1',[id])).rows[0].revision);
 const write=async(id,parent,extra={},actor=T)=>(await q('SELECT public.graphiscan_write_directory($1,$2,$3,$4,$5::jsonb,$6,$7) r',[actor,sessions[actor],'students.update',id,JSON.stringify({parent_id:parent,expected_revision:await rev(id),...extra}),null,U(n++)])).rows[0].r;
 check((await write(other,P)).code==='NOT_FOUND','Teacher changed another teacher student');check((await write(outside,P)).code==='NOT_FOUND','Teacher changed student outside grade scope');
 check((await write(own,P,{teacher_id:O})).code==='FORBIDDEN','Parent link allowed teacher reassignment');check((await write(own,P,{school_id:otherSchool})).code==='FORBIDDEN','Parent link allowed school move');
 check((await write(own,T)).code==='INVALID_ASSIGNMENT','Non-parent link allowed');check((await write(own,P,{},E)).code==='FORBIDDEN','Expert parent link allowed');
 check((await write(own,P,{expected_revision:await rev(own)+1})).code==='REVISION_CONFLICT','Stale parent link accepted');
 let linked=await write(own,P);check(!linked.code&&linked.data.parent_id===P,'Owned student parent link denied');
 const parentRows=async actor=>(await q("SELECT public.graphiscan_read_directory($1,$2,'students','',NULL,NULL,NULL,NULL,100,NULL) r",[actor,sessions[actor]])).rows[0].r.rows;
 check((await parentRows(P)).some(row=>row.student_id===own),'Linked parent cannot read student');
 linked=await write(own,Q);check(!linked.code&&linked.data.parent_id===Q,'Parent replacement denied');check(!(await parentRows(P)).some(row=>row.student_id===own),'Former parent retained student access');
 check((await parentRows(Q)).some(row=>row.student_id===own),'Replacement parent access missing');
 check(!(await write(own,null)).code,'Parent unlink denied');check(!(await parentRows(Q)).some(row=>row.student_id===own),'Unlinked parent retained student access');
 await q("UPDATE user_profiles SET account_status='disabled' WHERE user_id=$1",[P]);check((await lookup()).rows.length===0,'Disabled parent discovered');check((await write(own,P)).code==='INVALID_ASSIGNMENT','Disabled parent linked');
 await q("UPDATE user_profiles SET account_status='active',credential_update_pending=true WHERE user_id=$1",[P]);check((await lookup()).rows.length===0,'Credential-pending parent discovered');check((await write(own,P)).code==='INVALID_ASSIGNMENT','Credential-pending parent linked');
 await q('UPDATE user_profiles SET credential_update_pending=false WHERE user_id=$1',[P]);
 const payload=JSON.stringify({full_name:'Fictional New Child',age:8,school_id:school,grade_level:1,parent_id:P}),key='teacher_parent_create_fixture';
 const create=async()=>(await q('SELECT public.graphiscan_write_directory($1,$2,$3,NULL,$4::jsonb,$5,$6) r',[T,sessions[T],'students.create',payload,key,U(n++)])).rows[0].r;
 const created=await create();check(!created.code&&created.data.parent_id===P,'Creation with parent denied');check((await create()).data.student_id===created.data.student_id,'Parent-linked creation replay duplicated student');
 const before=await rev(own);await db.exec("CREATE FUNCTION pg_temp.reject_parent_link_audit() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.action='students.update' THEN RAISE EXCEPTION 'Fictional audit failure'; END IF; RETURN NEW; END $$;CREATE TRIGGER reject_parent_link_audit BEFORE INSERT ON audit_logs FOR EACH ROW EXECUTE FUNCTION pg_temp.reject_parent_link_audit();SAVEPOINT parent_audit;");
 let failed=false;try{await write(own,P)}catch{failed=true}await db.exec('ROLLBACK TO SAVEPOINT parent_audit;DROP TRIGGER reject_parent_link_audit ON audit_logs;');
 check(failed&&await rev(own)===before&&(await q('SELECT parent_id FROM students WHERE student_id=$1',[own])).rows[0].parent_id===null,'Audit failure partially saved parent link');
 check((await q("SELECT count(*)::int n FROM audit_logs WHERE actor_id=$1 AND action='students.update' AND resource_id=$2",[T,own])).rows[0].n===3,'Parent link changes not audited exactly once');
 await q('DELETE FROM privacy_agreement_acceptances WHERE user_id=$1',[T]);check((await lookup()).code==='PRIVACY_ACCEPTANCE_REQUIRED','Lookup bypassed privacy gate');check((await write(own,P)).code==='PRIVACY_ACCEPTANCE_REQUIRED','Link bypassed privacy gate');
 }finally{await db.exec('ROLLBACK')}
 console.log('Teacher parent linking SQL: PASS ('+checks+' checks).');return checks;
};
