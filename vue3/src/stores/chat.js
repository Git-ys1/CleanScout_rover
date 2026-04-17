import { defineStore } from 'pinia'
import { requestChatHistory, requestSendChatMessage } from '../api/chat.js'

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [],
    sending: false,
    draftText: '',
  }),
  actions: {
    setDraftText(text) {
      this.draftText = text
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
    },
  },
})
