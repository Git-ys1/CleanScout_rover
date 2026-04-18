import { get, post } from './http.js'

export function requestRegister(payload) {
  return post('/auth/register', payload)
}

export function requestLogin(payload) {
  return post('/auth/login', payload)
}

export function requestCurrentUser() {
  return get('/auth/me', { auth: true })
}

export function requestLogout() {
  return post('/auth/logout', {}, { auth: true })
}
