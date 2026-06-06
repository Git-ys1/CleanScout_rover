import { defineStore } from 'pinia'
import { requestChatHistory } from '../api/chat.js'
import { requestOpenClawAgentStatus, requestSendOpenClawMessage } from '../api/openclaw.js'
import { formatStatusText } from '../utils/status-display.js'

let streamingRunId = 0
const DEFAULT_DEVICE_ID = 'cleanscout-001'
const DEFAULT_AGENT_ID = 'pc-yusu-main'

function getDefaultTransport() {
  return {
    mode: 'mock',
    fallback: false,
    status: 'disabled',
    message: '当前默认使用模拟链路。',
    model: 'openclaw/default',
    apiMode: 'chat',
    deviceId: DEFAULT_DEVICE_ID,
    agentId: DEFAULT_AGENT_ID,
    pcWorkerOnline: false,
    openclawReachable: false,
    pendingRequests: 0,
    chatTimeoutMs: 0,
    lastHeartbeatAgeMs: null,
    routeMode: 'pc-worker',
    realtimeStreaming: false,
    displayStreaming: 'frontend-typewriter',
  }
}

function createMessageViewModel(message, overrides = {}) {
  const role = String(message?.role || 'assistant').trim() || 'assistant'
  const kind = role === 'user' ? 'user' : role === 'assistant' ? 'assistant' : 'system'
  const content = String(message?.content || '').trim()

  return {
    id: message?.id || `local-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
    role,
    kind,
    content,
    displayText: content,
    streaming: false,
    createdAt: message?.createdAt || new Date().toISOString(),
    ...overrides,
  }
}

function createSystemMessage(content, code = 'info') {
  return createMessageViewModel(
    {
      id: `system-${code}-${Date.now()}-${Math.random().toString(16).slice(2, 7)}`,
      role: 'system',
      content,
      createdAt: new Date().toISOString(),
    },
    {
      kind: 'system',
    }
  )
}

function buildTransportSystemMessage(transport) {
  const modeText = formatStatusText(transport?.mode, '未知链路')
  const statusText = formatStatusText(transport?.status, '未知状态')
  const apiText = formatStatusText(transport?.apiMode, '未知模式')
  const streamingText = transport?.realtimeStreaming
    ? '真流式返回'
    : transport?.displayStreaming === 'frontend-typewriter'
      ? '一次性返回，前端打字机展示'
      : '一次性返回'

  if (transport?.fallback) {
    return `当前链路已回退到${modeText}，状态为${statusText}，接口模式为${apiText}，展示方式为${streamingText}。`
  }

  return `当前链路为${modeText}，状态为${statusText}，接口模式为${apiText}，展示方式为${streamingText}。`
}

function isRecoverableOpenClawRequestError(error) {
  const code = String(error?.code || '').toUpperCase()
  const message = String(error?.message || '').toLowerCase()

  return (
    code === 'NETWORK_ERROR' ||
    code === 'OPENCLAW_WORKER_TIMEOUT' ||
    message.includes('timeout') ||
    message.includes('request:fail') ||
    message.includes('请求超时')
  )
}

function formatOpenClawRequestError(error) {
  const code = String(error?.code || '')

  if (code === 'PC_OPENCLAW_WORKER_OFFLINE') {
    return 'pc-openclaw-worker 当前离线，请先确认 UbuntuPC worker 已启动并连接云端。'
  }

  if (code === 'OPENCLAW_WORKER_TIMEOUT') {
    return 'OpenClaw 回复超时，可能仍在本机生成。已尝试同步最新对话记录。'
  }

  if (code === 'NETWORK_ERROR') {
    return '前端请求连接中断，后端可能仍在等待 worker 返回。已尝试同步最新对话记录。'
  }

  return error?.message || '消息发送失败，请稍后重试。'
}

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [],
    sending: false,
    draftText: '',
    transport: getDefaultTransport(),
  }),
  actions: {
    setDraftText(text) {
      this.draftText = text
    },
    setTransport(transport) {
      this.transport = {
        ...getDefaultTransport(),
        ...(transport || {}),
      }
    },
    replaceMessage(messageId, nextMessage) {
      this.messages = this.messages.map((message) => (message.id === messageId ? nextMessage : message))
    },
    appendSystemMessage(content, code = 'info') {
      this.messages = [...this.messages, createSystemMessage(content, code)]
    },
    async syncTransportStatus({ appendNotice = true } = {}) {
      const status = await requestOpenClawAgentStatus(DEFAULT_DEVICE_ID)

      this.setTransport({
        mode: status?.activeTransport || 'mock',
        fallback: false,
        status: status?.status || 'disabled',
        message: status?.message || getDefaultTransport().message,
        model: status?.model || getDefaultTransport().model,
        apiMode: status?.apiMode || getDefaultTransport().apiMode,
        deviceId: status?.deviceId || DEFAULT_DEVICE_ID,
        agentId: status?.agentId || DEFAULT_AGENT_ID,
        pcWorkerOnline: Boolean(status?.pcWorkerOnline),
        openclawReachable: Boolean(status?.openclawReachable),
        lastHeartbeatAt: status?.lastHeartbeatAt || '',
        lastHeartbeatAgeMs: status?.lastHeartbeatAgeMs ?? null,
        pendingRequests: status?.pendingRequests || 0,
        chatTimeoutMs: status?.chatTimeoutMs || 0,
        routeMode: status?.routeMode || 'pc-worker',
        realtimeStreaming: Boolean(status?.realtimeStreaming),
        displayStreaming: status?.displayStreaming || 'frontend-typewriter',
      })

      if (appendNotice) {
        this.appendSystemMessage(buildTransportSystemMessage(this.transport), 'transport')
      }

      return this.transport
    },
    async loadHistory() {
      const messages = await requestChatHistory()
      this.messages = Array.isArray(messages) ? messages.map((message) => createMessageViewModel(message)) : []
      return this.messages
    },
    async streamAssistantMessage(messageId, fullText) {
      const runId = Date.now()
      streamingRunId = runId
      const normalizedText = String(fullText || '')
      const totalLength = normalizedText.length
      let cursor = 0

      while (cursor < totalLength) {
        if (streamingRunId !== runId) {
          return
        }

        const step = totalLength > 180 ? 3 : totalLength > 90 ? 2 : 1
        cursor = Math.min(totalLength, cursor + step)
        this.messages = this.messages.map((message) =>
          message.id === messageId
            ? {
                ...message,
                displayText: normalizedText.slice(0, cursor),
                streaming: cursor < totalLength,
              }
            : message
        )
        await sleep(18)
      }
    },
    async sendMessage(inputText) {
      const content = String(inputText ?? this.draftText).trim()

      if (!content) {
        throw new Error('消息内容不能为空')
      }

      this.sending = true

      const tempUserId = `temp-user-${Date.now()}`
      const tempAssistantId = `temp-assistant-${Date.now()}`

      this.messages = [
        ...this.messages,
        createMessageViewModel({
          id: tempUserId,
          role: 'user',
          content,
          createdAt: new Date().toISOString(),
        }),
        createMessageViewModel(
          {
            id: tempAssistantId,
            role: 'assistant',
            content: '',
            createdAt: new Date().toISOString(),
          },
          {
            displayText: '已发送到云端，正在等待 UbuntuPC worker 与 OpenClaw 返回…',
            streaming: true,
          }
        ),
      ]

      try {
        const result = await requestSendOpenClawMessage({
          deviceId: DEFAULT_DEVICE_ID,
          conversationId: 'conv-cleanscout-001',
          message: content,
          mode: 'chat',
        })

        this.replaceMessage(tempUserId, createMessageViewModel(result.userMessage))
        this.replaceMessage(
          tempAssistantId,
          createMessageViewModel(result.replyMessage, {
            displayText: '',
            streaming: true,
          })
        )

        this.setTransport(result.transport)
        this.draftText = ''

        await this.streamAssistantMessage(tempAssistantId, result.replyMessage?.content || '')

        this.replaceMessage(tempAssistantId, createMessageViewModel(result.replyMessage))

        if (result.transport?.fallback) {
          this.appendSystemMessage(
            `当前对话已回退到${formatStatusText(result.transport.mode)}，原因：${result.transport.message || '上游链路不可用。'}`,
            'fallback'
          )
        }

        return result
      } catch (error) {
        const recoverable = isRecoverableOpenClawRequestError(error)
        const messageText = formatOpenClawRequestError(error)

        if (recoverable) {
          this.replaceMessage(
            tempAssistantId,
            createMessageViewModel(
              {
                id: tempAssistantId,
                role: 'assistant',
                content: messageText,
                createdAt: new Date().toISOString(),
              },
              {
                displayText: messageText,
                streaming: false,
              }
            )
          )
          this.appendSystemMessage('如果 OpenClaw 稍后返回，页面会自动同步历史记录；无需切换页面手动刷新。', 'openclaw-recovering')

          await sleep(1800)

          try {
            await this.loadHistory()
            await this.syncTransportStatus({ appendNotice: false })
            this.appendSystemMessage('已自动同步 OpenClaw 对话记录。', 'openclaw-history-sync')
          } catch (_syncError) {
            this.appendSystemMessage('自动同步历史记录失败，请稍后手动刷新对话页。', 'openclaw-history-sync-failed')
          }

          return {
            ok: false,
            recovered: true,
            error,
          }
        }

        this.messages = this.messages.filter((message) => message.id !== tempAssistantId)
        this.appendSystemMessage(messageText, 'send-error')
        throw error
      } finally {
        this.sending = false
      }
    },
    reset() {
      streamingRunId = Date.now()
      this.messages = []
      this.sending = false
      this.draftText = ''
      this.transport = getDefaultTransport()
    },
  },
})
