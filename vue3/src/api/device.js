import { get } from './http.js'

export function requestDeviceSummary() {
  return get('/device/summary', { auth: true })
}
