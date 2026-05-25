import { createHttpError, sendSuccess } from '../utils/response.js'
import { getOpenClawAgentStatus, sendOpenClawAgentChat } from '../services/openclawAgentService.js'

export async function status(req, res, next) {
  try {
    const deviceId = req.query?.deviceId || req.body?.deviceId
    return sendSuccess(res, getOpenClawAgentStatus(deviceId))
  } catch (error) {
    next(error)
  }
}

export async function chat(req, res, next) {
  try {
    const result = await sendOpenClawAgentChat(req.user, req.body)
    return sendSuccess(res, result, 201)
  } catch (error) {
    next(error.status ? error : createHttpError(400, error.message, 'OPENCLAW_CHAT_FAILED'))
  }
}
