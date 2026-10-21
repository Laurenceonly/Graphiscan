// Playwright CLI run-code fixture. Every API request is intercepted; no provider I/O.
async page => {
  const checks=[];let patches=[], conflict=false, listFailed=false, grants=true, optionPage=0;
  await page.unrouteAll({behavior:'ignoreErrors'});
  const expert='11111111-1111-4111-8111-111111111111';
  let record={result_id:'41',student_id:'17',revision:1,classification:'Normal',predicted_class_score:0.8,date_generated:'2026-10-20T00:00:00Z',report:{report_type:'Follow-up Screening'},model:{model_key:'fictional',model_version:'v1'},review:{status:'Validated',assigned_expert_id:null,expert_id:'historical-reviewer',remarks:'Fictional review',expert_recommendation:'Fictional recommendation',follow_up_needed:false}};
  const check=(name,value)=>{if(!value)throw Error(name);checks.push(name)};
  await page.route('**/api/**',async route=>{
    const request=route.request(),url=new URL(request.url()),path=url.pathname.replace('/api/v1','');
    if(!url.pathname.startsWith('/api/'))return route.continue();
    const send=(data,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
    if(request.method()==='OPTIONS')return route.fulfill({status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'}});
    if(path==='/session/login')return send({data:{access_token:'fictional-access',refresh_token:'fictional-refresh',expires_in:3600}});
    if(path==='/session/logout')return send({data:{}});
    if(path==='/me')return send({data:{full_name:'Fictional Admin',role:'admin',permissions:grants?['assignments.manage']:[],onboarding:{next_action:'ready'}}});
    if(path==='/schools'||path==='/students')return send({data:[],page:{next_cursor:null}});
    if(path==='/screenings'){
      if(listFailed)return send({error:{message:'Fictional list failure'}},503);
      return send({data:url.searchParams.has('cursor')?[]:[record],page:{next_cursor:url.searchParams.has('cursor')?null:'fictional-next'}});
    }
    if(path==='/screenings/41')return send({data:record});
    if(path==='/students/17')return send({data:{student_id:'17',full_name:'Fictional Student',school_id:'9',grade_level:2}});
    if(path==='/schools/9/assignment-options'){
      optionPage++;
      return send({data:url.searchParams.has('cursor')?[{user_id:expert,full_name:'Fictional Expert',role:'expert'}]:[{user_id:'parent-id',full_name:'Fictional Parent',role:'parent'}],page:{next_cursor:url.searchParams.has('cursor')?null:'choices-next'}});
    }
    if(path==='/screenings/41/expert-assignment'){
      patches.push(request.postDataJSON());
      if(conflict)return send({error:{code:'REVISION_CONFLICT',message:'Fictional revision conflict'}},409);
      record={...record,revision:record.revision+1,review:{...record.review,assigned_expert_id:patches.at(-1).assigned_expert_id}};
      return send({data:record});
    }
    if(path==='/screenings/41/image')return route.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aB1kAAAAASUVORK5CYII=','base64')});
    throw Error('Unexpected API route '+path);
  });
  await page.goto('http://127.0.0.1:5173/access');
  for(const [label,value] of [['Email address','fixture@example.invalid'],['Password','fictional-browser-only']]){
    const input=page.getByLabel(label,{exact:true});
    await input.click();await input.press('ControlOrMeta+A');await input.press('Backspace');await page.keyboard.insertText(value);
  }
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await page.getByRole('button',{name:'View result 41'}).waitFor();
  check('ready admin renders results',await page.getByText('Follow-up Screening',{exact:false}).count()>0);
  await page.getByRole('button',{name:'Load more results',exact:true}).click();
  await page.getByRole('button',{name:'Load more results',exact:true}).waitFor({state:'detached'});
  check('result pagination retains records and consumes cursor',await page.getByRole('button',{name:'View result 41'}).count()===1);
  await page.getByRole('button',{name:'View result 41'}).click();
  await page.getByRole('button',{name:'Load more eligible people'}).waitFor();
  check('non-experts excluded',await page.locator('.assignment-form option').filter({hasText:'Fictional Parent'}).count()===0);
  await page.getByRole('button',{name:'Load more eligible people'}).click();
  await page.getByLabel('Assigned expert',{exact:true}).selectOption(expert);
  await page.getByRole('button',{name:'Save expert assignment'}).click();
  await page.getByText('Expert assignment saved.',{exact:true}).waitFor();
  check('assignment uses screening revision and UUID',patches.length===1&&patches[0].expected_revision===1&&patches[0].assigned_expert_id===expert);
  check('review authorship preserved',await page.getByText('historical-reviewer',{exact:true}).isVisible());
  await page.getByRole('button',{name:'View handwriting image'}).click();
  await page.locator('.screening-image').waitFor();
  check('image uses local blob', (await page.locator('.screening-image').getAttribute('src')).startsWith('blob:'));
  conflict=true;
  await page.getByLabel('Assigned expert',{exact:true}).selectOption('');
  await page.getByRole('button',{name:'Save expert assignment'}).click();
  await page.getByText('Fictional revision conflict',{exact:true}).waitFor();
  check('conflict freezes save without replay',await page.getByRole('button',{name:'Save expert assignment'}).isDisabled()&&patches.length===2);
  await page.getByRole('button',{name:'Reload details'}).click();
  await page.getByRole('button',{name:'Load more eligible people'}).waitFor();
  check('reload clears stale image',await page.locator('.screening-image').count()===0);
  await page.setViewportSize({width:1440,height:1000});
  await page.screenshot({path:'output/playwright/hosted-admin-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  check('narrow layout fits',await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  await page.screenshot({path:'output/playwright/hosted-admin-mobile.png',fullPage:true});
  listFailed=true;
  await page.getByRole('button',{name:'Refresh results'}).click();
  await page.getByText('Fictional list failure',{exact:true}).waitFor();
  check('load failure is shown',await page.getByRole('alert').count()===1);
  grants=false;
  await page.getByRole('button',{name:'Refresh account',exact:true}).click();
  await page.getByText('Screening records require permission',{exact:false}).waitFor();
  check('permission loss hides detail and assignment',await page.locator('.screening-detail').count()===0);
  await page.getByRole('button',{name:'Sign out',exact:true}).click();
  await page.getByRole('button',{name:'Sign in',exact:true}).waitFor();
  check('signout clears results',await page.locator('.hosted-screenings').count()===0);
  return {passed:checks.length,checks,assignmentRequests:patches.length,optionPages:optionPage};
}
