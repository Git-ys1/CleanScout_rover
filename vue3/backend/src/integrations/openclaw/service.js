import { getSystemConfig } from '../../services/systemConfigService.js'
import {
  fetchOpenClawModels,
  getOpenClawRuntimeConfig,
  sendOpenClawChatCompletions,
  sendOpenClawResponses,
} from './client.js'

function buildBaseStatus(config) {
  return {
    status: 'disabled',
    activeTransport: 'mock',
    apiMode: config.apiMode,
    model: config.model,
    fallback: false,
    lastProbeAt: new Date().toISOString(),
    message: 'OpenClaw integration is disabled.',
  }
}

function normalizeMessageContent(content) {
  if (typeof content === 'string') {
    return content.trim()
  }

  if (Array.isArray(content)) {
    return content
      .map((item) => {
        if (typeof item === 'string') {
          return item.trim()
        }

        if (item && typeof item === 'object') {
          return String(item.text || item.content || '').trim()
        }

        return ''
      })
      .filter(Boolean)
      .join('\n')
  }

  if (content && typeof content === 'object') {
    return String(content.text || content.content || '').trim()
  }

  return ''
}

function extractModelIds(payload) {
  return Array.isArray(payload?.data)
    ? payload.data
        .map((item) => String(item?.id || '').trim())
        .filter(Boolean)
    : []
}

function extractChatCompletionText(payload) {
  const choice = payload?.choices?.[0]

  return (
    normalizeMessageContent(choice?.message?.content) ||
    normalizeMessageContent(choice?.text) ||
    normalizeMessageContent(payload?.output_text)
  )
}

function extractResponsesText(payload) {
  const outputText = normalizeMessageContent(payload?.output_text)

  if (outputText) {
    return outputText
  }

  const outputs = Array.isArray(payload?.output) ? payload.output : []

  return outputs
    .map((item) => {
      if (item?.content) {
        return normalizeMessageContent(item.content)
      }

      return normalizeMessageContent(item?.text)
    })
    .filter(Boolean)
    .join('\n')
}

function buildDisabledStatus(config, reason) {
  const status = buildBaseStatus(config)

  status.message = reason

  return status
}

function createTransportStatus(mode, status, config, extra = {}) {
  return {
    mode,
    fallback: false,
    status,
    model: config.model,
    apiMode: config.apiMode,
    ...extra,
  }
}

function buildGatewayMessages(historyMessages, content) {
  const normalizedHistory = Array.isArray(historyMessages)
    ? historyMessages
        .slice(-10)
        .map((message) => ({
          role: message.role === 'assistant' ? 'assistant' : 'user',
          content: String(message.content || '').trim(),
        }))
        .filter((message) => message.content)
    : []

  return [
    ...normalizedHistory,
    {
      role: 'user',
      content,
    },
  ]
}

export async function getOpenClawStatus() {
  const systemConfig = await getSystemConfig()
  const config = getOpenClawRuntimeConfig(systemConfig)

  if (!config.hardEnabled) {
    return buildDisabledStatus(config, 'OPENCLAW_ENABLED=false，backend 当前固定走 mock transport。')
  }

  if (!config.softEnabled) {
    return buildDisabledStatus(config, '后台软开关未开启，聊天链路当前固定走 mock transport。')
  }

  try {
    const modelsPayload = await fetchOpenClawModels(config)
    const modelIds = extractModelIds(modelsPayload)
    const hasTargetModel = modelIds.includes(config.model)

    if (!hasTargetModel) {
      return {
        ...buildBaseStatus(config),
        status: 'degraded',
        message: `OpenClaw 已响应 /v1/models，但未发现目标模型 ${config.model}。`,
        availableModels: modelIds,
      }
    }

    return {
      ...buildBaseStatus(config),
      status: 'healthy',
      activeTransport: 'openclaw',
      message: `OpenClaw 已就绪，当前将转发到 ${config.model}。`,
      availableModels: modelIds,
    }
  } catch (error) {
    return {
      ...buildBaseStatus(config),
      status: 'error',
      message: error.message || 'OpenClaw 探测失败',
    }
  }
}

export async function sendChatToOpenClaw({ content, historyMessages = [] }) {
  const systemConfig = await getSystemConfig()
  const config = getOpenClawRuntimeConfig(systemConfig)

  if (!config.hardEnabled || !config.softEnabled) {
    const error = new Error('OpenClaw transport is disabled.')

    error.code = 'OPENCLAW_DISABLED'

    throw error
  }

  if (config.apiMode === 'responses') {
    const payload = await sendOpenClawResponses(content, config)
    const replyText = extractResponsesText(payload)

    if (!replyText) {
      const error = new Error('OpenClaw /v1/responses did not return readable text.')

      error.code = 'OPENCLAW_EMPTY_REPLY'

      throw error
    }

    return {
      replyText,
      transport: createTransportStatus('openclaw', 'healthy', config),
    }
  }

  const payload = await sendOpenClawChatCompletions(buildGatewayMessages(historyMessages, content), config)
  const replyText = extractChatCompletionText(payload)

  if (!replyText) {
    const error = new Error('OpenClaw /v1/chat/completions did not return readable text.')

    error.code = 'OPENCLAW_EMPTY_REPLY'

    throw error
  }

  return {
    replyText,
    transport: createTransportStatus('openclaw', 'healthy', config),
  }
}
