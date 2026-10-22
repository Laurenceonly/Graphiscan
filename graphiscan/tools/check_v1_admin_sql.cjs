// Runs only in check_api_contract's disposable PostgreSQL; never connects to Auth.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
module.exports=async({db,root,U,validateRow})=>{
  let checks=0;
  const check=(ok,message)=>{assert(ok,message);checks++;};
  const q=(sql,args=[])=>db.query(sql,args);
  const read=name=>fs.readFileSync(path.join(root,'graphiscan/db/postgres',name+'.sql'),'utf8');
  await db.exec(`ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS email_confirmed_at timestamptz;
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS banned_until timestamptz;
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS deleted_at timestamptz;
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS raw_app_meta_data jsonb DEFAULT '{}';`);
  for(const file of ['015_privacy_test_audience','016_admin_reads','017_account_management',
    '018_account_issuance','019_admin_account_lifecycle','020_assignment_access'])await db.exec(read(file));
  // Reproduce the actual hosted leftover Supabase default privileges.
  await db.exec('GRANT TRUNCATE, REFERENCES, TRIGGER ON assignment_eligibilities TO anon, authenticated, service_role');
  check((await q(read('020_assignment_access_preflight'))).rows[0].assignment_table_protected===false,
    'Preflight missed leftover non-DML table privileges');
  await db.exec(read('021_assignment_table_privileges'));
  for(const file of ['017_account_management_preflight','018_account_issuance_preflight','019_admin_account_lifecycle_preflight','020_assignment_access_preflight']){
    const row=(await q(read(file))).rows[0];
    for(const [key,value]of Object.entries(row))check(value===true,file+': '+key);
  }
  await db.exec('BEGIN');
  try{
    const A=U(41001),R=U(41002),T=U(41003),B=U(41004),X=U(41005),Y=U(41006),request=U(41999);
    for(const [id,role]of [[A,'admin'],[R,'researcher'],[T,'teacher'],[B,'admin'],[Y,'teacher']]){
      await q('INSERT INTO auth.users(id,email,email_confirmed_at) VALUES($1,$2,clock_timestamp())',[id,id+'@example.invalid']);
      await q('INSERT INTO user_profiles(user_id,full_name,role,created_by,must_change_password) VALUES($1,$2,$3,$4,false)',[id,'Fictional '+role,role,A]);
    }
    const school=String((await q("INSERT INTO schools(name) VALUES('Admin checks fictional school') RETURNING school_id")).rows[0].school_id);
    await q('UPDATE privacy_agreements SET is_current=false');
    await q(`INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current)
      VALUES('admin-checks','Fictional','Fictional',encode(sha256(convert_to('Fictional','UTF8')),'hex'),$1,now(),now(),true)`,[A]);
    for(const id of [A,R,T,B,Y])await q("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES($1,'admin-checks')",[id]);
    for(const id of [A,R])await q("INSERT INTO user_permission_grants(user_id,permission_key,granted_by) VALUES($1,'accounts.manage',$2)",[id,A]);
    await q("INSERT INTO user_permission_grants(user_id,permission_key,granted_by) VALUES($1,'permissions.manage',$1)",[A]);
    await q("INSERT INTO user_permission_grants(user_id,permission_key,school_id,granted_by) VALUES($1,'assignments.manage',$2,$1)",[A,school]);
    let next=42000;const sessions={};
    async function fresh(id){const s=U(next++);await q('INSERT INTO auth.sessions(id,user_id,created_at) VALUES($1,$2,clock_timestamp())',[s,id]);sessions[id]=s;return s;}
    for(const id of [A,R,T,B,Y])await fresh(id);
    async function call(role,sql,args){
      await db.exec('SET LOCAL ROLE '+role);
      const result=(await q(sql,args)).rows[0].result;
      await db.exec('RESET ROLE');return result;
    }
    const writer=(sql,args)=>call('graphiscan_admin_writer',sql,args);
    const reader=(sql,args)=>call('graphiscan_api_reader',sql,args);
    const revision=async id=>Number((await q('SELECT revision FROM user_profiles WHERE user_id=$1',[id])).rows[0].revision);
    const detail=(actor,target,session=sessions[actor])=>reader('SELECT graphiscan_get_admin_account($1,$2,$3) result',[actor,session,target]);
    const update=async(actor,target,body)=>writer('SELECT graphiscan_update_account($1,$2,$3,$4::jsonb,$5) result',
      [actor,sessions[actor],target,JSON.stringify({expected_revision:await revision(target),...body}),request]);
    check((await detail(A,T)).data.user_id===T,'Authorized account detail unavailable');
    check((await detail(T,A)).code==='FORBIDDEN','Teacher read account details');
    check((await detail(A,T,U(49990))).code==='AUTHENTICATION_REQUIRED','Missing session read account details');
    check((await detail(A,U(49991))).code==='NOT_FOUND','Unknown account fabricated');
    check((await update(R,B,{full_name:'Changed protected account'})).code==='FORBIDDEN','Researcher edited protected admin');
    check((await update(A,A,{account_status:'disabled'})).code==='FORBIDDEN','Actor disabled self');
    check((await update(R,T,{permission_grants:[{permission_key:'assignments.manage',school_id:school}]})).code==='FORBIDDEN','Account grant implied permission management');
    check((await update(A,T,{permission_grants:[{permission_key:'assignments.manage',school_id:null}]})).code==='FORBIDDEN','Scoped grant ceiling widened');
    check((await update(A,T,{permission_grants:[{permission_key:'accounts.manage',school_id:school}]})).code==='INVALID_INPUT','Global-only grant accepted school scope');
    const stale=await revision(T),oldSession=sessions[T];
    const edited=await update(A,T,{full_name:'Fictional renamed teacher',school_ids:[school]});
    check(edited.code===null&&edited.data.school_ids.join()===school,'Account name/membership update failed');
    check((await detail(A,T)).data.full_name==='Fictional renamed teacher','Account details not refreshed');
    check((await q('SELECT count(*)::int n FROM app_session_revocations WHERE session_id=$1',[oldSession])).rows[0].n===1,'Membership update did not revoke target session');
    const staleWrite=await writer('SELECT graphiscan_update_account($1,$2,$3,$4::jsonb,$5) result',[A,sessions[A],T,JSON.stringify({expected_revision:stale,full_name:'Stale'}),request]);
    check(staleWrite.code==='REVISION_CONFLICT','Stale editor overwrote account');

    const operation=U(43001),email='admin-check-issued@example.invalid';
    const fields={full_name:'Fictional issued teacher',email,role:'teacher',school_ids:[school]};
    const begin=(actor,key,body=fields)=>writer('SELECT graphiscan_begin_account_issuance($1,$2,$3,$4::jsonb) result',[actor,sessions[actor],key,JSON.stringify(body)]);
    const finish=(key,target)=>writer('SELECT graphiscan_complete_account_issuance($1,$2,$3,$4,$5) result',[A,sessions[A],key,target,request]);
    await fresh(T);
    check((await begin(T,operation)).code==='FORBIDDEN','Teacher issued account');
    check((await begin(R,operation,{...fields,role:'admin'})).code==='FORBIDDEN','Researcher issued protected role');
    check((await begin(A,operation)).reserved===true,'Issuance reservation failed');
    check((await begin(A,operation)).code==='ACCOUNT_CREATION_PENDING','Pending issuance may replay provider call');
    check((await begin(A,operation,{...fields,full_name:'Changed'})).code==='ISSUANCE_CONFLICT','Changed issuance payload accepted');
    check((await begin(A,U(43002))).code==='EMAIL_UNAVAILABLE','Duplicate email reservation accepted');
    await q('INSERT INTO auth.users(id,email,email_confirmed_at) VALUES($1,$2,clock_timestamp())',[X,email]);
    check((await finish(operation,X)).code==='ISSUANCE_CONFLICT','Unmarked provider identity was attached');
    await q('UPDATE auth.users SET raw_app_meta_data=$2::jsonb WHERE id=$1',[X,JSON.stringify({graphiscan_issuance_id:operation})]);
    const created=await finish(operation,X);
    check(created.code===null&&created.data.must_change_password===true,'Issued user not forced through first password gate');
    check((await q('SELECT count(*)::int n FROM school_memberships WHERE user_id=$1',[X])).rows[0].n===1,'Initial school membership missing');
    check((await q('SELECT count(*)::int n FROM user_permission_grants WHERE user_id=$1',[X])).rows[0].n===0,'Issuance granted implicit permissions');
    check((await begin(A,operation)).data.user_id===X,'Completed issuance replay lost receipt');
    check((await q('SELECT count(*)::int n FROM user_profiles WHERE user_id=$1',[X])).rows[0].n===1,'Issuance duplicated profile');

    const start=async(actor,key,target,action,rev)=>writer('SELECT graphiscan_begin_admin_account_operation($1,$2,$3,$4,$5,$6,$7) result',[actor,sessions[actor],key,target,action,rev??await revision(target),request]);
    const complete=(actor,key)=>writer('SELECT graphiscan_complete_admin_account_operation($1,$2,$3,$4) result',[actor,sessions[actor],key,request]);
    const status=(actor,key)=>reader('SELECT graphiscan_read_admin_account_operation($1,$2,$3) result',[actor,sessions[actor],key]);
    const reset=U(44001),yRevision=await revision(Y);
    check((await start(A,U(44000),A,'reset_password')).code==='FORBIDDEN','Self credential operation accepted');
    check((await start(R,U(44000),B,'reset_password')).code==='FORBIDDEN','Researcher reset protected account');
    check((await start(A,reset,Y,'reset_password',yRevision)).reserved===true,'Reset reservation failed');
    check((await detail(A,Y)).data.credential_update_pending===true,'Pending reset did not block account');
    check((await start(A,reset,Y,'reset_password',yRevision)).code==='ACCOUNT_OPERATION_PENDING','Pending reset may repeat provider write');
    check((await update(A,Y,{full_name:'Unsafe pending edit'})).code==='ACCOUNT_OPERATION_PENDING','Pending credentials allowed ordinary account edit');
    check((await status(A,reset)).data.state==='pending','Pending operation status missing');
    check((await status(R,reset)).code==='NOT_FOUND','Another issuer read private operation');
    check((await complete(A,reset)).data.must_change_password===true,'Reset completion omitted forced password change');
    check((await detail(A,Y)).data.credential_update_pending===false,'Completed reset gate remained set');
    check((await complete(A,reset)).data.user_id===Y,'Completed reset receipt not replayable');
    check((await status(A,reset)).data.state==='completed','Completed operation status missing');
    check((await start(A,U(44002),Y,'delete')).code==='ACCOUNT_IN_USE','Account with session/consent history deleted');
    check((await start(A,U(44003),X,'delete')).code==='ACCOUNT_IN_USE','Account with membership deleted');
    check((await update(A,X,{school_ids:[]})).code===null,'Unused account membership removal failed');
    const removal=U(44004);
    check((await start(A,removal,X,'delete')).reserved===true,'Unused account delete reservation failed');
    check((await complete(A,removal)).code==='ACCOUNT_OPERATION_PENDING','Delete completed before provider removal');
    // Simulate provider hard-delete in this disposable fixture, then reconcile.
    await q('DELETE FROM auth.users WHERE id=$1',[X]);
    check((await complete(A,removal)).data.deleted===true,'Unused account deletion did not complete');
    check((await complete(A,removal)).data.deleted===true,'Deleted account receipt lost');
    check((await q('SELECT target_id FROM account_issuance_requests WHERE operation_id=$1',[operation])).rows[0].target_id===null,'Issuance FK prevented unused deletion');
    check((await detail(A,X)).code==='NOT_FOUND','Deleted profile survived provider removal');
    const audit=(await q("SELECT count(*)::int n FROM audit_logs WHERE resource_id=$1 AND action LIKE 'accounts.delete.%'",[X])).rows[0].n;
    check(audit===2,'Deletion start/completion audit lost');
    await require('./check_v1_assignment_access_sql.cjs')({db,U,A,R,T,B,school,sessions,fresh,revision,reader,writer,validateRow});
  }finally{await db.exec('ROLLBACK');}
  console.log(`Isolated account administration SQL: PASS (${checks} checks; simulated Auth only).`);
};
