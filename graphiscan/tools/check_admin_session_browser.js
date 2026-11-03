async page => {
  const checks=[],errors=[];
  for(const width of [1440,390]){
    const tab=await page.context().newPage();
    let refreshMode='ok',refreshes=0,logins=0,reads=0,role='admin';
    tab.on('pageerror',error=>errors.push(error.message));
    await tab.setViewportSize({width,height:900});
    await tab.route('**/api/v1/**',async route=>{
      const path=new URL(route.request().url()).pathname;
      let data=[];
      if(path.endsWith('/session/login')){
        logins++;data={access_token:'fixture-access',refresh_token:'fixture-refresh-0',expires_in:3600};
      }else if(path.endsWith('/session/refresh')){
        refreshes++;
        if(refreshMode==='offline')return route.abort('failed');
        if(refreshMode==='slow')await new Promise(resolve=>setTimeout(resolve,900));
        if(refreshMode==='revoked')return route.fulfill({status:401,contentType:'application/json',body:JSON.stringify({error:{code:'INVALID_SESSION',message:'Your session has ended.'}})});
        data={access_token:'fixture-access-'+refreshes,refresh_token:'fixture-refresh-'+refreshes,expires_in:3600};
      }else if(path.endsWith('/session/logout'))data={};
      else if(route.request().method()!=='GET')throw Error('Unexpected application write: '+path);
      else if(path.endsWith('/me')){
        reads++;data={user_id:'00000000-0000-4000-8000-000000000101',full_name:'Session Review Admin',role,permissions:['accounts.manage','audit.read'],onboarding:{next_action:'ready'}};
      }else if(path.endsWith('/schools'))data=[{school_id:'1',name:'Session Review School'}];
      else if(path.endsWith('/students'))data=[{student_id:'1',full_name:'Session Review Student',school_id:'1',grade_level:2}];
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({data,page:{next_cursor:null}})});
    });
    const check=(value,label)=>{if(!value)throw Error(width+': '+label);checks.push(width+': '+label)};
    const welcome=()=>tab.getByRole('heading',{name:'Welcome back',exact:true});
    const dashboard=()=>tab.getByRole('heading',{name:'Dashboard',exact:true});
    const login=async()=>{
      await tab.getByLabel('Email address',{exact:true}).fill('admin@example.invalid');
      await tab.getByLabel('Password',{exact:true}).fill('FictionalPass1!');
      await tab.getByRole('button',{name:'Sign in',exact:true}).click();
      await dashboard().waitFor();await tab.waitForURL('**/workspace');
    };
    await tab.goto('http://127.0.0.1:5173/login');
    await welcome().waitFor();
    await tab.getByLabel('Email address',{exact:true}).fill('unsent@example.invalid');
    await tab.reload();await welcome().waitFor();
    check(await tab.getByLabel('Email address',{exact:true}).inputValue()===''&&logins===0&&refreshes===0,'login refresh stays signed out and resets unsent form');
    await login();
    check(new URL(tab.url()).pathname==='/workspace','login opens dashboard');
    check(await tab.evaluate(()=>Object.keys(sessionStorage).filter(k=>k.startsWith('graphiscan:admin:refresh:')).length)===1,'tab has one saved refresh credential');
    refreshMode='slow';await tab.reload({waitUntil:'domcontentloaded'});
    await tab.getByRole('heading',{name:'Opening your workspace…',exact:true}).waitFor();
    check(!await welcome().isVisible()&&new URL(tab.url()).pathname==='/workspace','restoration waits on dashboard route without login flash');
    await dashboard().waitFor();refreshMode='ok';
    check(logins===1&&refreshes===1&&reads>=2,'reload validates saved session and reloads profile');
    await tab.reload();await dashboard().waitFor();
    check(logins===1&&refreshes===2,'second reload uses rotated session without signing in');
    await tab.goto('http://127.0.0.1:5173/login');await welcome().waitFor();
    const before=refreshes;await tab.reload();await welcome().waitFor();
    check(new URL(tab.url()).pathname==='/login'&&refreshes===before,'direct login-page refresh does not resume saved dashboard');
    await tab.goto('http://127.0.0.1:5173/workspace');await dashboard().waitFor();
    refreshMode='offline';await tab.reload();
    await tab.getByRole('heading',{name:'Your workspace could not be loaded',exact:true}).waitFor();
    check(new URL(tab.url()).pathname==='/workspace'&&!await welcome().isVisible(),'failed restore retains workspace route with retry');
    check(await tab.evaluate(()=>Object.keys(sessionStorage).some(k=>k.startsWith('graphiscan:admin:refresh:'))),'failed restore keeps resumable session');
    await tab.screenshot({path:'output/playwright/admin-session-retry-'+width+'.png',fullPage:false});
    refreshMode='ok';await tab.getByRole('button',{name:'Try again',exact:true}).click();await dashboard().waitFor();
    check(logins===1,'retry recovers without credential entry');
    refreshMode='revoked';await tab.reload();await welcome().waitFor();await tab.waitForURL('**/login');
    check(!await tab.evaluate(()=>Object.keys(sessionStorage).some(k=>k.startsWith('graphiscan:admin:refresh:'))),'revoked session clears saved credential and returns to login');
    refreshMode='ok';await login();
    role='teacher';await tab.reload();await welcome().waitFor();await tab.waitForURL('**/login');
    check(!await tab.evaluate(()=>Object.keys(sessionStorage).some(k=>k.startsWith('graphiscan:admin:refresh:'))),'changed role cannot restore admin workspace');
    role='admin';await login();
    if(width===390)await tab.getByRole('button',{name:'Open navigation',exact:true}).click();
    await tab.locator('.sidebar').getByRole('button',{name:'Logout',exact:true}).click();
    await tab.getByRole('heading',{name:'Log out?',exact:true}).waitFor();
    await tab.locator('.logout-confirm-modal').getByRole('button',{name:'Logout',exact:true}).click();
    await welcome().waitFor();
    await tab.goto('http://127.0.0.1:5173/workspace');await welcome().waitFor();await tab.waitForURL('**/login');
    check(!await tab.evaluate(()=>Object.keys(sessionStorage).some(k=>k.startsWith('graphiscan:admin:refresh:'))),'explicit logout cannot be restored by reloading workspace');
    check(await tab.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'page fits viewport');
    await tab.close();
  }
  if(errors.length)throw Error(errors.join('\n'));
  return {checks,pageErrors:errors};
}
