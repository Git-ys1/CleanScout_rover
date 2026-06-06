import WebSocket from 'ws'

function nowTs() {
  return Date.now()
}

function safeJsonParse(data) {
  try {
    return JSON.parse(String(data || ''))
  } catch (_error) {
    return null
  }
}

function appendQuery(url, params) {
  const parsed = new URL(url)

  for (const [key, value] of Object.entries(params)) {
    if (value) {
      parsed.searchParams.set(key, value)
    }
  }

  return parsed.toString()
}

export class CloudCameraClient {
  constructor(config) {
    this.config = config
    this.socket = null
    this.registered = false
    this.lastFrameBytes = 0
    this.lastError = ''
    this.heartbeatTimer = null
    this.connectedAt = 0
  }

  isOpen() {
    return this.socket?.readyState === WebSocket.OPEN
  }

  connect() {
    return new Promise((resolve, reject) => {
      const targetUrl = appendQuery(this.config.cloudWsUrl, {
        token: this.config.cloudToken,
        deviceId: this.config.deviceId,
        cameraId: this.config.cameraId,
      })

      this.socket = new WebSocket(targetUrl)

      const onError = (error) => {
        this.lastError = error.message || String(error)
        reject(error)
      }

      this.socket.once('error', onError)

      this.socket.on('open', () => {
        this.socket.off('error', onError)
        this.connectedAt = nowTs()
        this.register()
        this.heartbeatTimer = setInterval(() => this.heartbeat(), 5000)
        console.log(`[pc-camera-worker] cloud connected ${this.config.cloudWsUrl}`)
        resolve()
      })

      this.socket.on('message', (data) => this.handleMessage(data))
      this.socket.on('close', (code, reason) => {
        this.registered = false
        clearInterval(this.heartbeatTimer)
        this.heartbeatTimer = null
        console.warn(`[pc-camera-worker] cloud disconnected code=${code} reason=${String(reason || '')}`)
      })
      this.socket.on('error', (error) => {
        this.lastError = error.message || String(error)
        console.warn(`[pc-camera-worker] cloud socket error: ${this.lastError}`)
      })
    })
  }

  close() {
    clearInterval(this.heartbeatTimer)
    this.heartbeatTimer = null

    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.close(1000, 'worker shutdown')
    }
  }

  sendJson(payload) {
    if (!this.isOpen()) {
      return false
    }

    this.socket.send(JSON.stringify(payload))
    return true
  }

  register() {
    this.sendJson({
      type: 'CAMERA_REGISTER',
      deviceId: this.config.deviceId,
      cameraId: this.config.cameraId,
      source: 'esp32-cam-sta',
      cameraUrl: this.config.cameraSourceUrl,
      mode: this.config.uplinkMode,
      sourceMode: this.config.cameraMode,
      workerVersion: 'V-2.2.2',
      ts: nowTs(),
    })
  }

  startRawStream(extra = {}) {
    return this.sendJson({
      type: 'CAMERA_STREAM_START',
      deviceId: this.config.deviceId,
      cameraId: this.config.cameraId,
      mode: 'raw-mjpeg',
      contentType: extra.contentType || '',
      ts: nowTs(),
    })
  }

  heartbeat(extra = {}) {
    this.sendJson({
      type: 'CAMERA_HEARTBEAT',
      deviceId: this.config.deviceId,
      cameraId: this.config.cameraId,
      fps: extra.fps || 0,
      lastFrameBytes: this.lastFrameBytes,
      cameraReachable: Boolean(extra.cameraReachable),
      uplinkReady: this.isOpen(),
      lastError: this.lastError,
      ts: nowTs(),
    })
  }

  sendFrame(frame) {
    if (!this.isOpen()) {
      return false
    }

    if (this.socket.bufferedAmount > this.config.maxCloudBufferedBytes) {
      this.lastError = `cloud websocket buffered too much data: ${this.socket.bufferedAmount}`
      return false
    }

    this.lastFrameBytes = frame.length
    this.socket.send(frame, {
      binary: true,
    })
    return true
  }

  handleMessage(data) {
    const payload = safeJsonParse(data)

    if (!payload) {
      return
    }

    if (payload.type === 'CAMERA_REGISTER_ACK') {
      this.registered = true
      console.log(`[pc-camera-worker] registered device=${payload.deviceId} camera=${payload.cameraId}`)
      return
    }

    if (payload.type === 'CAMERA_HEARTBEAT_ACK') {
      return
    }

    if (payload.type === 'CAMERA_REPLACED') {
      console.warn('[pc-camera-worker] camera session replaced by another worker')
      return
    }

    if (payload.type === 'CAMERA_ERROR') {
      console.warn(`[pc-camera-worker] backend camera error ${payload.code || ''}: ${payload.message || ''}`)
    }
  }
}
