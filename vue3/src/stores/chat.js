import { defineStore } from 'pinia'
import { requestChatHistory, requestChatStatus, requestSendChatImage, requestSendChatMessage, downloadChatImage } from '../api/chat.js'
import { AUTH_TOKEN_STORAGE_KEY } from '../utils/constants.js'

const token = () => uni.getStorageSync(AUTH_TOKEN_STORAGE_KEY) || ''
const defaults = () => ({ mode: '', status: 'idle', message: '正在读取聊天模式…', fallback: false, displayStreaming: 'none' })
const newId = () => globalThis.crypto?.randomUUID?.() || `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`

async function viewMessage(message) {
  const result = { ...message, kind: message.role, displayText: message.content, streaming: false }
  if (message.type === 'image') {
    try { result.imageUrl = await downloadChatImage(message.imageUrl) }
    catch (error) { result.imageUrl = ''; result.imageError = error.message }
  }
  return result
}

export const useChatStore = defineStore('chat', {
  state: () => ({ messages: [], sending: false, draftText: '', pendingImage: '', pendingSend: null,
    errorText: '', transport: defaults(), generation: 0, historyRevision: 0 }),
  actions: {
    setDraftText(text) { this.draftText = text },
    setImage(filePath) { if (!this.sending) this.pendingImage = filePath || '' },
    setTransport(value) { this.transport = { ...defaults(), ...value } },
    appendSystemMessage(content) {
      this.messages.push({ id: newId(), role: 'system', kind: 'system', content, displayText: content })
    },
    async syncTransportStatus() {
      const owner = token(), generation = this.generation
      try {
        const status = await requestChatStatus()
        if (owner === token() && generation === this.generation) this.setTransport(status)
        return status
      } catch (error) {
        if (owner === token() && generation === this.generation) this.setTransport({ status: 'error', message: error.message })
        throw error
      }
    },
    async loadHistory() {
      const owner = token(), generation = this.generation
      const revision = this.historyRevision
      try {
        const history = await requestChatHistory()
        const messages = await Promise.all((history || []).map(viewMessage))
        if (owner === token() && generation === this.generation && revision === this.historyRevision) this.messages = messages
      } catch (error) {
        if (owner === token() && generation === this.generation) this.errorText = '历史记录加载失败：' + error.message
        throw error
      }
      return this.messages
    },
    async sendMessage(inputText) {
      if (this.sending) return
      const content = String(inputText ?? this.draftText).trim()
      const image = this.pendingImage
      if (!content && !image) throw new Error('请输入问题或选择图片')
      const owner = token(), generation = this.generation
      // Preserve the same ID and input on timeout/failure; the server replays a completed request.
      if (!this.pendingSend || this.pendingSend.content !== content || this.pendingSend.image !== image) {
        this.pendingSend = { content, image, requestId: newId() }
      }
      const request = this.pendingSend
      this.historyRevision++
      this.errorText = ''
      this.sending = true
      try {
        const result = image ? await requestSendChatImage(image, content, request.requestId)
          : await requestSendChatMessage(content, request.requestId)
        const pair = await Promise.all([viewMessage(result.userMessage), viewMessage(result.replyMessage)])
        if (owner !== token() || generation !== this.generation) return
        this.historyRevision++
        const ids = new Set(pair.map(item => item.id))
        this.messages = [...this.messages.filter(item => !ids.has(item.id)), ...pair]
        this.setTransport(result.transport)
        this.draftText = ''
        this.pendingImage = ''
        this.pendingSend = null
        return result
      } catch (error) {
        if (owner === token() && generation === this.generation) {
          this.errorText = (error.message || '发送失败') + '；输入已保留，再次点击发送可重试。'
          this.setTransport({ ...this.transport, status: 'error' })
        }
        throw error
      } finally {
        if (owner === token() && generation === this.generation) this.sending = false
      }
    },
    reset() {
      this.generation++
      this.messages = []
      this.sending = false
      this.draftText = ''
      this.pendingImage = ''
      this.pendingSend = null
      this.errorText = ''
      this.transport = defaults()
    },
  },
})
