import assert from 'node:assert/strict'
import { test } from 'node:test'
import WebSocket from 'ws'
import { imageForm, startTestApp } from './chat-test-harness.mjs'

const jpeg = Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46, 0x49, 0x46, 0xff, 0xd9])

test('existing chat API routes text through Orange Pi agent and persists its YOLO JPEG', async t => {
  Object.assign(process.env, {
    CHAT_PROVIDER: 'orangepi',
    AGENT_WS_ENABLED: 'true',
    AGENT_SHARED_SECRET: 'test-orangepi-agent-secret-at-least-32-chars',
    ORANGEPI_CHAT_TIMEOUT_MS: '2000',
  })
  const app = await startTestApp()
  t.after(() => app.close())
  const { agentRegistry } = await import('../src/agents/agentRegistry.js')
  const requests = []
  const socket = {
    readyState: WebSocket.OPEN,
    cleanScoutAgentKey: '',
    send(raw) {
      const payload = JSON.parse(raw)
      requests.push(payload)
      if (payload.type === 'ORANGEPI_CHAT_REQUEST') {
        setImmediate(() => agentRegistry.resolveOrangePiChat(socket, {
          type: 'ORANGEPI_CHAT_RESULT',
          requestId: payload.requestId,
          ok: true,
          reply: '测试：画面中检测到一个瓶子。',
          imageBase64: jpeg.toString('base64'),
          imageName: 'yolo-test.jpg',
          capturedAt: new Date().toISOString(),
          imageAgeMs: 120,
          yoloReachable: true,
          modelReady: true,
          model: 'agnes-2.5-flash',
        }))
      }
    },
    close() { this.readyState = WebSocket.CLOSED },
  }
  agentRegistry.register(socket, {
    token: process.env.AGENT_SHARED_SECRET,
    deviceId: 'cleanscout-001',
    agentId: 'orangepi-rk3588-test',
    agentType: 'orangepi-yolo-agent',
    capabilities: ['chat', 'yolo.snapshot'],
    yoloReachable: true,
    modelReady: true,
    model: 'agnes-2.5-flash',
  })
  t.after(() => agentRegistry.unregister(socket))

  const user = await app.login('orangepi-test-user')
  const status = await app.call('/api/chat/status', { token: user.token })
  assert.equal(status.status, 200)
  assert.equal(status.body.data.mode, 'orangepi')
  assert.equal(status.body.data.status, 'healthy')
  assert.equal(status.body.data.agentId, 'orangepi-rk3588-test')

  const response = await app.call('/api/chat/send', {
    token: user.token,
    method: 'POST',
    body: { content: '现在看到了什么？', requestId: crypto.randomUUID() },
  })
  assert.equal(response.status, 201)
  assert.equal(requests.at(-1).messages.at(-1).content, '现在看到了什么？')
  assert.equal(response.body.data.transport.mode, 'orangepi')
  assert.equal(response.body.data.replyMessage.type, 'image')
  assert.equal(response.body.data.replyMessage.content, '测试：画面中检测到一个瓶子。')
  assert.match(response.body.data.replyMessage.imageUrl, /^\/uploads\/chat\/[a-zA-Z0-9-]+\.jpg$/)

  const saved = await fetch(app.base + response.body.data.replyMessage.imageUrl, {
    headers: { Authorization: `Bearer ${user.token}` },
  })
  assert.equal(saved.status, 200)
  assert.deepEqual(Buffer.from(await saved.arrayBuffer()), jpeg)

  const history = await app.call('/api/chat/history', { token: user.token })
  assert.equal(history.body.data.length, 2)
  assert.equal(history.body.data[1].type, 'image')

  const upload = await app.call('/api/chat/image', {
    token: user.token,
    method: 'POST',
    body: imageForm({ content: '不要使用用户上传图片' }),
  })
  assert.equal(upload.status, 422)
  assert.equal(upload.body.code, 'CHAT_IMAGE_PROVIDER_UNSUPPORTED')
})
