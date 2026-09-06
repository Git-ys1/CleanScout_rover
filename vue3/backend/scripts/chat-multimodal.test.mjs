import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createServer } from 'node:http'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import { readFile } from 'node:fs/promises'
import { startTestApp, imageForm, backendRoot, png } from './chat-test-harness.mjs'

test('authenticated Express / Prisma multimodal workflow (stub upstream, no real API)', async t => {
  const received = []
  let behavior = 'ok'
  const stub = createServer(async (req, res) => {
    if (req.url === '/v1/models') {
      res.setHeader('Content-Type', 'application/json')
      res.end(JSON.stringify({ data: [{ id: 'openclaw/default' }] }))
      return
    }
    let raw = ''
    for await (const chunk of req) raw += chunk
    received.push({ body: JSON.parse(raw), authorization: req.headers.authorization, url: req.url })
    if (behavior === 'timeout') return
    if (behavior === 'http-error') { res.writeHead(429); res.end('{}'); return }
    if (behavior === 'invalid-json') { res.end('not-json'); return }
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify({ choices: [{ message: { content: behavior === 'empty' ? '' : '自动测试桩回复（不是实际识图）' }, finish_reason: 'stop' }] }))
  })
  await new Promise(resolve => stub.listen(0, '127.0.0.1', resolve))
  t.after(async () => { stub.closeAllConnections(); await new Promise(resolve => stub.close(resolve)) })
  Object.assign(process.env, { CHAT_PROVIDER: 'agnes', AGNES_API_KEY: 'test-only-placeholder',
    AGNES_BASE_URL: `http://127.0.0.1:${stub.address().port}/v1`, AGNES_TIMEOUT_MS: '1000' })
  const app = await startTestApp()
  t.after(() => app.close())
  const alice = await app.login('test-alice'), bob = await app.login('test-bob')
  const text = (token, content, requestId = crypto.randomUUID()) => app.call('/api/chat/send', { token, method: 'POST', body: { content, requestId } })
  const image = (token, options) => app.call('/api/chat/image', { token, method: 'POST', body: imageForm(options) })
  let imageMessage

  await t.test('mode, authenticated text and configurable prompt', async () => {
    process.env.AGNES_SYSTEM_PROMPT = 'CleanScout test system prompt'
    const status = await app.call('/api/chat/status', { token: alice.token })
    assert.equal(status.body.data.mode, 'agnes')
    assert.ok(!JSON.stringify(status.body).includes(process.env.AGNES_API_KEY))
    const response = await text(alice.token, 'text-question')
    assert.equal(response.status, 201)
    assert.equal(received.at(-1).body.messages[0].content, process.env.AGNES_SYSTEM_PROMPT)
    assert.equal(received.at(-1).body.messages.at(-1).content, 'text-question')
    assert.equal(received.at(-1).url, '/v1/chat/completions')
  })
  await t.test('image and question use Data URL, not upload path', async () => {
    const response = await image(alice.token, { content: 'image-question' })
    assert.equal(response.status, 201)
    imageMessage = response.body.data.userMessage
    assert.equal(imageMessage.content, 'image-question')
    const blocks = received.at(-1).body.messages.at(-1).content
    assert.equal(blocks[0].text, 'image-question')
    assert.equal(blocks[1].image_url.url, `data:image/png;base64,${png.toString('base64')}`)
    assert.ok(!JSON.stringify(received.at(-1).body).includes('/uploads/'))
  })
  await t.test('follow-up contains image; latest history, not earliest', async () => {
    await text(alice.token, 'follow-up')
    assert.ok(received.at(-1).body.messages.some(m => Array.isArray(m.content)))
    for (let i = 0; i < 14; i++) assert.equal((await text(alice.token, `recent-${i}`)).status, 201)
    const messages = received.at(-1).body.messages
    assert.equal(messages.length, 26) // system + latest 24 messages + current
    assert.ok(!JSON.stringify(messages).includes('text-question'))
    assert.ok(JSON.stringify(messages).includes('recent-12'))
    assert.equal(messages.at(-1).content, 'recent-13')
  })
  await t.test('history reload and authenticated image access isolate users', async () => {
    const history = await app.call('/api/chat/history', { token: alice.token })
    assert.ok(history.body.data.some(m => m.id === imageMessage.id))
    const restored = await fetch(app.base + imageMessage.imageUrl, { headers: { Authorization: `Bearer ${alice.token}` } })
    assert.equal(restored.status, 200)
    assert.deepEqual(Buffer.from(await restored.arrayBuffer()), png)
    assert.equal((await fetch(app.base + imageMessage.imageUrl)).status, 401)
    assert.equal((await fetch(app.base + imageMessage.imageUrl, { headers: { Authorization: `Bearer ${bob.token}` } })).status, 404)
    assert.equal((await app.call('/api/chat/history', { token: bob.token })).body.data.length, 0)
    await text(bob.token, 'bob-only')
    assert.equal(received.at(-1).body.messages.length, 2)
    assert.ok(!JSON.stringify(received.at(-1)).includes('recent-'))
  })
  await t.test('retry and concurrent repeated request persist only one pair', async () => {
    const id = crypto.randomUUID(), before = received.length
    const responses = await Promise.all([text(alice.token, 'idempotent', id), text(alice.token, 'idempotent', id)])
    assert.equal(responses[0].status, 201)
    assert.deepEqual(responses[0].body, responses[1].body)
    assert.equal(received.length, before + 1)
    assert.equal((await text(alice.token, 'different', id)).status, 409)
    assert.equal((await text(bob.token, 'other-user', id)).status, 201)
    const imageId = crypto.randomUUID()
    const first = await image(alice.token, { requestId: imageId })
    const second = await image(alice.token, { requestId: imageId })
    assert.equal(first.body.data.userMessage.id, second.body.data.userMessage.id)
  })
  await t.test('missing key fails explicitly without messages; original ID can retry', async () => {
    const before = await app.prisma.messageCache.count(), id = crypto.randomUUID()
    delete process.env.AGNES_API_KEY
    const response = await text(alice.token, 'retry-key', id)
    assert.equal(response.status, 503)
    assert.equal(response.body.code, 'AGNES_KEY_MISSING')
    assert.equal(await app.prisma.messageCache.count(), before)
    process.env.AGNES_API_KEY = 'test-only-placeholder'
    assert.equal((await text(alice.token, 'retry-key', id)).status, 201)
    assert.equal(await app.prisma.messageCache.count(), before + 2)
  })
  for (const [mode, status, code] of [['http-error', 502, 'AGNES_HTTP_ERROR'], ['empty', 502, 'AGNES_EMPTY_REPLY'],
    ['invalid-json', 502, 'AGNES_NETWORK_ERROR'], ['timeout', 504, 'AGNES_TIMEOUT']]) {
    await t.test(`model failure ${mode}: no fake reply or partial image/message`, async () => {
      const before = await app.prisma.messageCache.count()
      behavior = mode
      process.env.AGNES_TIMEOUT_MS = '100'
      const response = await image(bob.token)
      assert.equal(response.status, status)
      assert.equal(response.body.code, code)
      assert.equal(await app.prisma.messageCache.count(), before)
      behavior = 'ok'
      process.env.AGNES_TIMEOUT_MS = '1000'
    })
  }
  await t.test('network failure is explicit', async () => {
    const original = process.env.AGNES_BASE_URL
    process.env.AGNES_BASE_URL = 'http://127.0.0.1:1/v1'
    assert.equal((await text(bob.token, 'network-error')).body.code, 'AGNES_NETWORK_ERROR')
    process.env.AGNES_BASE_URL = original
  })
  await t.test('invalid format, signature, size and unauthenticated upload', async () => {
    assert.equal((await image(alice.token, { bytes: 'text', type: 'text/plain' })).status, 415)
    assert.equal((await image(alice.token, { bytes: '<script>bad</script>' })).status, 415)
    assert.equal((await image(alice.token, { bytes: Buffer.alloc(10 * 1024 * 1024 + 1) })).status, 400)
    assert.equal((await image(null)).status, 401)
  })
  await t.test('existing smoke:chat-image regression in explicit mock mode', async () => {
    process.env.CHAT_PROVIDER = 'mock'
    const result = await promisify(execFile)(process.execPath, ['scripts/smoke-chat-image.mjs'], { cwd: backendRoot,
      env: { ...process.env, SMOKE_BASE_URL: app.base, SMOKE_USERNAME: 'test-alice', SMOKE_PASSWORD: alice.password } })
    assert.match(result.stdout, /chat image smoke passed/)
    console.log(result.stdout.trim())
  })
  await t.test('OpenClaw disabled keeps labeled mock entry', async () => {
    process.env.CHAT_PROVIDER = 'openclaw'
    const result = await text(bob.token, 'legacy')
    assert.equal(result.body.data.transport.mode, 'mock')
    assert.match(result.body.data.replyMessage.content, /模拟回复/)
  })
  await t.test('enabled OpenClaw keeps text entry; errors never become successful mock replies', async () => {
    Object.assign(process.env, { OPENCLAW_ENABLED: 'true', OPENCLAW_BASE_URL: `http://127.0.0.1:${stub.address().port}`,
      OPENCLAW_API_MODE: 'chat', OPENCLAW_MODEL: 'openclaw/default' })
    await app.prisma.systemConfig.update({ where: { id: 'system' }, data: { openclawEnabled: true } })
    const response = await text(bob.token, 'openclaw-text')
    assert.equal(response.status, 201)
    assert.equal(response.body.data.transport.mode, 'openclaw')
    assert.equal((await image(bob.token)).body.code, 'CHAT_IMAGE_PROVIDER_UNSUPPORTED')
    const count = await app.prisma.messageCache.count()
    behavior = 'http-error'
    assert.equal((await text(bob.token, 'openclaw-error')).body.code, 'OPENCLAW_CHAT_FAILED')
    assert.equal(await app.prisma.messageCache.count(), count)
    behavior = 'ok'
    process.env.OPENCLAW_ENABLED = 'false'
  })
  await t.test('history exists in persistent Prisma database after reconnect', async () => {
    await app.prisma.$disconnect()
    const history = await app.call('/api/chat/history', { token: alice.token })
    assert.equal(history.status, 200)
    assert.ok(history.body.data.some(m => m.id === imageMessage.id))
    assert.deepEqual(await readFile(process.env.CHAT_UPLOAD_DIR + '/' + imageMessage.imageUrl.split('/').at(-1)), png)
  })
  await t.test('completed request is replayed from Prisma after disconnect', async () => {
    const saved = await app.prisma.chatRequest.findFirst({ where: { userId: bob.user.id, status: 'succeeded' } })
    const original = JSON.parse(saved.response)
    const before = received.length
    await app.prisma.$disconnect()
    const result = await text(bob.token, original.userMessage.content, saved.requestId)
    assert.equal(result.status, 201)
    assert.equal(result.body.data.replyMessage.id, original.replyMessage.id)
    assert.equal(received.length, before)
  })
})
