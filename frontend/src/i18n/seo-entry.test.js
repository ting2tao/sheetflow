// @vitest-environment node

import { execFileSync } from 'node:child_process'
import { mkdtemp, mkdir, readFile, readdir, writeFile } from 'node:fs/promises'
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
    expect(
      html.match(/content="%VITE_PUBLIC_SITE_URL%\/og-image\.png"/g),
    ).toHaveLength(2)
    expect(html).not.toContain(
      'content="%VITE_PUBLIC_SITE_URL%/favicon.svg"',
    )
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
    expect(
      html.match(/content="%VITE_PUBLIC_SITE_URL%\/og-image\.png"/g),
    ).toHaveLength(2)
    expect(html).not.toContain(
      'content="%VITE_PUBLIC_SITE_URL%/favicon.svg"',
    )
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

  test('ships a 1200 by 630 PNG social sharing image', async () => {
    const image = await readFile(
      path.join(frontendDir, 'public/og-image.png'),
    )

    expect(image.subarray(0, 8).toString('hex')).toBe('89504e470d0a1a0a')
    expect(image.subarray(12, 16).toString('ascii')).toBe('IHDR')
    expect(image.readUInt32BE(16)).toBe(1200)
    expect(image.readUInt32BE(20)).toBe(630)
  })
})

describe('SEO build configuration', () => {
  test.each([
    {
      label: 'a public HTTPS origin with trailing slashes',
      value: ' https://sheetflow.example/// ',
      expected: 'https://sheetflow.example',
    },
    {
      label: 'the local Docker HTTP origin',
      value: 'http://localhost///',
      expected: 'http://localhost',
    },
    {
      label: 'the IPv4 loopback HTTP origin',
      value: 'http://127.0.0.1:8080/',
      expected: 'http://127.0.0.1:8080',
    },
    {
      label: 'the IPv6 loopback HTTP origin',
      value: 'http://[::1]:8080/',
      expected: 'http://[::1]:8080',
    },
  ])('accepts and normalizes $label', async ({ value, expected }) => {
    const { normalizePublicSiteUrl } = await import('../../vite.config.js')

    expect(
      normalizePublicSiteUrl(value, { mode: 'production' }),
    ).toBe(expected)
  })

  test.each([
    { label: 'a missing value', value: undefined },
    { label: 'a public HTTP origin', value: 'http://not-production.example' },
    { label: 'a malformed value', value: 'not a URL' },
    { label: 'credentials', value: 'https://user:pass@example.com' },
    { label: 'a query', value: 'https://example.com?preview=true' },
    { label: 'a hash', value: 'https://example.com#preview' },
    { label: 'an encoded dot path', value: 'https://example.com/%2e%2e' },
    { label: 'an encoded slash path', value: 'https://example.com/%2F' },
    { label: 'a dot segment path', value: 'https://example.com/..' },
    { label: 'a path', value: 'https://example.com/path' },
  ])('rejects $label for production', async ({ value }) => {
    const { normalizePublicSiteUrl } = await import('../../vite.config.js')

    expect(() =>
      normalizePublicSiteUrl(value, { mode: 'production' }),
    ).toThrow(/VITE_PUBLIC_SITE_URL/)
  })

  test('uses the normalized public site URL in localized HTML', async () => {
    process.env.VITE_PUBLIC_SITE_URL = ' https://sheetflow.example/// '
    const { default: createConfig } = await import('../../vite.config.js')
    const config = createConfig({ command: 'build', mode: 'production' })

    expect(
      config.define['import.meta.env.VITE_PUBLIC_SITE_URL'],
    ).toBe(JSON.stringify('https://sheetflow.example'))
  })

  test('embeds the normalized public origin in the production runtime bundle', async () => {
    const temporaryRoot = await mkdtemp(
      path.join(tmpdir(), 'sheetflow-seo-runtime-'),
    )
    const distDir = path.join(temporaryRoot, 'dist')
    const viteBin = path.join(
      frontendDir,
      'node_modules/vite/bin/vite.js',
    )

    execFileSync(
      process.execPath,
      [viteBin, 'build', '--outDir', distDir, '--emptyOutDir'],
      {
        cwd: frontendDir,
        env: {
          ...process.env,
          VITE_PUBLIC_SITE_URL: 'https://sheetflow.example:443///',
        },
      },
    )

    const assetNames = await readdir(path.join(distDir, 'assets'))
    const mainBundleName = assetNames.find(name =>
      /^main-.*\.js$/.test(name),
    )
    expect(mainBundleName).toBeDefined()

    const mainBundle = await readFile(
      path.join(distDir, 'assets', mainBundleName),
      'utf8',
    )
    expect(mainBundle).toContain('https://sheetflow.example')
    expect(mainBundle).not.toContain('https://sheetflow.example:443///')
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
        VITE_PUBLIC_SITE_URL: 'https://sheetflow.example:443///',
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
    // Exact locations take precedence over the generic localized fallback.
    expect(nginx).toContain(
      'location = /robots.txt {\n        try_files /robots.txt =404;\n    }',
    )
    expect(nginx).toContain(
      'location = /sitemap.xml {\n        try_files /sitemap.xml =404;\n    }',
    )
    expect(nginx).toContain(
      'location = /zh {\n        return 301 /zh/;\n    }',
    )
    expect(nginx).toContain(
      'location = /en {\n        return 301 /en/;\n    }',
    )
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
    expect(workflow).toContain('case "$VITE_PUBLIC_SITE_URL" in')
    expect(workflow).toContain('https://*)')
    expect(workflow).toContain('build-args: |')
    expect(workflow).toContain(
      "description: 'Docker image tag to deploy (for example v1.0.0). Leave empty to use the triggering tag, or main for a branch/manual run.'",
    )
    expect(workflow).not.toContain('use the latest tag')
  })

  test('runs backend and frontend tests before building deployment images', async () => {
    const workflow = await readRepositoryFile('.github/workflows/ci-cd.yml')
    const backendJob = workflow.slice(
      workflow.indexOf('  build-backend:'),
      workflow.indexOf('  build-frontend:'),
    )
    const frontendJob = workflow.slice(
      workflow.indexOf('  build-frontend:'),
      workflow.indexOf('  deploy:'),
    )

    expect(backendJob).toContain('uses: actions/setup-python@v5')
    expect(backendJob).toContain("python-version: '3.11'")
    expect(backendJob).toContain(
      'pip install -r backend/requirements-dev.txt',
    )
    expect(backendJob).toContain('cd backend && PYTHONPATH=. pytest -q')
    expect(backendJob.indexOf('PYTHONPATH=. pytest -q')).toBeLessThan(
      backendJob.indexOf('- name: Build and push backend image'),
    )

    expect(frontendJob).toContain('uses: actions/setup-node@v4')
    expect(frontendJob).toContain("node-version: '20'")
    expect(frontendJob).toContain('cache: npm')
    expect(frontendJob).toContain(
      'cache-dependency-path: frontend/package-lock.json',
    )
    expect(frontendJob).toContain('cd frontend && npm ci')
    expect(frontendJob).toContain('cd frontend && npm test')
    expect(frontendJob.indexOf('cd frontend && npm test')).toBeLessThan(
      frontendJob.indexOf('- name: Build and push frontend image'),
    )
  })
})
