async page => {
  await page.unrouteAll({behavior:'ignoreErrors'});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  let failing=false,grants=true;
  const rows=[{result_id:'71',student_id:'17',classification:'Normal',date_generated:'2026-10-21',review:{status:'Pending',follow_up_needed:false}},{result_id:'72',student_id:'18',classification:'High Potential',date_generated:'2026-10-20',review:{status:'Validated',follow_up_needed:true}},{result_id:'73',student_id:'18',classification:'Historical category',date_generated:'2026-10-19',review:{status:'Flagged',follow_up_needed:false}}];
  await page.route('**/api/**',async route=>{
    const req=route.request(),url=new URL(req.url());if(!url.pathname.startsWith('/api/'))return route.continue();
    const path=url.pathname.replace('/api/v1','');
    const send=(data,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
    if(req.method()==='OPTIONS')return route.fulfill({status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'}});
    if(path==='/session/login')return send({data:{access_token:'fictional-only',refresh_token:'fictional-only',expires_in:3600}});
    if(path==='/session/logout')return send({data:{}});
    if(path==='/schools' && req.method()==='POST')return send({error:{message:'Synthetic unconfirmed school save'}},503);
    if(path==='/me')return send({data:{full_name:'Synthetic administrator',role:'admin',permissions:grants?['assignments.manage','schools.manage']:[],onboarding:{next_action:'ready'}}});
    if(path==='/students')return send({data:[{student_id:'17',full_name:'Synthetic student A',school_id:'9',grade_level:1},{student_id:'18',full_name:'Synthetic student B',school_id:'9',grade_level:2}],page:{next_cursor:'more-fixture-students'}});
    if(path==='/schools')return send({data:[{school_id:'9',name:'Synthetic school'}],page:{next_cursor:null}});
    if(path==='/screenings')return failing?send({error:{message:'Synthetic load failure'}},503):send({data:rows,page:{next_cursor:'more-fixture-screenings'}});
    throw Error('Unexpected request '+path);
  });
  const checks=[];
  async function nav(key,width){if(width<=1100)await page.getByRole('button',{name:'Open navigation',exact:true}).click();await page.locator('.sidebar').getByRole('button',{name:key,exact:true}).click();await page.locator('.sidebar').evaluate(el=>Promise.all(el.getAnimations().map(a=>a.finished)))}
  try {
    await page.setViewportSize({width:1440,height:1000});await page.goto('http://127.0.0.1:5173/login');
    await page.getByLabel('Email address',{exact:true}).fill('synthetic@example.invalid');await page.getByLabel('Password',{exact:true}).fill('fictional');await page.getByRole('button',{name:'Sign in',exact:true}).click();
    await page.waitForURL('**/workspace');await page.locator('.classification-legend').getByText('Historical category',{exact:true}).waitFor();
    for(const width of [1440,1280,1024,768,390,320]) {
      await page.setViewportSize({width,height:1000});
      const metrics=await page.evaluate(()=>({width:innerWidth,fits:document.documentElement.scrollWidth<=innerWidth,visibleCards:[...document.querySelectorAll('.dashboard-highlight-card')].map(n=>n.querySelector('strong').textContent.trim()),visibleSidebar:getComputedStyle(document.querySelector('.sidebar')).visibility,sidebarBackground:getComputedStyle(document.querySelector('.sidebar')).backgroundColor,topbarVisible:getComputedStyle(document.querySelector('.topbar')).display!=='none',titleSize:getComputedStyle(document.querySelector('.dashboard-toolbar h1')).fontSize,activityPoints:document.querySelectorAll('.workspace-activity-chart circle').length,brandLoaded:document.querySelector('.workspace-brand img').naturalWidth>0}));
      if(!metrics.fits||metrics.visibleCards.join(',')!=='3,2,1,1'||metrics.titleSize!=='28px'||metrics.sidebarBackground!=='rgb(255, 255, 255)'||!metrics.topbarVisible||metrics.activityPoints!==7||!metrics.brandLoaded)throw Error(JSON.stringify(metrics));
      await nav('Students',width);await page.getByRole('button',{name:'View or edit',exact:true}).first().waitFor();
      if([1440,390].includes(width)) {
        await page.screenshot({path:'output/playwright/hosted-students-reference-'+width+'.png',fullPage:true,animations:'disabled'});
        await page.getByRole('button',{name:'Add student',exact:true}).click();
        await page.getByRole('dialog',{name:'Add student',exact:true}).waitFor();
        const modal=await page.getByRole('dialog').evaluate(el=>{const r=el.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:innerWidth,height:innerHeight,focusInside:el.contains(document.activeElement)}});
        if(modal.left<0||modal.right>modal.width||modal.top<0||modal.bottom>modal.height||!modal.focusInside)throw Error('Student modal '+JSON.stringify(modal));
        await page.screenshot({path:'output/playwright/hosted-student-form-reference-'+width+'.png',fullPage:false,animations:'disabled'});
        await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'detached'});
      }
      await nav('Students',width);await page.locator('.directory-nav').getByRole('button',{name:'Schools',exact:true}).click();await page.getByText('Synthetic school',{exact:true}).waitFor();
      if([1440,390].includes(width)) {
        await page.getByRole('button',{name:'Add school',exact:true}).click();await page.getByRole('dialog',{name:'Add school',exact:true}).waitFor();
        await page.getByRole('button',{name:'Cancel',exact:true}).click();await page.getByRole('dialog').waitFor({state:'detached'});
      }
      await nav('Results',width);await page.getByRole('button',{name:'View result 71'}).waitFor();
      if([1440,390].includes(width))await page.screenshot({path:'output/playwright/hosted-screenings-reference-'+width+'.png',fullPage:true,animations:'disabled'});
      if(!await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth))throw Error('Record table page overflow '+width);
      await nav('Dashboard',width);await page.getByRole('heading',{name:'Dashboard',exact:true}).waitFor();
      if([1440,390].includes(width))await page.screenshot({path:'output/playwright/hosted-dashboard-final-'+width+'.png',fullPage:true,animations:'disabled'});
      if(width===1440)await page.screenshot({path:'output/playwright/hosted-dashboard-preview.png',fullPage:false,animations:'disabled'});
      checks.push(metrics);
    }
    failing=true;await page.getByRole('button',{name:'Refresh',exact:true}).click();await page.getByText('Some dashboard information could not be loaded. Refresh to try again.',{exact:true}).waitFor();
    failing=false;await page.getByRole('button',{name:'Refresh',exact:true}).click();await page.getByText('Some dashboard information could not be loaded. Refresh to try again.',{exact:true}).waitFor({state:'detached'});
    await page.setViewportSize({width:1440,height:1000});
    await nav('Students',1440);await page.locator('.directory-nav').getByRole('button',{name:'Schools',exact:true}).click();await page.getByRole('button',{name:'Add school',exact:true}).click();
    await page.getByLabel('School name',{exact:true}).fill('Synthetic uncertain school');
    await page.getByRole('dialog').getByRole('button',{name:'Save',exact:true}).click();
    await page.getByRole('dialog').getByText('Synthetic unconfirmed school save',{exact:true}).waitFor();
    await page.keyboard.press('Escape');
    if(!await page.getByRole('dialog').isVisible())throw Error('Uncertain save dismissed');
    await page.getByRole('dialog').getByRole('button',{name:'Sign out',exact:true}).click();await page.waitForURL('**/login');
    await page.getByLabel('Email address',{exact:true}).fill('synthetic@example.invalid');await page.getByLabel('Password',{exact:true}).fill('fictional');await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.waitForURL('**/workspace');
    await page.locator('.sidebar').getByRole('button',{name:'Logout',exact:true}).click();await page.getByRole('dialog').getByRole('button',{name:'Logout',exact:true}).click();await page.waitForURL('**/login');
    if(errors.length)throw Error(errors.join('\n'));
    return {checks,summaryCounts:true,paginationNotClaimedAsTotals:true,unknownClassificationPreserved:true,navigation:true,studentSchoolModals:true,uncertainSaveProtected:true,modalErrorVisible:true,uncertainSignoutAvailable:true,errorRetry:true,hostedLogout:true,pageErrors:errors};
  } finally {await page.unrouteAll({behavior:'ignoreErrors'});await page.setViewportSize({width:1440,height:900});await page.goto('http://127.0.0.1:5173/login')}
}
