import { sendSuccess } from '../utils/response.js'
import { getAsrStatus } from '../integrations/asr/service.js'
import { getOpenClawStatus } from '../integrations/openclaw/service.js'
import { getOpenMvSnapshot, getOpenMvStatus } from '../integrations/openmv/service.js'
import { getRosStatus } from '../integrations/ros/index.js'
import { createHttpError } from '../utils/response.js'
import { resolveAuthenticatedUserByToken } from '../middleware/authRequired.js'

export async function openClawStatus(_req, res, next) {
  try {
    const status = await getOpenClawStatus()
    return sendSuccess(res, status)
  } catch (error) {
    next(error)
  }
}

export async function asrStatus(_req, res, next) {
  try {
    const status = await getAsrStatus()
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

export async function openMvStatus(_req, res, next) {
  try {
    const status = await getOpenMvStatus()
    return sendSuccess(res, status)
  } catch (error) {
    next(error)
  }
}

export async function openMvSnapshot(req, res, next) {
  try {
    const headerToken = String(req.headers.authorization || '').startsWith('Bearer ')
      ? String(req.headers.authorization).slice(7).trim()
      : ''
    const queryToken = String(req.query.token || '').trim()
    const token = headerToken || queryToken

    if (!token) {
      throw createHttpError(401, '未提供 OpenMV 预览 token', 'AUTH_TOKEN_MISSING')
    }

    await resolveAuthenticatedUserByToken(token)

    const snapshot = await getOpenMvSnapshot()
    res.setHeader('Content-Type', snapshot.contentType || 'image/jpeg')
    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate')
    res.setHeader('Pragma', 'no-cache')
    res.setHeader('Expires', '0')
    res.status(200).send(snapshot.payload)
  } catch (error) {
    next(error.status ? error : createHttpError(502, error.message || 'OpenMV 预览获取失败', error.code || 'OPENMV_SNAPSHOT_FAILED'))
  }
}
