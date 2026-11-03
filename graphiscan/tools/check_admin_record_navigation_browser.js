async page => {
 const checks=[],errors=[];
 for(const width of [1440,390]){
  const tab=await page.context().newPage();await tab.setViewportSize({width,height:900});
  const reads={accounts:0,'audit-logs':0};let delay=600,permissions=['accounts.manage','audit.read'];
  tab.on('pageerror',e=>errors.push(e.message));
  await tab.route('**/api/v1/**',async route=>{
   const key=new URL(route.request().url()).pathname.split('/').at(-1);let data=[];
   if(key==='login')data={access_token:'fixture-access',refresh_token:'fixture-refresh',expires_in:3600};
   else if(key==='logout')data={};
   else if(route.request().method()!=='GET')throw Error('Unexpected write '+key);
   else if(key==='me')data={user_id:'00000000-0000-4000-8000-000000000101',full_name:'Navigation Review Admin',role:'admin',permissions,onboarding:{next_action:'ready'}};
   else if(key==='00000000-0000-4000-8000-000000000102')data={user_id:key,full_name:'Navigation Review Teacher',email:'teacher@example.invalid',role:'teacher',account_status:'active',school_ids:[],permission_grants:[],revision:1};
   else if(key==='accounts'){
    reads.accounts++;await new Promise(r=>setTimeout(r,delay));
    data=[{user_id:'00000000-0000-4000-8000-000000000102',full_name:'Navigation Review Teacher',email:'teacher@example.invalid',role:'teacher',account_status:'active',revision:1}];
   }else if(key==='audit-logs'){
    reads['audit-logs']++;await new Promise(r=>setTimeout(r,delay));
    data=[{log_id:'1',full_name:'Navigation Review Admin',role:'admin',action:'Fixture activity',created_at:'2026-11-01'}];
   }
   return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({data,page:{next_cursor:null}})});
  });
  const check=(ok,name)=>{if(!ok)throw Error(width+': '+name);checks.push(width+': '+name)};
  const go=async name=>{if(width<=1100)await tab.getByRole('button',{name:'Open navigation',exact:true}).click();await tab.locator('.sidebar').getByRole('button',{name,exact:true}).click()};
  const region=name=>tab.getByRole('region',{name,exact:true});
  await tab.goto('http://127.0.0.1:5173/login');await tab.getByLabel('Email address',{exact:true}).fill('admin@example.invalid');await tab.getByLabel('Password',{exact:true}).fill('FictionalPass1!');await tab.getByRole('button',{name:'Sign in',exact:true}).click();await tab.getByRole('heading',{name:'Dashboard',exact:true}).waitFor();
  await go('Users');await tab.getByRole('status',{name:'Loading users',exact:true}).waitFor();await region('User accounts').waitFor();
  check(reads.accounts===1,'Users loads once on first visit');
  await tab.locator('.hosted-record-filters select').first().selectOption('teacher');await tab.getByRole('button',{name:'Apply filters',exact:true}).click();await region('User accounts').waitFor();
  check(reads.accounts===2,'explicit user filters request records');
  await go('Audit Logs');await tab.getByRole('status',{name:'Loading audit logs',exact:true}).waitFor();await region('Audit activity').waitFor();
  check(reads['audit-logs']===1,'Audit loads once on first visit');
  await go('Users');check(await region('User accounts').isVisible(),'return to Users immediately shows records');
  check(!await tab.getByRole('status',{name:'Loading users',exact:true}).isVisible()&&reads.accounts===2,'return to Users has no skeleton or new request');
  check(await tab.locator('.hosted-record-filters select').first().inputValue()==='teacher','user filters survive section switching');
  await go('Dashboard');await go('Audit Logs');
  check(await region('Audit activity').isVisible()&&reads['audit-logs']===1,'return to Audit immediately shows cached records');
  check(!await tab.getByRole('status',{name:'Loading audit logs',exact:true}).isVisible(),'return to Audit has no skeleton');
  const auditUpdate=tab.waitForResponse(response=>new URL(response.url()).pathname.endsWith('/audit-logs'));
  await tab.locator('.hosted-admin-records').getByRole('button',{name:'Refresh',exact:true}).click();
  check(await region('Audit activity').isVisible(),'audit refresh retains visible records');
  await auditUpdate;
  check(reads['audit-logs']===2,'audit Refresh still requests updated data');
  await go('Users');const userUpdate=tab.waitForResponse(response=>new URL(response.url()).pathname.endsWith('/accounts'));await tab.locator('.hosted-admin-records').getByRole('button',{name:'Refresh',exact:true}).click();
  check(await region('User accounts').isVisible(),'user refresh retains visible records');
  await userUpdate;
  check(reads.accounts===3,'user Refresh still requests updated data');
  await tab.getByRole('button',{name:'Edit',exact:true}).click();await tab.getByRole('heading',{name:'Edit user',exact:true}).waitFor();await tab.getByRole('button',{name:'Close account editor',exact:true}).click();
  check(await region('User accounts').isVisible(),'account editor still opens and closes after caching');
  await go('Audit Logs');await go('Users');check(reads.accounts===3&&reads['audit-logs']===2,'repeated navigation does not refetch either list');
  await tab.screenshot({path:'output/playwright/admin-record-navigation-'+width+'.png',fullPage:false});
  permissions=[];await go('Settings');const profileUpdate=tab.waitForResponse(response=>new URL(response.url()).pathname.endsWith('/me'));await tab.locator('.workspace-account').getByRole('button',{name:'Refresh',exact:true}).click();await profileUpdate;await go('Users');
  await tab.getByText('Account records require account management access.',{exact:true}).waitFor();
  check(!await region('User accounts').isVisible(),'profile permission loss clears cached user records');
  await go('Audit Logs');await tab.getByText('Audit records require audit access.',{exact:true}).waitFor();
  check(!await region('Audit activity').isVisible(),'profile permission loss clears cached audit records');
  check(await tab.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'page fits viewport');
  await tab.close();
 }
 if(errors.length)throw Error(errors.join('\n'));
 return {checkCount:checks.length,checks,pageErrors:errors};
}
