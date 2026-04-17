import { createHttpError, sendSuccess } from '../utils/response.js'
import { executeAdminCommand } from '../services/adminService.js'

export async function command(req, res, next) {
  try {
    const commandText = req.body?.command

    if (!String(commandText || '').trim()) {
      throw createHttpError(400, '管理员命令不能为空', 'ADMIN_COMMAND_REQUIRED')
    }

    const result = await executeAdminCommand(commandText, req.user)
    return sendSuccess(res, result)
  } catch (error) {
    next(error.status ? error : createHttpError(400, error.message, 'ADMIN_COMMAND_FAILED'))
  }
}
