function parseBoolean(value) {
  return /^(1|true|yes|on)$/i.test(String(value || '').trim())
}

function parseNumber(value, fallback, min = 0) {
  const parsed = Number(value || fallback)

  if (!Number.isFinite(parsed) || parsed < min) {
    return fallback
  }

  return parsed
}

function parseList(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function normalizePath(value, fallback) {
  const normalized = String(value || fallback).trim() || fallback

  return normalized.startsWith('/') ? normalized : `/${normalized}`
}

export function getCameraConfig() {
  return {
    openMvInputMode: String(process.env.OPENMV_INPUT_MODE || '').trim().toLowerCase() || 'direct',
    ingestEnabled: parseBoolean(process.env.CAMERA_INGEST_ENABLED),
    ingestPath: normalizePath(process.env.CAMERA_INGEST_PATH, '/edge/camera'),
    ingestToken: String(process.env.CAMERA_INGEST_TOKEN || '').trim(),
    allowedDeviceIds: parseList(process.env.CAMERA_ALLOWED_DEVICE_IDS),
    allowedCameraIds: parseList(process.env.CAMERA_ALLOWED_CAMERA_IDS),
    staleMs: parseNumber(process.env.CAMERA_FRAME_STALE_MS, 3000, 500),
    maxFrameBytes: parseNumber(process.env.CAMERA_MAX_FRAME_BYTES, 300000, 1024),
    streamBoundary: String(process.env.CAMERA_STREAM_BOUNDARY || 'cleanscout-openmv').trim() || 'cleanscout-openmv',
    streamHeartbeatMs: parseNumber(process.env.CAMERA_STREAM_HEARTBEAT_MS, 1000, 250),
    streamIntervalMs: parseNumber(process.env.CAMERA_STREAM_INTERVAL_MS, 50, 16),
    rawSubscriberBufferBytes: parseNumber(process.env.CAMERA_RAW_SUBSCRIBER_BUFFER_BYTES, 1048576, 65536),
    maxViewers: parseNumber(process.env.CAMERA_MAX_VIEWERS, 3, 0),
  }
}

export function isPushStreamMode() {
  return getCameraConfig().openMvInputMode === 'push-stream'
}

export function isAllowedCameraIdentity(config, deviceId, cameraId) {
  const deviceAllowed = config.allowedDeviceIds.length === 0 || config.allowedDeviceIds.includes(deviceId)
  const cameraAllowed = config.allowedCameraIds.length === 0 || config.allowedCameraIds.includes(cameraId)

  return deviceAllowed && cameraAllowed
}
