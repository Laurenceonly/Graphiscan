// One interruptible fade for admin navigation and access-state changes.
// Presentation never delays rendering, remounts pages, or retains signed-out data.
const activeFades = new WeakMap()

export function cancelAdminFade(element) {
  if (element) activeFades.get(element)?.cancel()
}

export function fadeAdminSurface(element, { full = false } = {}) {
  if (!element) return
  const previous = activeFades.get(element)
  const style = getComputedStyle(element)
  const from = previous?.playState === 'running' ? style.opacity : full ? 0 : 0.6
  previous?.cancel()
  const preference = window.matchMedia('(prefers-reduced-motion: reduce)')
  // The first document already has an asset-ready startup reveal.
  if (preference.matches || document.querySelector('#admin-startup')) return
  const duration = parseFloat(style.getPropertyValue(full ? '--admin-motion-enter' : '--admin-motion-quick')) || (full ? 240 : 180)
  const easing = style.getPropertyValue('--admin-motion-ease').trim() || 'cubic-bezier(0.23, 1, 0.32, 1)'
  const animation = element.animate([{ opacity: from }, { opacity: 1 }], { duration, easing })
  activeFades.set(element, animation)
  const stopOnReduction = event => { if (event.matches) animation.cancel() }
  preference.addEventListener('change', stopOnReduction)
  const cleanup = () => {
    preference.removeEventListener('change', stopOnReduction)
    if (activeFades.get(element) === animation) activeFades.delete(element)
  }
  animation.finished.then(cleanup, cleanup)
}
