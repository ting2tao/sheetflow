import { readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const token = '__SHEETFLOW_PUBLIC_SITE_URL__'
const frontendDir = fileURLToPath(new URL('../', import.meta.url))
const siteUrl = process.env.VITE_PUBLIC_SITE_URL?.trim().replace(/\/+$/, '')
const distDir = process.env.SHEETFLOW_DIST_DIR
  ? resolve(process.env.SHEETFLOW_DIST_DIR)
  : resolve(frontendDir, 'dist')

if (!siteUrl) {
  throw new Error('VITE_PUBLIC_SITE_URL is required to write SEO files')
}

for (const fileName of ['sitemap.xml', 'robots.txt']) {
  const filePath = resolve(distDir, fileName)
  const source = await readFile(filePath, 'utf8')

  if (!source.includes(token)) {
    throw new Error(`${fileName} does not contain the required ${token} token`)
  }

  await writeFile(filePath, source.replaceAll(token, siteUrl), 'utf8')
}
