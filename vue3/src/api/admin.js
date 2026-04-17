import { get, patch, post, remove } from './http.js'

export function requestAdminCommand(command) {
  return post(
    '/admin/command',
    { command },
    { auth: true }
  )
}

export function requestAdminUsers() {
  return get('/admin/users', { auth: true })
}

export function requestCreateAdminUser(payload) {
  return post('/admin/users', payload, { auth: true })
}

export function requestUpdateAdminUser(userId, payload) {
  return patch(`/admin/users/${userId}`, payload, { auth: true })
}

export function requestDeleteAdminUser(userId) {
  return remove(`/admin/users/${userId}`, { auth: true })
}

export function requestSystemConfig() {
  return get('/admin/system-config', { auth: true })
}

export function requestUpdateSystemConfig(payload) {
  return patch('/admin/system-config', payload, { auth: true })
}
