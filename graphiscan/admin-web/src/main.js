import { createApp, nextTick } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import dialog from './directives/dialog'

createApp(App).directive('dialog', dialog).use(router).mount('#app')

async function revealStartup() {
  await router.isReady()
  await nextTick()
  const app = document.querySelector('#app')
  // Fetch assets together, and bound the wait rather than depending on the API.
  let fontReady = false
  const fonts = document.fonts
    ? Promise.all([400, 500, 600, 700].map(weight => document.fonts.load(`${weight} 16px Inter`)))
      .then(() => { fontReady = document.fonts.check('400 16px Inter') })
      .catch(() => {})
    : Promise.resolve()
  const images = [...app.querySelectorAll('img')].filter(image => image.getClientRects().length)
    .map(image => image.decode().catch(() => {}))
  let timeout
  await Promise.race([
    Promise.all([fonts, ...images]),
    new Promise(resolve => { timeout = setTimeout(resolve, 2200) }),
  ])
  clearTimeout(timeout)
  if (!fontReady) document.documentElement.style.setProperty('--font-ui', '"Segoe UI", system-ui, sans-serif')
  // Allow font/image layout to settle behind the cover before revealing it.
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  app.inert = false
  app.removeAttribute('aria-busy')
  const cover = document.querySelector('#admin-startup')
  cover?.classList.add('ready')
  setTimeout(() => cover?.remove(), 300)
}
void revealStartup()
