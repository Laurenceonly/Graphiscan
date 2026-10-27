import { site } from './config';
if (document.querySelector('.hero')) {
  const homeMotion = import('./motion');
  const initialSection = location.hash.slice(1);
  const navigationEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
  const isReload = navigationEntry?.type === 'reload';
  const pageLoaded = document.readyState === 'complete' ? Promise.resolve() : new Promise<void>(resolve => window.addEventListener('load', () => resolve(), { once: true }));
  const layoutReady = Promise.all([document.fonts.ready, pageLoaded]).then(() => new Promise<void>(resolve => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
  })).then(() => {
    // Fresh deep links align once; reload keeps the browser's restored position.
    if (!isReload && ['platform', 'understanding', 'people', 'questions'].includes(initialSection) && location.hash.slice(1) === initialSection) {
      document.getElementById(initialSection)?.scrollIntoView({ behavior: 'instant', block: 'start' });
    }
  });
  void Promise.all([homeMotion, layoutReady]).then(([motion]) => {
    const restoredScroll = { left: scrollX, top: scrollY, behavior: 'instant' as const };
    motion.initializeMotion();
    if (Math.abs(scrollY - restoredScroll.top) > 1 || Math.abs(scrollX - restoredScroll.left) > 1) window.scrollTo(restoredScroll);
  });
}

const menu = document.querySelector<HTMLButtonElement>('.menu-toggle');
const navigation = document.querySelector<HTMLElement>('#navigation');
let menuTransition: Animation | undefined;
let menuOperation = 0;
function setMenuSurface(open: boolean) {
  document.documentElement.classList.toggle('mobile-menu-open', open);
  document.querySelector('.site-header')?.classList.toggle('menu-is-open', open);
  document.querySelector('.site-header')?.classList.remove('menu-is-closing');
  document.querySelectorAll<HTMLElement>('main, .site-footer').forEach(element => { element.inert = open; });
}
function updateNavigationState() {
  navigation?.querySelectorAll<HTMLAnchorElement>('a[href^="#"]').forEach(link => {
    if (link.hash === location.hash) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
}
window.addEventListener('hashchange', updateNavigationState);
updateNavigationState();
function closeMenu(returnFocus = false, animated = true): Promise<boolean> {
  const wasOpen = navigation?.classList.contains('open') ?? false;
  const operation = ++menuOperation;
  const opacity = navigation ? Number(getComputedStyle(navigation).opacity) : 1;
  menuTransition?.cancel();
  menu?.setAttribute('aria-label', 'Open menu');
  menu?.setAttribute('aria-expanded', 'false');
  const finish = () => {
    navigation?.classList.remove('open');
    setMenuSurface(false);
    if (wasOpen && returnFocus) menu?.focus();
    return true;
  };
  if (!wasOpen || !navigation || !animated || matchMedia('(prefers-reduced-motion: reduce)').matches) return Promise.resolve(finish());
  document.querySelector('.site-header')?.classList.add('menu-is-closing');
  const transition = navigation.animate([{ opacity }, { opacity: 0 }], { duration: 300, easing: 'ease', fill: 'forwards' });
  menuTransition = transition;
  return transition.finished.then(() => {
    if (operation !== menuOperation) return false;
    finish();
    transition.cancel();
    return true;
  }).catch(() => false);
}
menu?.addEventListener('click', event => {
  const open = menu.getAttribute('aria-expanded') !== 'true';
  if (!open) { void closeMenu(false, event.detail !== 0); return; }
  ++menuOperation;
  const opacity = navigation?.classList.contains('open') ? Number(getComputedStyle(navigation).opacity) : 0;
  menuTransition?.cancel();
  menu.setAttribute('aria-expanded', 'true');
  menu.setAttribute('aria-label', 'Close menu');
  setMenuSurface(true);
  navigation?.classList.add('open');
  if (event.detail !== 0 && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    menuTransition = navigation?.animate([{ opacity }, { opacity: 1 }], { duration: 300, easing: 'ease' });
  }
});
navigation?.addEventListener('click', event => {
  const link = (event.target as Element).closest<HTMLAnchorElement>('a');
  if (!link) return;
  if (menu?.getAttribute('aria-expanded') === 'true' && link.hash && link.pathname === location.pathname) {
    event.preventDefault();
    void closeMenu(false, event.detail !== 0).then(closed => { if (closed) location.hash = link.hash; });
  } else void closeMenu(false, false);
});
document.addEventListener('pointerdown', event => {
  if (menu?.getAttribute('aria-expanded') === 'true' && event.target instanceof Node && !menu.contains(event.target) && !navigation?.contains(event.target)) closeMenu();
});
document.addEventListener('keydown', event => { if (event.key === 'Escape') void closeMenu(true, false); });
document.addEventListener('keydown', event => {
  if (event.key !== 'Tab' || menu?.getAttribute('aria-expanded') !== 'true') return;
  const targets = [...document.querySelectorAll<HTMLElement>('.site-header a[href], .menu-toggle')].filter(element => element.getClientRects().length > 0);
  const first = targets[0], last = targets[targets.length - 1];
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
});
matchMedia('(min-width: 1001px)').addEventListener('change', () => { void closeMenu(false, false); });

document.querySelectorAll<HTMLAnchorElement>('[data-admin-link]').forEach(link => {
  if (site.adminUrl) { link.href = site.adminUrl; link.hidden = false; link.rel = 'noopener noreferrer'; }
});
if (site.publicUrl) {
  const canonical = document.createElement('link'); canonical.rel = 'canonical';
  canonical.href = new URL(location.pathname, site.publicUrl).href; document.head.append(canonical);
}

// A missing artifact is a deliberate release state, never a dead download link.
if (site.apkUrl) {
  document.querySelectorAll('[data-release-badge]').forEach(el => { el.textContent = 'Android release available'; });
  document.querySelectorAll('[data-download-answer]').forEach(el => { el.textContent = 'The Android app is available on the download page. Check the release details and installation steps before installing.'; });
  const download = document.querySelector<HTMLAnchorElement>('#apk-download');
  if (download) { download.href = site.apkUrl; download.hidden = false; download.rel = 'noopener noreferrer'; }
  document.querySelector('#apk-unavailable')?.setAttribute('hidden', '');
  const status = document.querySelector('#release-status');
  if (status) status.textContent = 'Android release available';
  document.querySelectorAll('[data-unreleased-note]').forEach(el => { el.setAttribute('hidden', ''); });
  const metadata = document.querySelector('#release-metadata');
  if (metadata) for (const [label, value] of [['Version', site.version], ['File size', site.size], ['Released', site.releaseDate]]) {
    if (value) { const item = document.createElement('span'); item.textContent = `${label}: ${value}`; metadata.append(item); }
  }
}

type Role = 'teacher' | 'parent' | 'expert' | 'admin';
const roles: Record<Role, { title: string; description: string; features: string[]; image: string }> = {
  teacher: { title: 'Support your learners.', description: 'Upload handwriting photos for your assigned learners and keep their screening records together.', features: ['Take a photo or choose an image', 'Read screening results and expert notes', 'Return to earlier screening records'], image: 'teacher-home.png' },
  parent: { title: 'Stay informed about your child.', description: 'Read reports for your linked children when the expert review is marked Validated.', features: ['See the children linked to your account', 'Read released reports and expert notes', 'Find recommendations and follow-up information'], image: 'parent-home.png' },
  expert: { title: 'Review handwriting with context.', description: 'Open the screenings assigned to you and add your professional review.', features: ['View screening results and handwriting photos', 'Mark a review as Validated or Flagged', 'Add notes, recommendations and follow-up requests'], image: 'expert-home.png' },
  admin: { title: 'Keep the team organized.', description: 'Manage accounts, learners and screening assignments in your web workspace.', features: ['Manage accounts and learner records', 'Assign eligible experts to screenings', 'Check screening history, progress and activity'], image: 'admin-workspace.png' },
};
const rolePanel = document.querySelector('#role-panel');
if (rolePanel) {
  const content = document.createElement('div');
  content.className = 'role-copy-inner';
  content.append(...rolePanel.childNodes);
  rolePanel.append(content);
  for (const role of Object.values(roles)) {
    const guide = document.createElement('div');
    guide.className = 'role-size-guide';
    guide.setAttribute('aria-hidden', 'true');
    guide.inert = true;
    const title = document.createElement('h3'); title.textContent = role.title;
    const description = document.createElement('p'); description.textContent = role.description;
    const features = document.createElement('ul');
    features.append(...role.features.map(text => { const item = document.createElement('li'); item.textContent = text; return item; }));
    guide.append(title, description, features);
    rolePanel.append(guide);
  }
}
function setText(selector: string, value: string) { const el = document.querySelector(selector); if (el) el.textContent = value; }
function selectRole(button: HTMLButtonElement) {
  const role = button.dataset.role as Role; const data = roles[role];
  setText('#role-title', data.title); setText('#role-description', data.description);
  const list = document.querySelector('#role-features');
  if (list) { list.replaceChildren(...data.features.map(text => { const li = document.createElement('li'); li.textContent = text; return li; })); }
  const img = document.querySelector<HTMLImageElement>('#role-image');
  if (img) { img.src = `/images/${data.image}`; img.alt = `Actual ${role} workspace with fictional demonstration records`; img.width = role === 'admin' ? 1440 : 390; img.height = role === 'admin' ? 1000 : 844; }
  document.querySelector('.role-preview')?.classList.toggle('admin', role === 'admin');
  document.querySelector('#role-panel')?.setAttribute('aria-labelledby', button.id);
}
const steps = [
  { image: 'teacher-home.png', detail: 'Teachers upload handwriting photos for the learners assigned to them. An account is required.', alt: 'Teacher home screen with fictional records' },
  { image: 'expert-home.png', detail: 'The model provides screening information. An assigned expert reviews it and can add notes, recommendations and a follow-up request.', alt: 'Expert review workspace with fictional records' },
  { image: 'parent-home.png', detail: 'Parents see reports for their linked children only while the expert review is marked Validated. Each record shows its date and the model used.', alt: 'Parent workspace with fictional validated reports' },
];
// Invisible sizing copies keep the shared panel as tall as its longest step,
// including after font-size changes and responsive reflow.
const workflowPanel = document.querySelector('#workflow-panel');
if (workflowPanel) for (const step of steps) {
  const guide = document.createElement('p');
  guide.className = 'workflow-size-guide';
  guide.setAttribute('aria-hidden', 'true');
  guide.textContent = step.detail;
  workflowPanel.append(guide);
}
function selectStep(button: HTMLButtonElement) {
  const step = steps[Number(button.dataset.step)];
  setText('#workflow-detail', step.detail);
  const image = document.querySelector<HTMLImageElement>('#workflow-image');
  if (image) { image.src = `/images/${step.image}`; image.alt = step.alt; }
  document.querySelector('#workflow-panel')?.setAttribute('aria-labelledby', button.id);
}
function wireTabs(selector: string, onSelect: (button: HTMLButtonElement) => void) {
  const buttons = Array.from(document.querySelectorAll<HTMLButtonElement>(selector));
  function activate(button: HTMLButtonElement, focus = false) {
    buttons.forEach(item => { const selected = button === item; item.setAttribute('aria-selected', String(selected)); item.tabIndex = selected ? 0 : -1; item.classList.toggle('active', selected); });
    onSelect(button); if (focus) button.focus();
  }
  buttons.forEach((button, index) => {
    button.addEventListener('click', () => activate(button));
    button.addEventListener('keydown', event => {
      let next = index;
      const isVertical = button.closest('[role="tablist"]')?.getAttribute('aria-orientation') === 'vertical';
      if (event.key === (isVertical ? 'ArrowDown' : 'ArrowRight')) next = (index + 1) % buttons.length;
      else if (event.key === (isVertical ? 'ArrowUp' : 'ArrowLeft')) next = (index + buttons.length - 1) % buttons.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = buttons.length - 1;
      else return;
      event.preventDefault(); activate(buttons[next], true);
    });
  });
}
const tabsMedia = matchMedia('(max-width: 760px)');
function updateTabOrientation() {
  document.querySelectorAll('[role="tablist"]').forEach(list => list.setAttribute('aria-orientation', list.classList.contains('role-tabs') || tabsMedia.matches ? 'horizontal' : 'vertical'));
}
tabsMedia.addEventListener('change', updateTabOrientation); updateTabOrientation();
wireTabs('[data-role]', selectRole); wireTabs('[data-step]', selectStep);
