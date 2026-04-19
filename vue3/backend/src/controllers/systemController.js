import { prisma } from '../utils/prisma.js'
import { sendSuccess } from '../utils/response.js'

export async function health(_req, res, next) {
  try {
    await prisma.$queryRaw`SELECT 1`

    return sendSuccess(res, {
      service: 'ok',
      database: 'ok',
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    next(error)
  }
}
