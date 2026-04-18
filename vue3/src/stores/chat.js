import { defineStore } from 'pinia'
import { requestChatHistory, requestSendChatMessage } from '../api/chat.js'
import { requestOpenClawStatus } from '../api/integrations.js'

function getDefaultTransport() {
  return {
    mode: 'mock',
    fallback: false,
    status: 'disabled',
    message: '当前默认使用 mock transport。',
    model: 'openclaw/default',
    apiMode: 'chat',
  }
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
    async syncTransportStatus() {
      const status = await requestOpenClawStatus()

      this.setTransport({
        mode: status?.activeTransport || 'mock',
        fallback: false,
        status: status?.status || 'disabled',
        message: status?.message || getDefaultTransport().message,
        model: status?.model || getDefaultTransport().model,
        apiMode: status?.apiMode || getDefaultTransport().apiMode,
      })

      return this.transport
    },
    async loadHistory() {
      const messages = await requestChatHistory()
      this.messages = Array.isArray(messages) ? messages : []
      return this.messages
    },
    appendMessages(messages) {
      this.messages = [...this.messages, ...messages.filter(Boolean)]
    },
    async sendMessage(inputText) {
      const content = String(inputText ?? this.draftText).trim()

      if (!content) {
        throw new Error('消息内容不能为空')
      }

      this.sending = true

      try {
        const result = await requestSendChatMessage(content)
        this.appendMessages([result.userMessage, result.replyMessage])
        this.setTransport(result.transport)
        this.draftText = ''
        return result
      } finally {
        this.sending = false
      }
    },
    reset() {
      this.messages = []
      this.sending = false
      this.draftText = ''
      this.transport = getDefaultTransport()
    },
  },
})
