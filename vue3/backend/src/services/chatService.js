import { prisma } from '../utils/prisma.js'
import { createHttpError } from '../utils/response.js'

function buildWelcomeMessage(userId) {
  return {
    id: `welcome-${userId}`,
    role: 'assistant',
    content: 'Mock transport is active. The real rover link is not connected in V-1.1.0.',
    createdAt: new Date().toISOString(),
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
    id: message.id,
    role: message.role,
    content: message.content,
    createdAt: message.createdAt,
  }))
}

export async function sendChatMessage(userId, content) {
  const normalizedContent = String(content || '').trim()

  if (!normalizedContent) {
    throw createHttpError(400, '消息内容不能为空', 'CHAT_CONTENT_REQUIRED')
  }

  const userMessage = await prisma.messageCache.create({
    data: {
      userId,
      role: 'user',
      content: normalizedContent,
    },
  })

  const replyText = `Mock rover reply: received "${normalizedContent}" and queued it for future SocketTask transport.`

  const replyMessage = await prisma.messageCache.create({
    data: {
      userId,
      role: 'assistant',
      content: replyText,
    },
  })

  return {
    userMessage: {
      id: userMessage.id,
      role: userMessage.role,
      content: userMessage.content,
      createdAt: userMessage.createdAt,
    },
    replyMessage: {
      id: replyMessage.id,
      role: replyMessage.role,
      content: replyMessage.content,
      createdAt: replyMessage.createdAt,
    },
  }
}
