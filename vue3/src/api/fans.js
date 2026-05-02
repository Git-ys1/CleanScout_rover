import { get, post } from './http.js'

export function requestFanState() {
  return get('/device/fans/state', { auth: true })
}

export function requestFanEnable(payload) {
  return post('/device/fans/enable', payload, { auth: true })
}

export function requestFanPwm(payload) {
  return post('/device/fans/pwm', payload, { auth: true })
}
