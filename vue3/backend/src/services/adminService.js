import { createHttpError } from '../utils/response.js'

export async function executeAdminCommand(command, user) {
  const normalizedCommand = String(command || '').trim()

  if (!normalizedCommand) {
    throw createHttpError(400, '管理员命令不能为空', 'ADMIN_COMMAND_REQUIRED')
  }

  return {
    command: normalizedCommand,
    accepted: true,
    result: `Mock command "${normalizedCommand}" accepted by ${user.username}.`,
    executedAt: new Date().toISOString(),
  }
}
