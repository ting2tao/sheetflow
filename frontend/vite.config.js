import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

const configRoot = fileURLToPath(new URL('.', import.meta.url))

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, configRoot, '')
  const publicSiteUrl = env.VITE_PUBLIC_SITE_URL?.trim().replace(/\/+$/, '')

  if (mode === 'production' && !publicSiteUrl) {
    throw new Error('VITE_PUBLIC_SITE_URL is required for production builds')
  }

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
