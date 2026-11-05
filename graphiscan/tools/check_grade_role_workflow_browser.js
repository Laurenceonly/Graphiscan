async rootPage => {
  const context=rootPage.context(),errors=[],checks=[],captures=[],writes=[];
  for(const page of context.pages())if(page!==rootPage)await page.close();
  await rootPage.unrouteAll({behavior:'ignoreErrors'});
  const ids={teacher:'00000000-0000-4000-8000-000000000101',expert:'00000000-0000-4000-8000-000000000102',parent:'00000000-0000-4000-8000-000000000103',admin:'00000000-0000-4000-8000-000000000104'};
  const student={student_id:'9',full_name:'Fictional Workflow Student',age:8,grade_level:2,school_id:'9',teacher_id:ids.teacher,parent_id:ids.parent,revision:1};
  const models=['mobilenetv2','resnet50','efficientnetb0'].map((key,i)=>({model_id:String(i+1),model_key:key,model_version:'binary-fictional-litert-fp32-v1',task_type:'binary',is_selectable:true,is_default:i===0}));
  const records=[],requests=new Map(),gates={teacher:'change_password',expert:'ready',parent:'ready',admin:'ready'};
  let uncertainUpload=true,readDelay=0,failRead=false,denyDetail=false;
  const sample=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRusAAAAASUVORK5CYII=','base64');
  const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label)};
  const pages={teacher:rootPage,expert:await context.newPage(),parent:await context.newPage(),admin:await context.newPage()};
  for(const [role,page] of Object.entries(pages)){
    page.on('pageerror',e=>errors.push(role+': '+e.message));
    await page.addInitScript(()=>{
      const dispatch=HTMLInputElement.prototype.dispatchEvent;
      HTMLInputElement.prototype.dispatchEvent=function(event){
        if(this.type==='file'&&event.type==='click'){
          const canvas=document.createElement('canvas');canvas.width=32;canvas.height=32;
          const c=canvas.getContext('2d');c.fillStyle='white';c.fillRect(0,0,32,32);c.strokeStyle='black';c.strokeRect(8,8,16,16);
          const bytes=Uint8Array.from(atob(canvas.toDataURL('image/png').split(',')[1]),v=>v.charCodeAt(0));
          const transfer=new DataTransfer();transfer.items.add(new File([bytes],'fictional-sample.png',{type:'image/png'}));this.files=transfer.files;
          queueMicrotask(()=>this.dispatchEvent(new Event('change')));return true;
        }return dispatch.call(this,event);
      };
    });
    await page.route('**/api/v1/**',async route=>{
      const req=route.request(),url=new URL(req.url()),path=url.pathname.replace('/api/v1',''),method=req.method();
      const who=(req.headers().authorization||'').replace('Bearer fictional-','');
      const json=(data,status=200,extra={})=>route.fulfill({status,contentType:'application/json',body:JSON.stringify({data,page:{next_cursor:null},...extra})});
      const error=(status,code,message)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify({error:{code,message}})});
      if(path==='/session/login'||path==='/session/refresh')return json({access_token:'fictional-'+role,refresh_token:'fictional-'+role,expires_in:3600});
      if(path==='/session/logout')return json({});
      if(who!==role)return error(401,'AUTHENTICATION_REQUIRED','Fictional session required.');
      if(path==='/me')return json({user_id:ids[role],full_name:'Fictional '+role[0].toUpperCase()+role.slice(1),role,account_status:'active',permissions:role==='admin'?['accounts.manage','assignments.manage','schools.manage','audit.read']:[],onboarding:{next_action:gates[role]}});
      if(path==='/me/password'&&method==='POST'){gates[role]='accept_privacy';writes.push({role,path});return json({});}
      if(path==='/privacy-agreement')return json({title:'Data Privacy Agreement',version:'fictional-workflow-v1',content:'Fictional browser exercise only. No real consent or student data is recorded.'});
      if(path==='/me/privacy-acceptance'&&method==='POST'){gates[role]='ready';writes.push({role,path});return json({});}
      if(gates[role]!=='ready')return error(403,'PRIVACY_ACCEPTANCE_REQUIRED','Complete account setup.');
      if(method==='GET'&&readDelay)await new Promise(resolve=>setTimeout(resolve,readDelay));
      if(method==='GET'&&failRead&&path==='/screenings')return error(503,'FICTIONAL_UNAVAILABLE','Fictional screening read failed. Refresh to try again.');
      const visible=row=>role==='admin'||role==='teacher'||role==='expert'&&student.school_id==='9'&&student.grade_level===2||role==='parent'&&row.review.status==='Validated';
      if(path==='/students')return json([student]);
      if(path==='/students/9')return json(student);
      if(path==='/schools')return json([{school_id:'9',name:'Fictional Workflow School'}]);
      if(path==='/schools/9/assignment-options')return json([{user_id:ids.expert,full_name:'Fictional Expert',role:'expert'},{user_id:ids.parent,full_name:'Fictional Parent',role:'parent'}]);
      if(path==='/accounts')return json([]);
      if(path==='/accounts/'+ids.expert)return json({user_id:ids.expert,full_name:'Fictional Expert',role:'expert'});
      if(path==='/models')return json(models);
      if(path==='/screenings'&&method==='POST'){
        if(role!=='teacher')return error(403,'FORBIDDEN','Teacher access required.');
        const key=req.headers()['idempotency-key'],body=req.postData()||'';
        const field=name=>body.match(new RegExp('name="'+name+'"\\r\\n\\r\\n([^\\r]+)'))?.[1];
        writes.push({role,path,key,model:field('model_id')});
        if(!requests.has(key)){
          const chosen=models.find(row=>row.model_id===field('model_id'));
          if(!chosen||field('student_id')!=='9')return error(422,'INVALID_INPUT','Invalid fictional upload.');
          const id=String(17+records.length),reportId=String(100+records.length);
          const row={result_id:id,student_id:'9',revision:1,date_generated:'2026-11-03T02:00:0'+records.length+'Z',classification:'Normal',predicted_class_score:.8,class_scores:{normal:.8,high_potential:.2},model:chosen,report:{report_id:reportId,report_type:records.length?'Follow-up Screening':'Initial Screening'},review:{status:'Pending',assigned_expert_id:null,expert_id:null,revision:1,remarks:null,expert_recommendation:null,follow_up_needed:false}};
          records.push(row);requests.set(key,row);
        }
        if(uncertainUpload){uncertainUpload=false;return error(503,'FICTIONAL_UNCERTAIN','Fictional response lost after creation. Retry the same submission.');}
        return json(requests.get(key),201);
      }
      if(path.startsWith('/screening-requests/'))return json({state:'completed',result_id:requests.get(path.split('/').at(-1))?.result_id});
      if(path==='/screenings'||path==='/students/9/history'){
        let list=records.filter(visible).map(row=>structuredClone(row));
        if(url.searchParams.get('order')!=='oldest')list.reverse();
        return json(list);
      }
      const report=path.startsWith('/reports/'),id=path.split('/')[2];
      const row=report?records.find(row=>row.report.report_id===id):records.find(row=>row.result_id===id);
      if(row){
        if(!visible(row)||role==='parent'&&denyDetail)return error(404,'NOT_FOUND','This record is not available to your account.');
        if(path.endsWith('/expert-assignment')&&method==='PATCH'){
          if(role!=='admin')return error(403,'FORBIDDEN','Administrator required.');
          row.review.assigned_expert_id=req.postDataJSON().assigned_expert_id;row.revision++;writes.push({role,path});return json(row);
        }
        if(path.endsWith('/review')&&method==='PATCH'){
          if(role!=='expert'||student.school_id!=='9'||student.grade_level!==2)return error(403,'FORBIDDEN','Assigned expert required.');
          const body=req.postDataJSON();Object.assign(row.review,body,{revision:row.review.revision+1,expert_id:ids.expert,validation_date:'2026-11-03T02:30:00Z'});row.revision++;writes.push({role,path});return json(row);
        }
        if(path.endsWith('/image'))return route.fulfill({status:200,contentType:'image/png',body:sample});
        return json(report?{...row,report_type:row.report.report_type}:row);
      }
      return error(404,'NOT_FOUND','Unexpected fictional route '+path);
    });
  }
  const mobileUrl='http://localhost:5174';
  async function login(role,width=role==='admin'?1440:390){
    const page=pages[role];await page.setViewportSize({width,height:844});
    await page.goto(role==='admin'?'http://127.0.0.1:5173/login':mobileUrl);
    await page.getByRole('textbox',{name:'Email address',exact:true}).fill('fictional-'+role+'@example.invalid');
    await page.getByRole('textbox',{name:'Password',exact:true}).fill('Fictional!42Value');
    await page.getByRole('button',{name:'Sign in',exact:true}).click();
  }
  async function capture(role,name){
    const page=pages[role];await page.evaluate(()=>document.fonts.ready);
    await page.evaluate(()=>{window.scrollTo(0,0);for(const el of document.querySelectorAll('div'))if(el.scrollTop&&['auto','scroll'].includes(getComputedStyle(el).overflowY))el.scrollTop=0});
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'no document overflow '+name);
    await page.screenshot({path:'output/playwright/initial-flow-'+name+'.png',fullPage:role==='admin'});captures.push(name);
  }
  const teacher=pages.teacher,expert=pages.expert,parent=pages.parent,admin=pages.admin;
  await login('teacher');
  await teacher.getByRole('heading',{name:'Set your password',exact:true}).waitFor();
  check(await teacher.getByRole('button',{name:'Save password',exact:true}).isDisabled(),'password gate starts disabled');
  await teacher.getByRole('textbox',{name:'Current password',exact:true}).fill('Fictional!42Value');
  await teacher.getByRole('textbox',{name:'New password',exact:true}).fill('Different!42Value');
  await teacher.getByRole('textbox',{name:'Confirm new password',exact:true}).fill('Mismatch!42Value');
  check(await teacher.getByRole('button',{name:'Save password',exact:true}).isDisabled(),'password mismatch blocks submission');
  await teacher.getByRole('textbox',{name:'Confirm new password',exact:true}).fill('Different!42Value');
  await capture('teacher','password-390');
  await teacher.getByRole('button',{name:'Save password',exact:true}).click();
  await teacher.getByRole('button',{name:'Sign in',exact:true}).waitFor();
  await login('teacher');
  await teacher.getByRole('heading',{name:'Data Privacy Agreement',exact:true}).waitFor();
  check(await teacher.getByRole('button',{name:'Agree and continue',exact:true}).isDisabled(),'privacy gate needs explicit consent');
  await capture('teacher','privacy-390');
  await teacher.getByRole('switch',{name:'I agree to this version of the Data Privacy Agreement',exact:true}).click();
  await teacher.getByRole('button',{name:'Agree and continue',exact:true}).click();
  await teacher.getByRole('button',{name:'New screening',exact:true}).waitFor();
  check(writes.filter(w=>w.path==='/me/password').length===1&&writes.filter(w=>w.path==='/me/privacy-acceptance').length===1,'ordered single onboarding submissions');
  async function upload(model){
    await teacher.getByRole('tab',{name:'Home',exact:true}).click();
    await teacher.getByRole('button',{name:'New screening',exact:true}).click();
    await teacher.getByRole('radio',{name:student.full_name,exact:true}).click();
    for(const name of ['MobileNetV2','ResNet50','EfficientNetB0'])check(await teacher.getByRole('radio',{name,exact:true}).count()===1,'available model '+name);
    await teacher.getByRole('radio',{name:model,exact:true}).click();
    await teacher.getByRole('button',{name:'Choose image',exact:true}).click();
    await teacher.getByRole('img',{name:'Selected handwriting image',exact:true}).waitFor();
    const choose=await teacher.getByRole('button',{name:'Replace image',exact:true}).boundingBox(),camera=await teacher.getByRole('button',{name:'Use camera',exact:true}).boundingBox();
    check(Math.abs(choose.width-camera.width)<1&&Math.abs(choose.height-camera.height)<1&&Math.abs(choose.y-camera.y)<1,'image action alignment '+model);
    await capture('teacher','upload-'+model.toLowerCase()+'-390');
    await teacher.getByRole('button',{name:'Submit for screening',exact:true}).click();
    if(records.length===1&&writes.filter(w=>w.path==='/screenings').length===1){
      await teacher.getByRole('button',{name:'Retry the same submission',exact:true}).waitFor();
      check(await teacher.getByRole('button',{name:'Replace image',exact:true}).isDisabled(),'uncertain image locked');
      await teacher.getByRole('button',{name:'Retry the same submission',exact:true}).click();
    }
    await teacher.getByRole('button',{name:'Open report',exact:true}).waitFor();
    await teacher.getByRole('heading',{name:student.full_name,exact:true}).waitFor();
  }
  await upload('ResNet50');
  check(records.length===1&&records[0].report.report_type==='Initial Screening','one saved Initial despite uncertain response');
  const uploadWrites=writes.filter(w=>w.path==='/screenings');
  check(uploadWrites.length===2&&uploadWrites[0].key===uploadWrites[1].key,'same upload key on retry');
  check(records[0].model.model_key==='resnet50','chosen model saved');
  await teacher.getByRole('button',{name:'View handwriting image',exact:true}).click();
  await teacher.getByRole('img',{name:'Authorized handwriting sample',exact:true}).waitFor();
  await capture('teacher','initial-result-390');
  await login('parent');await parent.getByRole('tab',{name:'Reports',exact:true}).click();
  await parent.getByText('No screening records are available for your account.',{exact:true}).waitFor();
  check(await parent.getByRole('button',{name:'Open screening 17',exact:true}).count()===0,'pending absent from parent list');
  await capture('parent','pending-hidden-390');
  await login('admin');await admin.waitForURL('**/workspace');await admin.getByRole('button',{name:'Results',exact:true}).click();
  async function assign(id){
    await admin.reload();await admin.locator('.hosted-workspace').waitFor();
    await admin.locator('.sidebar').getByRole('button',{name:'Results',exact:true}).click();
    await admin.getByRole('button',{name:'View result '+id,exact:true}).click();
    check(!await admin.locator('.screening-detail .assignment-form').count(),'manual per-screening expert assignment is absent');
    check(records.find(row=>row.result_id===id).review.assigned_expert_id===null,'grade routing needs no per-screening assignment '+id);
  }
  await assign('17');await capture('admin','assignment-1440');
  await login('expert');
  async function review(id,status,remarks){
    await expert.getByRole('tab',{name:'Home',exact:true}).click();
    await expert.getByRole('button',{name:'Review screenings',exact:true}).click();
    await expert.getByRole('button',{name:'Open screening '+id,exact:true}).click();
    await expert.getByRole('button',{name:status,exact:true}).click();
    await expert.getByRole('textbox',{name:'Review remarks',exact:true}).fill(remarks);
    await expert.getByRole('textbox',{name:'Expert recommendation (optional)',exact:true}).fill('Fictional expert-authored recommendation for this UI exercise.');
    await expert.getByRole('button',{name:'Save review',exact:true}).click();
    await expert.getByText('Review saved.',{exact:true}).waitFor();
  }
  await review('17','Validated','Fictional expert validation.');
  await capture('expert','validated-review-390');
  await parent.getByRole('tab',{name:'Home',exact:true}).click();await parent.getByRole('tab',{name:'Reports',exact:true}).click();
  await parent.getByRole('button',{name:'Open screening 17',exact:true}).click();
  await parent.getByRole('button',{name:'View handwriting image',exact:true}).click();
  await parent.getByRole('img',{name:'Authorized handwriting sample',exact:true}).waitFor();
  check(await parent.getByRole('button',{name:'Save review',exact:true}).count()===0,'parent has no expert editor');
  await parent.getByRole('button',{name:'Open report',exact:true}).click();
  await parent.getByText('Fictional expert validation.',{exact:true}).last().waitFor();
  await capture('parent','released-report-390');
  await login('teacher');await upload('EfficientNetB0');
  check(records.length===2&&records[1].report.report_type==='Follow-up Screening','second upload saved Follow-up');
  await capture('teacher','followup-result-390');
  await assign('18');await login('expert');await review('18','Validated','Fictional follow-up validation.');
  await login('expert');await review('17','Flagged','Fictional flagged review revokes release.');
  await login('parent');await parent.getByRole('tab',{name:'Reports',exact:true}).click();
  await parent.getByRole('button',{name:'Open screening 18',exact:true}).waitFor();
  check(await parent.getByRole('button',{name:'Open screening 17',exact:true}).count()===0,'Flagged removed from parent list');
  check((await parent.getByRole('button',{name:'Open screening 18',exact:true}).innerText()).includes('Follow-up Screening'),'remaining parent result keeps Follow-up label');
  await parent.getByRole('button',{name:'Open screening 18',exact:true}).click();
  await parent.getByRole('button',{name:'View student history',exact:true}).click();
  await parent.getByRole('button',{name:'Open screening 18',exact:true}).waitFor();
  await capture('parent','followup-only-history-390');
  for(const role of ['teacher','expert','parent']){
    await login(role);const page=pages[role];
    for(const config of [{width:320,scheme:'light'},{width:390,scheme:'dark'},{width:768,scheme:'light'}]){
      await page.emulateMedia({colorScheme:config.scheme,reducedMotion:'reduce'});await login(role,config.width);
      await page.getByRole('tab',{name:'Home',exact:true}).click();await page.getByRole('heading',{name:'Fictional '+role[0].toUpperCase()+role.slice(1),exact:true}).waitFor();
      await capture(role,role+'-home-'+config.width+'-'+config.scheme);
      await page.getByRole('tab',{name:role==='teacher'?'Results':role==='expert'?'Reviews':'Reports',exact:true}).click();
      await page.getByRole('button',{name:'Open screening 18',exact:true}).waitFor();
      await capture(role,role+'-records-'+config.width+'-'+config.scheme);
      await page.getByRole('button',{name:'Open screening 18',exact:true}).click();
      await page.getByRole('button',{name:'Open report',exact:true}).waitFor();
      await capture(role,role+'-detail-'+config.width+'-'+config.scheme);
      await page.getByRole('button',{name:'View student history',exact:true}).click();
      await page.getByRole('button',{name:'Open screening 18',exact:true}).waitFor();
      await page.getByRole('button',{name:'Show oldest first',exact:true}).click();
      check(await page.getByRole('button',{name:'Show newest first',exact:true}).count()===1,'history order '+role+' '+config.width);
    }
  }
  await login('parent');await parent.getByRole('tab',{name:'Reports',exact:true}).click();
  await parent.getByRole('button',{name:'Open screening 18',exact:true}).click();
  await parent.getByRole('button',{name:'View handwriting image',exact:true}).click();
  await parent.getByRole('img',{name:'Authorized handwriting sample',exact:true}).waitFor();
  denyDetail=true;await parent.getByRole('button',{name:'Refresh record',exact:true}).click();
  await parent.getByText('This record is not available to your account.',{exact:true}).last().waitFor();
  check(await parent.getByRole('img',{name:'Authorized handwriting sample',exact:true}).count()===0,'denied refresh clears private image');
  check(await parent.getByRole('button',{name:'Open report',exact:true}).count()===0,'denied refresh clears report action');
  await capture('parent','revoked-detail-768');
  denyDetail=false;await parent.getByRole('button',{name:'Refresh record',exact:true}).click();
  await parent.getByRole('button',{name:'Open report',exact:true}).waitFor();
  await login('teacher');await teacher.getByRole('tab',{name:'Home',exact:true}).click();
  readDelay=650;await teacher.getByRole('tab',{name:'Results',exact:true}).click();await teacher.getByRole('tab',{name:'Students',exact:true}).click();
  await teacher.getByRole('heading',{name:student.full_name,exact:true}).waitFor();
  check(await teacher.getByRole('button',{name:'Open screening 18',exact:true}).count()===0,'rapid navigation rejects late results');
  readDelay=0;
  for(const width of [390,320]){await admin.setViewportSize({width,height:844});await capture('admin','admin-assignment-'+width);}
  check(errors.length===0,'zero page errors');
  return {checks:checks.length,captures,fictionalRecords:records.length,officialTypes:records.map(r=>r.report.report_type),fixtureWrites:writes.length,pageErrors:errors,scope:'Current school/grade expert responsibility with stateful fictional browser responses; grade assignments are fixture setup, separately checked by admin UI and SQL suites. No actual Auth, inference, Storage or hosted writes.'};
}
