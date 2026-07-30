import { createApp } from 'vue'
import App from './App.vue'
import { i18n } from './i18n'
import { localizedPath, resolveInitialLocale } from './i18n/locale'

if (window.location.pathname === '/') {
  window.location.replace(localizedPath(resolveInitialLocale()))
} else {
  createApp(App).use(i18n).mount('#app')
}
