import { get, post } from './http.js'

export function requestChatHistory() {
  return get('/chat/history', { auth: true })
}

export function requestSendChatMessage(content) {
  return post(
    '/chat/send',
    { content },
    { auth: true }
  )
}
