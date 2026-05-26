const JPEG_START = Buffer.from([0xff, 0xd8])
const JPEG_END = Buffer.from([0xff, 0xd9])

function now() {
  return Date.now()
}

function isJpeg(buffer) {
  return buffer.length >= 4 && buffer.subarray(0, 2).equals(JPEG_START) && buffer.subarray(buffer.length - 2).equals(JPEG_END)
}

function toIso(value) {
  return value ? new Date(value).toISOString() : null
}

function calculateFps(frameTimes) {
  if (frameTimes.length < 2) {
    return 0
  }

  const durationMs = frameTimes[frameTimes.length - 1] - frameTimes[0]

  if (durationMs <= 0) {
    return 0
  }

  return Math.round(((frameTimes.length - 1) * 10000) / durationMs) / 10
}

class CameraFrameHub {
  constructor() {
    this.reset()
  }

  reset() {
    this.connection = null
    this.deviceId = ''
    this.cameraId = ''
    this.source = ''
    this.sourceUrl = ''
    this.workerVersion = ''
    this.ingestConnected = false
    this.lastRegisterAt = 0
    this.lastHeartbeatAt = 0
    this.lastDisconnectAt = 0
    this.latestFrame = null
    this.latestFrameAt = 0
    this.latestFrameBytes = 0
    this.latestFrameSeq = 0
    this.lastRelayError = ''
    this.heartbeatFps = 0
    this.cameraReachable = false
    this.uplinkReady = false
    this.viewerCount = 0
    this.frameTimes = []
  }

  register(connection, payload = {}) {
    this.connection = connection
    this.deviceId = String(payload.deviceId || '').trim()
    this.cameraId = String(payload.cameraId || '').trim()
    this.source = String(payload.source || '').trim()
    this.sourceUrl = String(payload.cameraUrl || '').trim()
    this.workerVersion = String(payload.workerVersion || '').trim()
    this.ingestConnected = true
    this.lastRegisterAt = now()
    this.lastHeartbeatAt = this.lastRegisterAt
    this.lastRelayError = ''
  }

  heartbeat(connection, payload = {}) {
    if (connection !== this.connection) {
      return
    }

    this.lastHeartbeatAt = now()
    this.heartbeatFps = Number(payload.fps || 0) || this.heartbeatFps
    this.latestFrameBytes = Number(payload.lastFrameBytes || 0) || this.latestFrameBytes
    this.cameraReachable = Boolean(payload.cameraReachable)
    this.uplinkReady = Boolean(payload.uplinkReady)
    this.lastRelayError = String(payload.lastError || '')
  }

  acceptFrame(connection, payload, maxFrameBytes) {
    if (connection !== this.connection) {
      const error = new Error('camera frame belongs to an inactive connection')
      error.code = 'CAMERA_INACTIVE_CONNECTION'
      throw error
    }

    const frame = Buffer.isBuffer(payload) ? payload : Buffer.from(payload)

    if (frame.length > maxFrameBytes) {
      const error = new Error(`camera frame exceeds limit: ${frame.length} > ${maxFrameBytes}`)
      error.code = 'CAMERA_FRAME_TOO_LARGE'
      throw error
    }

    if (!isJpeg(frame)) {
      const error = new Error('camera frame is not a complete JPEG payload')
      error.code = 'CAMERA_INVALID_JPEG'
      throw error
    }

    const at = now()
    this.latestFrame = frame
    this.latestFrameAt = at
    this.latestFrameBytes = frame.length
    this.latestFrameSeq += 1
    this.cameraReachable = true
    this.uplinkReady = true
    this.frameTimes.push(at)

    while (this.frameTimes.length > 30) {
      this.frameTimes.shift()
    }

    return this.getLatestFrame()
  }

  disconnect(connection) {
    if (connection !== this.connection) {
      return
    }

    this.connection = null
    this.ingestConnected = false
    this.lastDisconnectAt = now()
    this.cameraReachable = false
    this.uplinkReady = false
  }

  setError(error) {
    this.lastRelayError = error?.message || String(error || '')
  }

  addViewer() {
    this.viewerCount += 1
    return this.viewerCount
  }

  removeViewer() {
    this.viewerCount = Math.max(0, this.viewerCount - 1)
    return this.viewerCount
  }

  getViewerCount() {
    return this.viewerCount
  }

  getActiveConnection() {
    return this.connection
  }

  getLatestFrame() {
    if (!this.latestFrame) {
      return null
    }

    return {
      buffer: this.latestFrame,
      at: this.latestFrameAt,
      bytes: this.latestFrameBytes,
      seq: this.latestFrameSeq,
    }
  }

  isFrameFresh(staleMs) {
    return Boolean(this.latestFrameAt && now() - this.latestFrameAt <= staleMs)
  }

  getStatus(config) {
    const current = now()
    const lastFrameAgeMs = this.latestFrameAt ? current - this.latestFrameAt : null
    const lastHeartbeatAgeMs = this.lastHeartbeatAt ? current - this.lastHeartbeatAt : null
    const frameFresh = this.isFrameFresh(config.staleMs)
    const cameraOnline = Boolean(this.ingestConnected && frameFresh)
    const fps = this.heartbeatFps || calculateFps(this.frameTimes)

    return {
      enabled: true,
      mode: 'mjpeg-stream-relay',
      cameraOnline,
      ingestConnected: this.ingestConnected,
      deviceId: this.deviceId,
      cameraId: this.cameraId,
      source: this.source || 'ubuntu-pc-camera-worker',
      sourceUrl: this.sourceUrl,
      workerVersion: this.workerVersion,
      lastRegisterAt: toIso(this.lastRegisterAt),
      lastHeartbeatAt: toIso(this.lastHeartbeatAt),
      lastDisconnectAt: toIso(this.lastDisconnectAt),
      lastFrameAt: toIso(this.latestFrameAt),
      lastFrameAgeMs,
      lastHeartbeatAgeMs,
      lastFrameBytes: this.latestFrameBytes,
      lastFrameSeq: this.latestFrameSeq,
      fps,
      viewerCount: this.viewerCount,
      staleMs: config.staleMs,
      maxViewers: config.maxViewers,
      cameraReachable: this.cameraReachable,
      uplinkReady: this.uplinkReady,
      lastRelayError: this.lastRelayError,
    }
  }
}

export const cameraFrameHub = new CameraFrameHub()
