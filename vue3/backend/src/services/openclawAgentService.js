import { randomUUID } from 'node:crypto'
import { agentRegistry } from '../agents/agentRegistry.js'
import { prisma } from '../utils/prisma.js'
import { createHttpError } from '../utils/response.js'

const DEFAULT_DEVICE_ID = 'cleanscout-001'
const DEFAULT_CONVERSATION_ID = 'conv-cleanscout-001'
const DEFAULT_MODEL = 'openclaw/default'

function parsePositiveInt(value, fallback) {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? Math.round(parsed) : fallback
}

function normalizeString(value, fallback = '') {
  const normalized = String(value || '').trim()
  return normalized || fallback
}

function getChatTimeoutMs() {
  return parsePositiveInt(process.env.OPENCLAW_CHAT_TIMEOUT_MS, 60000)
}

function serializeMessage(message) {
  return {
    id: message.id,
    role: message.role,
    content: message.content,
    createdAt: message.createdAt,
  }
}

function buildTransport(result, status) {
  const agent = result.agent || {}
  const timeoutMs = getChatTimeoutMs()

  return {
    mode: 'openclaw',
    fallback: false,
    status: 'healthy',
    message: 'pc-openclaw-worker 已返回 OpenClaw 回复。',
    worker: 'pc-openclaw-worker',
    gateway: 'openclaw',
    model: normalizeString(result.raw?.model || result.model || agent.model, DEFAULT_MODEL),
    apiMode: 'chat',
    deviceId: status.deviceId,
    agentId: normalizeString(agent.agentId || status.agentId, 'pc-yusu-main'),
    pcWorkerOnline: true,
    openclawReachable: true,
    latencyMs: result.latencyMs || 0,
    requestId: result.requestId || '',
    timeoutMs,
    realtimeStreaming: false,
    displayStreaming: 'frontend-typewriter',
  }
}

function buildStatusMessage(status) {
  if (!status.pcWorkerOnline) {
    return 'pc-openclaw-worker 未在线。'
  }

  if (!status.openclawReachable) {
    return 'pc-openclaw-worker 在线，但本机 OpenClaw Gateway 不可达。'
  }

  return 'pc-openclaw-worker 在线，OpenClaw Gateway 可达。'
}

export function getOpenClawAgentStatus(deviceId = DEFAULT_DEVICE_ID) {
  const status = agentRegistry.getOpenClawStatus(deviceId)
  const activeTransport = status.pcWorkerOnline ? 'openclaw' : 'mock'
  const healthStatus = status.pcWorkerOnline
    ? status.openclawReachable
      ? 'healthy'
      : 'degraded'
    : 'disabled'

  return {
    ...status,
    ok: true,
    status: healthStatus,
    activeTransport,
    apiMode: 'chat',
    routeMode: normalizeString(process.env.OPENCLAW_ROUTE_MODE, 'pc-worker'),
    chatTimeoutMs: getChatTimeoutMs(),
    realtimeStreaming: false,
    displayStreaming: 'frontend-typewriter',
    message: buildStatusMessage(status),
  }
}

export async function sendOpenClawAgentChat(user, payload = {}) {
  const content = normalizeString(payload.message || payload.content)
  const deviceId = normalizeString(payload.deviceId, DEFAULT_DEVICE_ID)
  const conversationId = normalizeString(payload.conversationId, DEFAULT_CONVERSATION_ID)

  if (!content) {
    throw createHttpError(400, '消息内容不能为空', 'OPENCLAW_CHAT_MESSAGE_REQUIRED')
  }

  const routeMode = normalizeString(process.env.OPENCLAW_ROUTE_MODE, 'pc-worker')

  if (routeMode !== 'pc-worker') {
    throw createHttpError(503, '当前 OpenClaw 路由未启用 pc-worker 模式', 'OPENCLAW_ROUTE_MODE_UNSUPPORTED')
  }

  const status = getOpenClawAgentStatus(deviceId)

  if (!status.pcWorkerOnline) {
    throw createHttpError(503, 'pc-openclaw-worker 当前不在线', 'PC_OPENCLAW_WORKER_OFFLINE')
  }

  const historyMessages = await prisma.messageCache.findMany({
    where: { userId: user.id },
    orderBy: { createdAt: 'asc' },
    take: 12,
  })

  const userMessage = await prisma.messageCache.create({
    data: {
      userId: user.id,
      role: 'user',
      content,
    },
  })

  const messages = [
    ...historyMessages.map((message) => ({
      role: message.role,
      content: message.content,
    })),
    {
      role: 'user',
      content,
    },
  ]

  const requestId = randomUUID()
  const requestLog = {
    requestId,
    conversationId,
    deviceId,
    userId: user.id,
  }
  console.log(`[openclaw-agent] chat-request ${JSON.stringify(requestLog)}`)

  let result

  try {
    result = await agentRegistry.sendOpenClawChat({
      deviceId,
      conversationId,
      messages,
      userId: user.id,
      timeoutMs: getChatTimeoutMs(),
      requestId,
    })
  } catch (error) {
    console.log(
      `[openclaw-agent] chat-failed ${JSON.stringify({
        ...requestLog,
        errorCode: error.code || 'OPENCLAW_WORKER_FAILED',
        status: 'failed',
      })}`
    )
    throw error.status ? error : createHttpError(502, error.message || 'OpenClaw worker 调用失败', error.code)
  }

  if (!result.ok) {
    const code = result.error?.code || 'OPENCLAW_WORKER_FAILED'
    const message = result.error?.message || 'OpenClaw worker 返回失败'
    console.log(
      `[openclaw-agent] chat-failed ${JSON.stringify({
        ...requestLog,
        agentId: result.agent?.agentId || '',
        errorCode: code,
        latencyMs: result.latencyMs || 0,
        status: 'failed',
      })}`
    )
    throw createHttpError(502, message, code)
  }

  const reply = normalizeString(result.reply)

  if (!reply) {
    throw createHttpError(502, 'OpenClaw worker 返回空回复', 'OPENCLAW_EMPTY_REPLY')
  }

  const replyMessage = await prisma.messageCache.create({
    data: {
      userId: user.id,
      role: 'assistant',
      content: reply,
    },
  })

  const transport = buildTransport(result, status)
  console.log(
    `[openclaw-agent] chat-ok ${JSON.stringify({
      ...requestLog,
      agentId: transport.agentId,
      latencyMs: transport.latencyMs,
      status: 'ok',
      replyLength: reply.length,
    })}`
  )

  return {
    ok: true,
    deviceId,
    conversationId,
    reply,
    transport,
    userMessage: serializeMessage(userMessage),
    replyMessage: serializeMessage(replyMessage),
    requestId: result.requestId || '',
    latencyMs: result.latencyMs || 0,
    realtimeStreaming: false,
    displayStreaming: 'frontend-typewriter',
  }
}
