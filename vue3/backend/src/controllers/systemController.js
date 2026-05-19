import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { prisma } from '../utils/prisma.js'
import { sendSuccess } from '../utils/response.js'

function readDeployRevision() {
  try {
    return readFileSync(join(process.cwd(), '.deploy-revision'), 'utf8').trim() || 'unknown'
  } catch (_error) {
    return 'unknown'
  }
}

export async function health(_req, res, next) {
  try {
    await prisma.$queryRaw`SELECT 1`

    return sendSuccess(res, {
      service: 'ok',
      database: 'ok',
      revision: readDeployRevision(),
      profile: process.env.APP_PROFILE || 'local-lan',
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    next(error)
  }
}
