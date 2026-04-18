import { createHttpError, sendSuccess } from '../utils/response.js'
import {
  createManagedUser,
  deleteManagedUser,
  executeAdminCommand,
  listManagedUsers,
  updateManagedUser,
} from '../services/adminService.js'
import { getSystemConfig, updateSystemConfig } from '../services/systemConfigService.js'

export async function listUsers(_req, res, next) {
  try {
    const users = await listManagedUsers()
    return sendSuccess(res, users)
  } catch (error) {
    next(error)
  }
}

export async function createUser(req, res, next) {
  try {
    const user = await createManagedUser(req.body)
    return sendSuccess(res, user, 201)
  } catch (error) {
    next(error)
  }
}

export async function updateUser(req, res, next) {
  try {
    const user = await updateManagedUser(req.params.id, req.body, req.user)
    return sendSuccess(res, user)
  } catch (error) {
    next(error)
  }
}

export async function deleteUser(req, res, next) {
  try {
    const result = await deleteManagedUser(req.params.id, req.user)
    return sendSuccess(res, result)
  } catch (error) {
    next(error)
  }
}

export async function getSystemConfigValue(_req, res, next) {
  try {
    const config = await getSystemConfig()
    return sendSuccess(res, config)
  } catch (error) {
    next(error)
  }
}

export async function patchSystemConfig(req, res, next) {
  try {
    const config = await updateSystemConfig(req.body)
    return sendSuccess(res, config)
  } catch (error) {
    next(error)
  }
}

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
