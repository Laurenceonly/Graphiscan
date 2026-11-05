// Stateful fictional account workflows. No hosted Auth or database mutations.
async rootPage => {
 const page=await rootPage.context().newPage(),checks=[],errors=[],writes=[];
 page.on('pageerror',error=>errors.push(error.message));
 const id=n=>'00000000-0000-4000-8000-'+String(n).padStart(12,'0');
 let rows,uncertain=false,conflict=false,deleteDenied=false;
 function seed(){rows=[{user_id:id(1),full_name:'Sample Admin',role:'admin'},{user_id:id(2),full_name:'Sample Teacher',role:'teacher'},{user_id:id(3),full_name:'Sample Other Admin',role:'admin'}].map(row=>({...row,email:'sample'+row.user_id.slice(-2)+'@example.invalid',account_status:'active',school_ids:[],permission_grants:[],revision:1,created_at:'2026-11-01'}))}
 seed();
 const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label)};
 await page.route('**/api/v1/**',async route=>{
  const req=route.request(),url=new URL(req.url()),path=url.pathname,key=path.split('/').at(-1),body=req.method()==='GET'?null:req.postDataJSON();
  const send=(data,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
  const fail=(status,code,message)=>send({error:{code,message}},status);
  let data=[];
  if(key==='login'||key==='refresh')data={access_token:'sample',refresh_token:'sample',expires_in:3600};
  else if(key==='logout')data={};
  else if(key==='me')data={user_id:id(1),full_name:'Sample Admin',role:'admin',permissions:['accounts.manage','schools.manage','audit.read','permissions.manage','assignments.manage'],onboarding:{next_action:'ready'}};
  else if(key==='schools')data=[{school_id:'9',name:'Sample School'}];
  else if(key==='accounts'&&req.method()==='POST'){
   writes.push({method:req.method(),path,body,key:req.headers()['idempotency-key']});
   const row={user_id:id(4),...body,account_status:'active',revision:1,permission_grants:[],school_ids:body.school_ids,must_change_password:body.role!=='admin'};rows.push(row);
   return send({data:row,credential_delivery:{status:'manual'}});
  }else if(key==='accounts'){
   data=rows.filter(row=>(!url.searchParams.get('account_status')||row.account_status===url.searchParams.get('account_status'))&&(!url.searchParams.get('role')||row.role===url.searchParams.get('role')));
  }else if(path.includes('/account-operations/'))data={state:'pending'};
  else if(key==='temporary-password'&&req.method()==='POST'){
   writes.push({method:req.method(),path,body,key:req.headers()['idempotency-key']});
   if(uncertain)return fail(503,'ACCOUNT_OPERATION_PENDING','Sample operation is pending.');
   data={};
  }else if(path.includes('/accounts/')){
   const row=rows.find(row=>row.user_id===key);
   if(req.method()==='PATCH'){
    writes.push({method:req.method(),path,body});
    if(conflict){conflict=false;return fail(409,'REVISION_CONFLICT','Sample record changed.')}
    if(body.expected_revision!==row.revision)throw Error('Missing current revision');
    Object.assign(row,body,{revision:row.revision+1});data={...row};
   }else if(req.method()==='DELETE'){
    writes.push({method:req.method(),path,body,key:req.headers()['idempotency-key']});
    if(deleteDenied)return fail(409,'ACCOUNT_IN_USE','This account has history and cannot be deleted.');
    rows=rows.filter(item=>item!==row);data={user_id:key,deleted:true};
   }else data={...row};
  }
  return send({data,page:{next_cursor:null}});
 });
 const go=async name=>{
  if(await page.getByRole('button',{name:'Open navigation',exact:true}).isVisible())await page.getByRole('button',{name:'Open navigation',exact:true}).click();
  await page.locator('.sidebar').getByRole('button',{name,exact:true}).click();
  await page.locator('.sidebar-backdrop').waitFor({state:'hidden'});
 };
 const editor=()=>page.getByRole('dialog',{name:'Edit user',exact:true});
 async function edit(name){
  const row=page.locator('.users-directory tbody tr').filter({hasText:name});
  await row.getByRole('button',{name:'Edit',exact:true}).click();await editor().waitFor();return editor();
 }
 async function action(name){await editor().getByRole('button',{name,exact:true}).click();return page.locator('dialog.account-action-dialog[open]')}
 page.setDefaultTimeout(10000);
 for(const width of [1440,390]){
  seed();uncertain=false;conflict=false;deleteDenied=false;
  await page.setViewportSize({width,height:900});await page.goto('http://127.0.0.1:5173/login');
  await page.getByLabel('Email address',{exact:true}).fill('fixture@example.invalid');await page.getByLabel('Password',{exact:true}).fill('fictional');await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.locator('.hosted-workspace').waitFor();await go('Users');
  await page.getByRole('button',{name:'Add user',exact:true}).click();
  let dialog=page.getByRole('dialog',{name:'Add user',exact:true});
  await dialog.getByLabel('Full name',{exact:true}).fill('Sample New Parent');
  await dialog.getByLabel('Login email',{exact:true}).fill('test.parent@graphiscan.com');
  check(await dialog.getByLabel('Login email',{exact:true}).getAttribute('readonly')===null,width+': login email editable');
  check(await dialog.getByRole('combobox',{name:'Give the user their login details',exact:true}).count()===0,width+': email-delivery option absent');
  await dialog.getByRole('combobox',{name:/^Role/}).selectOption('parent');
  await dialog.getByLabel('Temporary password',{exact:true}).fill('FictionalPass1!');
  const before=writes.length;await dialog.getByRole('button',{name:'Create user',exact:true}).click();await dialog.waitFor({state:'hidden'});
  await page.locator('.account-handover').waitFor();
  check(writes.length===before+1&&writes.at(-1).key&&writes.at(-1).body.delivery_method==='manual',width+': creates once with retry key');
  check(await page.locator('.account-handover input[type="password"]').count()===1,width+': handover password starts masked');
  await page.getByRole('button',{name:'Done with these details',exact:true}).click();
  check(await page.locator('.account-handover').count()===0,width+': handover secrets cleared on dismissal');
  dialog=await edit('Sample Teacher');await dialog.getByLabel('Full name',{exact:true}).fill('Sample Teacher Edited');
  await dialog.getByRole('button',{name:'Save changes',exact:true}).click();await dialog.waitFor({state:'hidden'});
  check(rows.find(row=>row.user_id===id(2)).full_name==='Sample Teacher Edited',width+': revision-checked edit');
  dialog=await edit('Sample Teacher Edited');const beforeCancel=writes.length;await dialog.getByLabel('Full name',{exact:true}).fill('Cancelled Draft');await dialog.getByRole('button',{name:'Cancel',exact:true}).click();
  check(writes.length===beforeCancel,width+': Cancel does not write');
  await edit('Sample Teacher Edited');dialog=await action('Disable account');await dialog.getByRole('button',{name:'Disable account',exact:true}).click();await dialog.waitFor({state:'hidden'});
  check(rows.find(row=>row.user_id===id(2)).account_status==='disabled',width+': disable preserves account');
  await page.locator('.hosted-record-filters').getByRole('combobox',{name:/^Status/}).selectOption('disabled');
  await edit('Sample Teacher Edited');dialog=await action('Activate account');await dialog.getByRole('button',{name:'Activate account',exact:true}).click();await dialog.waitFor({state:'hidden'});
  check(rows.find(row=>row.user_id===id(2)).account_status==='active',width+': activate preserves existing record');
  await page.locator('.hosted-record-filters').getByRole('combobox',{name:/^Status/}).selectOption('active');
  await edit('Sample Teacher Edited');dialog=await action('Reset password');
  await dialog.getByLabel('New temporary password',{exact:true}).fill('AnotherPass1!');await dialog.getByLabel('Your current password',{exact:true}).fill('FictionalPass1!');
  await dialog.getByRole('button',{name:'Reset password',exact:true}).click();await dialog.waitFor({state:'hidden'});
  check(writes.at(-1).key&&writes.at(-1).body.expected_revision===4,width+': reset uses current revision and retry key');
  await edit('Sample New Parent');dialog=await action('Delete account');
  await dialog.getByLabel('Type DELETE to confirm',{exact:true}).fill('DELETE');await dialog.getByLabel('Your current password',{exact:true}).fill('FictionalPass1!');
  await dialog.getByRole('button',{name:'Delete account',exact:true}).click();await dialog.waitFor({state:'hidden'});
  check(!rows.some(row=>row.user_id===id(4)),width+': confirmed unused-account deletion');
  await edit('Sample Teacher Edited');dialog=await action('Reset password');uncertain=true;
  await dialog.getByLabel('New temporary password',{exact:true}).fill('AnotherPass1!');await dialog.getByLabel('Your current password',{exact:true}).fill('FictionalPass1!');
  const beforeUncertain=writes.length;await dialog.getByRole('button',{name:'Reset password',exact:true}).click();await dialog.getByRole('button',{name:'Check status',exact:true}).waitFor();
  await page.keyboard.press('Escape');check(await dialog.isVisible(),width+': uncertain write blocks dismissal');
  check(await dialog.getByLabel('Your current password',{exact:true}).inputValue()==='',width+': uncertain failure clears credential input');
  await dialog.getByRole('button',{name:'Check status',exact:true}).click();await dialog.getByText(/This operation is still pending/).waitFor();
  check(writes.length===beforeUncertain+1,width+': status read never replays write');
  await dialog.getByRole('button',{name:'Close',exact:true}).click();await dialog.waitFor({state:'hidden'});uncertain=false;
  await go('Settings');await page.getByLabel('Current password',{exact:true}).fill('FictionalPass1!');
  await page.getByLabel('New password',{exact:true}).fill('AnotherPass1!');
  await page.getByLabel('Confirm new password',{exact:true}).fill('Mismatch1!');
  check(await page.getByRole('button',{name:'Change password',exact:true}).isDisabled(),width+': settings mismatch blocks submit');
  await go('Dashboard');await go('Settings');
  check(await page.getByLabel('New password',{exact:true}).inputValue()==='',width+': leaving settings clears password draft');
 }
 check(!errors.length,'no browser errors');
 await page.close();
 return {checks:checks.length,details:checks,fixtureWrites:writes.length};
}
