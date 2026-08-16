import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { randomUUID } from 'node:crypto'
import { prisma } from '../utils/prisma.js'
import { createHttpError } from '../utils/response.js'
import { getOpenClawStatus, sendChatToOpenClaw } from '../integrations/openclaw/service.js'

function buildWelcomeMessage(userId) {
  return {
    id: `welcome-${userId}`,
    role: 'assistant',
    content: '当前聊天链路会在 mock / OpenClaw transport 之间切换；真实树莓派实车链路将在后续轮次接入。',
    createdAt: new Date().toISOString(),
  }
}

function buildMockReplyText(content, transport) {
  const fallbackHint = transport.fallback ? ' 当前 OpenClaw 已回退到 mock transport。' : ''
  const transportHint = transport.status === 'disabled'
    ? ' 当前 OpenClaw 仍未开启。'
    : transport.status === 'healthy'
      ? ' 当前消息已改由 mock 兜底。'
      : ` 当前 OpenClaw 状态为 ${transport.status}。`

  return `Mock rover reply: received "${content}" and queued it for future SocketTask transport.${transportHint}${fallbackHint}`
}

function serializeMessage(message) {
  return {
    id: message.id,
    role: message.role,
    type: message.type || 'text',
    content: message.content,
    imageUrl: message.imageUrl || '',
    imageName: message.imageName || '',
    mimeType: message.mimeType || '',
    createdAt: message.createdAt,
  }
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

export async function getChatHistory(userId) {
  const messages = await prisma.messageCache.findMany({
    where: { userId },
    orderBy: { createdAt: 'asc' },
  })

  if (!messages.length) {
    return [buildWelcomeMessage(userId)]
  }

  return messages.map((message) => ({
    ...serializeMessage(message),
  }))
}

export async function sendChatMessage(userId, content) {
  const normalizedContent = String(content || '').trim()

  if (!normalizedContent) {
    throw createHttpError(400, '消息内容不能为空', 'CHAT_CONTENT_REQUIRED')
  }

  const historyMessages = await prisma.messageCache.findMany({
    where: { userId },
    orderBy: { createdAt: 'asc' },
    take: 12,
  })

  const userMessage = await prisma.messageCache.create({
    data: {
      userId,
      role: 'user',
      content: normalizedContent,
    },
  })

  const gatewayStatus = await getOpenClawStatus()
  let replyText = ''
  let transport = {
    mode: 'mock',
    fallback: gatewayStatus.status !== 'disabled',
    status: gatewayStatus.status,
    message: gatewayStatus.message,
    model: gatewayStatus.model,
    apiMode: gatewayStatus.apiMode,
  }

  if (gatewayStatus.status === 'healthy' && gatewayStatus.activeTransport === 'openclaw') {
    try {
      const result = await sendChatToOpenClaw({
        content: normalizedContent,
        historyMessages,
      })

      replyText = result.replyText
      transport = result.transport
    } catch (error) {
      transport = {
        mode: 'mock',
        fallback: true,
        status: 'error',
        message: error.message || 'OpenClaw 调用失败，已回退 mock transport。',
        model: gatewayStatus.model,
        apiMode: gatewayStatus.apiMode,
      }
    }
  }

  if (!replyText) {
    replyText = buildMockReplyText(normalizedContent, transport)
  }

  const replyMessage = await prisma.messageCache.create({
    data: {
      userId,
      role: 'assistant',
      content: replyText,
    },
  })

  return {
    userMessage: serializeMessage(userMessage),
    replyMessage: serializeMessage(replyMessage),
    transport,
  }
}

export async function sendChatImage(userId, file) {
  if (!file?.buffer?.length) {
    throw createHttpError(400, '图片文件为空', 'CHAT_IMAGE_EMPTY')
  }

  const detectedType = detectImageType(file.buffer)
  const declaredMimeType = String(file.mimetype || '').toLowerCase()

  if (!detectedType || detectedType.mimeType !== declaredMimeType) {
    throw createHttpError(415, '图片内容与声明格式不匹配', 'CHAT_IMAGE_SIGNATURE_INVALID')
  }

  const uploadDirectory = path.join(process.cwd(), 'uploads', 'chat')
  const fileName = `${Date.now()}-${randomUUID()}${detectedType.extension}`
  const imageUrl = `/uploads/chat/${fileName}`
  const originalName = normalizeOriginalFileName(file.originalname) || fileName

  await mkdir(uploadDirectory, { recursive: true })
  await writeFile(path.join(uploadDirectory, fileName), file.buffer)

  const userMessage = await prisma.messageCache.create({
    data: {
      userId,
      role: 'user',
      type: 'image',
      content: originalName,
      imageUrl,
      imageName: originalName,
      mimeType: detectedType.mimeType,
    },
  })

  const replyMessage = await prisma.messageCache.create({
    data: {
      userId,
      role: 'assistant',
      type: 'text',
      content: `已收到图片“${originalName}”，并保存到本地 backend。`,
    },
  })

  return {
    userMessage: serializeMessage(userMessage),
    replyMessage: serializeMessage(replyMessage),
    transport: {
      mode: 'mock',
      fallback: false,
      status: 'healthy',
      message: '图片已通过本地 backend 保存。',
      apiMode: 'local-image',
    },
  }
}
