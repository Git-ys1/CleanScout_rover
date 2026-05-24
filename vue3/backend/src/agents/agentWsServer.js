import WebSocket, { WebSocketServer } from 'ws'
import { agentRegistry } from './agentRegistry.js'

function parseBoolean(value) {
  return String(value || '').trim().toLowerCase() === 'true'
}

function getAgentWsConfig() {
  return {
    enabled: parseBoolean(process.env.AGENT_WS_ENABLED),
    path: String(process.env.AGENT_WS_PATH || '/ws/agents').trim() || '/ws/agents',
  }
}

function writeHttpError(socket, status, message) {
  socket.write(`HTTP/1.1 ${status} ${message}\r\nConnection: close\r\n\r\n`)
  socket.destroy()
}

function logAgent(event, details = {}) {
  console.log(
    `[agent-ws] ${event} ${JSON.stringify({
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

function readBearerToken(header) {
  const normalized = String(header || '')

  if (!normalized.startsWith('Bearer ')) {
    return ''
  }

  return normalized.slice(7).trim()
}

function sendAgentError(socket, error) {
  safeSend(socket, {
    type: 'AGENT_ERROR',
    ok: false,
    code: error.code || 'AGENT_WS_ERROR',
    message: error.message || 'agent websocket error',
    ts: Date.now(),
  })
}

export function attachAgentWsServer(server) {
  const wss = new WebSocketServer({ noServer: true })

  wss.on('connection', (socket, request) => {
    socket.cleanScoutAgentRemoteAddress = request.socket?.remoteAddress || ''
    socket.cleanScoutAgentAuthToken = readBearerToken(request.headers.authorization)

    logAgent('connection-open', {
      remoteAddress: socket.cleanScoutAgentRemoteAddress,
    })

    socket.on('message', (data) => {
      const payload = safeJsonParse(data)

      if (!payload || typeof payload !== 'object') {
        sendAgentError(socket, {
          code: 'AGENT_INVALID_JSON',
          message: 'message must be JSON',
        })
        return
      }

      try {
        if (payload.type === 'AGENT_REGISTER') {
          const agent = agentRegistry.register(socket, {
            ...payload,
            token: payload.token || socket.cleanScoutAgentAuthToken,
          })

          logAgent('register-accepted', {
            deviceId: agent.deviceId,
            agentId: agent.agentId,
            agentType: agent.agentType,
          })

          safeSend(socket, {
            type: 'AGENT_REGISTER_ACK',
            ok: true,
            deviceId: agent.deviceId,
            agentId: agent.agentId,
            agentType: agent.agentType,
            ts: Date.now(),
          })
          return
        }

        if (payload.type === 'AGENT_HEARTBEAT') {
          const agent = agentRegistry.heartbeat(socket, payload)

          safeSend(socket, {
            type: 'AGENT_HEARTBEAT_ACK',
            ok: true,
            deviceId: agent.deviceId,
            agentId: agent.agentId,
            ts: Date.now(),
          })
          return
        }

        if (payload.type === 'OPENCLAW_CHAT_RESULT') {
          const resolved = agentRegistry.resolveOpenClawChat(payload)

          if (!resolved) {
            logAgent('chat-result-orphan', {
              requestId: payload.requestId || '',
              agentId: agentRegistry.getBySocket(socket)?.agentId || '',
            })
          }
          return
        }

        sendAgentError(socket, {
          code: 'AGENT_UNSUPPORTED_MESSAGE',
          message: `unsupported agent message type: ${payload.type || 'missing'}`,
        })
      } catch (error) {
        logAgent('message-error', {
          code: error.code || 'AGENT_MESSAGE_FAILED',
          message: error.message || '',
        })
        sendAgentError(socket, error)
      }
    })

    socket.on('close', (code, reason) => {
      const agent = agentRegistry.getBySocket(socket)

      logAgent('connection-close', {
        code,
        reason: String(reason || ''),
        deviceId: agent?.deviceId || '',
        agentId: agent?.agentId || '',
      })
      agentRegistry.unregister(socket)
    })

    socket.on('error', (error) => {
      logAgent('socket-error', {
        message: error.message || '',
      })
    })
  })

  server.on('upgrade', (request, socket, head) => {
    const config = getAgentWsConfig()
    const pathname = new URL(request.url || '/', 'http://127.0.0.1').pathname

    if (pathname !== config.path) {
      return
    }

    if (!config.enabled) {
      logAgent('upgrade-rejected', {
        reason: 'disabled',
        path: pathname,
      })
      writeHttpError(socket, 503, 'Service Unavailable')
      return
    }

    logAgent('upgrade-accepted', {
      path: pathname,
      remoteAddress: request.socket?.remoteAddress || '',
    })

    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit('connection', ws, request)
    })
  })

  return wss
}
