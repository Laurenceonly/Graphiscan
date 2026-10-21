// All API calls are synthetic and intercepted. No provider or database I/O.
async page => {
  await page.unrouteAll({behavior:'ignoreErrors'});
  const checks=[],errors=[];let failHistory=false,passwordSaves=0,failAccountUpdate=true,accountUpdateCalls=0;
  page.on('pageerror',e=>errors.push(e.message));
  const result={result_id:'71',student_id:'17',classification:'Normal',date_generated:'2026-10-21T00:00:00Z',report:{report_type:'Initial Screening'},review:{status:'Validated',follow_up_needed:false}};
  await page.route('**/api/**',async route=>{
    const req=route.request(),url=new URL(req.url());if(!url.pathname.startsWith('/api/'))return route.continue();
    const path=url.pathname.replace('/api/v1','');const send=(body,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(body)});
    if(req.method()==='OPTIONS')return route.fulfill({status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'}});
    if(path==='/session/login')return send({data:{access_token:'synthetic-only',refresh_token:'synthetic-only',expires_in:3600}});
    if(path==='/session/logout')return send({data:{}});
    if(path==='/me')return send({data:{user_id:'00000000-0000-4000-8000-000000000001',full_name:'Synthetic Admin',role:'admin',permissions:['assignments.manage','accounts.manage','audit.read'],onboarding:{next_action:'ready'}}});
    if(path==='/accounts')return send({data:url.searchParams.has('cursor')?[{user_id:'00000000-0000-4000-8000-000000000003',full_name:'Synthetic Teacher',email:'teacher@example.invalid',role:'teacher',account_status:'active',revision:1,created_at:'2026-10-20T00:00:00Z'}]:[{user_id:'00000000-0000-4000-8000-000000000001',full_name:'Synthetic Admin User',email:'admin@example.invalid',role:'admin',account_status:'active',revision:1,created_at:'2026-10-21T00:00:00Z'}],page:{next_cursor:url.searchParams.has('cursor')?null:'account-page-2'}});
    if(path==='/accounts/00000000-0000-4000-8000-000000000003'&&req.method()==='PATCH'){
      accountUpdateCalls++;const body=req.postDataJSON();if(body.expected_revision!==1||'temporary_password' in body)throw Error('Unsafe account update payload');
      if(failAccountUpdate){failAccountUpdate=false;return send({error:{code:'SERVICE_UNAVAILABLE',message:'Synthetic temporary failure'}},503)}
      return send({data:{user_id:'00000000-0000-4000-8000-000000000003',full_name:'Synthetic Teacher',role:body.role||'teacher',account_status:body.account_status||'active',revision:2,school_ids:[],permissions:[],permission_grants:[],created_at:'2026-10-20T00:00:00Z',onboarding:{must_change_password:true,required_agreement_version:'fixture',accepted_agreement_version:null,next_action:'change_password'}}});
    }
    if(path==='/audit-logs')return send({data:[{log_id:'21',full_name:'Synthetic Admin User',role:'admin',action:'fictional_account_action',created_at:'2026-10-21T00:00:00Z'}],page:{next_cursor:null}});
    if(path==='/students')return send({data:[{student_id:'17',full_name:'Synthetic student',school_id:'9',grade_level:1}],page:{next_cursor:null}});
    if(path==='/schools')return send({data:[{school_id:'9',name:'Synthetic school'}],page:{next_cursor:null}});
    if(path==='/screenings')return send({data:[result],page:{next_cursor:null}});
    if(path==='/students/17/history')return failHistory?send({error:{message:'Synthetic history failure'}},503):send({data:url.searchParams.has('cursor')?[{...result,result_id:'72',classification:'Historical label'}]:[result],page:{next_cursor:url.searchParams.has('cursor')?null:'synthetic-next'}});
    if(path==='/me/password'){
      const body=req.postDataJSON();if(body.new_password!==body.confirm_password||!body.current_password)throw Error('Invalid password request');passwordSaves++;return send({data:{}});
    }
    throw Error('Unexpected API request '+path);
  });
  const check=(name,value)=>{if(!value)throw Error(name);checks.push(name)};
  async function nav(name,width){if(width<=1100)await page.getByRole('button',{name:'Open navigation',exact:true}).click();await page.locator('.sidebar').getByRole('button',{name,exact:true}).click();await page.locator('.sidebar').evaluate(el=>Promise.all(el.getAnimations().map(a=>a.finished)))}
  const menus=['Dashboard','Users','Students','Results','Progress','Audit Logs','Settings','Logout'];
  const headings={Users:'Users',Students:'Students',Results:'Screening results',Progress:'Student Progress','Audit Logs':'Audit Logs',Settings:'Settings',Dashboard:'Dashboard'};
  try{
    await page.setViewportSize({width:1440,height:1000});await page.goto('http://127.0.0.1:5173/login');
    const loginFont=await page.locator('.admin-signin-intro h1').evaluate(el=>getComputedStyle(el).fontFamily);
    await page.getByLabel('Email address',{exact:true}).fill('synthetic@example.invalid');await page.getByLabel('Password',{exact:true}).fill('fictional');await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.waitForURL('**/workspace');
    check('old menu choices and order',JSON.stringify(await page.locator('.sidebar .nav-link, .sidebar .logout-btn').allTextContents().then(values=>values.map(v=>v.trim())))===JSON.stringify(menus));
    for(const width of [1440,1280,1024,768,390,320]){
      await page.setViewportSize({width,height:1000});
      let headingOrigin=null;
      for(const name of menus.filter(v=>v!=='Logout')){
        await nav(name,width);await page.getByRole('heading',{name:headings[name],exact:true}).waitFor();
        const title=await page.getByRole('heading',{name:headings[name],exact:true}).evaluate(el=>{const box=el.getBoundingClientRect(),style=getComputedStyle(el);return {x:box.x,y:box.y+scrollY,font:style.fontFamily,size:style.fontSize,weight:style.fontWeight}});
        headingOrigin??=title;
        check(name+' heading typography at '+width,title.font===loginFont&&title.size==='28px'&&title.weight==='600');
        if(Math.abs(title.x-headingOrigin.x)>1||Math.abs(title.y-headingOrigin.y)>1)throw Error(name+' heading alignment '+width+': '+JSON.stringify({title,headingOrigin}));
        check(name+' heading alignment at '+width,true);
        check(name+' fits at '+width,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
        if(name==='Users'){
          await page.getByText('Synthetic Admin User',{exact:true}).waitFor();
          await page.getByRole('button',{name:'Load more',exact:true}).click();
          await page.getByText('Synthetic Teacher',{exact:true}).waitFor();
          check('account list pagination at '+width,await page.getByRole('button',{name:'Load more',exact:true}).count()===0);
          if(width===1440){
            const row=page.getByRole('row').filter({hasText:'Synthetic Teacher'});
            await row.getByRole('button',{name:'Edit',exact:true}).click();
            const editor=page.locator('.account-editor');await editor.getByRole('heading',{name:'Edit account'}).waitFor();
            await editor.getByLabel('Role').selectOption('parent');await editor.getByLabel('Status').selectOption('disabled');
            await editor.getByRole('button',{name:'Save changes'}).click();await editor.getByRole('alert').waitFor();
            check('failed account edit retains draft',await editor.getByLabel('Role').inputValue()==='parent'&&await editor.getByLabel('Status').inputValue()==='disabled');
            check('uncertain account write requires reconciliation',await editor.getByRole('button',{name:'Refresh account list'}).isEnabled()&&await editor.getByRole('button',{name:'Close account editor'}).isDisabled());
            await editor.press('Escape');check('uncertain account write cannot be dismissed',await editor.isVisible());
            await editor.getByRole('button',{name:'Refresh account list'}).click();await page.getByRole('status').filter({hasText:'Account list refreshed.'}).waitFor();
            check('account write is not blindly replayed',accountUpdateCalls===1&&await page.locator('.account-editor').isHidden());
          }
        }
        if(name==='Audit Logs')await page.getByText('fictional_account_action',{exact:true}).waitFor();
        if(name==='Progress'){
          await page.getByLabel('Student',{exact:true}).selectOption('17');await page.getByRole('button',{name:'View history',exact:true}).click();await page.getByRole('button',{name:'View history result 71',exact:true}).waitFor();
          await page.getByRole('button',{name:'Load more history',exact:true}).click();await page.getByRole('button',{name:'View history result 72',exact:true}).waitFor();
          check('history pagination at '+width,await page.getByRole('button',{name:'Load more history',exact:true}).count()===0);
        }
        if([1440,390].includes(width)&&['Users','Students','Results','Progress','Audit Logs','Settings'].includes(name))await page.screenshot({path:'output/playwright/hosted-'+name.toLowerCase().replace(' ','-')+'-'+width+'.png',fullPage:true,animations:'disabled'});
      }
    }
    await page.setViewportSize({width:1440,height:1000});await nav('Progress',1440);await page.getByLabel('Student',{exact:true}).selectOption('17');failHistory=true;
    await page.getByRole('button',{name:'View history',exact:true}).click();await page.getByText('Synthetic history failure',{exact:true}).waitFor();
    failHistory=false;await page.getByRole('button',{name:'View history',exact:true}).click();await page.getByRole('button',{name:'View history result 71',exact:true}).waitFor();check('history failure can retry',true);
    await nav('Settings',1440);
    await page.getByLabel('Current password',{exact:true}).fill('FictionalOld!1');await page.getByLabel('New password',{exact:true}).fill('FictionalNext!2');await page.getByLabel('Confirm new password',{exact:true}).fill('FictionalMismatch!3');
    await page.getByText('New passwords do not match.',{exact:true}).waitFor();
    check('password mismatch blocks request',passwordSaves===0&&await page.getByRole('button',{name:'Save password',exact:true}).isDisabled());
    await page.getByRole('button',{name:'Clear',exact:true}).click();
    check('clear removes password draft',await page.locator('.hosted-security input').evaluateAll(nodes=>nodes.every(n=>!n.value)));
    await page.getByLabel('Current password',{exact:true}).fill('FictionalOld!1');await page.getByLabel('New password',{exact:true}).fill('FictionalNext!2');await page.getByLabel('Confirm new password',{exact:true}).fill('FictionalNext!2');await page.getByRole('button',{name:'Save password',exact:true}).click();await page.waitForURL('**/login');
    check('password save requires fresh login',passwordSaves===1&&await page.getByLabel('Password',{exact:true}).inputValue()==='');
    if(errors.length)throw Error(errors.join('\n'));
    return {passed:checks.length,checks,pageErrors:errors};
  }finally{await page.unrouteAll({behavior:'ignoreErrors'});await page.setViewportSize({width:1440,height:900});await page.goto('http://127.0.0.1:5173/login')}
}
