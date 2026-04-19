import { get } from './http.js'

export function requestOpenClawStatus() {
  return get('/integrations/openclaw/status', { auth: true })
}

export function requestRosStatus() {
  return get('/integrations/ros/status', { auth: true })
}
