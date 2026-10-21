const assert=require('assert/strict');
module.exports=async({db,U,ids,sessions,results,schools})=>{
  let checks=0;const check=(ok,message)=>{assert(ok,message);checks++};
  const q=(sql,args=[])=>db.query(sql,args);
  await db.exec('SAVEPOINT screening_write_checks');
  const active={...sessions};
  const reviewSig='public.graphiscan_write_review(uuid,uuid,bigint,jsonb,text,uuid)';
  const assignmentSig='public.graphiscan_assign_expert(uuid,uuid,bigint,jsonb,uuid)';
  for(const sig of [reviewSig,assignmentSig]){
    check((await q("SELECT has_function_privilege('graphiscan_password_writer',$1,'EXECUTE') ok",[sig])).rows[0].ok,'Missing writer capability');
    for(const role of ['anon','authenticated','service_role','graphiscan_api_reader'])
      check(!(await q("SELECT has_function_privilege($1,$2,'EXECUTE') ok",[role,sig])).rows[0].ok,'Unexpected mutation grant '+role);
  }
  const mutate=async(role,operation,target,body,key='fictional-review-key-0001')=>{
    await db.exec('SET LOCAL ROLE graphiscan_password_writer');
    const sql=operation==='review'?'SELECT public.graphiscan_write_review($1,$2,$3,$4::jsonb,$5,$6) result':'SELECT public.graphiscan_assign_expert($1,$2,$3,$4::jsonb,$6) result';
    // Assignment has five SQL parameters; bind separately to avoid unused bind slots.
    const out=operation==='review'?await q(sql,[ids[role],active[role],target,JSON.stringify(body),key,U(16100)]):await q('SELECT public.graphiscan_assign_expert($1,$2,$3,$4::jsonb,$5) result',[ids[role],active[role],target,JSON.stringify(body),U(16100)]);
    await db.exec('RESET ROLE');return out.rows[0].result;
  };
  const read=async(role,result)=> (await q("SELECT public.graphiscan_read_screenings($1,$2,'screening','{}',NULL,NULL,1,$3,false) result",[ids[role],active[role],result])).rows[0].result;
  let current=(await read('expert',results[0])).rows[0];
  const body={status:'Validated',remarks:'Fictional human review',expert_recommendation:null,follow_up_needed:false,expected_revision:current.review.revision};
  const before=(await q('SELECT count(*)::integer n FROM expert_review_history WHERE result_id=$1',[results[0]])).rows[0].n;
  let r=await mutate('expert','review',results[0],body);
  check(r.code===null && r.data.status==='Validated','Assigned expert failed to validate');
  check(r.data.expert_id===ids.expert && r.data.provenance==='verified','Reviewer attribution not server-bound');
  check(r.data.revision===body.expected_revision+1,'Review revision not advanced');
  check((await read('parent',results[0])).rows.length===1,'Validation did not release report');
  check((await mutate('expert','review',results[0],body)).code===null,'Same-key review retry failed');
  check((await q('SELECT count(*)::integer n FROM expert_review_history WHERE result_id=$1',[results[0]])).rows[0].n===before+1,'Retry duplicated review history');
  check((await mutate('expert','review',results[0],{...body,remarks:'Changed body'})).code==='IDEMPOTENCY_CONFLICT','Changed review reused key');
  check((await mutate('expert','review',results[0],body,'fictional-review-key-0002')).code==='REVISION_CONFLICT','Stale review overwrote data');
  check((await mutate('teacher','review',results[0],body)).code==='FORBIDDEN','Teacher wrote expert review');
  check((await mutate('expert','review',results[1],body)).code==='NOT_FOUND','Expert reviewed unassigned record');
  current=(await read('expert',results[0])).rows[0];
  r=await mutate('expert','review',results[0],{...body,status:'Flagged',expected_revision:current.review.revision},'fictional-review-key-0003');
  check(r.code===null && (await read('parent',results[0])).rows.length===0,'Flagging did not withdraw parent access');
  check((await mutate('expert','review',results[0],body)).code==='REVISION_CONFLICT','Old completed retry returned a newer review as original');
  await q('INSERT INTO school_memberships(user_id,school_id,created_by) VALUES ($1,$2,$3)',[ids.expert,schools[0],ids.admin]);
  await q("INSERT INTO assignment_eligibilities(actor_id,candidate_id,school_id,assignment_role,granted_by) VALUES ($1,$2,$3,'expert',$4)",[ids.researcher,ids.expert,schools[0],ids.admin]);
  active.expert=U(16101);await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES ($1,$2,clock_timestamp())',[active.expert,ids.expert]);
  current=(await read('researcher',results[1])).rows[0];
  const assignment={assigned_expert_id:ids.expert,expected_revision:current.revision};
  r=await mutate('researcher','assignment',results[1],assignment);
  check(r.code===null && r.data.review.assigned_expert_id===ids.expert,'Eligible assignment failed');
  check(r.data.revision===current.revision+1 && r.data.review.revision===current.review.revision+1,'Assignment did not bump both revisions');
  check(r.data.review.expert_id===current.review.expert_id && r.data.review.status===current.review.status,'Assignment overwrote review authorship/state');
  check((await mutate('researcher','assignment',results[1],assignment)).code==='REVISION_CONFLICT','Stale assignment accepted');
  check((await mutate('researcher','assignment',results[2],{...assignment,expected_revision:1})).code==='NOT_FOUND','Scoped manager assigned another school');
  check((await mutate('admin','assignment',results[1],assignment)).code==='NOT_FOUND','schools.manage granted assignment');
  check((await mutate('researcher','assignment',results[1],{assigned_expert_id:ids.teacher,expected_revision:r.data.revision})).code==='INVALID_ASSIGNMENT','Teacher accepted as expert');
  r=await mutate('researcher','assignment',results[1],{assigned_expert_id:null,expected_revision:r.data.revision});
  check(r.code===null && r.data.review.assigned_expert_id===null,'Unassignment failed');
  check((await read('expert',results[1])).rows.length===0,'Unassigned expert retained record');
  await db.exec('ROLLBACK TO SAVEPOINT screening_write_checks; RELEASE SAVEPOINT screening_write_checks');
  console.log(`Isolated screening write SQL: PASS (${checks} checks; fictional records only).`);
};
