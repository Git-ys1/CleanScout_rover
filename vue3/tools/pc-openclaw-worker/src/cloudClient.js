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
  let registered = false
  let heartbeatCount = 0
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
    heartbeatCount += 1

    sendJson(socket, {
      type: 'AGENT_HEARTBEAT',
      agentId: config.agentId,
      deviceId: config.deviceId,
      openclawReachable: probe.reachable,
      gatewayBaseUrl: config.openclawBaseUrl,
      model: config.openclawModel,
      ts: nowTs(),
    })

    if (heartbeatCount === 1 || heartbeatCount % 6 === 0) {
      console.log(
        `[pc-openclaw-worker] heartbeat sent count=${heartbeatCount} openclawReachable=${probe.reachable} waitingFor=OPENCLAW_CHAT_REQUEST`
      )
    }
  }

  async function handleChatRequest(payload) {
    const startedAt = Date.now()
    console.log(
      `[pc-openclaw-worker] chat request received requestId=${payload.requestId || ''} conversationId=${payload.conversationId || ''}`
    )

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
      console.log(
        `[pc-openclaw-worker] chat result sent requestId=${payload.requestId || ''} ok=true latencyMs=${Date.now() - startedAt}`
      )
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
      console.warn(
        `[pc-openclaw-worker] chat result sent requestId=${payload.requestId || ''} ok=false code=${error.code || 'OPENCLAW_REQUEST_FAILED'} latencyMs=${Date.now() - startedAt}`
      )
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
      registered = true
      console.log(`[pc-openclaw-worker] registered device=${payload.deviceId} agent=${payload.agentId}`)
      console.log('[pc-openclaw-worker] token accepted; websocket session is authenticated and waiting for requests')
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
    registered = false
    heartbeatCount = 0

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
      console.warn(`[pc-openclaw-worker] disconnected registered=${registered} code=${code} reason=${String(reason || '')}`)
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
