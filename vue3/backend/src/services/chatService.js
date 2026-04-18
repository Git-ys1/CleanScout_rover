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
    content: message.content,
    createdAt: message.createdAt,
  }
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
