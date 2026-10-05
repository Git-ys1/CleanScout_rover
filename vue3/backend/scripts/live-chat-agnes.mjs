// Explicit opt-in real API check. Sends only a generated geometric scene and test questions.
import assert from 'node:assert/strict'
import { deflateSync } from 'node:zlib'
import { startTestApp, imageForm } from './chat-test-harness.mjs'

if (!process.env.AGNES_API_KEY) throw new Error('Set AGNES_API_KEY in the server process environment before this real API check.')
process.env.CHAT_PROVIDER = 'agnes'

function scene() {
  const width = 300, height = 160, rows = Buffer.alloc((width * 3 + 1) * height)
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      let rgb = [255, 255, 255]
      if (x >= 25 && x < 115 && y >= 35 && y < 125) rgb = [235, 30, 30]
      if ((x - 220) ** 2 + (y - 80) ** 2 < 45 ** 2) rgb = [20, 70, 235]
      rows.set(rgb, y * (width * 3 + 1) + 1 + x * 3)
    }
  }
  function chunk(name, data) {
    const type = Buffer.from(name), length = Buffer.alloc(4), sum = Buffer.alloc(4)
    length.writeUInt32BE(data.length)
    let crc = 0xffffffff
    for (const byte of Buffer.concat([type, data])) {
      crc ^= byte
      for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0)
    }
    sum.writeUInt32BE((crc ^ 0xffffffff) >>> 0)
    return Buffer.concat([length, type, data, sum])
  }
  const header = Buffer.alloc(13)
  header.writeUInt32BE(width); header.writeUInt32BE(height, 4); header[8] = 8; header[9] = 2
  return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]), chunk('IHDR', header), chunk('IDAT', deflateSync(rows)), chunk('IEND', Buffer.alloc(0))])
}

const app = await startTestApp()
try {
  const { token } = await app.login('live-synthetic-check')
  const bytes = scene(), requestId = crypto.randomUUID()
  const result = await app.call('/api/chat/image', { token, method: 'POST', body: imageForm({ bytes, name: 'synthetic-scene.png',
    content: '请用中文描述图中两个图形的形状、颜色和左右位置。', requestId }) })
  assert.equal(result.status, 201, JSON.stringify(result.body))
  console.log(JSON.stringify({ type: 'real-image-reply', model: result.body.data.transport.model, reply: result.body.data.replyMessage.content }))
  const followup = await app.call('/api/chat/send', { token, method: 'POST', body: {
    content: '右边图形是什么颜色、什么形状？请用中文简短回答。', requestId: crypto.randomUUID() } })
  assert.equal(followup.status, 201, JSON.stringify(followup.body))
  console.log(JSON.stringify({ type: 'real-followup-reply', reply: followup.body.data.replyMessage.content }))
  const restored = await app.call('/api/chat/history', { token })
  assert.equal(restored.body.data.length, 4)
  const image = await fetch(app.base + result.body.data.userMessage.imageUrl, { headers: { Authorization: `Bearer ${token}` } })
  assert.equal(image.status, 200)
  assert.deepEqual(Buffer.from(await image.arrayBuffer()), bytes)
  const replay = await app.call('/api/chat/image', { token, method: 'POST', body: imageForm({ bytes, name: 'synthetic-scene.png',
    content: '请用中文描述图中两个图形的形状、颜色和左右位置。', requestId }) })
  assert.equal(replay.body.data.replyMessage.id, result.body.data.replyMessage.id)
  assert.equal(await app.prisma.messageCache.count(), 4)
  console.log('Real HTTP image + follow-up + history + image reload + retry replay completed. Review the model replies above for factual accuracy.')
} finally {
  await app.close()
}
