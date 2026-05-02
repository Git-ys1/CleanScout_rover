import { Blob } from 'node:buffer'
import { createHttpError } from '../../utils/response.js'

const DEFAULT_ASR_BASE_URL = 'http://127.0.0.1:7001'
const DEFAULT_ASR_LANGUAGE = 'zh'
const DEFAULT_ASR_PROVIDER = 'funasr'
const DEFAULT_ASR_TIMEOUT_MS = 60000

function parseBoolean(value, fallback = false) {
  const normalized = String(value ?? '').trim().toLowerCase()

  if (!normalized) {
    return fallback
  }

  if (['1', 'true', 'yes', 'on'].includes(normalized)) {
    return true
  }

  if (['0', 'false', 'no', 'off'].includes(normalized)) {
    return false
  }

  return fallback
}

function normalizeBaseUrl(value) {
  return String(value || DEFAULT_ASR_BASE_URL).trim().replace(/\/+$/, '')
}

export function getAsrRuntimeConfig() {
  return {
    enabled: parseBoolean(process.env.ASR_ENABLED, false),
    provider: String(process.env.ASR_PROVIDER || DEFAULT_ASR_PROVIDER).trim() || DEFAULT_ASR_PROVIDER,
    baseUrl: normalizeBaseUrl(process.env.ASR_BASE_URL),
    language: String(process.env.ASR_LANGUAGE || DEFAULT_ASR_LANGUAGE).trim() || DEFAULT_ASR_LANGUAGE,
    requestTimeoutMs: Number(process.env.ASR_REQUEST_TIMEOUT_MS || DEFAULT_ASR_TIMEOUT_MS) || DEFAULT_ASR_TIMEOUT_MS,
  }
}

async function parseJsonSafely(response) {
  try {
    return await response.json()
  } catch (_error) {
    return null
  }
}

async function requestAsrService(pathname, options = {}) {
  const config = getAsrRuntimeConfig()

  if (!config.enabled) {
    throw createHttpError(503, '语音识别服务未启用', 'ASR_DISABLED')
  }

  const timeoutSignal = AbortSignal.timeout(config.requestTimeoutMs)
  const response = await fetch(`${config.baseUrl}${pathname}`, {
    ...options,
    signal: options.signal || timeoutSignal,
  })
  const payload = await parseJsonSafely(response)

  if (!response.ok || payload?.success === false) {
    throw createHttpError(
      response.status || 502,
      payload?.message || `ASR service request failed with status ${response.status}`,
      payload?.code || 'ASR_SERVICE_REQUEST_FAILED'
    )
  }

  return payload
}

export async function fetchAsrHealth() {
  return requestAsrService('/health', {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  })
}

export async function submitAsrRecognition({ buffer, filename, mimeType, language }) {
  if (!buffer || !buffer.length) {
    throw createHttpError(400, '未提供有效音频内容', 'ASR_AUDIO_REQUIRED')
  }

  const config = getAsrRuntimeConfig()
  const formData = new FormData()
  const blob = new Blob([buffer], {
    type: mimeType || 'application/octet-stream',
  })

  formData.append('file', blob, filename || 'recording.bin')
  formData.append('lang', language || config.language)

  return requestAsrService('/recognize', {
    method: 'POST',
    body: formData,
  })
}
