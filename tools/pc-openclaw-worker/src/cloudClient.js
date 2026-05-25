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

function sendJson(socket, payload) {
  if (socket.readyState !== WebSocket.OPEN) {
    return false
  }

  socket.send(JSON.stringify(payload))
  return true
}

function buildCapabilities() {
  return ['openclaw.chat', 'openclaw.status', 'openclaw.models']
}

function toErrorPayload(error) {
  return {
    code: error.code || 'OPENCLAW_REQUEST_FAILED',
    message: error.message || 'OpenClaw request failed',
  }
}

export function createCloudClient(config, openclawClient) {
  let socket = null
  let heartbeatTimer = null
  let reconnectTimer = null
  let lastProbe = {
    reachable: false,
  }

  function clearTimers() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }

    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  async function refreshProbe() {
    lastProbe = await openclawClient.probe()
    return lastProbe
  }

  async function sendRegister() {
    const probe = await refreshProbe()

    sendJson(socket, {
      type: 'AGENT_REGISTER',
      token: config.cloudAgentToken,
      agentType: config.agentType,
      deviceId: config.deviceId,
      agentId: config.agentId,
      capabilities: buildCapabilities(),
      version: '0.1.0',
      openclawReachable: probe.reachable,
      gatewayBaseUrl: config.openclawBaseUrl,
      model: config.openclawModel,
      ts: nowTs(),
    })
  }

  async function sendHeartbeat() {
    const probe = await refreshProbe()

    sendJson(socket, {
      type: 'AGENT_HEARTBEAT',
      agentId: config.agentId,
      deviceId: config.deviceId,
      openclawReachable: probe.reachable,
      gatewayBaseUrl: config.openclawBaseUrl,
      model: config.openclawModel,
      ts: nowTs(),
    })
  }

  async function handleChatRequest(payload) {
    const startedAt = Date.now()

    try {
      const result = await openclawClient.chat({
        messages: Array.isArray(payload.messages) ? payload.messages : [],
      })

      sendJson(socket, {
        type: 'OPENCLAW_CHAT_RESULT',
        requestId: payload.requestId,
        conversationId: payload.conversationId,
        ok: true,
        reply: result.reply,
        raw: result.raw,
        model: result.raw?.model || config.openclawModel,
        openclawReachable: true,
        latencyMs: Date.now() - startedAt,
      })
    } catch (error) {
      sendJson(socket, {
        type: 'OPENCLAW_CHAT_RESULT',
        requestId: payload.requestId,
        conversationId: payload.conversationId,
        ok: false,
        error: toErrorPayload(error),
        model: config.openclawModel,
        openclawReachable: false,
        latencyMs: Date.now() - startedAt,
      })
    }
  }

  function scheduleReconnect() {
    clearTimers()
    reconnectTimer = setTimeout(() => {
      connect()
    }, config.reconnectDelayMs)
  }

  function handleMessage(data) {
    const payload = safeJsonParse(data)

    if (!payload || typeof payload !== 'object') {
      return
    }

    if (payload.type === 'AGENT_REGISTER_ACK') {
      console.log(`[pc-openclaw-worker] registered device=${payload.deviceId} agent=${payload.agentId}`)
      return
    }

    if (payload.type === 'AGENT_ERROR') {
      console.warn(`[pc-openclaw-worker] agent error ${payload.code || ''}: ${payload.message || ''}`)
      return
    }

    if (payload.type === 'OPENCLAW_CHAT_REQUEST') {
      handleChatRequest(payload).catch((error) => {
        console.warn(`[pc-openclaw-worker] chat request failed: ${error.message || error}`)
      })
    }
  }

  function connect() {
    clearTimers()

    socket = new WebSocket(config.cloudWsUrl, {
      headers: config.cloudAgentToken
        ? {
            Authorization: `Bearer ${config.cloudAgentToken}`,
          }
        : {},
    })

    socket.on('open', () => {
      console.log(`[pc-openclaw-worker] connected ${config.cloudWsUrl}`)
      sendRegister().catch((error) => {
        console.warn(`[pc-openclaw-worker] register failed: ${error.message || error}`)
      })
      heartbeatTimer = setInterval(() => {
        sendHeartbeat().catch((error) => {
          console.warn(`[pc-openclaw-worker] heartbeat failed: ${error.message || error}`)
        })
      }, config.heartbeatIntervalMs)
    })

    socket.on('message', handleMessage)

    socket.on('close', (code, reason) => {
      console.warn(`[pc-openclaw-worker] disconnected code=${code} reason=${String(reason || '')}`)
      scheduleReconnect()
    })

    socket.on('error', (error) => {
      console.warn(`[pc-openclaw-worker] socket error: ${error.message || error}`)
    })
  }

  return {
    connect,
    getLastProbe() {
      return lastProbe
    },
  }
}
