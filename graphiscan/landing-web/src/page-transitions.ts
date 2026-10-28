const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const curtain = document.querySelector<HTMLElement>('.page-curtain');
let departure: Animation | undefined;
let recovery: number | undefined;
let navigating = false;
function restorePage() {
  departure?.cancel();
  departure = undefined;
  clearTimeout(recovery);
  navigating = false;
  if (curtain) { curtain.style.animation = 'none'; curtain.style.opacity = '0'; }
}
window.addEventListener('pageshow', event => { if (event.persisted) restorePage(); });
window.addEventListener('pagehide', restorePage);
document.addEventListener('click', event => {
  const link = event.target instanceof Element ? event.target.closest<HTMLAnchorElement>('a[href]') : null;
  if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
  const url = new URL(link.href);
  if (!['http:', 'https:'].includes(url.protocol)) return;
  if (url.origin === location.origin && url.pathname === location.pathname && url.search === location.search) return;
  const localPage = url.origin === location.origin && ['/', '/about/', '/privacy/', '/download/'].includes(url.pathname);
  if (!localPage && !link.hasAttribute('data-admin-link')) return;
  if (!curtain || reducedMotion.matches) return;
  event.preventDefault();
  if (navigating) return;
  navigating = true;
  const opacity = getComputedStyle(curtain).opacity;
  curtain.style.animation = 'none';
  departure = curtain.animate([{ opacity }, { opacity: 1 }], {
    duration: 280, easing: 'cubic-bezier(.23,1,.32,1)', fill: 'forwards',
  });
  // Recover if navigation fails or is canceled, including a return from admin.
  recovery = window.setTimeout(restorePage, 2500);
  void departure.finished.then(() => location.assign(url.href)).catch(restorePage);
});
reducedMotion.addEventListener('change', restorePage);
