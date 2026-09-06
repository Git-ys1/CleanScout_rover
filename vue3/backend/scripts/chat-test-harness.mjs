import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { execFileSync } from 'node:child_process'

export const backendRoot = fileURLToPath(new URL('../', import.meta.url))
export async function startTestApp() {
  const root = path.join(backendRoot, '.test-tmp')
  await mkdir(root, { recursive: true })
  const directory = await mkdtemp(path.join(root, 'chat-'))
  const envFile = path.join(directory, '.env')
  await writeFile(envFile, '')
  await writeFile(path.join(directory, 'test.db'), '')
  Object.assign(process.env, {
    ENV_FILE: envFile, DATABASE_URL: `file:../.test-tmp/${path.basename(directory)}/test.db`,
    CHAT_UPLOAD_DIR: path.join(directory, 'uploads'), JWT_SECRET: 'test-only-chat-integration-secret-not-for-deployment',
    OPENCLAW_ENABLED: 'false', CHAT_PROVIDER: process.env.CHAT_PROVIDER || 'mock',
  })
  execFileSync(process.execPath, [path.join(backendRoot, 'node_modules/prisma/build/index.js'), 'migrate', 'deploy'],
    { cwd: backendRoot, env: process.env, stdio: 'pipe' })
  const { default: app } = await import('../src/app.js')
  const { prisma } = await import('../src/utils/prisma.js')
  const http = await new Promise(resolve => { const server = app.listen(0, '127.0.0.1', () => resolve(server)) })
  const base = `http://127.0.0.1:${http.address().port}`
  async function call(url, { token, body, ...options } = {}) {
    const response = await fetch(base + url, { ...options,
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(body && !(body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}) },
      body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined })
    return { status: response.status, body: await response.json() }
  }
  async function login(username) {
    const password = 'test-password-123'
    const registration = await call('/api/auth/register', { method: 'POST', body: { username, password } })
    if (registration.status !== 201) throw new Error('Test user registration failed')
    const result = await call('/api/auth/login', { method: 'POST', body: { username, password } })
    if (result.status !== 200) throw new Error('Test login failed')
    return { token: result.body.data.token, user: result.body.data.user, password }
  }
  return { base, call, login, prisma, directory, async close() {
    await new Promise(resolve => { http.close(resolve); http.closeAllConnections() })
    await prisma.$disconnect()
    if (!path.resolve(directory).startsWith(path.resolve(root) + path.sep)) throw new Error('Invalid test cleanup path')
    await rm(directory, { recursive: true, force: true })
  } }
}

export const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWQAAAABJRU5ErkJggg==', 'base64')
export function imageForm({ bytes = png, type = 'image/png', name = 'test.png', content = '图里有什么？', requestId = crypto.randomUUID() } = {}) {
  const form = new FormData()
  form.append('file', new Blob([bytes], { type }), name)
  form.append('content', content)
  form.append('requestId', requestId)
  return form
}
