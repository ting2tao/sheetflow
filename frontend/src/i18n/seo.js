export const SEO_METADATA = {
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
}

function upsertHeadElement(selector, tagName, attributes = {}) {
  const matches = Array.from(document.head.querySelectorAll(selector))
  const element = matches.shift() ?? document.createElement(tagName)

  for (const duplicate of matches) {
    duplicate.remove()
  }
  for (const [name, value] of Object.entries(attributes)) {
    element.setAttribute(name, value)
  }
  if (!element.parentNode) {
    document.head.append(element)
  }

  return element
}

function setMeta(selector, identifyingAttributes, content) {
  upsertHeadElement(selector, 'meta', {
    ...identifyingAttributes,
    content,
  })
}

function setLink(selector, identifyingAttributes, href) {
  upsertHeadElement(selector, 'link', {
    ...identifyingAttributes,
    href,
  })
}

export function applyLocalizedSeo(locale, { origin } = {}) {
  const resolvedLocale = SEO_METADATA[locale] ? locale : 'zh-CN'
  const metadata = SEO_METADATA[resolvedLocale]
  const configuredOrigin = import.meta.env.VITE_PUBLIC_SITE_URL
  const siteOrigin = new URL(
    origin || configuredOrigin || window.location.origin,
  ).origin
  const pageUrl = `${siteOrigin}${metadata.path}`
  const imageUrl = `${siteOrigin}/og-image.png`

  document.documentElement.lang = resolvedLocale
  const title = upsertHeadElement('title', 'title')
  title.textContent = metadata.title

  setMeta('meta[name="title"]', { name: 'title' }, metadata.title)
  setMeta('meta[name="description"]', { name: 'description' }, metadata.description)
  setMeta('meta[name="keywords"]', { name: 'keywords' }, metadata.keywords)

  setMeta('meta[property="og:type"]', { property: 'og:type' }, 'website')
  setMeta('meta[property="og:title"]', { property: 'og:title' }, metadata.title)
  setMeta(
    'meta[property="og:description"]',
    { property: 'og:description' },
    metadata.description,
  )
  setMeta('meta[property="og:url"]', { property: 'og:url' }, pageUrl)
  setMeta('meta[property="og:locale"]', { property: 'og:locale' }, metadata.ogLocale)
  setMeta('meta[property="og:image"]', { property: 'og:image' }, imageUrl)

  setMeta('meta[name="twitter:card"]', { name: 'twitter:card' }, 'summary_large_image')
  setMeta('meta[name="twitter:title"]', { name: 'twitter:title' }, metadata.title)
  setMeta(
    'meta[name="twitter:description"]',
    { name: 'twitter:description' },
    metadata.description,
  )
  setMeta('meta[name="twitter:url"]', { name: 'twitter:url' }, pageUrl)
  setMeta('meta[name="twitter:image"]', { name: 'twitter:image' }, imageUrl)

  setLink('link[rel="canonical"]', { rel: 'canonical' }, pageUrl)
  const alternates = [
    ['zh-CN', `${siteOrigin}/zh/`],
    ['en', `${siteOrigin}/en/`],
    ['x-default', `${siteOrigin}/zh/`],
  ]
  for (const [hreflang, href] of alternates) {
    setLink(
      `link[rel="alternate"][hreflang="${hreflang}"]`,
      { rel: 'alternate', hreflang },
      href,
    )
  }

  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'WebApplication',
    name: 'SheetFlow',
    url: pageUrl,
    description: metadata.description,
    applicationCategory: 'UtilitiesApplication',
    operatingSystem: 'Web',
    inLanguage: resolvedLocale,
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: metadata.currency,
    },
    featureList: metadata.featureList,
  }
  const jsonLd = upsertHeadElement(
    'script[type="application/ld+json"]',
    'script',
    { type: 'application/ld+json' },
  )
  jsonLd.textContent = JSON.stringify(structuredData)
}
