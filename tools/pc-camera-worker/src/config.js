import { existsSync, readFileSync } from 'node:fs'
import os from 'node:os'
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

function parseOptionalFlag(value) {
  if (value === undefined || value === null || value === '') {
    return null
  }

  const normalized = String(value).trim().toLowerCase()

  if (['1', 'true', 'yes', 'on'].includes(normalized)) {
    return 1
  }

  if (['0', 'false', 'no', 'off'].includes(normalized)) {
    return 0
  }

  return null
}

function required(value, name) {
  const normalized = String(value || '').trim()

  if (!normalized) {
    throw new Error(`${name} is required`)
  }

  return normalized
}

function getLocalIpv4() {
  const interfaces = os.networkInterfaces()

  for (const entries of Object.values(interfaces)) {
    for (const entry of entries || []) {
      if (entry.family === 'IPv4' && !entry.internal) {
        return entry.address
      }
    }
  }

  return ''
}

function buildHostFromSuffix(ip, suffix) {
  const parts = String(ip || '').trim().split('.')

  if (parts.length !== 4 || !suffix) {
    return ''
  }

  return `${parts[0]}.${parts[1]}.${parts[2]}.${suffix}`
}

function buildCameraSourceUrl() {
  const explicitUrl = String(process.env.CAMERA_SOURCE_URL || '').trim()

  if (explicitUrl) {
    return explicitUrl
  }

  const hostSuffix = String(process.env.CAMERA_SOURCE_HOST_SUFFIX || '91').trim()
  const port = String(process.env.CAMERA_SOURCE_PORT || '81').trim()
  const path = String(process.env.CAMERA_SOURCE_PATH || '/stream').trim() || '/stream'
  const localIp = getLocalIpv4()
  const host = buildHostFromSuffix(localIp, hostSuffix)

  if (!host) {
    return ''
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `http://${host}:${port}${normalizedPath}`
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
    cameraSourceUrl: mock ? 'mock://local' : required(buildCameraSourceUrl(), 'CAMERA_SOURCE_URL'),
    cameraMode: String(process.env.CAMERA_MODE || 'mjpeg').trim().toLowerCase(),
    cameraFrameSize: Number.isFinite(Number(process.env.CAMERA_FRAMESIZE)) ? Number(process.env.CAMERA_FRAMESIZE) : null,
    cameraHMirror: parseOptionalFlag(process.env.CAMERA_HMIRROR),
    cameraVFlip: parseOptionalFlag(process.env.CAMERA_VFLIP),
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
