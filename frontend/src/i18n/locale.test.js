import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  DEFAULT_LOCALE,
  EN_LOCALE,
  LOCALE_STORAGE_KEY,
  ZH_LOCALE,
  localeFromPath,
  localizedPath,
  observeLocaleChanges,
  resolveInitialLocale,
  switchLocale,
} from './locale'

function setBrowserLanguages(languages) {
  Object.defineProperty(window.navigator, 'languages', {
    configurable: true,
    value: languages,
  })
}

function setBrowserLanguage(language) {
  Object.defineProperty(window.navigator, 'language', {
    configurable: true,
    value: language,
  })
}

describe('localeFromPath', () => {
  it.each([
    ['/zh/', ZH_LOCALE],
    ['/zh/features', ZH_LOCALE],
    ['/en/', EN_LOCALE],
    ['/en/features', EN_LOCALE],
    ['/fr/', null],
  ])('maps %s to %s', (pathname, locale) => {
    expect(localeFromPath(pathname)).toBe(locale)
  })
})

describe('resolveInitialLocale', () => {
  beforeEach(() => {
    window.localStorage.clear()
    setBrowserLanguages([])
    setBrowserLanguage('')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('prefers a locale in the URL over saved and browser preferences', () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, EN_LOCALE)
    setBrowserLanguages(['zh-TW'])

    expect(resolveInitialLocale({ pathname: '/zh/features' })).toBe(ZH_LOCALE)
  })

  it('uses the saved preference on the root path', () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, EN_LOCALE)
    setBrowserLanguages(['zh-CN'])

    expect(resolveInitialLocale({ pathname: '/' })).toBe(EN_LOCALE)
  })

  it.each([
    [['zh-CN'], ZH_LOCALE],
    [['zh-TW'], ZH_LOCALE],
    [['en-GB'], EN_LOCALE],
    [['fr-FR'], EN_LOCALE],
    [[], DEFAULT_LOCALE],
  ])('maps browser languages %j to %s', (languages, locale) => {
    setBrowserLanguages(languages)

    expect(resolveInitialLocale({ pathname: '/' })).toBe(locale)
  })

  it('falls back to browser language when localStorage cannot be read', () => {
    const storage = {
      getItem() {
        throw new Error('storage unavailable')
      },
    }

    expect(resolveInitialLocale({ pathname: '/', storage, languages: ['en-GB'] })).toBe(EN_LOCALE)
  })

  it.each([
    [undefined, 'zh-TW', ZH_LOCALE],
    [[], 'en-GB', EN_LOCALE],
    [[], '', DEFAULT_LOCALE],
  ])('falls back from browser languages %j to navigator.language %s', (languages, language, locale) => {
    setBrowserLanguages(languages)
    setBrowserLanguage(language)

    expect(resolveInitialLocale({ pathname: '/' })).toBe(locale)
  })
})

describe('localizedPath', () => {
  it('replaces a leading locale segment and preserves the remaining path', () => {
    expect(localizedPath(EN_LOCALE, '/zh/features')).toBe('/en/features/')
  })
})

describe('switchLocale', () => {
  beforeEach(() => {
    window.history.replaceState({ source: 'test' }, '', '/zh/')
    window.localStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('persists, pushes a localized URL, and emits a locale-change event', () => {
    const pushState = vi.spyOn(window.history, 'pushState')
    const listener = vi.fn()
    window.addEventListener('sheetflow:locale-change', listener)

    switchLocale(EN_LOCALE)

    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(EN_LOCALE)
    expect(pushState).toHaveBeenCalledWith({ source: 'test' }, '', '/en/')
    expect(window.location.pathname).toBe('/en/')
    expect(listener).toHaveBeenCalledWith(expect.objectContaining({ detail: EN_LOCALE }))
    window.removeEventListener('sheetflow:locale-change', listener)
  })

  it('ignores an unsupported locale', () => {
    const pushState = vi.spyOn(window.history, 'pushState')

    expect(switchLocale('fr-FR')).toBeUndefined()
    expect(pushState).not.toHaveBeenCalled()
  })

  it('continues switching when the saved preference cannot be written', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('storage unavailable')
    })

    expect(() => switchLocale(EN_LOCALE)).not.toThrow()
    expect(window.location.pathname).toBe('/en/')
  })

  it('preserves the current query string and hash', () => {
    window.history.replaceState({ source: 'test' }, '', '/zh/features?utm_source=newsletter#pricing')
    const pushState = vi.spyOn(window.history, 'pushState')

    switchLocale(EN_LOCALE)

    expect(pushState).toHaveBeenCalledWith(
      { source: 'test' },
      '',
      '/en/features/?utm_source=newsletter#pricing',
    )
  })
})

describe('observeLocaleChanges', () => {
  beforeEach(() => {
    window.history.replaceState(null, '', '/zh/')
  })

  it('syncs supported locales after navigation and can be detached', () => {
    const callback = vi.fn()
    const eventListener = vi.fn()
    window.addEventListener('sheetflow:locale-change', eventListener)
    const stopObserving = observeLocaleChanges(callback)

    window.history.pushState(null, '', '/en/')
    window.dispatchEvent(new PopStateEvent('popstate'))

    expect(callback).toHaveBeenCalledWith(EN_LOCALE)
    expect(eventListener).toHaveBeenCalledWith(expect.objectContaining({ detail: EN_LOCALE }))

    stopObserving()
    window.history.pushState(null, '', '/zh/')
    window.dispatchEvent(new PopStateEvent('popstate'))

    expect(callback).toHaveBeenCalledTimes(1)
    window.removeEventListener('sheetflow:locale-change', eventListener)
  })

  it('does not notify for paths without a supported locale', () => {
    const callback = vi.fn()
    const stopObserving = observeLocaleChanges(callback)

    window.history.pushState(null, '', '/fr/')
    window.dispatchEvent(new PopStateEvent('popstate'))

    expect(callback).not.toHaveBeenCalled()
    stopObserving()
  })
})
