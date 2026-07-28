// @vitest-environment node

import { execFileSync } from 'node:child_process'
import { mkdtemp, mkdir, readFile, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { afterEach, describe, expect, test } from 'vitest'

const frontendDir = fileURLToPath(new URL('../../', import.meta.url))
const repositoryDir = path.resolve(frontendDir, '..')

const readFrontendFile = (relativePath) =>
  readFile(path.join(frontendDir, relativePath), 'utf8')

const readRepositoryFile = (relativePath) =>
  readFile(path.join(repositoryDir, relativePath), 'utf8')

const originalPublicSiteUrl = process.env.VITE_PUBLIC_SITE_URL

afterEach(() => {
  if (originalPublicSiteUrl === undefined) {
    delete process.env.VITE_PUBLIC_SITE_URL
  } else {
    process.env.VITE_PUBLIC_SITE_URL = originalPublicSiteUrl
  }
})

describe('localized SEO entry points', () => {
  test('publishes a complete Chinese entry point', async () => {
    const html = await readFrontendFile('zh/index.html')

    expect(html).toContain('<html lang="zh-CN">')
    expect(html).toContain(
      '<title>SheetFlow - Excel 表格分页图片生成器｜免费在线工具</title>',
    )
    expect(html).toContain(
      '免费在线 Excel 转图片工具。上传 Excel 表格，自动分页生成 PNG/JPG 图片，支持固定表头和批量下载。',
    )
    expect(html).toContain(
      '<link rel="canonical" href="%VITE_PUBLIC_SITE_URL%/zh/">',
    )
    expect(html).toContain('hreflang="en"')
    expect(html).toContain('hreflang="zh-CN"')
    expect(html).toContain('hreflang="x-default"')
    expect(html).toContain('content="%VITE_PUBLIC_SITE_URL%/zh/"')
    expect(html).toContain('content="%VITE_PUBLIC_SITE_URL%/og-image.png"')
    expect(html).toContain('"inLanguage": "zh-CN"')
    expect(html).toContain('"priceCurrency": "CNY"')
    expect(html).toContain('<div id="app"></div>')
    expect(html).toContain('<script type="module" src="/src/main.js"></script>')
    expect(html).toContain('/favicon.svg')
    expect(html).toContain('googletagmanager.com/gtag/js')
    expect(html).not.toContain('yourdomain')
  })

  test('publishes a complete English entry point', async () => {
    const html = await readFrontendFile('en/index.html')

    expect(html).toContain('<html lang="en-US">')
    expect(html).toContain(
      '<title>SheetFlow - Excel Pagination Image Generator</title>',
    )
    expect(html).toContain(
      'Free online Excel-to-image tool. Paginate .xlsx sheets into PNG or JPG images with repeated headers and ZIP download.',
    )
    expect(html).toContain(
      '<link rel="canonical" href="%VITE_PUBLIC_SITE_URL%/en/">',
    )
    expect(html).toContain('hreflang="zh-CN"')
    expect(html).toContain('hreflang="en"')
    expect(html).toContain('hreflang="x-default"')
    expect(html).toContain('content="%VITE_PUBLIC_SITE_URL%/en/"')
    expect(html).toContain('content="%VITE_PUBLIC_SITE_URL%/og-image.png"')
    expect(html).toContain('"inLanguage": "en-US"')
    expect(html).toContain('"priceCurrency": "USD"')
    expect(html).toContain('<div id="app"></div>')
    expect(html).toContain('<script type="module" src="/src/main.js"></script>')
    expect(html).toContain('/favicon.svg')
    expect(html).toContain('googletagmanager.com/gtag/js')
    expect(html).not.toContain('yourdomain')
  })

  test('keeps the root entry neutral and out of search indexes', async () => {
    const html = await readFrontendFile('index.html')

    expect(html).toContain('<html lang="zh-CN">')
    expect(html).toContain('<title>SheetFlow</title>')
    expect(html).toContain('<meta name="robots" content="noindex, follow">')
    expect(html).toContain('<div id="app"></div>')
    expect(html).toContain('<script type="module" src="/src/main.js"></script>')
    expect(html).not.toContain('rel="canonical"')
    expect(html).not.toContain('application/ld+json')
    expect(html).not.toContain('<noscript>')
    expect(html).not.toContain('property="og:')
    expect(html).not.toContain('yourdomain')
  })

  test('lists both localized pages and all alternates in the sitemap', async () => {
    const sitemap = await readFrontendFile('public/sitemap.xml')
    const token = '__SHEETFLOW_PUBLIC_SITE_URL__'

    expect(sitemap).toContain('xmlns:xhtml="http://www.w3.org/1999/xhtml"')
    expect(sitemap.match(/<url>/g)).toHaveLength(2)
    expect(sitemap).toContain(`<loc>${token}/zh/</loc>`)
    expect(sitemap).toContain(`<loc>${token}/en/</loc>`)
    expect(sitemap.match(/hreflang="zh-CN"/g)).toHaveLength(2)
    expect(sitemap.match(/hreflang="en"/g)).toHaveLength(2)
    expect(sitemap.match(/hreflang="x-default"/g)).toHaveLength(2)
    expect(sitemap).not.toContain('yourdomain')
  })

  test('keeps protected paths out of robots and uses the public URL token', async () => {
    const robots = await readFrontendFile('public/robots.txt')

    // API and download output must remain excluded from crawler discovery.
    expect(robots).toContain('Disallow: /api/')
    expect(robots).toContain('Disallow: /download/')
    expect(robots).toContain(
      'Sitemap: __SHEETFLOW_PUBLIC_SITE_URL__/sitemap.xml',
    )
    expect(robots).not.toContain('yourdomain')
  })
})

describe('SEO build configuration', () => {
  test('requires a public site URL for production builds', async () => {
    delete process.env.VITE_PUBLIC_SITE_URL
    const { default: createConfig } = await import('../../vite.config.js')

    expect(() =>
      createConfig({ command: 'build', mode: 'production' }),
    ).toThrow(/VITE_PUBLIC_SITE_URL/)
  })

  test('normalizes the public site URL used in localized HTML', async () => {
    process.env.VITE_PUBLIC_SITE_URL = ' https://sheetflow.example/// '
    const { default: createConfig } = await import('../../vite.config.js')
    const config = createConfig({ command: 'build', mode: 'production' })

    expect(
      config.define['import.meta.env.VITE_PUBLIC_SITE_URL'],
    ).toBe(JSON.stringify('https://sheetflow.example'))
  })

  test('replaces every SEO host token without mutating the source files', async () => {
    const temporaryRoot = await mkdtemp(
      path.join(tmpdir(), 'sheetflow-seo-entry-'),
    )
    const distDir = path.join(temporaryRoot, 'dist')
    await mkdir(distDir)
    await writeFile(
      path.join(distDir, 'sitemap.xml'),
      '<loc>__SHEETFLOW_PUBLIC_SITE_URL__/zh/</loc>\n<loc>__SHEETFLOW_PUBLIC_SITE_URL__/en/</loc>',
      'utf8',
    )
    await writeFile(
      path.join(distDir, 'robots.txt'),
      'Sitemap: __SHEETFLOW_PUBLIC_SITE_URL__/sitemap.xml',
      'utf8',
    )

    execFileSync(process.execPath, ['scripts/write-seo-files.mjs'], {
      cwd: frontendDir,
      env: {
        ...process.env,
        VITE_PUBLIC_SITE_URL: 'https://sheetflow.example///',
        SHEETFLOW_DIST_DIR: distDir,
      },
    })

    const sitemap = await readFile(path.join(distDir, 'sitemap.xml'), 'utf8')
    const robots = await readFile(path.join(distDir, 'robots.txt'), 'utf8')
    const sourceSitemap = await readFrontendFile('public/sitemap.xml')

    expect(sitemap).toContain('https://sheetflow.example/zh/')
    expect(sitemap).toContain('https://sheetflow.example/en/')
    expect(robots).toBe(
      'Sitemap: https://sheetflow.example/sitemap.xml',
    )
    expect(sitemap).not.toContain('__SHEETFLOW_PUBLIC_SITE_URL__')
    expect(robots).not.toContain('__SHEETFLOW_PUBLIC_SITE_URL__')
    expect(sourceSitemap).toContain('__SHEETFLOW_PUBLIC_SITE_URL__')
  })

  test('wires localized build, proxy, container, and CI settings', async () => {
    const [
      viteConfig,
      main,
      nginx,
      packageJson,
      dockerfile,
      compose,
      workflow,
    ] = await Promise.all([
      readFrontendFile('vite.config.js'),
      readFrontendFile('src/main.js'),
      readFrontendFile('nginx.conf'),
      readFrontendFile('package.json'),
      readFrontendFile('Dockerfile'),
      readRepositoryFile('docker-compose.yml'),
      readRepositoryFile('.github/workflows/ci-cd.yml'),
    ])

    expect(viteConfig).toContain("fileURLToPath(new URL('.', import.meta.url))")
    expect(viteConfig).toContain("root: resolve(configRoot, 'index.html')")
    expect(viteConfig).toContain("zh: resolve(configRoot, 'zh/index.html')")
    expect(viteConfig).toContain("en: resolve(configRoot, 'en/index.html')")
    expect(viteConfig).toContain("'/api'")
    expect(main).toContain("window.location.pathname === '/'")
    expect(main).toContain(
      'window.location.replace(localizedPath(resolveInitialLocale()))',
    )
    expect(main).toContain('.use(i18n).mount')
    expect(nginx).toMatch(/location = \/ \{[\s\S]*try_files \/index\.html =404;/)
    expect(nginx).toContain('location /api/ {')
    expect(nginx).not.toContain('location ^~ /api/ {')
    expect(nginx).toContain('location /download/ {')
    expect(nginx).not.toContain('location ^~ /download/ {')
    expect(nginx).toMatch(/location \/zh\/ \{[\s\S]*\/zh\/index\.html;/)
    expect(nginx).toMatch(/location \/en\/ \{[\s\S]*\/en\/index\.html;/)
    expect(nginx).not.toContain('location ^~ /zh/ {')
    expect(nginx).not.toContain('location ^~ /en/ {')
    expect(nginx).toContain('return 302 /zh/;')
    expect(nginx).not.toContain('@localized_redirect')
    expect(nginx).toMatch(
      /location ~\* \\\.\(js\|css\|png\|jpg\|jpeg\|gif\|ico\|svg\)\$ \{\s+expires 1y;\s+add_header Cache-Control "public, immutable";\s+\}/,
    )
    expect(packageJson).toContain(
      '"build": "vite build && node scripts/write-seo-files.mjs"',
    )
    expect(dockerfile).toContain('ARG VITE_PUBLIC_SITE_URL')
    expect(dockerfile).toContain('ENV VITE_PUBLIC_SITE_URL=$VITE_PUBLIC_SITE_URL')
    expect(compose).toContain('VITE_PUBLIC_SITE_URL: ${VITE_PUBLIC_SITE_URL:-http://localhost}')
    expect(workflow).toContain('VITE_PUBLIC_SITE_URL: ${{ vars.PUBLIC_SITE_URL }}')
    expect(workflow).toContain('build-args: |')
  })
})
