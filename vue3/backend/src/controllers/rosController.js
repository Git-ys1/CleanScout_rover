import { createHttpError, sendSuccess } from '../utils/response.js'
import { getRosTelemetrySummary, sendRosCmdVel, sendRosManualPreset } from '../integrations/ros/index.js'

export async function telemetrySummary(_req, res, next) {
  try {
    const summary = await getRosTelemetrySummary()
    return sendSuccess(res, summary)
  } catch (error) {
    next(error)
  }
}

export async function cmdVel(req, res, next) {
  try {
    const result = await sendRosCmdVel(req.body || {}, 'admin')
    return sendSuccess(res, result, 201)
  } catch (error) {
    next(error.status ? error : createHttpError(400, error.message, 'ROS_CMD_VEL_FAILED'))
  }
}

export async function manualPreset(req, res, next) {
  try {
    const result = await sendRosManualPreset(req.body || {}, 'admin')
    return sendSuccess(res, result, 201)
  } catch (error) {
    next(error.status ? error : createHttpError(400, error.message, 'ROS_MANUAL_PRESET_FAILED'))
  }
}
