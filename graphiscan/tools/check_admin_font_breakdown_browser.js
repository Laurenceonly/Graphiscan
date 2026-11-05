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
    else if(key==='screenings')data=Array.from({length:12},(_,i)=>({...record(String(9+i%5),i+1,i%3===0?'High Potential':'Normal'),date_generated:'2026-11-'+String(5-Math.floor(i/2)).padStart(2,'0')+'T08:00:00Z',review:{status:['Pending','Validated','Flagged'][i%3],follow_up_needed:i%3===2}}));
    else if(key==='history'){
      const id=path.split('/').at(-2);
      if(historyDelay)await new Promise(resolve=>setTimeout(resolve,historyDelay));
      if(fail)return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{code:'UNAVAILABLE',message:'Sample history is unavailable.'}})});
      const labels=id==='10'?['Normal','High Potential','High Potential']:id==='11'?[]:id==='12'?['Normal']:id==='13'?['High Potential','Historical label','Normal']:['High Potential','High Potential','Normal','Normal'];
      data=labels.map((label,index)=>record(id,index+1,label));
    }
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({data,page:{next_cursor:null}})});
  });
  await page.addInitScript(()=>{
    window.fontSamples=[];
    const timer=setInterval(()=>{
      const node=document.querySelector('.workspace-brand > span')||document.querySelector('.access-brand');
      if(!node)return;
      const range=document.createRange();range.selectNodeContents(node);
      const cover=document.querySelector('#admin-startup');
      window.fontSamples.push({time:Math.round(performance.now()),visible:!cover||Number(getComputedStyle(cover).opacity)<.99,width:range.getBoundingClientRect().width,font:getComputedStyle(node).fontFamily,loaded:[...document.fonts].filter(face=>face.family.includes('Inter')&&face.status==='loaded').length});
    },40);
    setTimeout(()=>clearInterval(timer),7000);
  });
  let fontDelay=0,fontFailure=false;
  await page.route('**/fonts/InterVariable.woff2',async route=>{
    if(fontDelay)await new Promise(resolve=>setTimeout(resolve,fontDelay));
    if(fontFailure)return route.abort();
    await route.continue();
  });
  const login=async()=>{
    await page.getByLabel('Email address',{exact:true}).fill('fixture@example.invalid');
    await page.getByLabel('Password',{exact:true}).fill('fictional');
    await page.getByRole('button',{name:'Sign in',exact:true}).click();
    await page.locator('.hosted-workspace').waitFor();
    await page.locator('.breakdown-legend-row').first().waitFor();
  };
  await page.setViewportSize({width:1440,height:1000});
  for(const mode of [{name:'normal',delay:0},{name:'slow',delay:900},{name:'late',delay:3300},{name:'unavailable',delay:0,fail:true}]){
    fontDelay=mode.delay;fontFailure=!!mode.fail;
    for(const route of ['login','workspace']){
      await page.goto('http://127.0.0.1:5173/'+route,{waitUntil:'domcontentloaded'});
      await page.waitForFunction(()=>!document.querySelector('#admin-startup'));
      await page.waitForTimeout(mode.delay>2200?1800:300);
      const samples=await page.evaluate(()=>window.fontSamples);
      const visible=samples.filter(sample=>sample.visible);
      const sizes=new Set(visible.map(sample=>sample.width.toFixed(2)));
      check(visible.length>2&&sizes.size===1,mode.name+' '+route+': no visible font-width change');
      check(await page.locator('#app').evaluate(el=>!el.inert),mode.name+' '+route+': controls released');
      const final=visible.at(-1);
      check(mode.delay>2200||mode.fail?!final.font.includes('Inter'):final.font.includes('Inter')&&final.loaded>0,mode.name+' '+route+': final font chosen before reveal');
      if(route==='login')await login();
    }
  }
  fontDelay=0;fontFailure=false;
  await page.goto('http://127.0.0.1:5173/workspace');
  await page.waitForFunction(()=>!document.querySelector('#admin-startup'));
  await page.locator('.breakdown-legend-row').first().waitFor();
  for(const [width,height] of [[1440,1000],[1366,768],[390,844]]){
    await page.setViewportSize({width,height});
    const panel=page.locator('.workspace-breakdown-panel');
    await panel.scrollIntoViewIfNeeded();
    const sizes=await panel.evaluate(el=>{
      const ring=el.querySelector('.classification-ring').getBoundingClientRect(),legend=el.querySelector('.breakdown-legend').getBoundingClientRect(),box=el.getBoundingClientRect();
      return {round:Math.abs(ring.width-ring.height)<1,centered:Math.abs(ring.x+ring.width/2-(box.x+box.width/2))<2,legendBelow:legend.top>=ring.bottom,fit:el.scrollHeight<=el.clientHeight+1};
    });
    check(sizes.round&&sizes.centered&&sizes.legendBelow&&sizes.fit,width+': circle centered with legend below and no clipped panel');
    check(await panel.locator('.classification-ring strong').innerText()==='12',width+': correct total');
    await panel.locator('.breakdown-legend-row').filter({hasText:'Normal'}).click();
    check(await panel.locator('.classification-ring strong').innerText()==='8',width+': legend highlights matching count');
    await panel.locator('.breakdown-legend-row').filter({hasText:'Normal'}).click();
    await page.waitForTimeout(300);
    await page.screenshot({path:'output/playwright/dashboard-circle-'+width+'.png'});
  }
  await page.setViewportSize({width:1440,height:1000});
  await page.evaluate(()=>{document.activeElement?.blur();document.querySelector('.workspace-dashboard-grid').scrollTop=0});
  await page.mouse.move(0,0);
  await page.waitForTimeout(300);
  await page.screenshot({path:'graphiscan/admin-web/src/assets/admin-workspace-preview.png'});
  await page.goto('http://127.0.0.1:5173/login');
  await page.waitForFunction(()=>!document.querySelector('#admin-startup'));
  const image=page.locator('.login-product-preview img');
  check(await image.evaluate(el=>el.complete&&el.naturalWidth===1440&&el.naturalHeight===1000),'login displays the new dashboard capture');
  await page.screenshot({path:'output/playwright/login-latest-dashboard.png'});
  check(errors.length===0,'no uncaught browser errors');
  return {checks:checks.length,details:checks};
}
