import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'
import { messages } from '../i18n/messages'

function mountSwitcher(locale = 'zh-CN') {
  const i18n = createI18n({
    legacy: false,
    locale,
    fallbackLocale: 'zh-CN',
    messages,
  })

  return {
    i18n,
    wrapper: mount(LanguageSwitcher, {
      global: {
        plugins: [i18n],
      },
    }),
  }
}

function mountApp(locale = 'zh-CN') {
  const i18n = createI18n({
    legacy: false,
    locale,
    fallbackLocale: 'zh-CN',
    messages,
  })

  return {
    i18n,
    wrapper: mount(App, {
      global: {
        plugins: [i18n],
      },
    }),
  }
}

describe('LanguageSwitcher', () => {
  beforeEach(() => {
    window.history.replaceState(null, '', '/zh/')
    window.gtag = vi.fn()
    document.documentElement.lang = 'zh-CN'
  })

  afterEach(() => {
    delete window.gtag
    vi.restoreAllMocks()
  })

  it('switches locale, URL, document language, and analytics together', async () => {
    const { i18n, wrapper } = mountSwitcher()

    await wrapper.get('[data-locale="en-US"]').trigger('click')

    expect(i18n.global.locale.value).toBe('en-US')
    expect(window.location.pathname).toBe('/en/')
    expect(document.documentElement.lang).toBe('en-US')
    expect(window.gtag).toHaveBeenCalledWith('event', 'language_change', {
      from_language: 'zh-CN',
      to_language: 'en-US',
    })
  })

  it('marks the active language and ignores a click on it', async () => {
    const { wrapper } = mountSwitcher()
    const chinese = wrapper.get('[data-locale="zh-CN"]')

    expect(chinese.classes()).toContain('active')
    expect(chinese.attributes('aria-current')).toBe('true')
    await chinese.trigger('click')

    expect(window.location.pathname).toBe('/zh/')
    expect(window.gtag).not.toHaveBeenCalled()
  })
})

describe('App language integration', () => {
  let wrappers

  beforeEach(() => {
    wrappers = []
    window.gtag = vi.fn()
  })

  afterEach(() => {
    wrappers.forEach(wrapper => wrapper.unmount())
    delete window.gtag
    vi.unstubAllGlobals()
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  function trackedApp(locale = 'zh-CN') {
    const mounted = mountApp(locale)
    wrappers.push(mounted.wrapper)
    return mounted
  }

  async function selectFile(wrapper, file) {
    const input = wrapper.get('input[type="file"]')
    Object.defineProperty(input.element, 'files', {
      configurable: true,
      value: [file],
    })
    await input.trigger('change')
  }

  it('keeps the selected file and workflow step when the language changes', async () => {
    window.history.replaceState(null, '', '/zh/')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        job_id: 'job-1',
        sheets: [{ index: 0, name: 'Orders', rows: 10, columns: 4 }],
      }),
    }))
    const { wrapper } = trackedApp()
    const file = new File(['sheet'], 'orders.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })

    await selectFile(wrapper, file)
    await wrapper.get('.upload-section .btn-primary').trigger('click')
    await flushPromises()
    expect(wrapper.vm.step).toBe(2)

    await wrapper.get('[data-locale="en-US"]').trigger('click')

    expect(wrapper.vm.file).toBe(file)
    expect(wrapper.vm.step).toBe(2)
    expect(wrapper.get('.settings-section h2').text()).toBe('📋 Select Sheets')
  })

  it('recomputes a structured job message after a language change', async () => {
    vi.useFakeTimers()
    window.history.replaceState(null, '', '/zh/')
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: 'job-2',
          sheets: [{ index: 0, name: 'Orders', rows: 10, columns: 4 }],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'queued',
          message_code: 'preparing',
          message_params: { sheets: 1 },
        }),
      }))
    const { wrapper } = trackedApp()
    const file = new File(['sheet'], 'orders.xlsx')

    await selectFile(wrapper, file)
    await wrapper.get('.upload-section .btn-primary').trigger('click')
    await flushPromises()
    await wrapper.get('.settings-section .btn-primary').trigger('click')
    await flushPromises()

    expect(wrapper.get('.status-text').text()).toBe('准备处理 1 个 Sheet...')
    await wrapper.get('[data-locale="en-US"]').trigger('click')
    expect(wrapper.get('.status-text').text()).toBe('Preparing to process 1 sheet...')
  })

  it('shows no raw Chinese copy in the initial English workflow', () => {
    window.history.replaceState(null, '', '/en/')
    const { wrapper } = trackedApp('en-US')

    expect(wrapper.get('.main').text()).not.toMatch(/[\u3400-\u9fff]/u)
    expect(wrapper.get('.upload-section h2').text()).toBe('📁 Upload an Excel File')
  })

  it('syncs the composer and document language after browser navigation', async () => {
    window.history.replaceState(null, '', '/zh/')
    const { i18n, wrapper } = trackedApp()

    window.history.pushState(null, '', '/en/')
    window.dispatchEvent(new PopStateEvent('popstate'))
    await wrapper.vm.$nextTick()

    expect(i18n.global.locale.value).toBe('en-US')
    expect(document.documentElement.lang).toBe('en-US')
    expect(wrapper.get('.upload-section h2').text()).toBe('📁 Upload an Excel File')
  })
})
