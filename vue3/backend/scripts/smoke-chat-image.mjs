import assert from 'node:assert/strict'

const baseUrl = String(process.env.SMOKE_BASE_URL || 'http://127.0.0.1:3000').replace(/\/$/, '')
const username = process.env.SMOKE_USERNAME || 'admin'
const password = process.env.SMOKE_PASSWORD || '123456'

async function parseResponse(response) {
  const body = await response.json()
  return { response, body }
}

async function upload({ token, bytes, name, type }) {
  const form = new FormData()
  form.append('file', new Blob([bytes], { type }), name)
  return parseResponse(await fetch(`${baseUrl}/api/chat/image`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  }))
}

const login = await parseResponse(await fetch(`${baseUrl}/api/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password }),
}))
assert.equal(login.response.status, 200, `登录失败：${JSON.stringify(login.body)}`)
const token = login.body.data.token

const pngBytes = Uint8Array.from([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
  0x00, 0x00, 0x00, 0x0d, 0x49, 0x48, 0x44, 0x52,
])
const validPng = await upload({ token, bytes: pngBytes, name: 'smoke.png', type: 'image/png' })
assert.equal(validPng.response.status, 201, `合法 PNG 应返回 201：${JSON.stringify(validPng.body)}`)
assert.match(validPng.body.data.userMessage.imageUrl, /\.png$/)

const plainText = await upload({ token, bytes: 'plain text', name: 'payload.txt', type: 'text/plain' })
assert.equal(plainText.response.status, 415, '普通文本应返回 415')

const forgedMime = await upload({ token, bytes: '{"name":"payload"}', name: 'payload.html', type: 'image/png' })
assert.equal(forgedMime.response.status, 415, '伪造 MIME/危险扩展名应被拒绝')

const unauthorized = await upload({ bytes: pngBytes, name: 'unauthorized.png', type: 'image/png' })
assert.equal(unauthorized.response.status, 401, '未登录上传应返回 401')

console.log('chat image smoke passed: valid PNG 201, text 415, forged MIME 415, unauthenticated 401')
