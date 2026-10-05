import { randomUUID } from 'node:crypto'
import { agentRegistry } from '../agents/agentRegistry.js'
import { createHttpError } from '../utils/response.js'

const DEFAULT_DEVICE_ID = 'cleanscout-001'
const DEFAULT_CONVERSATION_ID = 'conv-cleanscout-001'
const MAX_IMAGE_BYTES = 5 * 1024 * 1024

function normalizeString(value, fallback = '') {
  const normalized = String(value || '').trim()
  return normalized || fallback
}

function parsePositiveInt(value, fallback) {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? Math.round(parsed) : fallback
}

function chatTimeoutMs() {
  return parsePositiveInt(process.env.ORANGEPI_CHAT_TIMEOUT_MS, 150000)
}

function normalizeHistory(messages) {
  return Array.isArray(messages)
    ? messages.slice(-20).map((message) => ({
        role: message.role === 'assistant' ? 'assistant' : 'user',
        content: normalizeString(message.content),
      })).filter((message) => message.content)
    : []
}

function decodeJpeg(value) {
  const encoded = normalizeString(value)
  if (!encoded || encoded.length % 4 !== 0 || !/^[A-Za-z0-9+/]+={0,2}$/.test(encoded)) {
    throw createHttpError(502, '香橙派 Agent 未返回有效截图', 'ORANGEPI_IMAGE_INVALID')
  }
  const buffer = Buffer.from(encoded, 'base64')
  if (!buffer.length || buffer.length > MAX_IMAGE_BYTES) {
    throw createHttpError(502, '香橙派 Agent 截图为空或超过 5 MB', 'ORANGEPI_IMAGE_INVALID')
  }
  if (!buffer.subarray(0, 3).equals(Buffer.from([0xff, 0xd8, 0xff])) ||
      !buffer.subarray(-2).equals(Buffer.from([0xff, 0xd9]))) {
    throw createHttpError(502, '香橙派 Agent 截图不是有效 JPEG', 'ORANGEPI_IMAGE_INVALID')
  }
  return buffer
}

function statusMessage(status) {
  if (!status.agentOnline) return '香橙派 Agent 未在线。'
  if (!status.yoloReachable) return '香橙派 Agent 在线，但没有实时 YOLO 画面。'
  if (!status.modelReady) return '香橙派 Agent 在线，但模型 API 未配置。'
  return '香橙派 Agent 在线，YOLO 画面与模型均已就绪。'
}

export function getOrangePiAgentStatus(deviceId = DEFAULT_DEVICE_ID) {
  const status = agentRegistry.getOrangePiStatus(deviceId)
  const health = !status.agentOnline ? 'disabled'
    : status.yoloReachable && status.modelReady ? 'healthy' : 'degraded'
  return {
    ...status,
    mode: 'orangepi',
    activeTransport: 'orangepi',
    fallback: false,
    status: health,
    message: statusMessage(status),
    apiMode: 'chat',
    chatTimeoutMs: chatTimeoutMs(),
    realtimeStreaming: false,
    displayStreaming: 'frontend-typewriter',
  }
}

export async function sendOrangePiAgentChat({ userId, content, historyMessages = [], deviceId, conversationId }) {
  const message = normalizeString(content)
  const targetDeviceId = normalizeString(deviceId, DEFAULT_DEVICE_ID)
  const targetConversationId = normalizeString(conversationId, DEFAULT_CONVERSATION_ID)
  if (!message) throw createHttpError(400, '消息内容不能为空', 'ORANGEPI_CHAT_MESSAGE_REQUIRED')

  const status = getOrangePiAgentStatus(targetDeviceId)
  if (!status.agentOnline) throw createHttpError(503, '香橙派 Agent 当前不在线', 'ORANGEPI_AGENT_OFFLINE')
  if (!status.modelReady) throw createHttpError(503, '香橙派 Agent 未配置模型 API', 'ORANGEPI_MODEL_NOT_READY')

  const requestId = randomUUID()
  let result
  try {
    result = await agentRegistry.sendOrangePiChat({
      deviceId: targetDeviceId,
      conversationId: targetConversationId,
      messages: [...normalizeHistory(historyMessages), { role: 'user', content: message }],
      userId,
      timeoutMs: chatTimeoutMs(),
      requestId,
    })
  } catch (error) {
    throw error.status ? error : createHttpError(502, error.message || '香橙派 Agent 调用失败', error.code)
  }

  if (!result.ok) {
    throw createHttpError(502, result.error?.message || '香橙派 Agent 返回失败',
      result.error?.code || 'ORANGEPI_AGENT_FAILED')
  }
  const replyText = normalizeString(result.reply)
  if (!replyText) throw createHttpError(502, '香橙派 Agent 返回空回复', 'ORANGEPI_EMPTY_REPLY')
  const imageBuffer = decodeJpeg(result.imageBase64)
  const capturedAt = normalizeString(result.capturedAt)

  return {
    replyText,
    replyImage: {
      buffer: imageBuffer,
      mimeType: 'image/jpeg',
      imageName: normalizeString(result.imageName, `yolo-${Date.now()}.jpg`),
    },
    transport: {
      ...getOrangePiAgentStatus(targetDeviceId),
      status: result.yoloReachable === false ? 'degraded' : 'healthy',
      message: '香橙派 Agent 已处理消息并返回 YOLO 截图。',
      model: normalizeString(result.model, status.model),
      agentId: normalizeString(result.agent?.agentId, status.agentId),
      requestId,
      latencyMs: result.latencyMs || 0,
      capturedAt,
      imageAgeMs: Number(result.imageAgeMs || 0),
      yoloReachable: result.yoloReachable !== false,
      modelReady: true,
    },
  }
}
