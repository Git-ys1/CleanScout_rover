import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

function loadDotEnv() {
  const envPath = resolve(process.cwd(), '.env')

  if (!existsSync(envPath)) {
    return
  }

  const content = readFileSync(envPath, 'utf8')

  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim()

    if (!trimmed || trimmed.startsWith('#') || !trimmed.includes('=')) {
      continue
    }

    const [key, ...rest] = trimmed.split('=')
    const value = rest.join('=').trim().replace(/^["']|["']$/g, '')

    if (!process.env[key]) {
      process.env[key] = value
    }
  }
}

function parseBoolean(value, fallback = false) {
  if (value === undefined || value === null || value === '') {
    return fallback
  }

  return /^(1|true|yes|on)$/i.test(String(value).trim())
}

function parseNumber(value, fallback, min = 0) {
  const parsed = Number(value || fallback)

  if (!Number.isFinite(parsed) || parsed < min) {
    return fallback
  }

  return parsed
}

function required(value, name) {
  const normalized = String(value || '').trim()

  if (!normalized) {
    throw new Error(`${name} is required`)
  }

  return normalized
}

export function loadConfig(argv = process.argv.slice(2)) {
  loadDotEnv()

  const mock = argv.includes('--mock') || parseBoolean(process.env.CAMERA_MOCK)
  const uplinkMode = String(process.env.CAMERA_UPLINK_MODE || 'raw-mjpeg').trim().toLowerCase()

  if (!['raw-mjpeg', 'jpeg-frame'].includes(uplinkMode)) {
    throw new Error(`CAMERA_UPLINK_MODE must be raw-mjpeg or jpeg-frame, got ${uplinkMode}`)
  }

  return {
    enabled: parseBoolean(process.env.CAMERA_WORKER_ENABLED, true),
    mock,
    deviceId: required(process.env.DEVICE_ID || 'pc-001', 'DEVICE_ID'),
    cameraId: required(process.env.CAMERA_ID || 'openmv-arm-cam-001', 'CAMERA_ID'),
    cameraSourceUrl: mock ? 'mock://local' : required(process.env.CAMERA_SOURCE_URL, 'CAMERA_SOURCE_URL'),
    cameraMode: String(process.env.CAMERA_MODE || 'mjpeg').trim().toLowerCase(),
    uplinkMode: mock ? 'jpeg-frame' : uplinkMode,
    targetFps: parseNumber(process.env.CAMERA_TARGET_FPS, 20, 1),
    maxFrameBytes: parseNumber(process.env.CAMERA_MAX_FRAME_BYTES, 500000, 1024),
    maxCloudBufferedBytes: parseNumber(process.env.CAMERA_MAX_CLOUD_BUFFERED_BYTES, 2097152, 65536),
    cameraConnectTimeoutMs: parseNumber(process.env.CAMERA_CONNECT_TIMEOUT_MS, 3000, 500),
    cameraReadTimeoutMs: parseNumber(process.env.CAMERA_READ_TIMEOUT_MS, 8000, 1000),
    cloudWsUrl: required(process.env.CAMERA_CLOUD_WS, 'CAMERA_CLOUD_WS'),
    cloudToken: required(process.env.CAMERA_CLOUD_TOKEN, 'CAMERA_CLOUD_TOKEN'),
    reconnectDelayMs: parseNumber(process.env.CAMERA_RECONNECT_DELAY_MS, 2000, 500),
    logLevel: String(process.env.CAMERA_LOG_LEVEL || 'info').trim().toLowerCase(),
  }
}
