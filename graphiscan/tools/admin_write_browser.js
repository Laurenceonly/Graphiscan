// Companion to check_admin_writes.py; all accounts here are disposable fixtures.
async page => {
  const base = 'http://127.0.0.1:5175';
  const password = 'Synthetic!2026Admin';
  const replacement = 'Synthetic!2026Changed';
  const checks = [];
  const record = (name, passed) => {
    if (!passed) throw new Error('Failed synthetic workflow: ' + name);
    checks.push(name);
  };
  let blocked = 0;
  await page.route('**/api/**', route => {
    const url = new URL(route.request().url());
    if (url.pathname.startsWith('/api/') && url.origin !== 'http://127.0.0.1:5001') {
      blocked++;
      return route.abort();
    }
    return route.continue();
  });
  const submit = async (button, suffix, expected = 200) => {
    const response = page.waitForResponse(r => r.url().endsWith(suffix) && r.request().method() === 'POST');
    await button.click();
    record(suffix + ':' + expected, (await response).status() === expected);
  };
  const login = async (value, expected = 200) => {
    await page.goto(base + '/login');
    await page.getByPlaceholder('Enter admin email').fill('fixture1@example.invalid');
    await page.getByPlaceholder('Enter password', {exact:true}).fill(value);
    await submit(page.getByRole('button', {name:'Sign in', exact:true}), '/api/admin/login', expected);
    if (expected === 200) await page.waitForURL('**/admin/dashboard');
  };
  const width = page.viewportSize()?.width <= 500 ? 390 : 1440;
  await page.setViewportSize({width,height:844});
  await login(password);
  await page.goto(base + '/admin/users');
  await page.getByRole('button', {name:'Add User',exact:true}).click();
  await page.getByPlaceholder('Enter full name').fill('Browser Synthetic Guest');
  await page.getByPlaceholder('Enter email address', {exact:true}).fill('browser-guest@example.invalid');
  await page.locator('.modal-backdrop select').selectOption('guest');
  await page.getByPlaceholder('Create password', {exact:true}).fill(password);
  await page.getByPlaceholder('Re-enter password', {exact:true}).fill(password);
  await submit(page.locator('.modal-backdrop button[type=submit]'), '/api/admin/users/add');
  await page.locator('.modal-backdrop').waitFor({state:'detached'});
  const guest = () => page.locator('tbody tr').filter({hasText:'browser-guest@example.invalid'});
  await guest().waitFor();
  record('created account visible', await guest().count() === 1);
  for (const [action, label] of [['disable','Disable'], ['restore','Restore']]) {
    await guest().getByRole('button', {name:label,exact:true}).click();
    const target = await guest().locator('button').count();
    record('account action available', target > 0);
    const response = page.waitForResponse(r=>r.url().endsWith('/'+action)&&r.request().method()==='POST');
    await page.locator('.modal-backdrop button.primary-modal-btn').click();
    record('browser '+action, (await response).status()===200);
    await page.locator('.modal-backdrop').waitFor({state:'detached'});
    await guest().getByRole('button',{name:action==='disable'?'Restore':'Disable',exact:true}).waitFor();
  }
  await page.goto(base + '/admin/students');
  await page.getByRole('button',{name:'Add Student',exact:true}).click();
  await page.getByPlaceholder('Enter student full name').fill('Browser Synthetic Student');
  await page.getByPlaceholder('Enter age').fill('8');
  await page.getByPlaceholder('Example: Grade 3').fill('Grade 2');
  await page.locator('.modal-backdrop select').nth(0).selectOption('2');
  await page.locator('.modal-backdrop select').nth(1).selectOption('3');
  await submit(page.getByRole('button',{name:'Create Student',exact:true}), '/api/admin/students/add');
  await page.locator('.modal-backdrop').waitFor({state:'detached'});
  const student=()=>page.locator('tbody tr').filter({hasText:'Browser Synthetic Student'});
  await student().waitFor();
  record('student creation persisted in list',await student().count()===1);
  for(const parent of ['4','']) {
    await student().locator('.guardian-link-btn').click();
    await page.locator('.modal-backdrop select').selectOption(parent);
    const response=page.waitForResponse(r=>r.url().endsWith('/guardian')&&r.request().method()==='POST');
    await page.getByRole('button',{name:'Save Guardian',exact:true}).click();
    record(parent?'guardian changed':'guardian removed',(await response).status()===200);
    await page.locator('.modal-backdrop').waitFor({state:'detached'});
  }
  const deleteRow=async row=>{
    await row.getByRole('button',{name:'Delete',exact:true}).click();
    await page.getByPlaceholder('DELETE', {exact:true}).fill('DELETE');
    await page.getByPlaceholder('Enter admin password', {exact:true}).fill('wrong-fixture-password');
    let response=page.waitForResponse(r=>r.url().endsWith('/delete')&&r.request().method()==='POST');
    await page.getByRole('button',{name:'Delete Permanently',exact:true}).click();
    record('incorrect deletion password denied',(await response).status()===403);
    await page.getByPlaceholder('Enter admin password',{exact:true}).fill(password);
    response=page.waitForResponse(r=>r.url().endsWith('/delete')&&r.request().method()==='POST');
    await page.getByRole('button',{name:'Delete Permanently',exact:true}).click();
    record('confirmed synthetic deletion',(await response).status()===200);
    await page.locator('.modal-backdrop').waitFor({state:'detached'});
    await row.waitFor({state:'detached'});
  };
  await deleteRow(student());
  await page.goto(base+'/admin/users');
  await guest().waitFor();
  await deleteRow(guest());
  await page.goto(base+'/admin/settings');
  await page.getByPlaceholder('Enter current password').fill(password);
  await page.getByPlaceholder('Create new password').fill(replacement);
  await page.getByPlaceholder('Re-enter new password').fill(replacement);
  await submit(page.getByRole('button',{name:'Change Password',exact:true}),'/api/admin/change-password');
  await page.waitForURL('**/login');
  await login(password,401);
  await login(replacement);
  await page.goto(base+'/admin/audit-logs');
  await page.locator('tbody tr').first().waitFor();
  record('audit activity visible',await page.locator('tbody tr').count()>=12);
  record('all API traffic isolated',blocked===0);
  return {width,passed:checks.length,checks};
}
