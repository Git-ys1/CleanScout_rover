import { get, post } from './http.js'
import { API_BASE_URL } from './config.js'
import { AUTH_TOKEN_STORAGE_KEY } from '../utils/constants.js'

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

export function requestSendChatImage(tempFilePath) {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync(AUTH_TOKEN_STORAGE_KEY) || ''

    uni.uploadFile({
      url: `${API_BASE_URL}/chat/image`,
      filePath: tempFilePath,
      name: 'file',
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success(response) {
        let body = {}

        try {
          body = typeof response.data === 'string' ? JSON.parse(response.data) : response.data || {}
        } catch (_error) {
          body = {}
        }

        if (response.statusCode >= 200 && response.statusCode < 300 && body.success !== false) {
          resolve(body.data)
          return
        }

        reject(new Error(body.message || `图片发送失败，状态码 ${response.statusCode}`))
      },
      fail(error) {
        reject(new Error(error.errMsg || '图片上传失败'))
      },
    })
  })
}
