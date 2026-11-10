// Actual final-report functions in disposable PostgreSQL; no hosted records.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
module.exports=async({db,root,U,validateRow})=>{
 let checks=0,n=991000;const q=(sql,args=[])=>db.query(sql,args),check=(ok,msg)=>{assert(ok,msg);checks++};
 await db.exec(fs.readFileSync(path.join(root,'graphiscan/db/postgres/030_final_screening_reports.sql'),'utf8'));
 await db.exec(fs.readFileSync(path.join(root,'graphiscan/db/postgres/031_parent_final_report.sql'),'utf8'));
 for(const [flag,value]of Object.entries((await q(fs.readFileSync(path.join(root,'graphiscan/db/postgres/031_parent_final_report_preflight.sql'),'utf8'))).rows[0]))check(value===true,'Parent final-report preflight '+flag);
 for(const [flag,value]of Object.entries((await q(fs.readFileSync(path.join(root,'graphiscan/db/postgres/030_final_screening_reports_preflight.sql'),'utf8'))).rows[0]))check(value===true,'Final-report preflight '+flag);
 const readSig='public.graphiscan_read_final_report(uuid,uuid,bigint)',writeSig='public.graphiscan_finalize_report(uuid,uuid,bigint,jsonb,text,uuid)',helperSig='public.graphiscan_final_context(uuid,uuid,bigint)';
 for(const sig of [readSig,writeSig,helperSig]){
   check((await q("SELECT prosecdef AND proconfig @> ARRAY['search_path=pg_catalog'] ok FROM pg_proc WHERE oid=$1::regprocedure",[sig])).rows[0].ok,'Unsafe definer');
   for(const role of ['anon','authenticated','service_role','graphiscan_api_reader','graphiscan_password_writer','graphiscan_admin_writer'])
     check((await q('SELECT has_function_privilege($1,$2,\'EXECUTE\') ok',[role,sig])).rows[0].ok===(sig===readSig&&role==='graphiscan_api_reader'||sig===writeSig&&role==='graphiscan_password_writer'),'Wrong capability ACL '+role+' '+sig);
 }
 for(const role of ['anon','authenticated','service_role','graphiscan_api_reader','graphiscan_password_writer','graphiscan_admin_writer'])
   check(!(await q("SELECT has_table_privilege($1,'public.final_screening_reports','SELECT,INSERT,UPDATE,DELETE') ok",[role])).rows[0].ok,'Direct table access '+role);
 for(const role of ['anon','authenticated','service_role','graphiscan_api_reader','graphiscan_password_writer','graphiscan_admin_writer'])
   check(!(await q("SELECT has_function_privilege($1,'public.graphiscan_final_history_read(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)','EXECUTE') ok",[role])).rows[0].ok,'Internal history reader exposed '+role);
 await db.exec('BEGIN');
 try{
 const ids={},sessions={};
 for(const [role,actual]of [['admin','admin'],['teacher','teacher'],['other','teacher'],['parent','parent'],['foreignParent','parent'],['expert','expert'],['foreignExpert','expert']]){
   ids[role]=U(n++);await q('INSERT INTO auth.users(id) VALUES($1)',[ids[role]]);
   await q('INSERT INTO user_profiles(user_id,full_name,role,created_by,must_change_password) VALUES($1,$2,$3,$4,false)',[ids[role],'Final fixture '+role,actual,U(1)]);
 }
 await q('UPDATE privacy_agreements SET is_current=false');
 await q("INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current) VALUES('final-fixture','Fictional','Fictional',encode(sha256(convert_to('Fictional','UTF8')),'hex'),$1,now(),now(),true)",[ids.admin]);
 for(const id of Object.values(ids))await q("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES($1,'final-fixture')",[id]);
 const school=String((await q("INSERT INTO schools(name) VALUES('Final report fixture school') RETURNING school_id")).rows[0].school_id);
 for(const role of ['teacher','other','expert','foreignExpert']){
   await q('INSERT INTO school_memberships(user_id,school_id,created_by) VALUES($1,$2,$3)',[ids[role],school,ids.admin]);
   await q('INSERT INTO user_school_grades(user_id,school_id,grade_level,created_by) VALUES($1,$2,$3,$4)',[ids[role],school,role==='foreignExpert'?2:1,ids.admin]);
 }
 for(const role of Object.keys(ids)){sessions[role]=U(n++);await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES($1,$2,clock_timestamp())',[sessions[role],ids[role]]);}
 const student=String((await q("INSERT INTO students(full_name,school_id,grade_level,teacher_id,parent_id) VALUES('Fictional final child',$1,1,$2,$3) RETURNING student_id",[school,ids.teacher,ids.parent])).rows[0].student_id);
 const model=(await q('SELECT model_id FROM model_registry LIMIT 1')).rows[0].model_id;
 async function screening(kind,status='Validated',expert='expert'){
   const sample=(await q("INSERT INTO handwriting_samples(student_id,teacher_id,storage_path) VALUES($1,$2,'private/final-fixture-do-not-return') RETURNING sample_id",[student,ids.teacher])).rows[0].sample_id;
   const result=String((await q(`INSERT INTO screening_results(sample_id,model_id,task_type,classification,confidence_score,class_probabilities,decision_rule,model_snapshot,provenance)
     VALUES($1,$2,'binary','Normal',0.9,'{"normal":0.9,"high_potential":0.1}','{"kind":"argmax"}',
     '{"model_key":"mobilenetv2","model_version":"fixture","architecture":"Fictional","preprocessing_key":"fixture"}','verified') RETURNING result_id`,[sample,model])).rows[0].result_id);
   await q('INSERT INTO screening_expert_assignments(result_id,assigned_expert_id,assigned_by) VALUES($1,$2,$3)',[result,ids[expert],ids.admin]);
   await q('INSERT INTO expert_validations(result_id,status,expert_id,remarks,validation_date) VALUES($1,$2,$3,$4,$5)',[result,status,status==='Pending'?null:ids[expert],status==='Pending'?null:'Fictional observation',status==='Pending'?null:new Date().toISOString()]);
   await q("INSERT INTO screening_reports(student_id,result_id,report_type,school_context) VALUES($1,$2,$3,jsonb_build_object('school_id',$4::text,'school_name','Fictional','grade_level',1))",[student,result,kind,school]);
   return result;
 }
 const read=async(role)=>(await q('SELECT public.graphiscan_read_final_report($1,$2,$3) result',[ids[role],sessions[role],student])).rows[0].result;
 const body=data=>({summary:'Initial and follow-up observations.',conclusion:'Expert concludes this monitoring period.',next_steps:'Continue classroom support.',history_fingerprint:data.history_fingerprint,expected_revision:data.revision});
 const save=async(role,payload,key='fictional-final-key-0001')=>(await q('SELECT public.graphiscan_finalize_report($1,$2,$3,$4::jsonb,$5,$6) result',[ids[role],sessions[role],student,JSON.stringify(payload),key,U(n++)])).rows[0].result;
 const first=await screening('Initial Screening');let r=await read('expert');
 check(r.code===null&&r.data.can_finalize,'Reviewed Initial with no follow-up could not finalize');
 await db.exec('SAVEPOINT initial_only');
 const initialFinal=await save('expert',body(r.data),'fictional-initial-final-0001');
 check(initialFinal.data.state==='Finalized'&&initialFinal.data.final_report.screenings.length===1,'Initial-only final report failed');
 check((await read('parent')).data.state==='Finalized','Parent could not read Initial-only final report');
 if(validateRow){const v=validateRow('FinalReportState',initialFinal.data);check(v.ok,'Initial-only schema '+JSON.stringify(v.errors));}
 await db.exec('ROLLBACK TO SAVEPOINT initial_only');
 check((await read('parent')).code==='NOT_FOUND','Parent read unpublished conclusion');
 check((await read('other')).code==='NOT_FOUND','Foreign teacher read history');
 const second=await screening('Follow-up Screening','Pending');r=await read('expert');
 check(!r.data.can_finalize,'Pending report finalized');
 check((await save('expert',body(r.data))).code==='FINAL_REPORT_NOT_READY','Write bypassed readiness');
 check((await save('teacher',body(r.data))).code==='FORBIDDEN','Teacher finalized');
 await q("UPDATE expert_validations SET status='Validated',expert_id=$2,remarks='Follow-up observed',validation_date=now() WHERE result_id=$1",[second,ids.expert]);
 await q('UPDATE expert_validations SET follow_up_needed=true WHERE result_id=$1',[second]);
 r=await read('expert');check(!r.data.can_finalize,'Latest requested follow-up allowed finalization');
 check((await save('expert',body(r.data))).code==='FINAL_REPORT_NOT_READY','Follow-up-needed write bypass');
 await q('UPDATE expert_validations SET follow_up_needed=false WHERE result_id=$1',[second]);
 r=await read('expert');check(r.data.can_finalize&&r.data.screenings.length===2,'Reviewed history not ready');
 const draft=body(r.data);const final=await save('expert',draft);
 check(final.code===null&&final.data.state==='Finalized','Finalize failed '+JSON.stringify(final));
 check(final.data.final_report.expert_name==='Final fixture expert','Wrong author');
 check(final.data.final_report.screenings.length===2,'Incomplete final snapshot');
 check(!JSON.stringify(final).includes('private/final-fixture'),'Storage path leaked');
 if(validateRow){const v=validateRow('FinalReportState',final.data);check(v.ok,'Final report/schema '+JSON.stringify(v.errors));}
 const again=await save('expert',draft);check(again.data.final_report.final_report_id===final.data.final_report.final_report_id,'Retry duplicated final report');
 check((await q('SELECT count(*)::int n FROM final_screening_reports WHERE student_id=$1',[student])).rows[0].n===1,'Duplicate snapshot');
 check((await save('expert',{...draft,conclusion:'Changed text'})).code==='IDEMPOTENCY_CONFLICT','Changed retry accepted');
 check((await read('teacher')).data.state==='Finalized','Teacher could not read final report');
 check((await read('parent')).data.state==='Finalized','Linked parent could not read validated final report');
 check((await read('foreignParent')).code==='NOT_FOUND','Foreign parent read final report');
 await q("UPDATE expert_validations SET status='Flagged' WHERE result_id=$1",[second]);
 r=await read('expert');check(r.data.state==='Monitoring'&&r.data.final_report===null,'Review change left final current');
 check((await read('parent')).code==='NOT_FOUND','Flagged history leaked to parent');
 check((await save('expert',draft)).code==='REVISION_CONFLICT','Old retry became current after review change');
 const flagged=await save('expert',body(r.data),'fictional-final-key-0002');
 check(flagged.data.state==='Finalized','Reviewed flagged case could not conclude');
 const parentFlagged=await read('parent');check(parentFlagged.data?.final_report?.screenings.length===2&&parentFlagged.data.final_report.screenings.some(row=>row.review.status==='Flagged'),'Linked parent could not read final report with flagged screening');
 check((await read('foreignParent')).code==='NOT_FOUND','Foreign parent read flagged final report');
 check((await q("SELECT public.graphiscan_read_screenings($1,$2,'screening','{}',NULL,NULL,1,$3,false) result",[ids.parent,sessions.parent,second])).rows[0].result.rows.length===0,'Flagged individual screening exposed');
 await db.exec('SAVEPOINT parent_access');
 await q('UPDATE students SET parent_id=NULL WHERE student_id=$1',[student]);
 check((await read('parent')).code==='NOT_FOUND','Former parent read final report');
 await db.exec('ROLLBACK TO SAVEPOINT parent_access');
 await db.exec('SAVEPOINT parent_privacy');
 await q('DELETE FROM privacy_agreement_acceptances WHERE user_id=$1',[ids.parent]);
 check((await read('parent')).code==='PRIVACY_ACCEPTANCE_REQUIRED','Parent privacy gate bypassed');
 await db.exec('ROLLBACK TO SAVEPOINT parent_privacy');
 await db.exec('SAVEPOINT parent_session');
 await q('DELETE FROM auth.sessions WHERE id=$1',[sessions.parent]);
 check((await read('parent')).code==='AUTHENTICATION_REQUIRED','Parent session gate bypassed');
 await db.exec('ROLLBACK TO SAVEPOINT parent_session');
 const third=await screening('Follow-up Screening');r=await read('expert');
 check(r.data.state==='Monitoring'&&r.data.screenings.length===3,'New follow-up did not reopen monitoring');
 check((await read('parent')).code==='NOT_FOUND','Parent read stale final after new screening');
 check((await save('expert',body(flagged.data),'fictional-final-key-0003')).code==='REVISION_CONFLICT','Stale history fingerprint accepted');
 await q('UPDATE screening_expert_assignments SET assigned_expert_id=$2 WHERE result_id=$1',[third,ids.foreignExpert]);
 check((await read('expert')).data.screenings.length===3,'Per-record assignment overrode current grade responsibility');
 check((await read('foreignExpert')).code==='NOT_FOUND','Expert crossed current grade responsibility');
 await q('UPDATE screening_expert_assignments SET assigned_expert_id=$2 WHERE result_id=$1',[third,ids.expert]);
 await q('UPDATE students SET grade_level=2 WHERE student_id=$1',[student]);
 check((await read('expert')).code==='NOT_FOUND','Changed student grade retained old expert access');
 await q('UPDATE students SET grade_level=1 WHERE student_id=$1',[student]);
 // Exercise the reader limit+1 seam: the final snapshot must include every page.
 for(let i=0;i<99;i++)await screening('Follow-up Screening');r=await read('expert');
 check(r.data.screenings.length===102,'Full history pagination dropped or duplicated screenings');
 check(new Set(r.data.screenings.map(row=>row.result_id)).size===102,'Repeated history seam');
 await q('DELETE FROM privacy_agreement_acceptances WHERE user_id=$1',[ids.expert]);
 check((await read('expert')).code==='PRIVACY_ACCEPTANCE_REQUIRED','Privacy gate bypassed');
 await q('DELETE FROM auth.sessions WHERE id=$1',[sessions.teacher]);
 check((await read('teacher')).code==='AUTHENTICATION_REQUIRED','Revoked session read final report');
 await db.exec('SAVEPOINT immutable');let immutable=false;
 try{await q("UPDATE final_screening_reports SET conclusion='tampered' WHERE student_id=$1",[student])}catch{immutable=true;await db.exec('ROLLBACK TO SAVEPOINT immutable')}
 check(immutable,'Final snapshot mutable');
 }finally{await db.exec('ROLLBACK')}
 console.log(`Isolated final report SQL: PASS (${checks} checks; fictional records only).`);
};
