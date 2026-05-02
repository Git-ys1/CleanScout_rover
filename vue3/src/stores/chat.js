import { defineStore } from 'pinia'
import { requestChatHistory, requestSendChatMessage } from '../api/chat.js'
import { requestOpenClawStatus } from '../api/integrations.js'
import { formatStatusText } from '../utils/status-display.js'

let streamingRunId = 0

function getDefaultTransport() {
  return {
    mode: 'mock',
    fallback: false,
    status: 'disabled',
    message: '当前默认使用模拟链路。',
    model: 'openclaw/default',
    apiMode: 'chat',
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

  if (transport?.fallback) {
    return `当前链路已回退到${modeText}，状态为${statusText}，接口模式为${apiText}。`
  }

  return `当前链路为${modeText}，状态为${statusText}，接口模式为${apiText}。`
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
      const status = await requestOpenClawStatus()

      this.setTransport({
        mode: status?.activeTransport || 'mock',
        fallback: false,
        status: status?.status || 'disabled',
        message: status?.message || getDefaultTransport().message,
        model: status?.model || getDefaultTransport().model,
        apiMode: status?.apiMode || getDefaultTransport().apiMode,
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
            displayText: '正在生成…',
            streaming: true,
          }
        ),
      ]

      try {
        const result = await requestSendChatMessage(content)

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
        this.messages = this.messages.filter((message) => message.id !== tempAssistantId)
        this.appendSystemMessage(error.message || '消息发送失败，请稍后重试。', 'send-error')
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
