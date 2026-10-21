// Read-only layout checks. No login/provider calls and no credentials entered.
async page => {
  await page.unrouteAll({behavior:'ignoreErrors'});
  const checks=[];
  try{
    for(const [width,height] of [[1920,1080],[1440,900],[1366,768],[1024,768],[980,900],[768,1024],[390,844],[320,640],[844,390]]){
      await page.setViewportSize({width,height});
      await page.goto('http://127.0.0.1:5173/login');
      await page.getByRole('heading',{name:'Welcome back',exact:true}).waitFor();
      const initial=await page.evaluate(()=>{
        const form=document.querySelector('.admin-signin-form'),shell=document.querySelector('.access-login-layout'),brand=document.querySelector('.access-brand');
        const box=el=>{const r=el.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom}};
        const inputs=[...form.querySelectorAll('input')];
        return {fits:document.documentElement.scrollWidth<=innerWidth,viewportWidth:document.documentElement.clientWidth,form:box(form),shell:box(shell),brand:box(brand),title:getComputedStyle(form.querySelector('h1')).fontSize,inputs:inputs.map(el=>({size:getComputedStyle(el).fontSize,value:el.value,box:box(el.closest('.admin-signin-input'))})),toggle:box(form.querySelector('.admin-signin-toggle')),submit:box(form.querySelector('.admin-signin-submit')),panelVisible:getComputedStyle(document.querySelector('.login-right')).display!=='none',previewLoaded:document.querySelector('.login-product-preview img').naturalWidth>0,laptop:box(document.querySelector('.login-product-preview')),hero:box(document.querySelector('.login-product-panel'))};
      });
      if(!initial.fits||initial.title!=='28px'||initial.inputs.some(input=>input.size!=='16px'||input.value||input.box.height<52)||initial.toggle.height<44||initial.submit.height<48||initial.form.x<0||initial.form.right>width||initial.brand.bottom>initial.form.y||initial.panelVisible!==(width>980)||!initial.previewLoaded)throw Error(JSON.stringify({width,height,initial}));
      if(initial.shell.x!==0||initial.shell.y!==0||Math.abs(initial.shell.width-initial.viewportWidth)>1||initial.shell.height<height)throw Error('Login does not fill tab: '+JSON.stringify({width,height,initial}));
      if(initial.panelVisible&&(initial.laptop.x<initial.hero.x||initial.laptop.right>initial.hero.right||initial.laptop.y<initial.hero.y||initial.laptop.bottom>initial.hero.bottom))throw Error('Laptop preview cropped: '+JSON.stringify({width,height,initial}));
      const alignment=await page.evaluate(()=>{const box=selector=>document.querySelector(selector).getBoundingClientRect();const panel=document.querySelector('.login-right');return {title:box('.admin-signin-intro h1').x,field:box('.admin-signin-input').x,label:box('.admin-signin-field label').x,rightTitle:box('.hero-content h2').x,rightCopy:box('.hero-content p').x,panelX:box('.login-right').x,shellWidth:box('.access-login-layout').width,visible:getComputedStyle(panel).display!=='none'}});
      if(Math.abs(alignment.title-alignment.field)>1||Math.abs(alignment.label-alignment.field)>1||(alignment.visible&&(Math.abs(alignment.rightTitle-alignment.rightCopy)>1||Math.abs(alignment.panelX-alignment.shellWidth*.42)>1)))throw Error('Copy or split alignment: '+JSON.stringify(alignment));
      if(alignment.visible&&!await page.locator('.hero-content h2').evaluate(el=>el.scrollWidth<=el.clientWidth&&el.getBoundingClientRect().height<=parseFloat(getComputedStyle(el).lineHeight)+1))throw Error('Right heading is clipped or wraps');
      if(!await page.evaluate(()=>['.admin-signin-intro h1','.admin-signin-intro p','.access-session-note'].every(selector=>getComputedStyle(document.querySelector(selector)).textAlign==='center')))throw Error('Requested login copy is not centered');
      await page.getByLabel('Email address',{exact:true}).focus();
      const focused=await page.getByLabel('Email address',{exact:true}).evaluate(el=>({font:getComputedStyle(el).fontSize,height:el.closest('.admin-signin-input').getBoundingClientRect().height}));
      if(focused.font!=='16px'||focused.height!==initial.inputs[0].box.height)throw Error('Input changed size on focus');
      await page.locator('.admin-signin-toggle').click();
      await page.locator('.admin-signin-toggle').evaluate(el=>el.blur());
      if(await page.getByLabel('Password',{exact:true}).getAttribute('type')!=='text')throw Error('Show password failed');
      await page.locator('.admin-signin-toggle').click();
      await page.locator('.admin-signin-toggle').evaluate(el=>el.blur());
      if([1920,1440,1366,390].includes(width))await page.screenshot({path:'output/playwright/hosted-login-final-'+width+'.png',fullPage:true,animations:'disabled'});
      checks.push({width,height,formWidth:Math.round(initial.form.width),fits:true,emptyInputs:true,stableInput:true,panelVisible:initial.panelVisible});
    }
    return {checks,scope:'layout only; no Auth requests'};
  }finally{await page.setViewportSize({width:1440,height:900});await page.goto('http://127.0.0.1:5173/login')}
}
