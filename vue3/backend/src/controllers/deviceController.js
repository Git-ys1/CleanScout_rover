import { getDeviceSummary } from '../services/deviceService.js'
import { sendSuccess } from '../utils/response.js'

export async function summary(_req, res, next) {
  try {
    const deviceSummary = await getDeviceSummary()
    return sendSuccess(res, deviceSummary)
  } catch (error) {
    next(error)
  }
}
