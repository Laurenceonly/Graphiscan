const assert=require('assert/strict');
module.exports=async({db,U,ids,sessions,students,model,validateRow})=>{
  let checks=0;const check=(ok,message)=>{assert(ok,message);checks++};
  const q=(sql,args=[])=>db.query(sql,args);
  await db.exec('SAVEPOINT screening_upload_checks');
  const m=(await q('SELECT * FROM model_registry WHERE model_id=$1',[model])).rows[0];
  const runtime={model_key:m.model_key,model_version:m.model_version,preprocessing_key:m.preprocessing_key,decision_rule:m.decision_rule,artifact_sha256:'a'.repeat(64)};
  const call=async(name,args,writer=true)=>{
    await db.exec('SET LOCAL ROLE '+(writer?'graphiscan_password_writer':'graphiscan_api_reader'));
    const sqls={reserve:'SELECT public.graphiscan_reserve_screening($1,$2,$3::jsonb,$4,$5::jsonb,$6,$7) result',complete:'SELECT public.graphiscan_complete_screening($1,$2,$3,$4::jsonb,$5) result',fail:'SELECT public.graphiscan_fail_screening($1,$2,$3) result',state:'SELECT public.graphiscan_screening_request($1,$2,$3) result',image:'SELECT public.graphiscan_screening_image($1,$2,$3) result',models:'SELECT public.graphiscan_model_catalogue($1,$2,$3,$4) result',cleanup:'SELECT public.graphiscan_screening_cleanup($1,$2,$3) result'};
    const r=(await q(sqls[name],args)).rows[0].result;await db.exec('RESET ROLE');return r;
  };
  const reserve=(key,student=students[2],options={})=>call('reserve',[ids.teacher,sessions.teacher,JSON.stringify({student_id:student,image_sha256:'b'.repeat(64),model_id:null,...options.payload}),key,JSON.stringify(options.runtime??runtime),options.bucket??'fictional-private',U(17100)]);
  const prediction={classification:'Normal',class_scores:{normal:0.4,high_potential:0.6},predicted_class_score:0.4};
  const complete=(key,body=prediction)=>call('complete',[ids.teacher,sessions.teacher,key,JSON.stringify(body),U(17100)]);
  const state=key=>call('state',[ids.teacher,sessions.teacher,key],false);
  const first='fictional-upload-key-0001',second='fictional-upload-key-0002',failed='fictional-upload-key-0003';
  check((await reserve(first,students[1])).code==='NOT_FOUND','Teacher reserved another student');
  check((await reserve(first,students[2],{bucket:'fictional-public'})).code==='STORAGE_UNAVAILABLE','Public bucket accepted');
  check((await reserve(first,students[2],{runtime:{...runtime,model_version:'wrong'}})).code==='MODEL_UNAVAILABLE','Runtime/model mismatch accepted');
  let r=await reserve(first);check(r.state==='reserved','New request not durably reserved');
  check(r.object_key.startsWith('screenings/')&&!r.object_key.includes(ids.teacher),'Object key reveals identity');
  check((await state(first)).data.state==='processing','Reservation status missing');
  check((await reserve(first)).state==='processing','Retry acquired another worker reservation');
  check((await reserve(first,students[2],{payload:{image_sha256:'c'.repeat(64)}})).code==='IDEMPOTENCY_CONFLICT','Changed image reused key');
  check((await reserve(second)).state==='reserved','Independent second request not reserved');
  r=await complete(first);check(r.code===null && !!r.result_id,'First completion failed');
  const result1=r.result_id;
  r=await complete(second);check(r.code===null && r.result_id!==result1,'Second completion failed');
  const reports=(await q('SELECT report_type FROM screening_reports WHERE student_id=$1 ORDER BY report_id',[students[2]])).rows;
  check(reports.length===2&&reports[0].report_type==='Initial Screening'&&reports[1].report_type==='Follow-up Screening','Initial/Follow-up completion order wrong');
  check((await q("SELECT count(*)::integer n FROM screening_reports WHERE student_id=$1 AND report_type='Initial Screening'",[students[2]])).rows[0].n===1,'Duplicate Initial reports');
  check((await complete(first)).result_id===result1,'Completion retry duplicated assessment');
  check((await reserve(first)).result_id===result1,'Completed upload retry duplicated assessment');
  r=await state(first);check(r.data.state==='completed'&&r.data.result_id===result1,'Completed recovery missing');
  {const valid=validateRow('ScreeningRequest',r.data);check(valid.ok,'Request state schema mismatch');}
  check((await call('fail',[ids.teacher,first,'commit_failed'])).state==='completed','Lost commit acknowledgement removed completed request');
  check((await q('SELECT count(*)::integer n FROM storage_cleanup_jobs')).rows[0].n===0,'Completed image queued for deletion');
  r=await call('image',[ids.parent,sessions.parent,result1],false);check(r.code==='NOT_FOUND','Parent accessed Pending image');
  r=await call('image',[ids.teacher,sessions.teacher,result1],false);check(r.storage_path.startsWith('fictional-private/screenings/'),'Authorized image locator missing');
  r=await call('models',[ids.teacher,sessions.teacher,null,25],false);check(r.rows.length>0,'Model catalogue missing');
  {const valid=validateRow('Model',r.rows[0]);check(valid.ok,'Model catalogue/schema mismatch: '+JSON.stringify(valid.errors));}
  check((await reserve(failed)).state==='reserved','Failure case reserve failed');
  check((await call('fail',[ids.teacher,failed,'commit_failed'])).state==='failed','Failure not durable');
  check((await state(failed)).data.state==='failed','Failed recovery missing');
  check((await reserve(failed)).state==='failed','Failed request restarted side effects');
  check((await q('SELECT count(*)::integer n FROM storage_cleanup_jobs')).rows[0].n===1,'Failed upload has no durable cleanup intent');
  await call('fail',[ids.teacher,failed,'upload_failed']);
  check((await q('SELECT count(*)::integer n FROM storage_cleanup_jobs')).rows[0].n===1,'Failure retry duplicated cleanup job');
  r=await call('cleanup',['list',null,null]);check(r.rows.length===1,'Failed object not offered to cleanup worker');
  const cleanupId=r.rows[0].cleanup_id;
  await call('cleanup',['ack',cleanupId,false]);
  check((await call('cleanup',['list',null,null])).rows.length===0,'Failed deletion did not back off');
  check((await q('SELECT attempts FROM storage_cleanup_jobs WHERE cleanup_id=$1',[cleanupId])).rows[0].attempts===1,'Cleanup attempts not recorded');
  await call('cleanup',['ack',cleanupId,true]);
  const expired='fictional-upload-key-expired';await reserve(expired);
  await q("UPDATE screening_upload_jobs SET created_at=now()-interval '30 minutes' WHERE actor_id=$1 AND idempotency_key=$2",[ids.teacher,expired]);
  check((await call('cleanup',['list',null,null])).rows.length===1,'Abandoned work was not reconciled');
  check((await state(expired)).data.error_code==='SCREENING_EXPIRED','Expired request state missing');
  check((await complete(expired)).code==='REQUEST_IN_PROGRESS','Expired worker finalized after cleanup reservation');
  // Confirm all new capabilities are server-only; writer cannot browse private rows.
  for(const table of ['screening_upload_jobs','handwriting_samples','screening_results'])
    check(!(await q("SELECT has_table_privilege('graphiscan_password_writer',$1,'SELECT,INSERT,UPDATE,DELETE') ok",[table])).rows[0].ok,'Writer gained direct table access');
  await db.exec('ROLLBACK TO SAVEPOINT screening_upload_checks; RELEASE SAVEPOINT screening_upload_checks');
  console.log(`Isolated screening upload SQL: PASS (${checks} checks; no provider/model calls).`);
};
