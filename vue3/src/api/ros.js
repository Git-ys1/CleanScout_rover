import { get, post } from './http.js'

export function requestRosTelemetrySummary() {
  return get('/ros/telemetry/summary', { auth: true })
}

export function requestRosCmdVel(payload) {
  return post('/ros/cmd-vel', payload, { auth: true })
}

export function requestRosManualPreset(payload) {
  return post('/ros/manual-preset', payload, { auth: true })
}
