import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import SeoContent from './SeoContent.vue'
import { messages } from '../i18n/messages'

function mountSeoContent(locale = 'zh-CN') {
  const i18n = createI18n({
    legacy: false,
    locale,
    fallbackLocale: 'zh-CN',
    messages,
  })

  return {
    i18n,
    wrapper: mount(SeoContent, {
      global: {
        plugins: [i18n],
      },
    }),
  }
}

async function revealSeoContent(wrapper) {
  vi.advanceTimersByTime(100)
  await wrapper.vm.$nextTick()
}

describe('SeoContent', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders the Chinese SEO heading after its delayed display', async () => {
    const { wrapper } = mountSeoContent()

    expect(wrapper.find('.seo-content').exists()).toBe(false)
    vi.advanceTimersByTime(99)
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.seo-content').exists()).toBe(false)

    vi.advanceTimersByTime(1)
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('SheetFlow 是什么？')
  })

  it('renders English SEO copy from the active locale', async () => {
    const { wrapper } = mountSeoContent('en-US')

    await revealSeoContent(wrapper)

    expect(wrapper.text()).toContain('What is SheetFlow?')
  })

  it('renders English tuple entries and usage strings without coercion', async () => {
    const { wrapper } = mountSeoContent('en-US')

    await revealSeoContent(wrapper)

    const featureItems = wrapper.findAll('.content-section ul li')
    const scenarioItems = wrapper.findAll('.scenario')
    const usageItems = wrapper.findAll('.content-section ol li')
    const faqItems = wrapper.findAll('.faq-item')

    expect(featureItems).toHaveLength(6)
    expect(featureItems[0].find('strong').text()).toBe('Excel to image')
    expect(featureItems[0].text()).toContain('Supports .xlsx files and preserves table styling')

    expect(scenarioItems).toHaveLength(4)
    expect(scenarioItems[0].find('h3').text()).toBe('💰 Refund forms')
    expect(scenarioItems[0].find('p').text()).toBe(
      'Generate refund-form images for customer support',
    )

    expect(usageItems).toHaveLength(6)
    expect(usageItems[0].text()).toBe('Upload an .xlsx Excel file')

    expect(faqItems).toHaveLength(4)
    expect(faqItems[0].find('h3').text()).toBe('Which Excel formats are supported?')
    expect(faqItems[0].find('p').text()).toBe('SheetFlow currently supports .xlsx files.')
    expect(wrapper.text()).not.toContain('undefined')
  })

  it('updates visible SEO content when the composer locale changes', async () => {
    const { i18n, wrapper } = mountSeoContent()

    await revealSeoContent(wrapper)
    expect(wrapper.text()).toContain('SheetFlow 是什么？')

    i18n.global.locale.value = 'en-US'
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('What is SheetFlow?')
  })
})
