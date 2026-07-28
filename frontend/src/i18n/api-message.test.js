import { createI18n } from 'vue-i18n'
import { describe, expect, it } from 'vitest'
import { localizeApiError, localizeJobMessage } from './api-message'
import { messages } from './messages'

function translator(locale = 'en-US') {
  const i18n = createI18n({
    legacy: false,
    locale,
    fallbackLocale: 'zh-CN',
    messages,
  })

  return i18n.global.t
}

describe('localizeJobMessage', () => {
  it('formats a Chinese sheet page progress message', () => {
    expect(localizeJobMessage({
      message_code: 'processing_sheet_page',
      message_params: { sheet_name: 'Orders', current: 2, total: 5 },
    }, translator('zh-CN'))).toBe('正在处理：Orders - 第 2/5 页')
  })

  it('selects the English completed plural form', () => {
    expect(localizeJobMessage({
      message_code: 'completed',
      message_params: { sheets: 1, pages: 2 },
    }, translator())).toBe('Complete! Processed 1 sheet and generated 2 images')
  })

  it('returns a legacy message when no message code is supplied', () => {
    expect(localizeJobMessage({ message: '旧版消息' }, translator())).toBe('旧版消息')
  })

  it('returns the English generic error for an unknown message code', () => {
    expect(localizeJobMessage({ message_code: 'unknown_code' }, translator())).toBe(
      'Something went wrong. Please try again.',
    )
  })

  it('does not expose a legacy message for an unknown structured code', () => {
    expect(localizeJobMessage({
      message_code: 'unknown_code',
      message: 'Internal backend detail',
    }, translator())).toBe('Something went wrong. Please try again.')
  })

  it('returns the generic error for a null job payload', () => {
    expect(localizeJobMessage(null, translator())).toBe(
      'Something went wrong. Please try again.',
    )
  })
})

describe('localizeApiError', () => {
  it('formats a structured error detail with its parameters', () => {
    expect(localizeApiError({
      detail: { code: 'file.unsupported_type', params: { supported: '.xlsx' } },
    }, translator())).toBe('Only .xlsx Excel files are supported.')
  })
})

describe('message catalog contracts', () => {
  it('interpolates and pluralizes page counts', () => {
    expect(translator('zh-CN')('progress.pageCount', { count: 2 })).toBe('2 页')
    expect(translator()('progress.pageCount', { count: 1 }, 1)).toBe('1 page')
    expect(translator()('progress.pageCount', { count: 2 }, 2)).toBe('2 pages')
  })

  it('interpolates error prefixes', () => {
    expect(translator('zh-CN')('errors.prefix', { message: '失败' })).toBe('错误：失败')
    expect(translator()('errors.prefix', { message: 'failed' })).toBe('Error: failed')
  })

  it('uses title-description tuples for SEO collection items', () => {
    for (const locale of ['zh-CN', 'en-US']) {
      const seo = messages[locale].seo
      expect(seo.features).toHaveLength(6)
      expect(seo.scenarios).toHaveLength(4)
      expect(seo.faq).toHaveLength(4)

      for (const collection of [seo.features, seo.scenarios, seo.faq]) {
        expect(collection.every(item => (
          Array.isArray(item)
          && item.length === 2
          && item.every(value => typeof value === 'string')
        ))).toBe(true)
      }

      expect(seo.usage.every(item => typeof item === 'string')).toBe(true)
    }

    expect(messages['zh-CN'].seo.faq[0][1]).toBe('目前支持 .xlsx 格式。')
  })
})
