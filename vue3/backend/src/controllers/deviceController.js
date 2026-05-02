import { getRosFanState, sendRosFanEnable, sendRosFanPwm } from '../integrations/ros/index.js'
import { getDeviceSummary } from '../services/deviceService.js'
import { createHttpError, sendSuccess } from '../utils/response.js'

export async function summary(_req, res, next) {
  try {
    const deviceSummary = await getDeviceSummary()
    return sendSuccess(res, deviceSummary)
  } catch (error) {
    next(error)
  }
}

export async function fansState(_req, res, next) {
  try {
    const fanState = await getRosFanState()
    return sendSuccess(res, fanState)
  } catch (error) {
    next(error)
  }
}

export async function fansEnable(req, res, next) {
  try {
    const result = await sendRosFanEnable(req.body || {})
    return sendSuccess(res, result, 201)
  } catch (error) {
    next(error.status ? error : createHttpError(400, error.message, 'ROS_FAN_ENABLE_FAILED'))
  }
}

export async function fansPwm(req, res, next) {
  try {
    const result = await sendRosFanPwm(req.body || {})
    return sendSuccess(res, result, 201)
  } catch (error) {
    next(error.status ? error : createHttpError(400, error.message, 'ROS_FAN_PWM_FAILED'))
  }
}
