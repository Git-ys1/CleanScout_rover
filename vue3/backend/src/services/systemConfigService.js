import { prisma } from '../utils/prisma.js'
import { createHttpError } from '../utils/response.js'

export const SYSTEM_CONFIG_ID = 'system'

export async function getSystemConfig() {
  return prisma.systemConfig.upsert({
    where: { id: SYSTEM_CONFIG_ID },
    update: {},
    create: {
      id: SYSTEM_CONFIG_ID,
      registrationEnabled: true,
      appEnabled: true,
      maintenanceMessage: '',
      openclawEnabled: false,
    },
  })
}

export async function updateSystemConfig(payload) {
  const data = {}

  if (payload.registrationEnabled !== undefined) {
    data.registrationEnabled = Boolean(payload.registrationEnabled)
  }

  if (payload.appEnabled !== undefined) {
    data.appEnabled = Boolean(payload.appEnabled)
  }

  if (payload.openclawEnabled !== undefined) {
    data.openclawEnabled = Boolean(payload.openclawEnabled)
  }

  if (payload.maintenanceMessage !== undefined) {
    data.maintenanceMessage = String(payload.maintenanceMessage || '').trim()
  }

  if (!Object.keys(data).length) {
    throw createHttpError(400, '未提供可更新字段', 'SYSTEM_CONFIG_PATCH_EMPTY')
  }

  return prisma.systemConfig.update({
    where: { id: SYSTEM_CONFIG_ID },
    data,
  })
}
