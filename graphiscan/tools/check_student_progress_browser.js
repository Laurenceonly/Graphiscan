// Fictional browser-only progress checks; all API traffic is intercepted.
async page=>{
 const checks=[],errors=[];page.on('pageerror',error=>errors.push(error.message));
 const record=(id,classification,date,type='Follow-up Screening')=>({result_id:String(id),student_id:String(Math.floor(id/10)),classification,predicted_class_score:.99,date_generated:date,report:{report_type:type},review:{status:'Validated'}});
 const series=[record(11,'High Potential','2026-08-01T08:00:00Z','Initial Screening'),record(12,'Normal','2026-09-01T08:00:00Z'),record(13,'Historical label','2026-10-01T08:00:00Z'),record(14,'Normal','2026-11-01T08:00:00Z')];
 for(const [width,height]of [[1440,900],[1366,768],[390,844]]){
  await page.unrouteAll({behavior:'ignoreErrors'});let failMiddle=true,permissions=true;const reads=[];
  await page.route('**/api/v1/**',async route=>{
   const request=route.request(),url=new URL(request.url()),path=url.pathname,key=path.split('/').at(-1);let data=[],cursor=null;
   const send=(data,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
   if(key==='login'||key==='refresh')data={access_token:'fixture',refresh_token:'fixture',expires_in:3600};
   else if(request.method()!=='GET')throw Error('Unexpected write '+path);
   else if(key==='me')data={user_id:'00000000-0000-4000-8000-000000000101',full_name:'Fictional Progress Admin',role:'admin',permissions:permissions?['assignments.manage']:[],onboarding:{next_action:'ready'}};
   else if(key==='schools')data=[{school_id:'1',name:'Fictional School'}];
   else if(key==='students')data=Array.from({length:6},(_,i)=>({student_id:String(i+1),full_name:'Fictional Student '+(i+1),school_id:'1',grade_level:1}));
   else if(key==='history'){
    const id=path.split('/').at(-2),next=url.searchParams.get('cursor');reads.push({id,cursor:next,limit:url.searchParams.get('limit'),order:url.searchParams.get('order')});
    if(!permissions)return send({error:{code:'NOT_FOUND',message:'Student history is unavailable.'}},404);
    if(id==='1'){data=next?series.slice(2):series.slice(0,2);cursor=next?null:'student-one-next';}
    else if(id==='2')data=[];
    else if(id==='3'){await new Promise(resolve=>setTimeout(resolve,450));data=[record(31,'High Potential','2026-08-01T08:00:00Z','Initial Screening')];cursor='slow-next';}
    else if(id==='4'){if(next&&failMiddle)return send({error:{code:'UNAVAILABLE',message:'Fictional next-page failure'}},503);data=[record(next?42:41,'Normal',next?'2026-09-01T08:00:00Z':'2026-08-01T08:00:00Z',next?'Follow-up Screening':'Initial Screening')];cursor=next?null:'student-four-next';}
    else if(id==='5')data=[record(51,'Normal','2026-08-01T08:00:00Z','Initial Screening')];
    else if(id==='6'){data=[record(61,'Normal','2026-08-01T08:00:00Z','Initial Screening')];cursor='repeated';}
   }else if(path.match(/\/screenings\/\d+$/))data=record(Number(key),'Normal','2026-08-01T08:00:00Z','Initial Screening');
   else if(path.match(/\/students\/\d+$/))data={student_id:key,full_name:'Fictional Student '+key,school_id:'1',grade_level:1};
   return send({data,page:{next_cursor:cursor}});
  });
  const check=(ok,label)=>{if(!ok)throw Error(width+': '+label);checks.push(width+': '+label)};
  await page.setViewportSize({width,height});await page.goto('http://127.0.0.1:5173/login');await page.getByLabel('Email address',{exact:true}).fill('fixture@example.invalid');await page.getByLabel('Password',{exact:true}).fill('fictional');await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.locator('.hosted-workspace').waitFor();
  const go=async name=>{if(width<=1100)await page.getByRole('button',{name:'Open navigation',exact:true}).click();await page.locator('.sidebar').getByRole('button',{name,exact:true}).click();await page.locator('.sidebar-backdrop').waitFor({state:'hidden'});};
  await go('Progress');const root=page.locator('.hosted-progress'),picker=root.getByLabel('Student',{exact:true});
  const load=async id=>{await picker.selectOption(id);await root.getByRole('button',{name:'View progress',exact:true}).click();};
  await load('1');const chart=root.locator('.screening-trend');await chart.waitFor();
  check(reads.filter(read=>read.id==='1').length===2&&reads.filter(read=>read.id==='1').every(read=>read.order==='oldest'&&read.limit==='100'),'complete history follows student-bound oldest-first pagination');
  check(await chart.locator('.trend-point').count()===4&&await root.locator('tbody tr').count()===4,'chart and table include all history pages');
  check((await chart.locator('.trend-readout').innerText()).includes('Initial Screening'),'timeline starts with earliest initial record');
  check(await chart.locator('.trend-point').evaluateAll(items=>items.map(el=>parseFloat(el.style.left)).every((value,index,all)=>index===0||value>all[index-1])),'screenings are plotted in chronological order');
  check(await chart.locator('.trend-point').evaluateAll(items=>items.map(el=>el.style.top).join(',')==='32px,132px,202px,132px'),'vertical positions use recorded categories, not confidence');
  check(await chart.locator('.trend-line').count()===1,'unknown historical label breaks the line instead of becoming a binary prediction');
  await chart.getByLabel('Selected screening',{exact:true}).selectOption('13');check((await chart.locator('.trend-readout').innerText()).includes('Historical label'),'selection preserves original stored label');
  await chart.locator('.trend-point').nth(2).focus();await page.keyboard.press('Home');check(await chart.locator('.trend-point').first().getAttribute('aria-pressed')==='true','keyboard Home selects initial screening');await page.keyboard.press('ArrowRight');check(await chart.locator('.trend-point').nth(1).getAttribute('aria-pressed')==='true','keyboard arrows inspect next screening');
  check(!await chart.innerText().then(text=>text.includes('%')),'chart does not present model confidence as progress');
  check(await chart.locator('.trend-plot').evaluate(el=>!['auto','scroll'].includes(getComputedStyle(el).overflowX)&&!['auto','scroll'].includes(getComputedStyle(el).overflowY)&&el.scrollHeight<=el.clientHeight+1),'chart fits without its own scrollbars');
  check(await root.locator('.table-wrapper').evaluate(el=>el.clientHeight>=el.querySelector('table').getBoundingClientRect().height-2&&el.getBoundingClientRect().height>100),'screening table keeps natural height instead of shrinking below chart');
  await chart.getByLabel('Selected screening',{exact:true}).selectOption('11');await page.screenshot({path:'output/playwright/student-progress-chart-'+width+'.png'});
  check(await page.evaluate(()=>scrollY===0&&document.documentElement.scrollWidth<=innerWidth),'workspace remains fixed without page overflow');
  await load('2');await root.getByText('No screening records were found for this student.',{exact:true}).waitFor();check(await chart.count()===0,'empty student has no invented progress');
  const slow=page.waitForResponse(response=>response.url().includes('/students/3/history')),slowRequest=page.waitForRequest(request=>request.url().includes('/students/3/history'));await load('3');await slowRequest;
  await load('2');await root.getByText('No screening records were found for this student.',{exact:true}).waitFor();await slow;check(await chart.count()===0&&reads.filter(read=>read.id==='3').length===1,'switching student ignores late pages and stops old cursor loop');
  await load('4');await root.getByText('Fictional next-page failure',{exact:true}).waitFor();check(await chart.count()===0,'partial failed history is not presented as complete');failMiddle=false;await root.getByRole('button',{name:'View progress',exact:true}).click();await chart.waitFor();check(await chart.locator('.trend-point').count()===2,'retry loads complete history');
  await load('6');await root.getByText('Screening history could not be completed. Try again.',{exact:true}).waitFor();check(reads.filter(read=>read.id==='6').length===2&&await chart.count()===0,'repeated cursor is rejected without an infinite read loop');
  await load('5');await chart.waitFor();check(await chart.locator('.trend-point').count()===1&&await chart.locator('.trend-line').count()===0,'one screening is a point without a fabricated trend');await chart.getByRole('button',{name:'View screening',exact:true}).click();await page.getByRole('heading',{name:'Initial screening',exact:true}).waitFor();check(true,'chart opens the existing authorized screening detail');
  await go('Progress');await load('5');await chart.waitFor();permissions=false;await go('Settings');const changed=page.waitForResponse(response=>new URL(response.url()).pathname.endsWith('/me'));await page.locator('.workspace-account').getByRole('button',{name:'Refresh',exact:true}).click();await changed;await go('Progress');check(await picker.inputValue()===''&&await chart.count()===0,'account refresh clears student selection and cached chart');await load('5');await root.getByText('Student history is unavailable.',{exact:true}).waitFor();check(await chart.count()===0,'denied history stays hidden');
 }
 if(errors.length)throw Error(errors.join('\n'));return {checks:checks.length,details:checks,pageErrors:errors};
}
