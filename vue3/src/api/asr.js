import { API_BASE_URL } from './config.js'
import { get } from './http.js'
import { AUTH_TOKEN_STORAGE_KEY } from '../utils/constants.js'

function createRequestError({ message, status = 0, code = 'ASR_REQUEST_FAILED' }) {
  const error = new Error(message || '语音识别请求失败')
  error.status = status
  error.code = code
  return error
}

function readAuthHeader() {
  const token = uni.getStorageSync(AUTH_TOKEN_STORAGE_KEY) || ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function parseBody(rawBody) {
  if (!rawBody) {
    return {}
  }

  if (typeof rawBody === 'object') {
    return rawBody
  }

  try {
    return JSON.parse(rawBody)
  } catch (_error) {
    return {}
  }
}

async function uploadRecordingByFetch({ file, fileName, lang = 'zh' }) {
  const formData = new FormData()
  const normalizedFile = file instanceof File
    ? file
    : new File([file], fileName || 'recording.webm', {
        type: file?.type || 'application/octet-stream',
      })

  formData.append('file', normalizedFile, normalizedFile.name)
  formData.append('lang', lang)

  const response = await fetch(`${API_BASE_URL}/asr/transcribe`, {
    method: 'POST',
    headers: {
      ...readAuthHeader(),
    },
    body: formData,
  })
  const body = await response.json().catch(() => ({}))

  if (response.ok && body.success !== false) {
    return body.data
  }

  throw createRequestError({
    message: body.message || `语音识别请求失败，状态码 ${response.status}`,
    status: response.status,
    code: body.code || 'ASR_TRANSCRIBE_FAILED',
  })
}

function uploadRecordingByUni({ tempFilePath, lang = 'zh' }) {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${API_BASE_URL}/asr/transcribe`,
      filePath: tempFilePath,
      name: 'file',
      formData: {
        lang,
      },
      header: {
        ...readAuthHeader(),
      },
      success: (response) => {
        const body = parseBody(response.data)

        if (response.statusCode >= 200 && response.statusCode < 300 && body.success !== false) {
          resolve(body.data)
          return
        }

        reject(
          createRequestError({
            message: body.message || `语音识别请求失败，状态码 ${response.statusCode}`,
            status: response.statusCode,
            code: body.code || 'ASR_TRANSCRIBE_FAILED',
          })
        )
      },
      fail: (error) => {
        reject(
          createRequestError({
            message: error.errMsg || '语音识别上传失败',
            code: 'ASR_UPLOAD_FAILED',
          })
        )
      },
    })
  })
}

export function requestAsrStatus() {
  return get('/integrations/asr/status', { auth: true })
}

export async function uploadAsrRecording({ tempFilePath, file, fileName, lang = 'zh' }) {
  if (file) {
    return uploadRecordingByFetch({ file, fileName, lang })
  }

  if (tempFilePath) {
    return uploadRecordingByUni({ tempFilePath, lang })
  }

  throw createRequestError({
    message: '未提供有效的录音文件',
    code: 'ASR_AUDIO_REQUIRED',
  })
}
