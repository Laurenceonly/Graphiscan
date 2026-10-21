import { nextTick } from 'vue'

let nextDialogId = 0
let openDialogs = 0
const states = new WeakMap()
const focusableSelector = 'a[href], button, input, select, textarea, [tabindex]'

function focusable(root) {
  return [...root.querySelectorAll(focusableSelector)].filter(element =>
    element.tabIndex >= 0 && !element.disabled && element.getClientRects().length && !element.closest('[inert]')
  )
}

// Keep the existing modal markup while sharing keyboard and focus behavior.
export default {
  mounted(backdrop, binding) {
    const dialog = backdrop.querySelector('section')
    const heading = dialog?.querySelector('h2')
    if (!dialog || !heading) return

    const opener = document.activeElement
    const inertSiblings = []
    let branch = backdrop
    while (branch.parentElement && branch !== document.body) {
      for (const sibling of branch.parentElement.children) {
        if (sibling !== branch) {
          inertSiblings.push([sibling, sibling.inert])
          sibling.inert = true
        }
      }
      branch = branch.parentElement
    }

    heading.id ||= `admin-dialog-title-${++nextDialogId}`
    dialog.setAttribute('role', 'dialog')
    dialog.setAttribute('aria-modal', 'true')
    dialog.setAttribute('aria-labelledby', heading.id)
    dialog.tabIndex = -1
    const state = { close: binding.value, opener, inertSiblings }
    const focusFirst = () => {
      const initial = dialog.matches('.danger-modal, .logout-confirm-modal')
        ? dialog.querySelector('.cancel-btn')
        : dialog.querySelector('input:not(:disabled), select:not(:disabled)')
      const target = initial || focusable(dialog)[0] || dialog
      target.focus({ preventScroll: true })
    }
    state.onKeydown = event => {
      if (event.key === 'Escape') {
        event.preventDefault()
        event.stopPropagation()
        state.close?.()
      } else if (event.key === 'Tab') {
        const controls = focusable(dialog)
        const first = controls[0] || dialog
        const last = controls.at(-1) || dialog
        if (!dialog.contains(document.activeElement) || document.activeElement === dialog ||
          (event.shiftKey && document.activeElement === first) ||
          (!event.shiftKey && document.activeElement === last)) {
          event.preventDefault()
          const target = event.shiftKey ? last : first
          target.focus()
        }
      }
    }
    state.onFocus = event => {
      if (!dialog.contains(event.target)) focusFirst()
    }
    states.set(backdrop, state)
    document.addEventListener('keydown', state.onKeydown, true)
    document.addEventListener('focusin', state.onFocus)
    openDialogs++
    document.body.classList.add('admin-dialog-open')
    nextTick(() => { if (backdrop.isConnected) focusFirst() })
  },
  updated(backdrop, binding) {
    const state = states.get(backdrop)
    if (state) state.close = binding.value
  },
  beforeUnmount(backdrop) {
    const state = states.get(backdrop)
    if (!state) return
    document.removeEventListener('keydown', state.onKeydown, true)
    document.removeEventListener('focusin', state.onFocus)
    for (const [sibling, wasInert] of state.inertSiblings) sibling.inert = wasInert
    if (--openDialogs === 0) document.body.classList.remove('admin-dialog-open')
    if (state.opener?.isConnected) state.opener.focus({ preventScroll: true })
    states.delete(backdrop)
  }
}
