import WebSocket, { WebSocketServer } from 'ws'
import { getCameraConfig, isAllowedCameraIdentity } from './cameraConfig.js'
import { cameraFrameHub } from './cameraFrameHub.js'

function writeHttpError(socket, status, message) {
  socket.write(`HTTP/1.1 ${status} ${message}\r\nConnection: close\r\n\r\n`)
  socket.destroy()
}

function logCamera(event, details = {}) {
  console.log(
    `[camera-ingest] ${event} ${JSON.stringify({
      ...details,
      at: new Date().toISOString(),
    })}`
  )
}

function safeJsonParse(data) {
  try {
    return JSON.parse(String(data || ''))
  } catch (_error) {
    return null
  }
}

function safeSend(socket, payload) {
  if (socket.readyState !== WebSocket.OPEN) {
    return false
  }

  socket.send(JSON.stringify(payload))
  return true
}

function readHeaderValue(headers, name) {
  const value = headers[name.toLowerCase()]

  if (Array.isArray(value)) {
    return String(value[0] || '').trim()
  }

  return String(value || '').trim()
}

function readToken(request, url) {
  const bearer = readHeaderValue(request.headers, 'authorization')

  if (bearer.startsWith('Bearer ')) {
    return bearer.slice(7).trim()
  }

  return (
    url.searchParams.get('token') ||
    readHeaderValue(request.headers, 'x-camera-token')
  ).trim()
}

function readIdentity(request, url) {
  return {
    deviceId: String(url.searchParams.get('deviceId') || readHeaderValue(request.headers, 'x-device-id')).trim(),
    cameraId: String(url.searchParams.get('cameraId') || readHeaderValue(request.headers, 'x-camera-id')).trim(),
  }
}

function validateUpgrade(request, url, config) {
  if (!config.ingestEnabled) {
    const error = new Error('camera ingest is disabled')
    error.status = 503
    error.code = 'CAMERA_INGEST_DISABLED'
    throw error
  }

  if (!config.ingestToken) {
    const error = new Error('CAMERA_INGEST_TOKEN is not configured')
    error.status = 503
    error.code = 'CAMERA_TOKEN_NOT_CONFIGURED'
    throw error
  }

  const token = readToken(request, url)

  if (token !== config.ingestToken) {
    const error = new Error('invalid camera ingest token')
    error.status = 401
    error.code = 'CAMERA_TOKEN_INVALID'
    throw error
  }
}

function validateRegister(payload, config) {
  const deviceId = String(payload.deviceId || '').trim()
  const cameraId = String(payload.cameraId || '').trim()

  if (!deviceId || !cameraId) {
    const error = new Error('CAMERA_REGISTER requires deviceId and cameraId')
    error.code = 'CAMERA_REGISTER_INVALID'
    throw error
  }

  if (!isAllowedCameraIdentity(config, deviceId, cameraId)) {
    const error = new Error(`camera identity is not allowed: ${deviceId}/${cameraId}`)
    error.code = 'CAMERA_IDENTITY_FORBIDDEN'
    throw error
  }
}

export function attachCameraIngestWsServer(server) {
  const wss = new WebSocketServer({ noServer: true })

  wss.on('connection', (socket, request) => {
    const config = getCameraConfig()
    const requestUrl = new URL(request.url || '/', 'http://127.0.0.1')
    const queryIdentity = readIdentity(request, requestUrl)
    let registered = false

    socket.cleanScoutCameraRemoteAddress = request.socket?.remoteAddress || ''

    logCamera('connection-open', {
      remoteAddress: socket.cleanScoutCameraRemoteAddress,
      deviceId: queryIdentity.deviceId,
      cameraId: queryIdentity.cameraId,
    })

    socket.on('message', (data, isBinary) => {
      try {
        if (isBinary) {
          if (!registered) {
            throw Object.assign(new Error('binary frame received before CAMERA_REGISTER'), {
              code: 'CAMERA_NOT_REGISTERED',
            })
          }

          const frame = cameraFrameHub.acceptFrame(socket, data, config.maxFrameBytes)

          if (frame.seq === 1 || frame.seq % 60 === 0) {
            logCamera('frame-accepted', {
              deviceId: cameraFrameHub.deviceId,
              cameraId: cameraFrameHub.cameraId,
              seq: frame.seq,
              bytes: frame.bytes,
            })
          }
          return
        }

        const payload = safeJsonParse(data)

        if (!payload || typeof payload !== 'object') {
          throw Object.assign(new Error('message must be JSON or binary JPEG'), {
            code: 'CAMERA_INVALID_MESSAGE',
          })
        }

        if (payload.type === 'CAMERA_REGISTER') {
          validateRegister(payload, config)

          const activeConnection = cameraFrameHub.getActiveConnection()

          if (activeConnection && activeConnection !== socket && activeConnection.readyState === WebSocket.OPEN) {
            safeSend(activeConnection, {
              type: 'CAMERA_REPLACED',
              ok: false,
              message: 'camera session replaced by a newer worker connection',
              ts: Date.now(),
            })
            activeConnection.close(1000, 'replaced')
          }

          cameraFrameHub.register(socket, payload)
          registered = true

          logCamera('register-accepted', {
            deviceId: payload.deviceId,
            cameraId: payload.cameraId,
            source: payload.source || '',
          })

          safeSend(socket, {
            type: 'CAMERA_REGISTER_ACK',
            ok: true,
            deviceId: payload.deviceId,
            cameraId: payload.cameraId,
            ts: Date.now(),
          })
          return
        }

        if (payload.type === 'CAMERA_HEARTBEAT') {
          cameraFrameHub.heartbeat(socket, payload)
          safeSend(socket, {
            type: 'CAMERA_HEARTBEAT_ACK',
            ok: true,
            ts: Date.now(),
          })
          return
        }

        throw Object.assign(new Error(`unsupported camera message type: ${payload.type || 'missing'}`), {
          code: 'CAMERA_UNSUPPORTED_MESSAGE',
        })
      } catch (error) {
        cameraFrameHub.setError(error)
        logCamera('message-error', {
          code: error.code || 'CAMERA_MESSAGE_FAILED',
          message: error.message || '',
        })
        safeSend(socket, {
          type: 'CAMERA_ERROR',
          ok: false,
          code: error.code || 'CAMERA_MESSAGE_FAILED',
          message: error.message || 'camera ingest message failed',
          ts: Date.now(),
        })
      }
    })

    socket.on('close', (code, reason) => {
      logCamera('connection-close', {
        code,
        reason: String(reason || ''),
        deviceId: cameraFrameHub.deviceId,
        cameraId: cameraFrameHub.cameraId,
      })
      cameraFrameHub.disconnect(socket)
    })

    socket.on('error', (error) => {
      cameraFrameHub.setError(error)
      logCamera('socket-error', {
        message: error.message || '',
      })
    })
  })

  server.on('upgrade', (request, socket, head) => {
    const config = getCameraConfig()
    const requestUrl = new URL(request.url || '/', 'http://127.0.0.1')
    const pathname = requestUrl.pathname

    if (pathname !== config.ingestPath) {
      return
    }

    try {
      validateUpgrade(request, requestUrl, config)
    } catch (error) {
      logCamera('upgrade-rejected', {
        path: pathname,
        code: error.code || 'CAMERA_UPGRADE_REJECTED',
        message: error.message || '',
      })
      writeHttpError(socket, error.status || 403, error.status === 401 ? 'Unauthorized' : 'Forbidden')
      return
    }

    logCamera('upgrade-accepted', {
      path: pathname,
      remoteAddress: request.socket?.remoteAddress || '',
    })

    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit('connection', ws, request)
    })
  })

  return wss
}
