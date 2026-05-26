import { fetchOpenMvSnapshotBuffer, getOpenMvRuntimeConfig, probeOpenMv } from './client.js'
import { getCameraConfig, isPushStreamMode } from '../../camera/cameraConfig.js'
import { cameraFrameHub } from '../../camera/cameraFrameHub.js'

function buildBaseStatus(config) {
  return {
    enabled: config.enabled,
    status: 'disabled',
    mode: config.mode,
    baseUrl: config.baseUrl,
    streamPath: config.streamPath,
    snapshotPath: config.snapshotPath,
    previewRefreshMs: config.refreshMs,
    lastProbeAt: new Date().toISOString(),
    message: 'OpenMV preview is disabled.',
  }
}

export async function getOpenMvStatus() {
  const config = getOpenMvRuntimeConfig()

  if (!config.enabled) {
    return {
      ...buildBaseStatus(config),
      message: 'OPENMV_ENABLED=false，当前未启用 OpenMV 图像预览。',
    }
  }

  if (isPushStreamMode()) {
    const cameraConfig = getCameraConfig()
    const cameraStatus = cameraFrameHub.getStatus(cameraConfig)
    const status = cameraStatus.cameraOnline ? 'healthy' : cameraStatus.ingestConnected ? 'degraded' : 'error'

    return {
      ...buildBaseStatus(config),
      ...cameraStatus,
      status,
      mode: 'mjpeg-stream-relay',
      baseUrl: '',
      message: cameraStatus.cameraOnline
        ? 'ESP32-CAM MJPEG 云端图传已接入。'
        : '等待 UbuntuPC camera-worker 上送 ESP32-CAM 图像帧。',
      streamPath: '/api/integrations/openmv/stream',
      snapshotPath: '/api/integrations/openmv/snapshot',
      previewPath: '/api/integrations/openmv/stream',
      snapshotFallbackPath: '/api/integrations/openmv/snapshot',
      previewRefreshMs: 0,
      inputMode: cameraConfig.openMvInputMode,
    }
  }

  try {
    const probe = await probeOpenMv(config)

    return {
      ...buildBaseStatus(config),
      status: 'healthy',
      message: `OpenMV ${config.mode.toUpperCase()} 图传可访问。`,
      contentType: probe.contentType,
      targetUrl: probe.targetUrl,
      previewPath: '/api/integrations/openmv/snapshot',
    }
  } catch (error) {
    return {
      ...buildBaseStatus(config),
      status: 'error',
      message: error.message || 'OpenMV 探测失败。',
    }
  }
}

export async function getOpenMvSnapshot() {
  const config = getOpenMvRuntimeConfig()

  if (!config.enabled) {
    const error = new Error('OpenMV preview is disabled.')
    error.status = 404
    error.code = 'OPENMV_DISABLED'
    throw error
  }

  if (isPushStreamMode()) {
    const cameraConfig = getCameraConfig()
    const frame = cameraFrameHub.getLatestFrame()

    if (!frame || !cameraFrameHub.isFrameFresh(cameraConfig.staleMs)) {
      const error = new Error('No fresh ESP32-CAM frame is available.')
      error.status = 503
      error.code = 'CAMERA_FRAME_UNAVAILABLE'
      throw error
    }

    return {
      contentType: 'image/jpeg',
      payload: frame.buffer,
      sourceUrl: 'camera-frame-hub',
    }
  }

  return fetchOpenMvSnapshotBuffer(config)
}
