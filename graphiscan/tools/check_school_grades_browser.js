async page => {
 const checks=[],errors=[];
 for(const width of [1440,390]){
  const tab=await page.context().newPage();await tab.setViewportSize({width,height:1000});tab.on('pageerror',e=>errors.push(e.message));
  const teacher='00000000-0000-4000-8000-000000000201',parent='00000000-0000-4000-8000-000000000202',expert='00000000-0000-4000-8000-000000000203';
  let slow=false,failGrade2=false,created=null,studentWrites=0,nameReads=0,allowNames=true;
  const queries=[],writes=[],accountFilters=[];
  const baseStudents=[{student_id:'11',full_name:'Grade One Student',grade_level:1,school_id:'1',age:8,teacher_id:teacher,parent_id:parent,revision:1},{student_id:'12',full_name:'Grade One Second Student',grade_level:1,school_id:'1',age:8,teacher_id:null,parent_id:null,revision:1},{student_id:'21',full_name:'Grade Two Student',grade_level:2,school_id:'1',age:9,teacher_id:teacher,parent_id:null,revision:1}];
  await tab.route('**/api/v1/**',async route=>{
   const request=route.request(),url=new URL(request.url()),path=url.pathname,key=path.split('/').at(-1);let data=[],next=null;
   if(key==='login'||key==='refresh')data={access_token:'fixture-access',refresh_token:'fixture-refresh',expires_in:3600};
   else if(key==='logout')data={};
   else if(request.method()==='POST'&&key==='students'){
    const body=request.postDataJSON();writes.push({body,key:request.headers()['idempotency-key']});studentWrites++;
    created={...body,student_id:'22',revision:1};data=created;
   }else if(request.method()!=='GET')throw Error('Unexpected write '+path);
   else if(key==='me')data={user_id:'00000000-0000-4000-8000-000000000101',full_name:'School Grade Review Admin',role:'admin',permissions:['assignments.manage','schools.manage','audit.read',...(allowNames?['accounts.manage']:[])],onboarding:{next_action:'ready'}};
   else if(key==='accounts')accountFilters.push(url.searchParams.get('account_status'));
   else if(key==='schools')data=[{school_id:'1',name:'Grade Review Elementary School'}];
   else if(key==='students'){
    const grade=url.searchParams.get('grade_level'),cursor=url.searchParams.get('cursor');queries.push({resource:'students',school:url.searchParams.get('school_id'),grade,cursor});
    if(slow&&grade)await new Promise(r=>setTimeout(r,grade==='1'?700:grade==='2'?400:20));
    if(failGrade2&&grade==='2')return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{code:'UNAVAILABLE',message:'Fixture grade unavailable'}})});
    const all=[...baseStudents,...(created?[created]:[])];
    if(grade==='1'){data=cursor?[baseStudents[1]]:[baseStudents[0]];next=cursor?null:'grade-one-next';}
    else data=grade?all.filter(s=>String(s.grade_level)===grade):all;
   }else if(path.match(/\/students\/\d+$/))data=[...baseStudents,...(created?[created]:[])].find(s=>s.student_id===key);
   else if(key==='assignment-options')data=[{user_id:teacher,full_name:'Grade Teacher',role:'teacher'}];
   else if(key==='screenings'){
    const grade=url.searchParams.get('grade_level');queries.push({resource:'screenings',school:url.searchParams.get('school_id'),grade,cursor:url.searchParams.get('cursor')});
    if(slow&&grade)await new Promise(r=>setTimeout(r,grade==='1'?700:grade==='2'?400:20));
    data=grade==='3'?[]:[{result_id:grade==='2'?'21':'11',student_id:grade==='2'?'21':'11',classification:'Normal',date_generated:'2026-11-01T08:00:00Z',review:{status:'Pending',assigned_expert_id:expert},report:{report_type:'Initial Screening'}}];
   }else if(path.includes('/accounts/')&&key!== 'accounts'){
    nameReads++;data={user_id:key,full_name:key===teacher?'Grade Teacher':key===parent?'Previous Parent':'Grade Expert',account_status:key===parent?'disabled':'active',role:key===teacher?'teacher':key===parent?'parent':'expert'};
   }
   return route.fulfill({status:request.method()==='POST'&&key==='students'?201:200,contentType:'application/json',body:JSON.stringify({data,page:{next_cursor:next},warnings:[]})});
  });
  const check=(ok,name)=>{if(!ok)throw Error(width+': '+name);checks.push(width+': '+name)};
  const go=async name=>{if(width<=1100)await tab.getByRole('button',{name:'Open navigation',exact:true}).click();await tab.locator('.sidebar').getByRole('button',{name,exact:true}).click()};
  await tab.goto('http://127.0.0.1:5173/login');await tab.getByLabel('Email address',{exact:true}).fill('admin@example.invalid');await tab.getByLabel('Password',{exact:true}).fill('FictionalPass1!');await tab.getByRole('button',{name:'Sign in',exact:true}).click();await tab.getByRole('heading',{name:'Dashboard',exact:true}).waitFor();
  check(accountFilters[0]==='active','Users initially requests active accounts; retired accounts stay behind status filter');
  await go('Schools');await tab.getByRole('button',{name:'View grades',exact:true}).click();
  const school=tab.locator('.school-people');await school.getByRole('heading',{name:'Grade 1 students',exact:true}).waitFor();await school.getByText('Grade Teacher',{exact:true}).waitFor();await school.getByText('Previous Parent (disabled)',{exact:true}).waitFor();
  check(await school.getByRole('button',{name:/^Grade [123]$/,exact:true}).count()===3,'school exposes only Grades1-3');
  check(await school.getByText('Grade One Student',{exact:true}).first().isVisible()&&!await school.getByText('Grade Two Student',{exact:true}).first().isVisible(),'grade1 roster excludes grade2');
  check(await school.getByText('Grade Expert',{exact:true}).isVisible(),'grade screening shows assigned expert');
  check(await school.getByText('Previous Parent (disabled)',{exact:true}).isVisible(),'old linked account status is explicit');
  await school.getByRole('button',{name:'Load more students',exact:true}).click();await school.getByText('Grade One Second Student',{exact:true}).waitFor();
  check(queries.some(q=>q.resource==='students'&&q.school==='1'&&q.grade==='1'&&q.cursor==='grade-one-next'),'pagination keeps school and grade scope');
  await school.getByRole('button',{name:'Grade 2',exact:true}).click();await school.getByText('Grade Two Student',{exact:true}).first().waitFor();
  check(!await school.getByText('Grade One Student',{exact:true}).first().isVisible()&&queries.some(q=>q.resource==='students'&&q.grade==='2'&&!q.cursor),'grade change clears old rows and cursor');
  await school.getByRole('button',{name:'Add student',exact:true}).click();const dialog=tab.locator('dialog.directory-editor');await dialog.waitFor();
  check(await dialog.locator('.directory-fields select').inputValue()==='2','Add student prefills selected grade');
  check(await dialog.getByRole('combobox',{name:/^School/}).inputValue()==='1','Add student prefills selected school');
  await dialog.getByLabel('Student name',{exact:true}).fill('New Grade Two Student');await dialog.getByRole('combobox',{name:/^Teacher/}).selectOption(teacher);await dialog.getByRole('button',{name:'Add student',exact:true}).click();await school.getByText('New Grade Two Student',{exact:true}).waitFor();
  check(studentWrites===1&&writes[0].body.school_id==='1'&&writes[0].body.grade_level===2&&!!writes[0].key,'one student save uses selected school/grade and retry key');
  check(await school.getByRole('button',{name:'Grade 2',exact:true}).getAttribute('aria-pressed')==='true','successful save refreshes same grade');
  await school.getByRole('button',{name:'View student Grade Two Student',exact:true}).click();await dialog.waitFor();check(await dialog.getByLabel('Student name',{exact:true}).inputValue()==='Grade Two Student','grade roster opens existing student editor');await dialog.getByRole('button',{name:'Close dialog',exact:true}).click();
  const refresh=tab.locator('.directory').getByRole('button',{name:'Refresh',exact:true});await refresh.click();await school.getByText('New Grade Two Student',{exact:true}).waitFor();
  check(await school.getByRole('heading',{name:'Grade 2 students',exact:true}).isVisible(),'directory refresh preserves chosen grade');
  check(await tab.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'populated grade roster fits viewport');await tab.screenshot({path:'output/playwright/admin-school-grade-roster-'+width+'.png',fullPage:true});
  failGrade2=true;await school.getByRole('button',{name:'Grade 3',exact:true}).click();await school.getByRole('button',{name:'Grade 2',exact:true}).click();await school.getByRole('button',{name:'Try again',exact:true}).waitFor();failGrade2=false;await school.getByRole('button',{name:'Try again',exact:true}).click();await school.getByText('Grade Two Student',{exact:true}).first().waitFor();check(true,'failed grade read retries current grade');
  slow=true;const oldOne=tab.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/students')&&new URL(r.url()).searchParams.get('grade_level')==='1');await school.getByRole('button',{name:'Grade 1',exact:true}).click();const oldTwo=tab.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/students')&&new URL(r.url()).searchParams.get('grade_level')==='2');await school.getByRole('button',{name:'Grade 2',exact:true}).click();await school.getByRole('button',{name:'Grade 3',exact:true}).click();await school.getByText('No students are available in Grade 3 for this school.',{exact:true}).waitFor();await Promise.all([oldOne,oldTwo]);
  check(!await school.getByText('Grade One Student',{exact:true}).first().isVisible()&&!await school.getByText('Grade Two Student',{exact:true}).first().isVisible(),'late grade responses cannot overwrite latest selection');slow=false;
  check(queries.filter(q=>q.grade).every(q=>q.school==='1'&&['1','2','3'].includes(q.grade)),'all grade reads stay in selected school');
  check(await tab.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'grade page fits viewport');await tab.screenshot({path:'output/playwright/admin-school-grades-'+width+'.png',fullPage:true});
  const oldNameReads=nameReads;allowNames=false;await go('Settings');const meUpdated=tab.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/me'));await tab.locator('.workspace-account').getByRole('button',{name:'Refresh',exact:true}).click();await meUpdated;await go('Schools');
  if(!await school.isVisible())await tab.getByRole('button',{name:'View grades',exact:true}).click();await school.getByRole('button',{name:'Grade 1',exact:true}).click();await school.getByText('Account '+teacher,{exact:true}).waitFor();
  check(nameReads===oldNameReads,'account-name requests require account-management permission');
  await tab.close();
 }
 if(errors.length)throw Error(errors.join('\n'));
 return {checkCount:checks.length,checks,pageErrors:errors};
}
