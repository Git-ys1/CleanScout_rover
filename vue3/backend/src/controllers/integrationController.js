import { sendSuccess } from '../utils/response.js'
import { getOpenClawStatus } from '../integrations/openclaw/service.js'
import { getRosStatus } from '../integrations/ros/index.js'

export async function openClawStatus(_req, res, next) {
  try {
    const status = await getOpenClawStatus()
    return sendSuccess(res, status)
  } catch (error) {
    next(error)
  }
}

export async function rosStatus(_req, res, next) {
  try {
    const status = await getRosStatus()
    return sendSuccess(res, status)
  } catch (error) {
    next(error)
  }
}
