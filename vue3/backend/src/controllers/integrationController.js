import { sendSuccess } from '../utils/response.js'
import { getOpenClawStatus } from '../integrations/openclaw/service.js'

export async function openClawStatus(_req, res, next) {
  try {
    const status = await getOpenClawStatus()
    return sendSuccess(res, status)
  } catch (error) {
    next(error)
  }
}
