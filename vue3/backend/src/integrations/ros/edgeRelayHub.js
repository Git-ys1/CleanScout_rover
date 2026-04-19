import bcrypt from 'bcrypt'
import WebSocket, { WebSocketServer } from 'ws'
import { prisma } from '../../utils/prisma.js'
import { isZeroCommand } from './dto.js'

function safeJsonParse(data) {
  try {
    return JSON.parse(String(data || ''))
  } catch (_error) {
    return null
  }
}

function stringifyJson(value, fallback) {
  try {
    return JSON.stringify(value ?? fallback)
  } catch (_error) {
    return JSON.stringify(fallback)
  }
}

function getOpenConstant() {
  return WebSocket.OPEN
}

function isOpen(socket) {
  return socket && socket.readyState === getOpenConstant()
}

function writeHttpError(socket, status, message) {
  socket.write(`HTTP/1.1 ${status} ${message}\r\nConnection: close\r\n\r\n`)
  socket.destroy()
}

function logEdge(event, details = {}) {
  console.log(
    `[edge-relay] ${event} ${JSON.stringify({
      ...details,
      at: new Date().toISOString(),
    })}`
  )
}

function toIsoTime(value) {
  if (!value) {
    return new Date().toISOString()
  }

  const numericValue = Number(value)
  const date = Number.isFinite(numericValue) ? new Date(numericValue) : new Date(value)
  return Number.isNaN(date.getTime()) ? new Date().toISOString() : date.toISOString()
}

function toDate(value) {
  return new Date(toIsoTime(value))
}

function createAllowedDeviceSet(value) {
  return new Set(
    String(value || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
  )
}

function buildTelemetrySummary(deviceId, payload, cache) {
  return {
    deviceId,
    online: true,
    transport: 'edge-relay',
    lastUpdate: toIsoTime(payload.ts),
    telemetry: cache.getTelemetrySummary(),
    scanSummary: payload.scanSummary || null,
  }
}

export function createEdgeRelayHub(config, cache) {
  let wss = null
  let pingTimer = null
  let sequence = 0
  const sessions = new Map()
  const allowedDeviceIds = createAllowedDeviceSet(config.edgeAllowedDeviceIds)

  function isEnabled() {
    return Boolean(config.enabled && config.edgeRelayEnabled)
  }

  function isAllowedDeviceId(deviceId) {
    return allowedDeviceIds.size === 0 || allowedDeviceIds.has(deviceId)
  }

  function sendJson(socket, payload) {
    if (!isOpen(socket)) {
      return false
    }

    socket.send(JSON.stringify(payload))
    return true
  }

  function reject(socket, code, message) {
    logEdge('reject', {
      code,
      message,
      deviceId: socket.edgeRelaySession?.deviceId || '',
      remoteAddress: socket.edgeRelayRemoteAddress || '',
    })
    cache.setRelayError(`${code}: ${message}`)
    sendJson(socket, {
      op: 'error',
      code,
      message,
      ts: Date.now(),
    })
    socket.close(1008, code)
  }

  function getActiveSession() {
    for (const session of sessions.values()) {
      if (isOpen(session.socket)) {
        return session
      }
    }

    return null
  }

  async function updateDeviceDisconnect(deviceId) {
    try {
      await prisma.edgeDevice.update({
        where: { deviceId },
        data: {
          lastDisconnectAt: new Date(),
        },
      })
    } catch (error) {
      cache.setRelayError(error.message || 'Edge relay disconnect update failed')
    }
  }

  function closeExistingSession(deviceId, nextSocket) {
    const existing = sessions.get(deviceId)

    if (!existing || existing.socket === nextSocket) {
      return
    }

    if (isOpen(existing.socket)) {
      logEdge('replace-session', {
        deviceId,
      })
      existing.socket.close(4000, 'EDGE_DEVICE_REPLACED')
    }

    sessions.delete(deviceId)
  }

  async function authenticateHello(socket, payload) {
    const deviceId = String(payload?.deviceId || '').trim()
    const token = String(payload?.token || '').trim()

    if (!deviceId) {
      reject(socket, 'EDGE_HELLO_DEVICE_ID_REQUIRED', 'deviceId is required')
      return false
    }

    if (!isAllowedDeviceId(deviceId)) {
      reject(socket, 'EDGE_DEVICE_NOT_ALLOWED', 'deviceId is not allowed')
      return false
    }

    const edgeDevice = await prisma.edgeDevice.findUnique({
      where: { deviceId },
    })

    if (!edgeDevice || !edgeDevice.isEnabled) {
      reject(socket, 'EDGE_DEVICE_DISABLED', 'edge device is not registered or disabled')
      return false
    }

    if (config.edgeDeviceAuthRequired) {
      const tokenValid = token ? await bcrypt.compare(token, edgeDevice.tokenHash) : false

      if (!tokenValid) {
        reject(socket, 'EDGE_DEVICE_AUTH_FAILED', 'edge device token is invalid')
        return false
      }
    }

    const now = new Date()
    const topics = payload?.topics && typeof payload.topics === 'object' ? payload.topics : {}
    const capabilities = Array.isArray(payload?.capabilities) ? payload.capabilities : []

    await prisma.edgeDevice.update({
      where: { deviceId },
      data: {
        transport: 'edge-relay',
        topicsJson: stringifyJson(topics, {}),
        capabilitiesJson: stringifyJson(capabilities, []),
        lastSeenAt: now,
        lastHelloAt: now,
      },
    })

    closeExistingSession(deviceId, socket)

    const session = {
      socket,
      deviceId,
      topics,
      capabilities,
      lastSeenAt: now.getTime(),
      lastTelemetryAt: '',
    }

    socket.edgeRelaySession = session
    sessions.set(deviceId, session)
    cache.setEdgeRelayConnected({ connected: true, deviceId, at: now.toISOString() })
    logEdge('hello-accepted', {
      deviceId,
      capabilities,
      topics,
    })

    sendJson(socket, {
      op: 'hello_ack',
      deviceId,
      accepted: true,
      ts: Date.now(),
    })

    return true
  }

  async function handleHeartbeat(session, payload) {
    const timestamp = toIsoTime(payload?.ts)
    session.lastSeenAt = new Date(timestamp).getTime()
    cache.markHeartbeat(timestamp)

    await prisma.edgeDevice.update({
      where: { deviceId: session.deviceId },
      data: {
        lastSeenAt: toDate(timestamp),
      },
    })
  }

  async function handleTelemetry(session, payload) {
    const timestamp = toIsoTime(payload?.ts)
    session.lastSeenAt = new Date(timestamp).getTime()
    session.lastTelemetryAt = timestamp

    cache.updateEdgeTelemetry(payload)

    await prisma.edgeDevice.update({
      where: { deviceId: session.deviceId },
      data: {
        lastSeenAt: toDate(timestamp),
      },
    })

    await prisma.deviceCache.upsert({
      where: { deviceId: session.deviceId },
      update: {
        summaryJson: stringifyJson(buildTelemetrySummary(session.deviceId, payload, cache), {}),
      },
      create: {
        deviceId: session.deviceId,
        summaryJson: stringifyJson(buildTelemetrySummary(session.deviceId, payload, cache), {}),
      },
    })
  }

  async function handleAuthenticatedMessage(socket, payload) {
    const session = socket.edgeRelaySession

    if (!session) {
      reject(socket, 'EDGE_HELLO_REQUIRED', 'hello is required before telemetry')
      return
    }

    if (payload.op === 'heartbeat') {
      await handleHeartbeat(session, payload)
      return
    }

    if (payload.op === 'telemetry') {
      await handleTelemetry(session, payload)
      return
    }

    cache.setRelayError(`Unsupported edge-relay op: ${payload.op || 'missing'}`)
  }

  async function handleMessage(socket, data) {
    const payload = safeJsonParse(data)

    if (!payload || typeof payload !== 'object') {
      reject(socket, 'EDGE_INVALID_JSON', 'message must be JSON')
      return
    }

    try {
      if (!socket.edgeRelaySession) {
        if (payload.op !== 'hello') {
          reject(socket, 'EDGE_HELLO_REQUIRED', 'first message must be hello')
          return
        }

        await authenticateHello(socket, payload)
        return
      }

      await handleAuthenticatedMessage(socket, payload)
    } catch (error) {
      cache.setRelayError(error.message || 'edge-relay message failed')
      reject(socket, 'EDGE_MESSAGE_FAILED', error.message || 'edge-relay message failed')
    }
  }

  function handleConnection(socket) {
    socket.edgeRelayRemoteAddress = socket._socket?.remoteAddress || ''
    logEdge('connection-open', {
      remoteAddress: socket.edgeRelayRemoteAddress,
    })

    const helloTimer = setTimeout(() => {
      if (!socket.edgeRelaySession) {
        reject(socket, 'EDGE_HELLO_TIMEOUT', 'hello timeout')
      }
    }, config.edgeHelloTimeoutMs)

    socket.on('message', (data) => {
      handleMessage(socket, data).catch((error) => {
        cache.setRelayError(error.message || 'edge-relay message failed')
      })
    })

    socket.on('close', (code, reason) => {
      clearTimeout(helloTimer)
      const session = socket.edgeRelaySession
      const reasonText = String(reason || '')
      logEdge('connection-close', {
        code,
        reason: reasonText,
        deviceId: session?.deviceId || '',
        remoteAddress: socket.edgeRelayRemoteAddress || '',
      })

      if (code !== 1000 && code !== 1005) {
        cache.setRelayError(`${code}: ${reasonText || 'edge-relay closed'}`)
      }

      if (!session) {
        return
      }

      if (sessions.get(session.deviceId)?.socket === socket) {
        sessions.delete(session.deviceId)
        cache.setEdgeRelayConnected({ connected: false })
        updateDeviceDisconnect(session.deviceId).catch(() => {})
      }
    })

    socket.on('error', (error) => {
      cache.setRelayError(error.message || 'edge-relay socket error')
    })
  }

  function checkSessions() {
    const now = Date.now()

    for (const session of sessions.values()) {
      if (!isOpen(session.socket)) {
        continue
      }

      if (now - session.lastSeenAt > config.edgeHeartbeatTimeoutMs) {
        session.socket.close(4001, 'EDGE_HEARTBEAT_TIMEOUT')
        continue
      }

      session.socket.ping()
    }
  }

  function attach(server) {
    if (wss) {
      return
    }

    wss = new WebSocketServer({ noServer: true })
    wss.on('connection', handleConnection)

    server.on('upgrade', (request, socket, head) => {
      const pathname = new URL(request.url || '/', 'http://127.0.0.1').pathname

      if (pathname !== config.edgeRelayPath) {
        socket.destroy()
        return
      }

      if (!isEnabled()) {
        logEdge('upgrade-rejected', {
          reason: 'disabled',
          path: pathname,
        })
        writeHttpError(socket, 503, 'Service Unavailable')
        return
      }

      logEdge('upgrade-accepted', {
        path: pathname,
        remoteAddress: request.socket?.remoteAddress || '',
      })

      wss.handleUpgrade(request, socket, head, (ws) => {
        wss.emit('connection', ws, request)
      })
    })

    pingTimer = setInterval(checkSessions, config.edgeServerPingIntervalMs)
  }

  async function sendCommand(command) {
    if (!isEnabled()) {
      throw new Error('edge-relay transport is disabled')
    }

    const session = getActiveSession()

    if (!session) {
      throw new Error('edge-relay device is not connected')
    }

    sequence += 1

    const frame = isZeroCommand(command)
      ? {
          op: 'stop',
          seq: sequence,
        }
      : {
          op: 'manual_control',
          seq: sequence,
          vx: Number(command.linear?.x || 0),
          vy: Number(command.linear?.y || 0),
          wz: Number(command.angular?.z || 0),
          holdMs: Number(command.holdMs || 0),
        }

    sendJson(session.socket, frame)
    cache.applyCommand(command)

    return {
      seq: sequence,
      frame,
      deviceId: session.deviceId,
    }
  }

  function getStatus() {
    const session = getActiveSession()

    if (!session) {
      cache.setEdgeRelayConnected({ connected: false })
    }

    return {
      ...cache.getStatusSnapshot(),
      edgeRelayConnected: Boolean(session),
      edgeDeviceId: session?.deviceId || '',
      lastTelemetryAt: session?.lastTelemetryAt || cache.getStatusSnapshot().lastTelemetryAt,
    }
  }

  function close() {
    if (pingTimer) {
      clearInterval(pingTimer)
      pingTimer = null
    }

    if (wss) {
      wss.close()
      wss = null
    }
  }

  return {
    attach,
    close,
    getStatus,
    sendCommand,
  }
}
