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

  it.each([
    [1, 1, 'Complete! Processed 1 sheet and generated 1 image'],
    [1, 2, 'Complete! Processed 1 sheet and generated 2 images'],
    [2, 1, 'Complete! Processed 2 sheets and generated 1 image'],
    [2, 2, 'Complete! Processed 2 sheets and generated 2 images'],
  ])('formats an English completion for %i sheets and %i pages', (sheets, pages, expected) => {
    expect(localizeJobMessage({
      message_code: 'completed',
      message_params: { sheets, pages },
    }, translator())).toBe(expected)
  })

  it.each([
    [1, 'Preparing to process 1 sheet...'],
    [2, 'Preparing to process 2 sheets...'],
  ])('pluralizes an English preparation for %i sheets', (sheets, expected) => {
    expect(localizeJobMessage({
      message_code: 'preparing',
      message_params: { sheets },
    }, translator())).toBe(expected)
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
  it('pluralizes the generate action from a named count', () => {
    expect(translator()('settings.start', { count: 1 })).toBe('🚀 Generate (1 sheet)')
    expect(translator()('settings.start', { count: 2 })).toBe('🚀 Generate (2 sheets)')
  })

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

  it('matches the exact English error and SEO copy contract', () => {
    expect(messages['en-US'].errors).toMatchObject({
      'file.not_found': 'The file no longer exists. Please upload it again.',
      'job.not_found': 'The job does not exist. Please upload the file again.',
      'job.not_completed': 'The job is not complete yet.',
      'output.not_found': 'The ZIP file does not exist.',
    })

    expect(messages['en-US'].seo).toEqual({
      whatTitle: '🎯 What is SheetFlow?',
      whatBody: 'SheetFlow is a free online Excel-to-image tool. Upload an Excel file, choose pagination rules, and download the generated high-quality images in a ZIP archive.',
      featuresTitle: '✨ Key Features',
      features: [
        ['Excel to image', 'Supports .xlsx files and preserves table styling'],
        ['Smart pagination', 'Choose header rows and data rows per page'],
        ['Repeated headers', 'Include fixed headers in every image'],
        ['Multiple formats', 'Export PNG or JPG images'],
        ['Batch processing', 'Process multiple sheets in one job'],
        ['One-click download', 'Download all images in a ZIP archive'],
      ],
      scenariosTitle: '📋 Use Cases',
      scenarios: [
        ['💰 Refund forms', 'Generate refund-form images for customer support'],
        ['📦 Order snapshots', 'Convert order data into images for sharing or archiving'],
        ['📊 Data reports', 'Turn Excel reports into presentation-ready images'],
        ['🎨 Marketing assets', 'Create table-based campaign assets quickly'],
      ],
      usageTitle: '🚀 How to Use SheetFlow',
      usage: [
        'Upload an .xlsx Excel file',
        'Select the sheets to process',
        'Set header rows and data rows per page',
        'Choose PNG or JPG',
        'Click Generate',
        'Download the ZIP archive',
      ],
      faqTitle: '❓ Frequently Asked Questions',
      faq: [
        ['Which Excel formats are supported?', 'SheetFlow currently supports .xlsx files.'],
        ['Are complex Excel formulas supported?', 'SheetFlow reads cached formula results but does not recalculate formulas.'],
        ['What image quality does SheetFlow use?', 'Images are rendered at 2x resolution. PNG is lossless, while JPG quality is adjustable.'],
        ['Is there a file-size limit?', 'For the best experience, use files under 10 MB and sheets under 10,000 rows.'],
      ],
    })
  })
})
