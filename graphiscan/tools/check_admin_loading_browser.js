async page => {
 const checks=[],errors=[];
 for(const width of [1440,390]){
  const tab=await page.context().newPage();await tab.setViewportSize({width,height:1000});
  tab.on('pageerror',e=>errors.push(e.message));
  const held=new Set(['schools','students','screenings','accounts','audit-logs']),pending=new Map();let failAccounts=false,holdRefresh=false;
  const release=key=>{held.delete(key);for(const done of pending.get(key)||[])done();pending.delete(key)};
  await tab.route('**/api/v1/**',async route=>{
   const url=new URL(route.request().url()),key=url.pathname.split('/').at(-1);
   if(held.has(key)||key==='refresh'&&holdRefresh)await new Promise(resolve=>{pending.set(key,[...(pending.get(key)||[]),resolve])});
   let data=[];
   if(key==='login'||key==='refresh')data={access_token:'fixture-access',refresh_token:'fixture-refresh',expires_in:3600};
   else if(key==='logout')data={};
   else if(route.request().method()!=='GET')throw Error('Unexpected write '+url.pathname);
   else if(key==='me')data={user_id:'00000000-0000-4000-8000-000000000101',full_name:'Loading Review Admin',role:'admin',permissions:['accounts.manage','audit.read','assignments.manage','schools.manage'],onboarding:{next_action:'ready'}};
   else if(key==='schools')data=[{school_id:'1',name:'Loading Review School'}];
   else if(key==='students')data=[{student_id:'1',full_name:'Loading Review Student',school_id:'1',grade_level:2}];
   else if(key==='screenings')data=[{result_id:'1',student_id:'1',classification:'Normal',predicted_class_score:.8,date_generated:'2026-11-01T08:00:00Z',review:{status:'Pending'},report:{report_type:'Initial Screening'}}];
   else if(key==='accounts'){
    if(failAccounts)return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{message:'Fixture read unavailable',code:'UNAVAILABLE'}})});
    data=[{user_id:'00000000-0000-4000-8000-000000000102',full_name:'Loading Review Teacher',email:'teacher@example.invalid',role:'teacher',account_status:'active',revision:1}];
   }else if(key==='audit-logs')data=[{log_id:'1',full_name:'Loading Review Admin',role:'admin',action:'Fixture activity',created_at:'2026-11-01'}];
   return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({data,page:{next_cursor:null}})});
  });
  const check=(ok,name)=>{if(!ok)throw Error(width+': '+name);checks.push(width+': '+name)};
  const go=async name=>{
   if(width<=1100)await tab.getByRole('button',{name:'Open navigation',exact:true}).click();
   await tab.locator('.sidebar').getByRole('button',{name,exact:true}).click();
  };
  const loading=async(label,blockedControl)=>{
   await tab.getByRole('status',{name:label,exact:true}).waitFor();
   check(!await tab.getByRole('heading',{name:blockedControl,exact:true}).isVisible(),'whole '+blockedControl+' heading is placeholder');
   check(width<=1100?await tab.getByRole('button',{name:'Open navigation',exact:true}).isVisible():await tab.locator('.sidebar').isVisible(),blockedControl+' retains navigation');
   check(await tab.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),blockedControl+' loading fits viewport');
  };
  await tab.goto('http://127.0.0.1:5173/login');
  await tab.getByLabel('Email address',{exact:true}).fill('admin@example.invalid');await tab.getByLabel('Password',{exact:true}).fill('FictionalPass1!');
  await tab.getByRole('button',{name:'Sign in',exact:true}).click();await tab.locator('.hosted-workspace').waitFor();
  await loading('Loading dashboard','Dashboard');
  check(!await tab.getByRole('region',{name:'Loaded record counts',exact:true}).isVisible(),'dashboard summary is also placeholder');
  await tab.screenshot({path:'output/playwright/admin-whole-loading-dashboard-'+width+'.png',fullPage:false});
  await go('Students');await loading('Loading students','Students');check(!await tab.getByLabel('Search students',{exact:true}).isVisible(),'student filters hidden during first read');
  await go('Schools');await loading('Loading schools','Schools');
  await go('Progress');await loading('Loading progress','Student Progress');
  await go('Settings');await tab.getByRole('heading',{name:'Settings',exact:true}).waitFor();
  check(await tab.locator('.workspace-account .admin-page-skeleton').count()===0,'Settings has no artificial page skeleton');
  await go('Users');await loading('Loading users','Users');check(!await tab.getByLabel('Search users',{exact:true}).isVisible(),'user filters hidden during first read');
  await go('Audit Logs');await loading('Loading audit logs','Audit Logs');
  await go('Results');await loading('Loading screening results','Screening results');
  release('schools');release('students');release('screenings');release('accounts');release('audit-logs');
  await tab.getByRole('heading',{name:'Screening results',exact:true}).waitFor();
  check(await tab.getByRole('region',{name:'Screening records',exact:true}).isVisible(),'results resolve to records');
  held.add('screenings');await tab.locator('.hosted-screenings').getByRole('button',{name:'Refresh',exact:true}).click();
  check(await tab.getByRole('region',{name:'Screening records',exact:true}).isVisible()&&!await tab.getByRole('status',{name:'Loading screening results',exact:true}).isVisible(),'later refresh retains result content');release('screenings');
  await go('Users');await tab.getByRole('heading',{name:'Users',exact:true}).waitFor();
  held.add('accounts');await tab.locator('.hosted-admin-records').getByRole('button',{name:'Refresh',exact:true}).click();
  check(await tab.getByRole('region',{name:'User accounts',exact:true}).isVisible()&&!await tab.getByRole('status',{name:'Loading users',exact:true}).isVisible(),'later user refresh retains content');release('accounts');
  await go('Dashboard');await tab.getByRole('heading',{name:'Dashboard',exact:true}).waitFor();
  check(await tab.locator('.modern-admin-dashboard .admin-page-skeleton').count()===0,'dashboard reveals all ready content');
  let before;
  if(width>1100)before=await tab.locator('.sidebar .workspace-brand').evaluate(el=>{const r=el.getBoundingClientRect(),i=el.querySelector('img').getBoundingClientRect(),s=getComputedStyle(el);return {x:r.x,y:r.y,width:r.width,height:r.height,imgWidth:i.width,imgHeight:i.height,font:s.fontSize,weight:s.fontWeight,gap:s.gap}});
  holdRefresh=true;await tab.reload({waitUntil:'domcontentloaded'});await tab.locator('.admin-restore-skeleton').waitFor();await tab.locator('#admin-startup').waitFor({state:'detached'});
  if(width>1100){
   const after=await tab.locator('.restore-rail .workspace-brand').evaluate(el=>{const r=el.getBoundingClientRect(),i=el.querySelector('img').getBoundingClientRect(),s=getComputedStyle(el);return {x:r.x,y:r.y,width:r.width,height:r.height,imgWidth:i.width,imgHeight:i.height,font:s.fontSize,weight:s.fontWeight,gap:s.gap}});
   check(JSON.stringify(before)===JSON.stringify(after),'refresh logo and text have exact same geometry as real sidebar');
   check(await tab.locator('.restore-rail').evaluate(el=>el.getBoundingClientRect().width)===240,'refresh sidebar matches 240px workspace');
  }else check(!await tab.locator('.restore-rail').isVisible(),'mobile refresh has no mismatched sidebar logo');
  await tab.screenshot({path:'output/playwright/admin-matched-brand-'+width+'.png',fullPage:false});
  holdRefresh=false;release('refresh');await tab.locator('.hosted-workspace').waitFor();await tab.getByRole('heading',{name:'Dashboard',exact:true}).waitFor();
  await go('Settings');failAccounts=true;await go('Users');await tab.locator('.hosted-admin-records:visible').getByRole('button',{name:'Refresh',exact:true}).click();await tab.getByRole('button',{name:'Try again',exact:true}).waitFor();
  check(!await tab.getByRole('status',{name:'Loading users',exact:true}).isVisible(),'failed initial read ends skeleton and shows retry');
  failAccounts=false;await tab.getByRole('button',{name:'Try again',exact:true}).click();await tab.getByRole('region',{name:'User accounts',exact:true}).waitFor();
  check(await tab.getByRole('region',{name:'User accounts',exact:true}).isVisible(),'initial error retry recovers records');
  await tab.emulateMedia({reducedMotion:'reduce'});held.add('accounts');await tab.reload();await tab.getByRole('heading',{name:'Dashboard',exact:true}).waitFor();await go('Users');await tab.getByRole('status',{name:'Loading users',exact:true}).waitFor();
  check(await tab.locator('.hosted-admin-records:visible .shape').first().evaluate(el=>getComputedStyle(el).animationName)==='none','reduced motion disables page skeleton pulse');release('accounts');
  await tab.close();
 }
 if(errors.length)throw Error(errors.join('\n'));
 return {checkCount:checks.length,checks,pageErrors:errors};
}
