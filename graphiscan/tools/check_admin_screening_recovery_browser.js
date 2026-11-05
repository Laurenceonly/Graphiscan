async rootPage => {
 const page=await rootPage.context().newPage(),checks=[],errors=[],queries=[];
 let failList=true,failStudent=false,failImage=false,imageReads=0;
 const result={result_id:'1',student_id:'9',classification:'Normal',predicted_class_score:.8,date_generated:'2026-11-01T08:00:00Z',review:{status:'Validated',expert_id:null,follow_up_needed:false},report:{report_type:'Initial Screening'}};
 const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label)};
 page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/api/v1/**',async route=>{
  const req=route.request(),url=new URL(req.url()),key=url.pathname.split('/').at(-1);
  const send=(data,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
  const fail=message=>send({error:{code:'UNAVAILABLE',message}},503);
  let data=[];
  if(key==='login'||key==='refresh')data={access_token:'fixture',refresh_token:'fixture',expires_in:3600};
  else if(req.method()!=='GET')throw Error('Unexpected write');
  else if(key==='me')data={user_id:'00000000-0000-4000-8000-000000000101',full_name:'Sample Admin',role:'admin',permissions:['assignments.manage','accounts.manage','audit.read'],onboarding:{next_action:'ready'}};
  else if(key==='schools')data=[{school_id:'9',name:'Sample School'}];
  else if(key==='students')data=[{student_id:'9',full_name:'Sample Student',school_id:'9',grade_level:2}];
  else if(key==='screenings'){queries.push(url.search);if(failList)return fail('Sample list unavailable.');data=[result]}
  else if(url.pathname.endsWith('/screenings/1/image')){
   imageReads++;if(failImage)return fail('Sample image unavailable.');
   return route.fulfill({status:200,contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRusAAAAASUVORK5CYII=','base64')});
  }
  else if(url.pathname.endsWith('/screenings/1'))data=result;
  else if(url.pathname.endsWith('/students/9')){if(failStudent)return fail('Sample student unavailable.');data={student_id:'9',full_name:'Sample Student',school_id:'9',grade_level:2}}
  return send({data,page:{next_cursor:null}});
 });
 const go=async name=>{if(await page.getByRole('button',{name:'Open navigation',exact:true}).isVisible())await page.getByRole('button',{name:'Open navigation',exact:true}).click();await page.locator('.sidebar').getByRole('button',{name,exact:true}).click();await page.locator('.sidebar-backdrop').waitFor({state:'hidden'})};
 for(const width of [1440,390]){
  failList=true;
  await page.setViewportSize({width,height:900});await page.goto('http://127.0.0.1:5173/login');await page.getByLabel('Email address',{exact:true}).fill('fixture@example.invalid');await page.getByLabel('Password',{exact:true}).fill('fictional');await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.locator('.hosted-workspace').waitFor();await go('Results');
  const root=page.locator('.hosted-screenings');
  await root.getByRole('button',{name:'Try again',exact:true}).waitFor();failList=false;await root.getByRole('button',{name:'Try again',exact:true}).click();
  await root.getByRole('button',{name:'View result 1',exact:true}).waitFor();check(true,width+': initial list failure has working retry');
  await root.getByRole('combobox',{name:/^Review status/}).selectOption('Validated');await root.getByRole('combobox',{name:/^Grade/}).selectOption('2');await root.getByRole('button',{name:'Apply filters',exact:true}).click();
  await page.waitForTimeout(80);
  check(queries.at(-1).includes('validation_status=Validated')&&queries.at(-1).includes('grade_level=2'),width+': result filters retain server parameters');
  failStudent=true;await root.getByRole('button',{name:'View result 1',exact:true}).click();
  const detail=root.locator('.screening-detail');
  await detail.getByText('Sample student unavailable.',{exact:false}).waitFor();check(await detail.getByRole('button',{name:'Try again',exact:true}).isVisible(),width+': dependent read error remains visible in details');
  failStudent=false;await detail.getByRole('button',{name:'Try again',exact:true}).click();await detail.getByText('Sample Student',{exact:true}).waitFor();
  check(await root.locator('.admin-summary-grid').count()===0,width+': detail hides list summaries');
  failImage=true;await detail.getByRole('button',{name:'View handwriting image',exact:true}).click();await detail.getByText('Sample image unavailable.',{exact:false}).waitFor();
  check(await detail.getByRole('button',{name:'Try again',exact:true}).isVisible(),width+': image failure has visible retry');
  failImage=false;await detail.getByRole('button',{name:'Try again',exact:true}).click();await detail.getByRole('img',{name:'Submitted handwriting sample'}).waitFor();
  const beforeHide=imageReads;await detail.getByRole('button',{name:'Hide handwriting image',exact:true}).click();
  check(await detail.locator('img').count()===0&&imageReads===beforeHide,width+': hide releases image without network request');
  await detail.getByRole('button',{name:'Close details',exact:true}).click();await detail.waitFor({state:'hidden'});
  check(await root.locator('.admin-summary-grid').count()===1,width+': closing details restores overview');
 }
 check(!errors.length,'no browser errors');await page.close();return {checks:checks.length,details:checks};
}
