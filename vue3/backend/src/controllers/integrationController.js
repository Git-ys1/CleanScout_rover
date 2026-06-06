import { sendSuccess } from '../utils/response.js'
import { getAsrStatus } from '../integrations/asr/service.js'
import { getOpenClawStatus } from '../integrations/openclaw/service.js'
import { getOpenMvSnapshot, getOpenMvStatus } from '../integrations/openmv/service.js'
import { getRosStatus } from '../integrations/ros/index.js'
import { getOpenClawAgentStatus } from '../services/openclawAgentService.js'
import { createHttpError } from '../utils/response.js'
import { resolveAuthenticatedUserByToken } from '../middleware/authRequired.js'
import { getCameraConfig, isPushStreamMode } from '../camera/cameraConfig.js'
import { cameraFrameHub } from '../camera/cameraFrameHub.js'
import { streamLatestMjpeg } from '../camera/mjpegStream.js'

async function resolveOpenMvPreviewUser(req) {
  const headerToken = String(req.headers.authorization || '').startsWith('Bearer ')
    ? String(req.headers.authorization).slice(7).trim()
    : ''
  const queryToken = String(req.query.token || '').trim()
  const token = headerToken || queryToken

  if (!token) {
    throw createHttpError(401, '未提供 OpenMV 预览 token', 'AUTH_TOKEN_MISSING')
  }

  return resolveAuthenticatedUserByToken(token)
}

export async function openClawStatus(_req, res, next) {
  try {
    if (String(process.env.OPENCLAW_ROUTE_MODE || '').trim() === 'pc-worker') {
      return sendSuccess(res, getOpenClawAgentStatus())
    }

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
    await resolveOpenMvPreviewUser(req)

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

export async function openMvStream(req, res, next) {
  try {
    await resolveOpenMvPreviewUser(req)

    if (!isPushStreamMode()) {
      throw createHttpError(404, 'OpenMV MJPEG stream relay is not enabled.', 'OPENMV_STREAM_NOT_ENABLED')
    }

    streamLatestMjpeg(req, res, cameraFrameHub, getCameraConfig())
  } catch (error) {
    next(error.status ? error : createHttpError(502, error.message || 'OpenMV stream 获取失败', error.code || 'OPENMV_STREAM_FAILED'))
  }
}
