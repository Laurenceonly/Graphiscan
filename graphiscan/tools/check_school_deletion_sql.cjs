const fs=require('fs'),path=require('path'),assert=require('assert/strict');
module.exports=async({db,root})=>{
 let checks=0,n=941000;const U=n=>`00000000-0000-4000-8000-${String(n).padStart(12,'0')}`;
 const check=(ok,message)=>{assert(ok,message);checks++},q=(s,p=[])=>db.query(s,p);
 await db.exec(fs.readFileSync(path.join(root,'graphiscan/db/postgres/026_school_deletion.sql'),'utf8'));
 const signature='public.graphiscan_school_deletion(uuid,uuid,text,bigint,jsonb,text,uuid)';
 for(const role of ['anon','authenticated','service_role','graphiscan_api_reader','graphiscan_admin_writer'])check(!(await q("SELECT has_function_privilege($1,$2,'EXECUTE') ok",[role,signature])).rows[0].ok,'Unauthorized execute '+role);
 check((await q("SELECT has_function_privilege('graphiscan_password_writer',$1,'EXECUTE') ok",[signature])).rows[0].ok,'Missing writer capability');
 await db.exec('BEGIN');try{
 const A=U(940001),T=U(940002),E=U(940003),R=U(940004),B=U(940005);
 for(const [id,role]of [[A,'admin'],[T,'teacher'],[E,'expert'],[R,'researcher'],[B,'admin']]){
 await q('INSERT INTO auth.users(id,email,email_confirmed_at) VALUES($1,$2,now())',[id,id+'@example.invalid']);
 await q('INSERT INTO user_profiles(user_id,full_name,role,created_by,must_change_password) VALUES($1,$2,$3,$4,false)',[id,'Fictional '+role,role,A]);}
 await q('UPDATE privacy_agreements SET is_current=false');
 await q("INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current) VALUES('delete-school-fixture','Fictional','Fictional',encode(sha256(convert_to('Fictional','UTF8')),'hex'),$1,now(),now(),true)",[A]);
 for(const id of [A,T,E,R,B])await q("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES($1,'delete-school-fixture')",[id]);
 for(const id of [A,R])await q("INSERT INTO user_permission_grants(user_id,permission_key,granted_by) VALUES($1,'schools.manage',$2)",[id,A]);
 const sessions={};for(const id of [A,T,E,R,B]){sessions[id]=U(n++);await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES($1,$2,clock_timestamp())',[sessions[id],id]);}
 const school=String((await q("INSERT INTO schools(name) VALUES('Fictional deletion school') RETURNING school_id")).rows[0].school_id);
 const call=async(actor=A,op='schools.delete_check',body={},session=sessions[actor])=>(await q('SELECT public.graphiscan_school_deletion($1,$2,$3,$4,$5::jsonb,NULL,$6) r',[actor,session,op,school,JSON.stringify(body),U(n++)])).rows[0].r;
 check((await call()).data.can_delete,'Unused school not deletable');
 for(const actor of [T,E,R,B])check((await call(actor)).code==='FORBIDDEN','Role/scope permitted '+actor);
 check((await call(A,'schools.delete_check',{},U(n++))).code==='AUTHENTICATION_REQUIRED','Missing session permitted');
 const body={expected_revision:1,confirmation:'DELETE'};
 check((await call(A,'schools.delete',{...body,expected_revision:2})).code==='REVISION_CONFLICT','Stale revision permitted');
 for(const bad of [{},{...body,confirmation:'yes'},{...body,cascade:true}])check((await call(A,'schools.delete',bad)).code==='INVALID_INPUT','Invalid deletion accepted');
 for(const id of [T,E])await q('INSERT INTO school_memberships(user_id,school_id,created_by) VALUES($1,$2,$3)',[id,school,A]);
 await q("INSERT INTO students(full_name,school_id,grade_level,teacher_id) VALUES('Fictional student',$1,1,$2)",[school,T]);
 let info=(await call()).data;check(info.students===1&&info.teachers===1&&info.experts===1&&!info.can_delete,'Linked counts incorrect');
 check((await call(A,'schools.delete',body)).code==='SCHOOL_IN_USE','Linked school deleted');
 await q('DELETE FROM students WHERE school_id=$1',[school]);await q('DELETE FROM school_memberships WHERE school_id=$1',[school]);
 await db.exec('CREATE TABLE public.school_delete_extra(school_id bigint REFERENCES public.schools(school_id) ON DELETE CASCADE)');
 await q('INSERT INTO school_delete_extra VALUES($1)',[school]);
 check(!(await call()).data.can_delete,'Future cascading reference ignored');
 check((await call(A,'schools.delete',body)).code==='SCHOOL_IN_USE','Future cascading reference deleted');await q('DELETE FROM school_delete_extra');
 await db.exec('SAVEPOINT audit_failure');
 await db.exec("CREATE FUNCTION public.reject_school_delete_audit() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.action='schools.delete' THEN RAISE EXCEPTION 'Fixture audit unavailable'; END IF; RETURN NEW; END $$; CREATE TRIGGER reject_school_delete_audit BEFORE INSERT ON audit_logs FOR EACH ROW EXECUTE FUNCTION public.reject_school_delete_audit();");
 let failed=false;try{await call(A,'schools.delete',body)}catch{failed=true}await db.exec('ROLLBACK TO audit_failure');check(failed,'Audit failure not surfaced');
 check((await call()).data.can_delete,'Audit failure removed school');
 check((await call(A,'schools.delete',body)).data.deleted,'Unused school deletion failed');
 check((await call()).code==='NOT_FOUND','Deleted school still readable');
 check((await q("SELECT count(*)::int n FROM audit_logs WHERE action='schools.delete' AND resource_id=$1",[school])).rows[0].n===1,'Deletion audit missing/duplicated');
 console.log(`School deletion SQL: ${checks} checks pass; disposable database only.`);
 }finally{await db.exec('ROLLBACK')}
};
