// Fictional browser checks: no real authentication, student records, or writes.
async page => {
  const checks=[],errors=[],reads=[];
  page.on('pageerror',error=>errors.push(error.message));
  const check=(condition,label)=>{if(!condition)throw Error(label);checks.push(label)};
  await page.unrouteAll({behavior:'ignoreErrors'});
  await page.addInitScript(()=>{
    window.motionLog=[];
    const animate=Element.prototype.animate;
    Element.prototype.animate=function(frames,options){
      window.motionLog.push({target:this.className,frames,duration:options?.duration});
      return animate.call(this,frames,options);
    };
  });
  let historyDelay=0,fail=false;
  const students=Array.from({length:30},(_,i)=>({student_id:String(i+9),full_name:'Sample Student '+String(i+1).padStart(2,'0'),grade_level:i%3+1,school_id:'9'}));
  const record=(student,index,label)=>({result_id:student+'-'+index,student_id:student,classification:label,date_generated:'2026-'+String(index+6).padStart(2,'0')+'-15T08:00:00Z',review:{status:'Validated'},report:{report_type:index===1?'Initial Screening':'Follow-up Screening'}});
  await page.route('**/api/v1/**',async route=>{
    const request=route.request(),url=new URL(request.url()),path=url.pathname,key=path.split('/').at(-1);
    reads.push(path);
    let data=[];
    if(['login','refresh'].includes(key))data={access_token:'fictional',refresh_token:'fictional',expires_in:3600};
    else if(key==='logout')data={};
    else if(request.method()!=='GET')throw Error('Unexpected write: '+path);
    else if(key==='me')data={user_id:'00000000-0000-4000-8000-000000000101',full_name:'Sample Admin',role:'admin',permissions:['accounts.manage','schools.manage','assignments.manage','audit.read'],onboarding:{next_action:'ready'}};
    else if(key==='accounts')data=[{user_id:'teacher-fixture',full_name:'Sample Teacher',email:'teacher@example.invalid',role:'teacher',account_status:'active',revision:1}];
    else if(key==='audit-logs')data=[{log_id:'1',full_name:'Sample Admin',role:'admin',action:'Viewed records',created_at:'2026-10-25'}];
    else if(key==='schools')data=[{school_id:'9',name:'Sample School'}];
    else if(key==='students')data=students;
    else if(key==='screenings')data=[record('9',1,'High Potential'),record('9',2,'Normal')];
    else if(key==='history'){
      const id=path.split('/').at(-2);
      if(historyDelay)await new Promise(resolve=>setTimeout(resolve,historyDelay));
      if(fail)return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{code:'UNAVAILABLE',message:'Sample history is unavailable.'}})});
      const labels=id==='10'?['Normal','High Potential','High Potential']:id==='11'?[]:id==='12'?['Normal']:id==='13'?['High Potential','Historical label','Normal']:['High Potential','High Potential','Normal','Normal'];
      data=labels.map((label,index)=>record(id,index+1,label));
    }
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({data,page:{next_cursor:null}})});
  });
  const nav=async name=>{
    if(await page.getByRole('button',{name:'Open navigation',exact:true}).isVisible())await page.getByRole('button',{name:'Open navigation',exact:true}).click();
    await page.locator('.sidebar').getByRole('button',{name,exact:true}).click();
    await page.locator('.sidebar-backdrop').waitFor({state:'hidden'});
  };
  const login=async()=>{
    await page.getByLabel('Email address',{exact:true}).fill('fixture@example.invalid');
    await page.getByLabel('Password',{exact:true}).fill('fictional');
    await page.getByRole('button',{name:'Sign in',exact:true}).click();
    await page.locator('.hosted-workspace').waitFor();
    await page.waitForFunction(()=>!document.querySelector('.dashboard-page .admin-page-skeleton'));
  };
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.setViewportSize({width:1440,height:900});
  await page.goto('http://127.0.0.1:5173/login');
  await page.waitForFunction(()=>!document.querySelector('#admin-startup'));
  check(await page.locator('#app').evaluate(el=>!el.inert),'startup releases login controls');
  check(await page.evaluate(()=>getComputedStyle(document.body).backgroundColor==='rgb(255, 255, 255)'),'startup and login use white canvas');
  await login();
  check(await page.evaluate(()=>window.motionLog.some(item=>item.target==='hosted-admin'&&item.duration===240)),'sign-in fades the new workspace for 240ms');
  for(const name of ['Users','Students','Schools','Results','Progress','Audit Logs','Settings','Dashboard']){
    const before=await page.evaluate(()=>window.motionLog.length);
    await nav(name);
    check(await page.evaluate(before=>window.motionLog.slice(before).some(item=>item.target==='content'&&item.duration===180),before),'page fade: '+name);
    check(await page.evaluate(()=>!document.querySelector('.sidebar').getAnimations().length&&!document.querySelector('.topbar').getAnimations().length),'stationary desktop shell: '+name);
  }
  await page.evaluate(()=>{for(const text of ['Users','Students','Results','Settings','Dashboard'])document.querySelectorAll('.sidebar .nav-link').forEach(button=>{if(button.textContent.trim()===text)button.click()})});
  await page.locator('.content').evaluate(async element=>{await Promise.all(element.getAnimations().map(animation=>animation.finished.catch(()=>{})))});
  check(await page.locator('.content').evaluate(el=>getComputedStyle(el).opacity==='1'&&!el.getAnimations().length),'rapid navigation settles fully visible');
  const root=page.locator('.hosted-progress');
  const pick=async number=>{
    await root.getByRole('searchbox').fill('Sample Student '+String(number).padStart(2,'0'));
    await root.getByRole('button',{name:'View progress',exact:true}).click();
  };
  const geometry=()=>root.evaluate(el=>{
    const box=selector=>{const r=el.querySelector(selector).getBoundingClientRect();return {y:r.y,height:r.height}};
    return {chart:box('.progress-chart-panel'),search:box('.progress-search'),table:box('.table-wrapper')};
  });
  for(const [width,height]of [[1440,900],[1366,768],[390,844]]){
    await page.setViewportSize({width,height});
    await nav('Progress');
    const empty=await geometry();
    historyDelay=500;
    await pick(1);
    await root.getByText('Loading screenings...', {exact:true}).waitFor();
    const loading=await geometry();
    check(JSON.stringify(empty)===JSON.stringify(loading),width+': choosing student does not move chart or list');
    await root.locator('.trend-point').first().waitFor();
    await root.locator('.progress-chart-stage[aria-busy="false"]').waitFor();
    check(JSON.stringify(empty)===JSON.stringify(await geometry()),width+': completed history keeps the same geometry');
    check(await root.locator('.trend-point').count()===4,width+': four actual screenings');
    check(await root.locator('.trend-lines').evaluate(el=>getComputedStyle(el).animationName.startsWith('trend-draw')),width+': chronological line reveal');
    await root.locator('.trend-point').first().focus();
    await root.locator('.trend-tooltip').waitFor();
    check((await root.locator('.trend-tooltip').innerText()).includes('Initial'),width+': keyboard point shows screening details');
    await page.keyboard.press('End');
    check((await root.locator('.trend-point').last().getAttribute('aria-pressed'))==='true',width+': keyboard End selects latest');
    await page.keyboard.press('Escape');
    await root.locator('.trend-tooltip').waitFor({state:'hidden'});
    const beforeSwitch=await geometry();
    await pick(2);
    await root.getByText('Loading screenings...', {exact:true}).waitFor();
    check(await root.locator('.trend-point').count()===0,width+': previous student data clears while loading');
    check(JSON.stringify(beforeSwitch)===JSON.stringify(await geometry()),width+': switching students keeps layout fixed');
    await root.locator('.trend-point').first().waitFor();
    check(await root.locator('.trend-point').count()===3,width+': replacement student series');
    await pick(3);
    await root.getByText('No screenings recorded for this student.',{exact:true}).waitFor();
    check(JSON.stringify(beforeSwitch)===JSON.stringify(await geometry()),width+': empty history keeps chart height');
    historyDelay=0;
    await pick(4);
    await root.locator('.trend-point').waitFor();
    check(await root.locator('.trend-line').count()===0,width+': singleton has no invented trend');
    await pick(5);
    await root.locator('.trend-point.unknown').waitFor();
    check(await root.locator('.trend-line').count()===0,width+': unknown label breaks connecting line');
    fail=true;await pick(6);
    await root.getByRole('button',{name:'Try again',exact:true}).waitFor();
    check(JSON.stringify(beforeSwitch)===JSON.stringify(await geometry()),width+': failed read keeps geometry');
    fail=false;await root.getByRole('button',{name:'Try again',exact:true}).click();
    await root.locator('.trend-point').first().waitFor();
    await root.getByRole('searchbox').fill('');
    const scroll=await root.evaluate(el=>{
      const list=el.querySelector('.table-wrapper'),search=el.querySelector('.progress-search');
      const y=search.getBoundingClientRect().top;list.scrollTop=200;
      return {scrollable:list.scrollHeight>list.clientHeight,fixed:y===search.getBoundingClientRect().top,listHeight:list.clientHeight,overflow:document.documentElement.scrollWidth>innerWidth,chartScroll:el.querySelector('.progress-chart-panel').scrollHeight>el.querySelector('.progress-chart-panel').clientHeight+1};
    });
    check(scroll.scrollable&&scroll.fixed&&scroll.listHeight>90&&!scroll.overflow&&!scroll.chartScroll,width+': only student list scrolls, usable table height');
    await pick(1);await root.locator('.trend-point').first().waitFor();
    await root.locator('.trend-point').nth(2).focus();
    await page.waitForTimeout(320); await page.screenshot({path:'output/playwright/admin-motion-progress-'+width+'.png'});
    await nav('Dashboard');
  }
  await page.setViewportSize({width:1440,height:900});
  await nav('Progress');
  historyDelay=650;
  await pick(1);await root.getByText('Loading screenings...', {exact:true}).waitFor();
  await pick(2);await root.locator('.trend-point').first().waitFor();
  await page.waitForTimeout(700);
  check(await root.locator('.trend-point').count()===3,'rapid student changes ignore late prior response');
  historyDelay=0;
  const beforeDialog=await page.evaluate(()=>window.motionLog.length);
  await page.locator('.sidebar').getByRole('button',{name:'Logout',exact:true}).click();
  await page.getByRole('dialog').waitFor();
  check(await page.evaluate(before=>window.motionLog.slice(before).some(item=>String(item.target).includes('modal-backdrop')&&item.duration===240),beforeDialog),'dialog uses shared reveal');
  check(await page.getByRole('dialog').evaluate(el=>el.contains(document.activeElement)),'dialog receives focus immediately');
  await page.keyboard.press('Escape');
  await page.getByRole('dialog').waitFor({state:'hidden'});
  check(await page.locator('.sidebar').getByRole('button',{name:'Logout',exact:true}).evaluate(el=>el===document.activeElement),'dialog restores opener focus');
  await page.emulateMedia({reducedMotion:'reduce'});
  const beforeReduced=await page.evaluate(()=>window.motionLog.length);
  await nav('Settings');await nav('Progress');await pick(1);await root.locator('.trend-point').first().waitFor();
  check(await page.evaluate(before=>window.motionLog.length===before,beforeReduced),'reduced-motion navigation has no fade');
  check(await root.locator('.trend-lines').evaluate(el=>getComputedStyle(el).animationName==='none'),'reduced-motion chart has no reveal');
  await page.locator('.sidebar').getByRole('button',{name:'Logout',exact:true}).click();
  await page.getByRole('dialog').getByRole('button',{name:'Logout',exact:true}).click();
  await page.getByRole('button',{name:'Sign in',exact:true}).waitFor();
  check(await page.locator('.hosted-workspace').count()===0,'logout removes workspace without retaining old data');
  await page.emulateMedia({reducedMotion:'no-preference'});
  await login();
  await nav('Progress');await pick(1);await root.locator('.trend-point').first().waitFor();
  await root.getByRole('searchbox').fill('');
  await page.setViewportSize({width:1920,height:992});
  await page.bringToFront();
  check(errors.length===0,'no browser errors');
  return {checks:checks.length,details:checks};
}
