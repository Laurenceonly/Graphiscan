// Additive student projection and scope tests in disposable PostgreSQL only.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
module.exports=async({db,root,U,validateRow})=>{
 let checks=0,n=984000;const check=(ok,msg)=>{assert(ok,msg);checks++},q=(sql,args=[])=>db.query(sql,args);
 await db.exec(fs.readFileSync(path.join(root,'graphiscan/db/postgres/025_expert_grade_responsibility.sql'),'utf8'));
 const signature='public.graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)';
 const migration=fs.readFileSync(path.join(root,'graphiscan/db/postgres/028_student_display_names.sql'),'utf8');
 const before=(await q('SELECT pg_get_functiondef($1::regprocedure) body',[signature])).rows[0].body;
 const counts=(await q('SELECT (SELECT count(*) FROM students) students,(SELECT count(*) FROM user_profiles) profiles')).rows[0];
 for(const oldEnd of ['\n','\r\n'])for(const newEnd of ['\n','\r\n']){await db.exec(before.replace(/\r?\n/g,oldEnd));await db.exec(migration.replace(/\r?\n/g,newEnd));check((await q("SELECT strpos(prosrc,'-- student display names028')>0 ok FROM pg_proc WHERE oid=$1::regprocedure",[signature])).rows[0].ok,'LF/CRLF student migration failed');}
 const installed=(await q('SELECT pg_get_functiondef($1::regprocedure) body',[signature])).rows[0].body;
 await db.exec(migration);check((await q('SELECT pg_get_functiondef($1::regprocedure) body',[signature])).rows[0].body===installed,'Student migration rerun changed function');
 check(JSON.stringify((await q('SELECT (SELECT count(*) FROM students) students,(SELECT count(*) FROM user_profiles) profiles')).rows[0])===JSON.stringify(counts),'Migration changed records');
 const flags=(await q(fs.readFileSync(path.join(root,'graphiscan/db/postgres/028_student_display_names_preflight.sql'),'utf8'))).rows[0];for(const [flag,value]of Object.entries(flags))check(value===true,'Student display preflight '+flag);
 const unexpected=before.replace("'teacher_id',s.teacher_id::text,'parent_id',s.parent_id::text,","'changed_teacher_id',s.teacher_id::text,'parent_id',s.parent_id::text,");check(unexpected!==before,'Unexpected reader fixture unchanged');await db.exec(unexpected);let denied=false;try{await db.exec(migration)}catch(error){denied=error.message.includes('unexpected directory reader body');await db.exec('ROLLBACK')}check(denied,'Student migration accepted unknown reader body');await db.exec(installed);
 await db.exec('BEGIN');try{
 const A=U(983001),T=U(983002),O=U(983003),P=U(983004),Q=U(983005),E=U(983006);
 for(const [id,role]of [[A,'admin'],[T,'teacher'],[O,'teacher'],[P,'parent'],[Q,'parent'],[E,'expert']]){await q('INSERT INTO auth.users(id,email,email_confirmed_at) VALUES($1,$2,now())',[id,id+'@fixture.invalid']);await q('INSERT INTO user_profiles(user_id,full_name,role,created_by,must_change_password) VALUES($1,$2,$3,$4,false)',[id,'Display fixture '+role+' '+id.slice(-1),role,A]);}
 await q('UPDATE privacy_agreements SET is_current=false');await q("INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current) VALUES('student-display-fixture','Fictional','Fictional',encode(sha256(convert_to('Fictional','UTF8')),'hex'),$1,now(),now(),true)",[A]);
 for(const id of [A,T,O,P,Q,E])await q("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES($1,'student-display-fixture')",[id]);
 const school=String((await q("INSERT INTO schools(name) VALUES('Fictional Display School') RETURNING school_id")).rows[0].school_id),otherSchool=String((await q("INSERT INTO schools(name) VALUES('Other Display School') RETURNING school_id")).rows[0].school_id);
 for(const id of [T,O,E]){await q('INSERT INTO school_memberships(user_id,school_id,created_by) VALUES($1,$2,$3)',[id,school,A]);await q('INSERT INTO user_school_grades(user_id,school_id,grade_level,created_by) VALUES($1,$2,1,$3)',[id,school,A]);}
 await q("INSERT INTO user_permission_grants(user_id,permission_key,school_id,granted_by) VALUES($1,'assignments.manage',$2,$1)",[A,school]);
 const sessions={};for(const id of [A,T,O,P,Q,E]){sessions[id]=U(n++);await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES($1,$2,clock_timestamp())',[sessions[id],id]);}
 const child=async(teacher,parent,grade=1,whichSchool=school)=>String((await q("INSERT INTO students(full_name,age,school_id,grade_level,teacher_id,parent_id) VALUES('Fictional Display Child',8,$1,$2,$3,$4) RETURNING student_id",[whichSchool,grade,teacher,parent])).rows[0].student_id);
 const own=await child(T,P),unlinked=await child(T,null),other=await child(O,Q),outside=await child(T,Q,2),otherSchoolChild=await child(T,Q,1,otherSchool);
 const read=async(actor=T,id=null,session=sessions[actor])=>(await q('SELECT public.graphiscan_read_directory($1,$2,$3,\'\',NULL,NULL,NULL,NULL,100,$4) r',[actor,session,id?'student':'students',id])).rows[0].r;
 const data=(await read(T,own)).rows[0];check(data.school_name==='Fictional Display School'&&data.parent_name==='Display fixture parent 4','Authorized display names incorrect');check(validateRow('Student',data).ok,'Student schema rejects display fields');
 check(!('email' in data)&&!('classification' in data)&&!('credentials' in data),'Student context exposed unrelated account/screening data');
 check((await read(T,unlinked)).rows[0].parent_name===null,'Unlinked parent name invented');
 for(const id of [other,outside,otherSchoolChild])check((await read(T,id)).rows.length===0,'Teacher display read widened scope');
 check((await read(P,own)).rows[0].parent_name===data.parent_name,'Parent own-child detail missing');check((await read(P,other)).rows.length===0,'Parent saw unrelated student names');
 check((await read(E,own)).rows[0].school_name===data.school_name,'Scoped expert student context missing');check((await read(E,outside)).rows.length===0,'Expert outside-grade display read allowed');
 check((await read(A,own)).rows[0].parent_name===data.parent_name,'Scoped admin student context missing');check((await read(A,otherSchoolChild)).rows.length===0,'Admin display read widened school grant');
 check((await read(T,null)).rows.every(row=>[own,unlinked].includes(row.student_id)&&row.school_name===data.school_name),'Display list changed teacher ownership scope');
 await q("UPDATE schools SET name='Renamed Fictional School' WHERE school_id=$1",[school]);check((await read(T,own)).rows[0].school_name==='Renamed Fictional School','Student read returned stale school name');
 await q('UPDATE students SET parent_id=$1 WHERE student_id=$2',[Q,own]);check((await read(T,own)).rows[0].parent_name==='Display fixture parent 5','Student read returned stale linked parent');check((await read(P,own)).rows.length===0,'Former parent retained student detail');
 check((await read(T,own,U(n++))).code==='AUTHENTICATION_REQUIRED','Display read bypassed current session');
 await q('DELETE FROM privacy_agreement_acceptances WHERE user_id=$1',[T]);check((await read(T,own)).code==='PRIVACY_ACCEPTANCE_REQUIRED','Display read bypassed privacy gate');
 }finally{await db.exec('ROLLBACK')}
 console.log('Student display names SQL: PASS ('+checks+' checks).');return checks;
};
