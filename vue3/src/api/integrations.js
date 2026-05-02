import { API_BASE_URL } from './config.js'
import { get } from './http.js'

export function requestOpenClawStatus() {
  return get('/integrations/openclaw/status', { auth: true })
}

export function requestAsrStatus() {
  return get('/integrations/asr/status', { auth: true })
}

export function requestOpenMvStatus() {
  return get('/integrations/openmv/status', { auth: true })
}

export function requestRosStatus() {
  return get('/integrations/ros/status', { auth: true })
}

export function buildOpenMvSnapshotUrl(token, cacheBust = Date.now()) {
  const query = [
    `token=${encodeURIComponent(String(token || '').trim())}`,
    `ts=${encodeURIComponent(String(cacheBust))}`,
  ].join('&')

  return `${API_BASE_URL}/integrations/openmv/snapshot?${query}`
}
