import { API_BASE_URL, REQUEST_TIMEOUT } from './config.js'
import { AUTH_TOKEN_STORAGE_KEY } from '../utils/constants.js'

function createRequestError({ message, status = 0, code = 'REQUEST_FAILED' }) {
  const error = new Error(message || '请求失败')
  error.status = status
  error.code = code
  return error
}

export function request({ url, method = 'GET', data, auth = false, header = {} }) {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync(AUTH_TOKEN_STORAGE_KEY) || ''

    uni.request({
      url: `${API_BASE_URL}${url}`,
      method,
      data,
      timeout: REQUEST_TIMEOUT,
      header: {
        'Content-Type': 'application/json',
        ...(auth && token ? { Authorization: `Bearer ${token}` } : {}),
        ...header,
      },
      success: (response) => {
        const body = response.data || {}

        if (response.statusCode >= 200 && response.statusCode < 300 && body.success !== false) {
          resolve(body.data)
          return
        }

        reject(
          createRequestError({
            message: body.message || `请求失败，状态码 ${response.statusCode}`,
            status: response.statusCode,
            code: body.code || 'API_REQUEST_FAILED',
          })
        )
      },
      fail: (error) => {
        reject(
          createRequestError({
            message: error.errMsg || '网络请求失败',
            code: 'NETWORK_ERROR',
          })
        )
      },
    })
  })
}

export function get(url, options = {}) {
  return request({
    url,
    method: 'GET',
    ...options,
  })
}

export function post(url, data, options = {}) {
  return request({
    url,
    method: 'POST',
    data,
    ...options,
  })
}
