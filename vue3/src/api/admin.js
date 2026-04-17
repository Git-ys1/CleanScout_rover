import { post } from './http.js'

export function requestAdminCommand(command) {
  return post(
    '/admin/command',
    { command },
    { auth: true }
  )
}
