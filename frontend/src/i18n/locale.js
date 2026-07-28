export const ZH_LOCALE = 'zh-CN'
export const EN_LOCALE = 'en-US'
export const DEFAULT_LOCALE = ZH_LOCALE
export const SUPPORTED_LOCALES = [ZH_LOCALE, EN_LOCALE]
export const LOCALE_STORAGE_KEY = 'sheetflow.locale'

const PATH_LOCALES = {
  zh: ZH_LOCALE,
  en: EN_LOCALE,
}

function isSupportedLocale(locale) {
  return SUPPORTED_LOCALES.includes(locale)
}

function browserLanguages() {
  return typeof navigator === 'undefined' ? [] : navigator.languages || []
}

function browserLocale(languages) {
  const language = languages.find(Boolean)

  if (!language) return DEFAULT_LOCALE
  return language.toLowerCase().startsWith('zh') ? ZH_LOCALE : EN_LOCALE
}

function savedLocale(storage) {
  try {
    const locale = storage?.getItem(LOCALE_STORAGE_KEY)
    return isSupportedLocale(locale) ? locale : null
  } catch {
    return null
  }
}

function defaultStorage() {
  try {
    return typeof window === 'undefined' ? null : window.localStorage
  } catch {
    return null
  }
}

export function localeFromPath(pathname) {
  const match = typeof pathname === 'string' && pathname.match(/^\/(zh|en)(?:\/|$)/)
  return match ? PATH_LOCALES[match[1]] : null
}

export function resolveInitialLocale(options = {}) {
  const pathname = options.pathname ?? (typeof window === 'undefined' ? '/' : window.location.pathname)
  const urlLocale = localeFromPath(pathname)
  if (urlLocale) return urlLocale

  const locale = savedLocale(options.storage ?? defaultStorage())
  if (locale) return locale

  return browserLocale(options.languages ?? browserLanguages())
}

export function localizedPath(locale, pathname = typeof window === 'undefined' ? '/' : window.location.pathname) {
  const prefix = locale === ZH_LOCALE ? 'zh' : 'en'
  const normalizedPath = `/${String(pathname || '/').replace(/^\/+/, '')}`
  const remainingPath = normalizedPath.replace(/^\/(?:zh|en)(?=\/|$)/, '') || '/'
  const path = `/${prefix}${remainingPath}`.replace(/\/{2,}/g, '/')

  return path.endsWith('/') ? path : `${path}/`
}

export function switchLocale(locale) {
  if (!isSupportedLocale(locale)) return

  try {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  } catch {
    // A blocked storage area must not prevent a locale switch.
  }

  const path = localizedPath(locale)
  window.history.pushState(window.history.state, '', path)
  window.dispatchEvent(new CustomEvent('sheetflow:locale-change', { detail: locale }))
}
