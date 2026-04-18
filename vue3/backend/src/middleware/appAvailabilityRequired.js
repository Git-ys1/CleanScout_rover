import { getSystemConfig } from '../services/systemConfigService.js'
import { createHttpError } from '../utils/response.js'

export async function appAvailabilityRequired(req, _res, next) {
  try {
    const systemConfig = await getSystemConfig()
    req.systemConfig = systemConfig

    if (req.user?.role === 'admin' || systemConfig.appEnabled) {
      next()
      return
    }

    const maintenanceMessage = systemConfig.maintenanceMessage || '系统维护中'
    next(createHttpError(503, maintenanceMessage, 'SYSTEM_MAINTENANCE'))
  } catch (error) {
    next(error)
  }
}
