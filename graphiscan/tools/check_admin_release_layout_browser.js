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
    else if(key==='accounts')data=[{user_id:'teacher-fixture',full_name:'Sample Teacher',email:'teacher@example.invalid',role:'teacher',account_status:'active',revision:1}]; else if(path.endsWith('/accounts/teacher-fixture'))data={user_id:'teacher-fixture',full_name:'Sample Teacher',email:'teacher@example.invalid',role:'teacher',account_status:'active',revision:1,school_ids:['9'],permission_grants:[]};
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
  page.setDefaultTimeout(8000);
  const issues=[];
  const nav=async name=>{
    const open=page.getByRole('button',{name:'Open navigation',exact:true});
    if(await open.isVisible())await open.click();
    await page.locator('.sidebar').getByRole('button',{name,exact:true}).click();
    await page.locator('.sidebar-backdrop').waitFor({state:'hidden'});
  };
  await page.goto('http://127.0.0.1:5173/login');
  await page.getByLabel('Email address',{exact:true}).fill('fixture@example.invalid');
  await page.getByLabel('Password',{exact:true}).fill('fictional');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await page.locator('.hosted-workspace').waitFor();
  async function inspect(label){
    const found=await page.evaluate(()=>{
      const issues=[],content=document.querySelector('.content');
      if(document.documentElement.scrollWidth>innerWidth+1)issues.push('document horizontal overflow');
      if(document.documentElement.scrollHeight>innerHeight+1)issues.push('document vertical overflow');
      const text=content.innerText;if(/[\u00e2\u00c2\ufffd]/.test(text))issues.push('garbled text');
      for(const el of content.querySelectorAll('input,select,textarea')){
        if(!el.getClientRects().length)continue;
        if(!el.labels?.length&&!el.getAttribute('aria-label')&&!el.getAttribute('aria-labelledby'))issues.push('unlabelled '+el.tagName);
      }
      for(const el of content.querySelectorAll('.table-wrapper')){
        if(!el.getClientRects().length||!el.querySelector('tbody tr'))continue;
        if(el.clientHeight<48)issues.push('table viewport too short: '+el.clientHeight);
      }
      const heading=[...content.querySelectorAll('h1,h2')].find(el=>el.getClientRects().length);
      if(heading){const box=heading.getBoundingClientRect();if(box.top<0||box.bottom>innerHeight)issues.push('page title clipped')}
      return issues;
    });
    checks.push(label);if(found.length)issues.push({label,found});
  }
  async function inspectDialog(label){
    const dialog=page.locator('dialog[open], [role="dialog"]').filter({visible:true}).last();
    await dialog.waitFor();
    const result=await dialog.evaluate(el=>{
      const r=el.getBoundingClientRect();return {fits:r.width<=innerWidth-8&&r.height<=innerHeight-8&&r.top>=0&&r.left>=0,focused:el.contains(document.activeElement),overflow:el.scrollWidth>el.clientWidth+1};
    });
    checks.push(label);if(!result.fits||!result.focused||result.overflow)issues.push({label,result});
    await page.keyboard.press('Escape');
    await dialog.waitFor({state:'hidden'});
  }
  for(const [width,height] of [[1920,1080],[1440,900],[1366,768],[1024,768],[768,1024],[390,844],[320,568],[568,320]]){
    await page.setViewportSize({width,height});
    for(const name of ['Dashboard','Users','Students','Schools','Results','Progress','Audit Logs','Settings']){
      await nav(name);
      await inspect(width+'x'+height+' '+name);
      if(name==='Progress'){
        await page.locator('.hosted-progress').getByRole('button',{name:'View progress',exact:true}).first().click();
        await page.locator('.trend-point').first().waitFor();
        await inspect(width+'x'+height+' populated progress');
      }
    }
    await nav('Users');
    await page.getByRole('button',{name:'Add user',exact:true}).click();await inspectDialog(width+' Add user modal');
    await page.locator('.users-directory .account-edit').first().click();await inspectDialog(width+' Edit user modal');
    await nav('Students');await page.getByRole('button',{name:'Add student',exact:true}).click();await inspectDialog(width+' Add student modal');
    await nav('Schools');await page.getByRole('button',{name:'Add school',exact:true}).click();await inspectDialog(width+' Add school modal');
    if(width>=1101){
      await page.locator('.sidebar').getByRole('button',{name:'Logout',exact:true}).click();await inspectDialog(width+' Logout modal');
    }
    await nav('Dashboard');
    await page.screenshot({path:'output/playwright/prepush-dashboard-'+width+'x'+height+'.png'});
  }
  return {checks:checks.length,issues,pageErrors:errors};
}
