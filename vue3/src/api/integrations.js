import { get } from './http.js'

export function requestOpenClawStatus() {
  return get('/integrations/openclaw/status', { auth: true })
}
