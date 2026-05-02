import { fetchAsrHealth, getAsrRuntimeConfig, submitAsrRecognition } from './client.js'

function buildDisabledStatus(message = '语音识别服务未启用') {
  const config = getAsrRuntimeConfig()

  return {
    enabled: false,
    provider: config.provider,
    language: config.language,
    status: 'disabled',
    message,
  }
}

export async function getAsrStatus() {
  const config = getAsrRuntimeConfig()

  if (!config.enabled) {
    return buildDisabledStatus()
  }

  try {
    const payload = await fetchAsrHealth()

    return {
      enabled: true,
      provider: config.provider,
      language: payload?.data?.language || config.language,
      status: payload?.data?.status || 'healthy',
      message: payload?.data?.message || 'FunASR 服务运行正常',
      model: payload?.data?.model || '',
    }
  } catch (error) {
    return {
      enabled: true,
      provider: config.provider,
      language: config.language,
      status: 'error',
      message: error.message || 'FunASR 服务不可用',
      model: '',
    }
  }
}

export async function transcribeAudioFile({ buffer, filename, mimeType, language }) {
  const config = getAsrRuntimeConfig()
  const payload = await submitAsrRecognition({
    buffer,
    filename,
    mimeType,
    language,
  })
  const data = payload?.data || {}

  return {
    text: String(data.text || '').trim(),
    durationMs: Number(data.durationMs || 0),
    provider: config.provider,
    language: data.language || language || config.language,
    model: data.model || 'paraformer-zh',
    segments: Array.isArray(data.segments) ? data.segments : [],
    audioFormat: data.audioFormat || '',
    sampleRate: Number(data.sampleRate || 0),
  }
}
