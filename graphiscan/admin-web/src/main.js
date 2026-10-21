import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import dialog from './directives/dialog'

createApp(App).directive('dialog', dialog).use(router).mount('#app')
