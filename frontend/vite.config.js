import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

const configRoot = fileURLToPath(new URL('.', import.meta.url))

export function normalizePublicSiteUrl(value, { mode = 'development' } = {}) {
  const trimmed = typeof value === 'string' ? value.trim() : ''

  if (!trimmed) {
    if (mode === 'production') {
      throw new Error('VITE_PUBLIC_SITE_URL is required for production builds')
    }

    return ''
  }

  let siteUrl

  try {
    siteUrl = new URL(trimmed)
  } catch {
    throw new Error('VITE_PUBLIC_SITE_URL must be a valid absolute URL')
  }

  if (!['http:', 'https:'].includes(siteUrl.protocol)) {
    throw new Error('VITE_PUBLIC_SITE_URL must use HTTP or HTTPS')
  }

  if (siteUrl.username || siteUrl.password) {
    throw new Error('VITE_PUBLIC_SITE_URL must not contain credentials')
  }

  if (
    siteUrl.search ||
    siteUrl.hash ||
    trimmed.includes('?') ||
    trimmed.includes('#')
  ) {
    throw new Error('VITE_PUBLIC_SITE_URL must not contain a query or hash')
  }

  const rawOriginPattern =
    /^[A-Za-z][A-Za-z\d+.-]*:\/\/[^/\\?#\s]+\/*$/

  if (!rawOriginPattern.test(trimmed)) {
    throw new Error('VITE_PUBLIC_SITE_URL must not contain a path')
  }

  const localHosts = new Set(['localhost', '127.0.0.1', '[::1]'])
  const isLocalHttp =
    siteUrl.protocol === 'http:' && localHosts.has(siteUrl.hostname)

  if (
    mode === 'production' &&
    siteUrl.protocol !== 'https:' &&
    !isLocalHttp
  ) {
    throw new Error(
      'VITE_PUBLIC_SITE_URL must use HTTPS except for local development',
    )
  }

  return siteUrl.origin
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, configRoot, '')
  const publicSiteUrl = normalizePublicSiteUrl(
    env.VITE_PUBLIC_SITE_URL,
    { mode },
  )

  return {
    plugins: [vue()],
    define: publicSiteUrl
      ? {
          'import.meta.env.VITE_PUBLIC_SITE_URL':
            JSON.stringify(publicSiteUrl),
        }
      : {},
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      rollupOptions: {
        input: {
          root: resolve(configRoot, 'index.html'),
          zh: resolve(configRoot, 'zh/index.html'),
          en: resolve(configRoot, 'en/index.html'),
        },
      },
    },
    test: {
      environment: 'jsdom',
      clearMocks: true,
    },
  }
})
