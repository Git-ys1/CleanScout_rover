import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdir, mkdtemp, rm } from 'node:fs/promises'
import { pathToFileURL, fileURLToPath } from 'node:url'
import path from 'node:path'
import { build } from 'esbuild'
import { createPinia, setActivePinia } from 'pinia'

const root = fileURLToPath(new URL('../', import.meta.url))
await mkdir(path.join(root, '.test-tmp'), { recursive: true })
const directory = await mkdtemp(path.join(root, '.test-tmp/store-'))
const output = path.join(directory, 'stores.mjs')
await build({ stdin: { contents: "export { useChatStore } from './src/stores/chat.js'; export { useAuthStore } from './src/stores/auth.js';", resolveDir: root },
  bundle: true, platform: 'node', format: 'esm', external: ['pinia', 'vue'], outfile: output,
  define: { 'import.meta.env': JSON.stringify({ VITE_API_BASE_URL: 'http://127.0.0.1:3000/api' }) } })
const { useChatStore, useAuthStore } = await import(pathToFileURL(output).href)
await test('real Pinia store: retries, images and login isolation', async t => {
  t.after(async () => {
    if (!path.resolve(directory).startsWith(path.join(root, '.test-tmp') + path.sep)) throw Error('Invalid cleanup path')
    await rm(directory, { recursive: true, force: true })
  })
  let authToken = 'alice', fail = false, delayed, calls = []
  const data = { userMessage: { id: 'u1', role: 'user', type: 'image', content: 'question', imageUrl: '/uploads/chat/test.png' },
    replyMessage: { id: 'a1', role: 'assistant', content: 'test reply' }, transport: { mode: 'agnes', status: 'healthy' } }
  globalThis.uni = {
    getStorageSync: () => authToken, setStorageSync: () => {}, removeStorageSync: () => {},
    request(options) {
      calls.push(options)
      if (delayed === true) { delayed = options; return }
      const isStatus = options.url.endsWith('/status'), isHistory = options.url.endsWith('/history')
      options.success(fail ? { statusCode: 504, data: { success: false, code: 'AGNES_TIMEOUT', message: 'model timeout' } }
        : { statusCode: 200, data: { data: isStatus ? data.transport : isHistory ? [data.userMessage, data.replyMessage] : data } })
    },
    uploadFile(options) { calls.push(options); options.success(fail ? { statusCode: 502, data: JSON.stringify({ message: 'model failed' }) }
      : { statusCode: 201, data: JSON.stringify({ data }) }) },
    downloadFile(options) { assert.equal(options.header.Authorization, `Bearer ${authToken}`); options.success({ statusCode: 200, tempFilePath: 'blob:private-image' }) },
  }
  await t.test('image waits for question and explicit send; failed retry reuses ID', async () => {
    setActivePinia(createPinia())
    const store = useChatStore()
    store.setImage('blob:selected'); store.setDraftText('question')
    assert.equal(calls.length, 0)
    fail = true
    await assert.rejects(store.sendMessage())
    assert.equal(store.messages.length, 0)
    assert.equal(store.pendingImage, 'blob:selected')
    assert.match(store.errorText, /model failed/)
    const requestId = calls.at(-1).formData.requestId
    fail = false
    await store.sendMessage()
    assert.equal(calls.at(-1).formData.requestId, requestId)
    assert.equal(calls.at(-1).formData.content, 'question')
    assert.equal(store.messages.length, 2)
    assert.equal(store.messages[0].imageUrl, 'blob:private-image')
    assert.equal(store.pendingImage, '')
    assert.equal(store.transport.mode, 'agnes')
  })
  await t.test('text timeout retains input without a fake assistant and reuses request', async () => {
    setActivePinia(createPinia())
    const store = useChatStore(); store.setDraftText('text')
    fail = true
    await assert.rejects(store.sendMessage())
    const requestId = calls.at(-1).data.requestId
    assert.equal(store.draftText, 'text'); assert.equal(store.messages.length, 0)
    fail = false
    await store.sendMessage()
    assert.equal(calls.at(-1).data.requestId, requestId)
  })
  await t.test('history restores authenticated images and actual mode', async () => {
    setActivePinia(createPinia())
    const store = useChatStore()
    await store.loadHistory(); await store.syncTransportStatus()
    assert.equal(store.messages[0].imageUrl, 'blob:private-image')
    assert.equal(store.messages[0].content, 'question')
    assert.equal(store.transport.mode, 'agnes')
  })
  await t.test('double click and late reply after logout do not leak into another login', async () => {
    setActivePinia(createPinia())
    const store = useChatStore(), auth = useAuthStore()
    auth.applySession('alice', { id: 'alice' }); store.setDraftText('private')
    delayed = true
    const send = store.sendMessage(), count = calls.length
    await store.sendMessage()
    assert.equal(calls.length, count)
    auth.clearSession(); authToken = 'bob'; auth.applySession('bob', { id: 'bob' })
    delayed.success({ statusCode: 201, data: { data } })
    await send
    assert.equal(store.messages.length, 0)
    assert.equal(store.sending, false)
    delayed = false
  })
})
