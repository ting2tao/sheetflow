import { createI18n } from 'vue-i18n'
import { resolveInitialLocale } from './locale'
import { messages } from './messages'

export const i18n = createI18n({
  legacy: false,
  locale: resolveInitialLocale(),
  fallbackLocale: 'zh-CN',
  messages,
  missingWarn: import.meta.env.DEV,
  fallbackWarn: import.meta.env.DEV,
})
