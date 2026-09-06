import { mkdir, writeFile, readFile, unlink } from 'node:fs/promises'
import path from 'node:path'
import { randomUUID, createHash } from 'node:crypto'
import { prisma } from '../utils/prisma.js'
import { createHttpError } from '../utils/response.js'
import { getOpenClawStatus, sendChatToOpenClaw } from '../integrations/openclaw/service.js'
import { callAgnes, getAgnesConfig } from '../integrations/agnes/client.js'

const userQueues = new Map()
const MAX_IMAGE_BYTES = 10 * 1024 * 1024
const uploadDirectory = () => path.resolve(process.env.CHAT_UPLOAD_DIR || path.join(process.cwd(), 'uploads', 'chat'))
function serializeMessage(message) {
  return { id: message.id, role: message.role, type: message.type || 'text', content: message.content,
    imageUrl: message.imageUrl || '', imageName: message.imageName || '', mimeType: message.mimeType || '', createdAt: message.createdAt }
}
function detectImageType(buffer) {
  if (buffer?.subarray(0, 3).equals(Buffer.from([0xff, 0xd8, 0xff]))) {
    return { mimeType: 'image/jpeg', extension: '.jpg' }
  }

  if (buffer?.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))) {
    return { mimeType: 'image/png', extension: '.png' }
  }

  const gifHeader = buffer?.subarray(0, 6).toString('ascii')
  if (gifHeader === 'GIF87a' || gifHeader === 'GIF89a') {
    return { mimeType: 'image/gif', extension: '.gif' }
  }

  if (
    buffer?.subarray(0, 4).toString('ascii') === 'RIFF'
    && buffer?.subarray(8, 12).toString('ascii') === 'WEBP'
  ) {
    return { mimeType: 'image/webp', extension: '.webp' }
  }

  return null
}

function normalizeOriginalFileName(value) {
  const originalName = String(value || '').trim()

  if (!originalName) {
    return ''
  }

  const decodedName = Buffer.from(originalName, 'latin1').toString('utf8')

  return decodedName.includes('\uFFFD') ? originalName : decodedName
}


export function getChatMode() {
  const mode = String(process.env.CHAT_PROVIDER || 'openclaw').trim().toLowerCase()
  if (!['agnes', 'openclaw', 'mock'].includes(mode)) throw createHttpError(503, 'CHAT_PROVIDER 配置无效', 'CHAT_CONFIG_INVALID')
  return mode
}

export async function getChatStatus() {
  const mode = getChatMode()
  if (mode === 'agnes') {
    const config = getAgnesConfig()
    return { mode, activeTransport: mode, fallback: false, status: config.key ? 'ready' : 'error',
      model: config.model, apiMode: 'chat', chatTimeoutMs: config.timeoutMs,
      message: config.key ? 'Agnes 图片理解与文字对话；内容将发送至云端模型。' : '服务端未配置 AGNES_API_KEY',
      displayStreaming: 'none', realtimeStreaming: false }
  }
  if (mode === 'mock') return { mode, activeTransport: mode, status: 'ready', fallback: false, message: '模拟模式：不会调用模型或理解图片。' }
  const status = await getOpenClawStatus()
  return { ...status, mode: status.activeTransport, fallback: status.activeTransport !== 'openclaw' }
}

export async function getChatHistory(userId) {
  const messages = await prisma.messageCache.findMany({ where: { userId },
    orderBy: [{ createdAt: 'desc' }, { id: 'desc' }], take: 100 })
  return messages.reverse().map(serializeMessage)
}

export async function getChatImagePath(userId, url) {
  if (!/^\/uploads\/chat\/[a-zA-Z0-9-]+\.(jpg|png|gif|webp)$/.test(url)) {
    throw createHttpError(404, '图片不存在', 'CHAT_IMAGE_NOT_FOUND')
  }
  const owned = await prisma.messageCache.findFirst({ where: { userId, imageUrl: url, type: 'image' } })
  if (!owned) throw createHttpError(404, '图片不存在', 'CHAT_IMAGE_NOT_FOUND')
  return path.join(uploadDirectory(), path.basename(url))
}

async function modelMessages(userId, history, current, file) {
  let imageBudget = 4
  const messages = []
  for (const message of [...history, current].reverse()) {
    if (message.type !== 'image') {
      messages.push({ role: message.role, content: message.content })
      continue
    }
    if (imageBudget-- <= 0) {
      messages.push({ role: message.role, content: message.content + '\n[较早图片已超出图片上下文窗口]' })
      continue
    }
    let buffer
    try {
      buffer = message === current ? file.buffer : await readFile(await getChatImagePath(userId, message.imageUrl))
    } catch {
      throw createHttpError(409, '上下文图片不可读取，请重新上传图片或联系管理员', 'CHAT_IMAGE_UNAVAILABLE')
    }
    const detected = detectImageType(buffer)
    if (!detected || detected.mimeType !== message.mimeType || buffer.length > MAX_IMAGE_BYTES) {
      throw createHttpError(415, '上下文图片格式或大小无效', 'CHAT_IMAGE_SIGNATURE_INVALID')
    }
    messages.push({ role: message.role, content: [
      { type: 'text', text: message.content || '请描述图片的内容。' },
      { type: 'image_url', image_url: { url: `data:${detected.mimeType};base64,${buffer.toString('base64')}` } },
    ] })
  }
  return messages.reverse()
}

async function generate(userId, history, current, file) {
  const mode = getChatMode()
  if (mode === 'agnes') {
    return { replyText: await callAgnes(await modelMessages(userId, history, current, file)),
      transport: { ...(await getChatStatus()), status: 'healthy' } }
  }
  const transport = await getChatStatus()
  if (mode === 'openclaw' && transport.activeTransport === 'openclaw' && transport.status === 'healthy') {
    if (file) throw createHttpError(422, '当前 OpenClaw 入口只支持文字；图片理解请配置 Agnes 模式', 'CHAT_IMAGE_PROVIDER_UNSUPPORTED')
    try {
      return await sendChatToOpenClaw({ content: current.content, historyMessages: history })
    } catch {
      throw createHttpError(502, 'OpenClaw 调用失败，请重试；未生成模拟回复', 'OPENCLAW_CHAT_FAILED')
    }
  }
  if (mode === 'openclaw' && transport.status !== 'disabled') {
    throw createHttpError(502, 'OpenClaw 不可用，请联系管理员或显式切换 mock 模式', 'OPENCLAW_CHAT_FAILED')
  }
  return { replyText: file ? '【模拟回复，未调用视觉模型】图片已保存；请启用 Agnes 进行图片理解。'
    : `【模拟回复，未调用模型】收到：${current.content}`, transport: { ...transport, mode: 'mock', activeTransport: 'mock' } }
}

// Serialize turns for each user in this Express process, without blocking other users.
async function inUserQueue(userId, action) {
  const previous = userQueues.get(userId) || Promise.resolve()
  const next = previous.catch(() => {}).then(action)
  userQueues.set(userId, next)
  try { return await next } finally { if (userQueues.get(userId) === next) userQueues.delete(userId) }
}

async function sendTurn(userId, content, file, requestedId) {
  const normalizedContent = String(content || '').trim()
  if (!normalizedContent && !file) throw createHttpError(400, '消息内容不能为空', 'CHAT_CONTENT_REQUIRED')
  if (normalizedContent.length > 12000) throw createHttpError(400, '消息不能超过 12000 字', 'CHAT_CONTENT_TOO_LONG')
  const requestId = requestedId || randomUUID() // Legacy clients may omit it; new UI always sends one.
  if (typeof requestId !== 'string' || !/^[a-zA-Z0-9_-]{1,100}$/.test(requestId)) {
    throw createHttpError(400, '请求 ID 无效', 'CHAT_REQUEST_ID_INVALID')
  }
  let detected
  if (file) {
    if (!file.buffer?.length) throw createHttpError(400, '图片文件为空', 'CHAT_IMAGE_EMPTY')
    if (file.buffer.length > MAX_IMAGE_BYTES) throw createHttpError(413, '图片不能超过 10 MB', 'CHAT_IMAGE_TOO_LARGE')
    detected = detectImageType(file.buffer)
    if (!detected || detected.mimeType !== String(file.mimetype || '').toLowerCase()) {
      throw createHttpError(415, '图片内容与声明格式不匹配', 'CHAT_IMAGE_SIGNATURE_INVALID')
    }
  }
  const fingerprint = createHash('sha256').update(JSON.stringify([normalizedContent, detected?.mimeType || '', file?.originalname || '']))
    .update(file?.buffer || '').digest('hex')
  return inUserQueue(userId, async () => {
    const key = { userId_requestId: { userId, requestId } }
    const claim = randomUUID()
    let record = await prisma.chatRequest.findUnique({ where: key })
    if (!record) {
      try {
        record = await prisma.chatRequest.create({ data: { userId, requestId, fingerprint, claim } })
      } catch (error) {
        if (error.code !== 'P2002') throw error
        record = await prisma.chatRequest.findUnique({ where: key })
      }
    }
    if (record.fingerprint !== fingerprint) throw createHttpError(409, '同一请求 ID 不能用于不同消息', 'CHAT_REQUEST_CONFLICT')
    if (record.status === 'succeeded') return JSON.parse(record.response)
    if (record.claim !== claim) {
      const acquired = await prisma.chatRequest.updateMany({ where: { id: record.id, OR: [
        { status: 'failed' }, { status: 'processing', updatedAt: { lt: new Date(Date.now() - 180000) } },
      ] }, data: { claim, status: 'processing' } })
      if (!acquired.count) throw createHttpError(409, '此消息仍在处理中，请稍后使用原请求重试', 'CHAT_REQUEST_PENDING')
    }
    let imagePath
    try {
      const history = (await prisma.messageCache.findMany({ where: { userId, role: { in: ['user', 'assistant'] } },
        orderBy: [{ createdAt: 'desc' }, { id: 'desc' }], take: 24 })).reverse()
      const current = { role: 'user', type: file ? 'image' : 'text',
        content: normalizedContent || '请描述图片的内容。', mimeType: detected?.mimeType || null }
      const result = await generate(userId, history, current, file)
      if (file) {
        const name = `${Date.now()}-${randomUUID()}${detected.extension}`
        current.imageUrl = `/uploads/chat/${name}`
        current.imageName = normalizeOriginalFileName(file.originalname) || name
        await mkdir(uploadDirectory(), { recursive: true })
        imagePath = path.join(uploadDirectory(), name)
        await writeFile(imagePath, file.buffer)
      }
      return await prisma.$transaction(async (tx) => {
        // A stale worker must not commit after another process reclaimed its request.
        const owned = await tx.chatRequest.updateMany({ where: { id: record.id, claim, status: 'processing' },
          data: { status: 'succeeded' } })
        if (!owned.count) throw createHttpError(409, '请求已由其他处理器接管，请重试获取结果', 'CHAT_REQUEST_PENDING')
        const now = new Date(Math.max(Date.now(), new Date(history.at(-1)?.createdAt || 0).getTime() + 1))
        const userMessage = await tx.messageCache.create({ data: { userId, ...current, createdAt: now } })
        const replyMessage = await tx.messageCache.create({ data: { userId, role: 'assistant',
          content: result.replyText, createdAt: new Date(now.getTime() + 1) } })
        const response = { userMessage: serializeMessage(userMessage), replyMessage: serializeMessage(replyMessage), transport: result.transport }
        await tx.chatRequest.update({ where: { id: record.id }, data: { response: JSON.stringify(response) } })
        return response
      })
    } catch (error) {
      if (imagePath) await unlink(imagePath).catch(() => {})
      await prisma.chatRequest.updateMany({ where: { id: record.id, claim, status: 'processing' },
        data: { status: 'failed' } })
      if (error.status) throw error
      throw createHttpError(500, '消息保存失败，请使用原请求重试', 'CHAT_STORAGE_ERROR')
    }
  })
}

export const sendChatMessage = (userId, content, requestId) => sendTurn(userId, content, null, requestId)
export const sendChatImage = (userId, file, content, requestId) => sendTurn(userId, content, file, requestId)
