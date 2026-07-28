import { readFile } from 'node:fs/promises'
import { beforeEach, describe, expect, it } from 'vitest'
import { SEO_METADATA, applyLocalizedSeo } from './seo'

const origin = 'https://sheetflow.example'

function metaContent(selector) {
  return document.head.querySelector(selector)?.getAttribute('content')
}

function linkHref(selector) {
  return document.head.querySelector(selector)?.getAttribute('href')
}

describe('SEO_METADATA', () => {
  it('matches the localized static entry metadata exactly', () => {
    expect(SEO_METADATA).toEqual({
      'zh-CN': {
        path: '/zh/',
        title: 'SheetFlow - Excel 表格分页图片生成器｜免费在线工具',
        description: '免费在线 Excel 转图片工具。上传 Excel 表格，自动分页生成 PNG/JPG 图片，支持固定表头和批量下载。',
        keywords: 'Excel转图片,表格截图,Excel分页,批量生成图片,固定表头,Excel工具,在线表格工具',
        ogLocale: 'zh_CN',
        currency: 'CNY',
        featureList: [
          '上传 Excel 表格',
          '自动分页生成图片',
          '重复固定表头',
          'PNG/JPG 图片输出',
          'ZIP 批量下载',
        ],
      },
      'en-US': {
        path: '/en/',
        title: 'SheetFlow - Excel Pagination Image Generator',
        description: 'Free online Excel-to-image tool. Paginate .xlsx sheets into PNG or JPG images with repeated headers and ZIP download.',
        keywords: 'Excel to image,Excel pagination,spreadsheet screenshot,repeated headers,PNG,JPG,ZIP download,online Excel tool',
        ogLocale: 'en_US',
        currency: 'USD',
        featureList: [
          'Upload Excel spreadsheets',
          'Automatically paginate sheets',
          'Repeat fixed headers',
          'Export PNG or JPG images',
          'Download every page as a ZIP archive',
        ],
      },
    })
  })

  it.each([
    ['zh-CN', '../../zh/index.html'],
    ['en-US', '../../en/index.html'],
  ])('stays aligned with the %s static entry', async (locale, path) => {
    const metadata = SEO_METADATA[locale]
    const html = await readFile(new URL(path, import.meta.url), 'utf8')

    expect(html).toContain(`<title>${metadata.title}</title>`)
    expect(html).toContain(
      `<meta name="description" content="${metadata.description}">`,
    )
    expect(html).toContain(
      `<meta name="keywords" content="${metadata.keywords}">`,
    )
    expect(html).toContain(`content="${metadata.ogLocale}"`)
    expect(html).toContain(`"priceCurrency": "${metadata.currency}"`)
    for (const feature of metadata.featureList) {
      expect(html).toContain(`"${feature}"`)
    }
  })
})

describe('applyLocalizedSeo', () => {
  beforeEach(() => {
    document.head.innerHTML = ''
    document.documentElement.lang = ''
  })

  it('replaces Chinese head metadata with complete English metadata without duplicates', () => {
    applyLocalizedSeo('zh-CN', { origin })
    applyLocalizedSeo('en-US', { origin })
    applyLocalizedSeo('en-US', { origin })

    const metadata = SEO_METADATA['en-US']
    expect(document.documentElement.lang).toBe('en-US')
    expect(document.title).toBe(metadata.title)
    expect(metaContent('meta[name="title"]')).toBe(metadata.title)
    expect(metaContent('meta[name="description"]')).toBe(metadata.description)
    expect(metaContent('meta[name="keywords"]')).toBe(metadata.keywords)
    expect(metaContent('meta[property="og:title"]')).toBe(metadata.title)
    expect(metaContent('meta[property="og:description"]')).toBe(metadata.description)
    expect(metaContent('meta[property="og:url"]')).toBe(`${origin}/en/`)
    expect(metaContent('meta[property="og:locale"]')).toBe('en_US')
    expect(metaContent('meta[property="og:image"]')).toBe(`${origin}/og-image.png`)
    expect(metaContent('meta[name="twitter:title"]')).toBe(metadata.title)
    expect(metaContent('meta[name="twitter:description"]')).toBe(metadata.description)
    expect(metaContent('meta[name="twitter:url"]')).toBe(`${origin}/en/`)
    expect(metaContent('meta[name="twitter:image"]')).toBe(`${origin}/og-image.png`)
    expect(linkHref('link[rel="canonical"]')).toBe(`${origin}/en/`)

    expect(
      Array.from(document.head.querySelectorAll('link[rel="alternate"]')).map(link => ({
        hreflang: link.getAttribute('hreflang'),
        href: link.getAttribute('href'),
      })),
    ).toEqual([
      { hreflang: 'zh-CN', href: `${origin}/zh/` },
      { hreflang: 'en', href: `${origin}/en/` },
      { hreflang: 'x-default', href: `${origin}/zh/` },
    ])

    const structuredData = JSON.parse(
      document.head.querySelector('script[type="application/ld+json"]').textContent,
    )
    expect(structuredData).toMatchObject({
      '@context': 'https://schema.org',
      '@type': 'WebApplication',
      name: 'SheetFlow',
      url: `${origin}/en/`,
      description: metadata.description,
      inLanguage: 'en-US',
      featureList: metadata.featureList,
      offers: {
        '@type': 'Offer',
        price: '0',
        priceCurrency: 'USD',
      },
    })

    for (const selector of [
      'meta[name="title"]',
      'meta[name="description"]',
      'meta[name="keywords"]',
      'meta[property="og:title"]',
      'meta[property="og:description"]',
      'meta[property="og:url"]',
      'meta[property="og:locale"]',
      'meta[property="og:image"]',
      'meta[name="twitter:title"]',
      'meta[name="twitter:description"]',
      'meta[name="twitter:url"]',
      'meta[name="twitter:image"]',
      'link[rel="canonical"]',
      'link[rel="alternate"][hreflang="zh-CN"]',
      'link[rel="alternate"][hreflang="en"]',
      'link[rel="alternate"][hreflang="x-default"]',
      'script[type="application/ld+json"]',
    ]) {
      expect(document.head.querySelectorAll(selector), selector).toHaveLength(1)
    }
  })

  it('uses the browser origin by default', () => {
    applyLocalizedSeo('zh-CN')

    expect(linkHref('link[rel="canonical"]')).toBe(`${window.location.origin}/zh/`)
    expect(metaContent('meta[property="og:image"]')).toBe(
      `${window.location.origin}/og-image.png`,
    )
  })
})
