import { get, post } from './http.js'
import { API_BASE_URL } from './config.js'
import { AUTH_TOKEN_STORAGE_KEY } from '../utils/constants.js'

export function requestChatHistory() {
  return get('/chat/history', { auth: true })
}

export function requestChatStatus() {
  return get('/chat/status', { auth: true })
}

export function requestSendChatMessage(content, requestId) {
  return post(
    '/chat/send',
    { content, requestId },
    { auth: true, timeout: 150000 }
  )
}

export function requestSendChatImage(tempFilePath, content, requestId) {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync(AUTH_TOKEN_STORAGE_KEY) || ''

    uni.uploadFile({
      url: `${API_BASE_URL}/chat/image`,
      filePath: tempFilePath,
      name: 'file',
      formData: { content, requestId },
      timeout: 150000,
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

        reject(Object.assign(new Error(body.message || `图片发送失败，状态码 ${response.statusCode}`), { code: body.code, status: response.statusCode }))
      },
      fail(error) {
        reject(new Error(error.errMsg || '图片上传失败'))
      },
    })
  })
}

export function downloadChatImage(imageUrl) {
  const origin = API_BASE_URL.replace(/\/api\/?$/, '')
  // Only send the user's bearer token to our own backend.
  if (!/^\/uploads\/chat\/[a-zA-Z0-9-]+\.(jpg|png|gif|webp)$/.test(imageUrl)) return Promise.reject(new Error('图片地址无效'))
  return new Promise((resolve, reject) => uni.downloadFile({
    url: `${origin}${imageUrl}`,
    header: { Authorization: `Bearer ${uni.getStorageSync(AUTH_TOKEN_STORAGE_KEY) || ''}` },
    timeout: 30000,
    success: (response) => response.statusCode === 200 ? resolve(response.tempFilePath) : reject(new Error('图片不可读取')),
    fail: () => reject(new Error('图片下载失败，请刷新重试')),
  }))
}
