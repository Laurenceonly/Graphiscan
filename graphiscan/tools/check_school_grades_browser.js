async page => {
 const checks=[],errors=[];
 for(const [width,height] of [[1440,900],[1366,768],[390,844]]){
  const tab=await page.context().newPage();await tab.setViewportSize({width,height});tab.on('pageerror',e=>errors.push(e.message));
  const teacher='00000000-0000-4000-8000-000000000201',parent='00000000-0000-4000-8000-000000000202',expert='00000000-0000-4000-8000-000000000203';
  let slow=false,failGrade2=false,created=null,studentWrites=0,nameReads=0,allowNames=true;
  const queries=[],writes=[],accountFilters=[],historyReads=[],historyOwners={};
  const baseStudents=[{student_id:'11',full_name:'Grade One Student',grade_level:1,school_id:'1',age:8,teacher_id:teacher,parent_id:parent,revision:1},{student_id:'12',full_name:'Grade One Second Student',grade_level:1,school_id:'1',age:8,teacher_id:null,parent_id:null,revision:1},{student_id:'21',full_name:'Grade Two Student',grade_level:2,school_id:'1',age:9,teacher_id:teacher,parent_id:null,revision:1}];
  await tab.route('**/api/v1/**',async route=>{
   const request=route.request(),url=new URL(request.url()),path=url.pathname,key=path.split('/').at(-1);let data=[],next=null;
   if(key==='login'||key==='refresh')data={access_token:'fixture-access',refresh_token:'fixture-refresh',expires_in:3600};
   else if(key==='logout')data={};
   else if(request.method()==='POST'&&key==='students'){
    const body=request.postDataJSON();writes.push({body,key:request.headers()['idempotency-key']});studentWrites++;
    created={...body,student_id:'22',revision:1};data=created;
   }else if(request.method()==='PATCH'&&path.match(/\/students\/\d+$/)){
    const body=request.postDataJSON(),current=[...baseStudents,...(created?[created]:[])].find(s=>s.student_id===key);if(body.expected_revision!==current.revision)throw Error('Missing current revision');Object.assign(current,body,{revision:current.revision+1});data={...current};studentWrites++;writes.push({body});
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
   else if(key==='assignment-options'){
    const grade=url.searchParams.get('grade_level');queries.push({resource:'grade-assignments',school:path.split('/').at(-2),grade,cursor:url.searchParams.get('cursor')});
    if(slow&&grade)await new Promise(r=>setTimeout(r,grade==='1'?700:grade==='2'?400:20));
    data=grade==='3'?[]:[{user_id:teacher,full_name:'Grade Teacher',role:'teacher'},{user_id:expert,full_name:'Grade Expert',role:'expert'},{user_id:expert,full_name:'Grade Expert',role:'expert'},{user_id:'00000000-0000-4000-8000-000000000204',full_name:'Second Grade Expert',role:'expert'}];
   }
   else if(key==='history'){const id=path.split('/').at(-2),cursor=url.searchParams.get('cursor'),resultId=cursor?'102':'101';historyOwners[resultId]=id;historyReads.push({id,cursor});data=[{result_id:resultId,student_id:id,classification:'Normal',date_generated:'2026-11-01T08:00:00Z',review:{status:cursor?'Pending':'Validated',expert_id:cursor?null:expert,assigned_expert_id:'00000000-0000-4000-8000-000000000204',follow_up_needed:false},report:{report_type:cursor?'Follow-up Screening':'Initial Screening'}}];next=cursor?null:'student-history-next';}
   else if(path.match(/\/screenings\/\d+$/))data={result_id:key,student_id:historyOwners[key]||'11',classification:'Normal',date_generated:'2026-11-01T08:00:00Z',review:{status:key==='102'?'Pending':'Validated',expert_id:key==='102'?null:expert,assigned_expert_id:'00000000-0000-4000-8000-000000000204'},report:{report_type:key==='102'?'Follow-up Screening':'Initial Screening'}};
   else if(key==='screenings'){
    const grade=url.searchParams.get('grade_level');queries.push({resource:'screenings',school:url.searchParams.get('school_id'),grade,cursor:url.searchParams.get('cursor')});
    if(slow&&grade)await new Promise(r=>setTimeout(r,grade==='1'?700:grade==='2'?400:20));
    data=grade==='3'?[]:[{result_id:grade==='2'?'21':'11',student_id:grade==='2'?'21':'11',classification:'Normal',date_generated:'2026-11-01T08:00:00Z',review:{status:'Pending',assigned_expert_id:expert},report:{report_type:'Initial Screening'}},{result_id:'90',student_id:'11',review:{assigned_expert_id:expert}},{result_id:'91',student_id:'11',review:{assigned_expert_id:'00000000-0000-4000-8000-000000000204'}}];
   }else if(path.includes('/accounts/')&&key!== 'accounts'){
    nameReads++;data={user_id:key,full_name:key===teacher?'Grade Teacher':key===parent?'Previous Parent':key===expert?'Grade Expert':'Second Grade Expert',account_status:key===parent?'disabled':'active',role:key===teacher?'teacher':key===parent?'parent':'expert'};
   }
   return route.fulfill({status:request.method()==='POST'&&key==='students'?201:200,contentType:'application/json',body:JSON.stringify({data,page:{next_cursor:next},warnings:[]})});
  });
  const check=(ok,name)=>{if(!ok)throw Error(width+': '+name);checks.push(width+': '+name)};
  const go=async name=>{if(width<=1100)await tab.getByRole('button',{name:'Open navigation',exact:true}).click();await tab.locator('.sidebar').getByRole('button',{name,exact:true}).click()};
  await tab.goto('http://127.0.0.1:5173/login');await tab.getByLabel('Email address',{exact:true}).fill('admin@example.invalid');await tab.getByLabel('Password',{exact:true}).fill('FictionalPass1!');await tab.getByRole('button',{name:'Sign in',exact:true}).click();await tab.getByRole('heading',{name:'Dashboard',exact:true}).waitFor();
  check(accountFilters[0]==='active','Users initially requests active accounts; retired accounts stay behind status filter');
  await go('Schools');await tab.getByRole('button',{name:'View',exact:true}).click();
  const school=tab.locator('.school-people');await school.getByRole('heading',{name:'Grade 1 students',exact:true}).waitFor();await school.getByText('Grade Teacher',{exact:true}).waitFor();await school.getByText('Previous Parent (disabled)',{exact:true}).waitFor();
  check(await school.getByRole('button',{name:/^Grade [123]$/,exact:true}).count()===3,'school exposes only Grades1-3');
  check(await school.getByText('Grade One Student',{exact:true}).first().isVisible()&&!await school.getByText('Grade Two Student',{exact:true}).first().isVisible(),'grade1 roster excludes grade2');
  check(await school.getByText('Grade Expert',{exact:true}).isVisible(),'grade screening shows assigned expert');
  check(await school.locator('.school-staff').getByText('Grade Expert',{exact:true}).count()===1&&await school.locator('.school-staff').getByText('Second Grade Expert',{exact:true}).count()===1,'staff section deduplicates repeated expert assignments and keeps multiple experts');
  check(await school.getByRole('columnheader',{name:'Assigned teacher',exact:true}).count()===0,'student table does not repeat teacher assignments');
  check(await school.getByText('Previous Parent (disabled)',{exact:true}).isVisible(),'old linked account status is explicit');
  const dimensions=await school.locator('.school-grade-actions > button').evaluateAll(items=>items.map(el=>({width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height})));
  check(dimensions.length===2&&dimensions.every(item=>item.height===44&&Math.abs(item.width-dimensions[0].width)<1),'school detail header buttons match');
  const tabs=await school.locator('.school-grades > button').evaluateAll(items=>items.map(el=>el.getBoundingClientRect().width));check(tabs.every(value=>Math.abs(value-tabs[0])<1),'grade tabs have equal widths');
  const body=await school.locator('.school-detail-content').boundingBox(),nav=await school.locator('.school-grades').boundingBox();check(body.y>=nav.y+nav.height&&body.y+body.height<=height,'rosters stay below tabs within viewport');
  check(await school.evaluate(el=>getComputedStyle(el).display==='flex'&&getComputedStyle(el).overflowY==='hidden'),'school header stays fixed above scrolling records');
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
  check(await school.locator('.school-staff').getByText('Grade Teacher',{exact:true}).count()===1&&await school.locator('tbody').getByText('Grade Teacher',{exact:true}).count()===0,'shared teacher appears once above student rows');
  await school.getByRole('button',{name:'View student Grade Two Student',exact:true}).click();const profile=tab.locator('.student-profile');await profile.getByRole('heading',{name:'Grade Two Student',exact:true}).waitFor();
  check(await tab.locator('dialog[open]').count()===0&&await profile.locator('input,select,textarea,button[type="submit"]').count()===0,'View student opens a read-only full page without a modal or save controls');
  check(studentWrites===1&&await profile.locator('.student-information > div').count()===9,'student page shows complete record details without writes');
  await profile.getByRole('button',{name:'Load more screenings',exact:true}).click();await profile.getByRole('button',{name:'View screening 102',exact:true}).waitFor();check(historyReads.some(q=>q.id==='21'&&q.cursor==='student-history-next'),'student screenings use their own scoped paginated history');
  check(await tab.locator('.sidebar .nav-link').count()===8,'student page adds no sidebar destination');
  await profile.locator('.student-profile-content').evaluate(el=>el.scrollTop=0);
  await tab.screenshot({path:'output/playwright/admin-student-view-'+width+'.png'});
  await profile.getByRole('button',{name:'Edit student',exact:true}).click();await dialog.waitFor();check(await dialog.getByLabel('Student name',{exact:true}).inputValue()==='Grade Two Student'&&await dialog.getByRole('heading',{name:'Edit student',exact:true}).isVisible(),'explicit Edit student opens editor with fresh data');
  await dialog.getByRole('button',{name:'Cancel',exact:true}).click();check(studentWrites===1,'cancelling explicit edit makes no write');
  await profile.getByRole('button',{name:'Edit student',exact:true}).click();await dialog.waitFor();await dialog.getByLabel('Age',{exact:true}).fill('10');await dialog.getByRole('button',{name:'Save changes',exact:true}).click();await dialog.waitFor({state:'hidden'});await profile.locator('.student-information').getByText('10',{exact:true}).waitFor();check(studentWrites===2,'saving explicit edit refreshes the student page with current data');
  await profile.getByRole('button',{name:/^Back to /}).click();check(await school.getByRole('button',{name:'Grade 2',exact:true}).getAttribute('aria-pressed')==='true','Back returns to the original school grade');
  await school.getByRole('button',{name:'View student Grade Two Student',exact:true}).click();await profile.getByRole('heading',{name:'Grade Two Student',exact:true}).waitFor();check(await profile.locator('input,select,textarea').count()===0,'reopening View resets to read-only mode');await profile.getByRole('button',{name:/^Back to /}).click();
  check(await tab.locator('.directory-page-actions').count()===0,'Refresh and Add school are absent while viewing a school');
  check(await tab.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'populated grade roster fits viewport');await tab.screenshot({path:'output/playwright/admin-school-grade-roster-'+width+'.png',fullPage:true});
  failGrade2=true;await school.getByRole('button',{name:'Grade 3',exact:true}).click();await school.getByRole('button',{name:'Grade 2',exact:true}).click();await school.getByRole('button',{name:'Try again',exact:true}).waitFor();failGrade2=false;await school.getByRole('button',{name:'Try again',exact:true}).click();await school.getByText('Grade Two Student',{exact:true}).first().waitFor();check(true,'failed grade read retries current grade');
  slow=true;const oldOne=tab.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/students')&&new URL(r.url()).searchParams.get('grade_level')==='1');await school.getByRole('button',{name:'Grade 1',exact:true}).click();const oldTwo=tab.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/students')&&new URL(r.url()).searchParams.get('grade_level')==='2');await school.getByRole('button',{name:'Grade 2',exact:true}).click();await school.getByRole('button',{name:'Grade 3',exact:true}).click();await school.getByText('No students are available in Grade 3 for this school.',{exact:true}).waitFor();await Promise.all([oldOne,oldTwo]);
  check(!await school.getByText('Grade One Student',{exact:true}).first().isVisible()&&!await school.getByText('Grade Two Student',{exact:true}).first().isVisible(),'late grade responses cannot overwrite latest selection');slow=false;
  check(queries.filter(q=>q.grade).every(q=>q.school==='1'&&['1','2','3'].includes(q.grade)),'all grade reads stay in selected school');
  await school.getByRole('button',{name:'Close',exact:true}).click();check(await tab.locator('.directory-page-actions').getByRole('button',{name:'Refresh',exact:true}).count()===0&&await tab.locator('.directory-page-actions').getByRole('button',{name:'Add school',exact:true}).isVisible(),'closing school restores list actions');
  await tab.getByRole('button',{name:'View',exact:true}).click();await school.getByRole('heading',{name:'Grade 1 students',exact:true}).waitFor();
  check(await tab.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'grade page fits viewport');await tab.screenshot({path:'output/playwright/admin-school-grades-'+width+'.png',fullPage:true});
  const oldNameReads=nameReads;allowNames=false;await go('Settings');const meUpdated=tab.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/me'));await tab.reload();await tab.locator('.hosted-workspace').waitFor();await meUpdated;await go('Schools');
  if(!await school.isVisible())await tab.getByRole('button',{name:'View',exact:true}).click();await school.getByRole('button',{name:'Grade 1',exact:true}).click();await school.getByText('Account '+teacher,{exact:true}).waitFor();
  check(nameReads===oldNameReads,'account-name requests require account-management permission');
  await school.getByRole('button',{name:'View student Grade One Student',exact:true}).click();await profile.getByRole('heading',{name:'Grade One Student',exact:true}).waitFor();check(await profile.locator('input,select,textarea').count()===0,'student details remain read-only without account-name permission');await profile.getByRole('button',{name:/^Back to /}).click();
  await go('Students');const search=tab.getByLabel('Search students',{exact:true});await search.fill('Grade');await tab.locator('.hosted-students-table button').first().click();await profile.getByRole('heading',{name:'Grade One Student',exact:true}).waitFor();check(await profile.isVisible(),'main Students list opens the same student page');await profile.getByRole('button',{name:'Back to Students',exact:true}).click();check(await search.inputValue()==='Grade','Back preserves the Students list filter');
  allowNames=true;await go('Settings');const namesRestored=tab.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/me'));await tab.reload();await tab.locator('.hosted-workspace').waitFor();await namesRestored;
  await go('Students');await tab.locator('.hosted-students-table button').first().click();await profile.getByRole('button',{name:'View screening 101',exact:true}).waitFor();await profile.getByRole('button',{name:'View screening 101',exact:true}).click();const screening=tab.locator('.screening-detail');await screening.getByRole('heading',{name:'Initial screening',exact:true}).waitFor();await screening.getByText('Grade Expert',{exact:true}).waitFor();
  check(await screening.locator('.assignment-form,select').count()===0,'screening detail has no manual expert-assignment form');check(await screening.getByText('Grade Expert',{exact:true}).isVisible()&&!await screening.getByText('Second Grade Expert',{exact:true}).count(),'Reviewed by uses actual reviewer rather than assigned expert');check(await screening.getByRole('heading',{name:'Initial screening',exact:true}).isVisible(),'initial screening title replaces Result ID');
  await go('Students');await tab.locator('.hosted-students-table button').first().click();await profile.getByRole('button',{name:'Load more screenings',exact:true}).click();await profile.getByRole('button',{name:'View screening 102',exact:true}).click();await screening.getByRole('heading',{name:'Follow-up screening',exact:true}).waitFor();check(await screening.getByText('Not reviewed',{exact:true}).isVisible(),'follow-up screening title and pending reviewer state are accurate');await tab.screenshot({path:'output/playwright/admin-screening-follow-up-'+width+'.png'});
  await tab.close();
 }
 if(errors.length)throw Error(errors.join('\n'));
 return {checkCount:checks.length,checks,pageErrors:errors};
}
