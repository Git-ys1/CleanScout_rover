import { randomUUID } from 'node:crypto'
import WebSocket from 'ws'

function parseBoolean(value) {
  return String(value || '').trim().toLowerCase() === 'true'
}

function parsePositiveInt(value, fallback) {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? Math.round(parsed) : fallback
}

function nowIso() {
  return new Date().toISOString()
}

function isOpen(socket) {
  return socket && socket.readyState === WebSocket.OPEN
}

function normalizeString(value, fallback = '') {
  const normalized = String(value || '').trim()
  return normalized || fallback
}

function normalizeDeviceId(value) {
  return normalizeString(value, 'cleanscout-001')
}

function createAgentError(code, message, status = 503) {
  const error = new Error(message)
  error.code = code
  error.status = status
  return error
}

function getAgentRuntimeConfig() {
  return {
    enabled: parseBoolean(process.env.AGENT_WS_ENABLED),
    sharedSecret: normalizeString(process.env.AGENT_SHARED_SECRET),
    chatTimeoutMs: parsePositiveInt(process.env.OPENCLAW_CHAT_TIMEOUT_MS, 60000),
    heartbeatTimeoutMs: parsePositiveInt(process.env.AGENT_HEARTBEAT_TIMEOUT_MS, 30000),
  }
}

function safeSend(socket, payload) {
  if (!isOpen(socket)) {
    return false
  }

  socket.send(JSON.stringify(payload))
  return true
}

class AgentRegistry {
  constructor() {
    this.agents = new Map()
    this.pendingRequests = new Map()
  }

  makeKey(deviceId, agentType, agentId) {
    return `${deviceId}::${agentType}::${agentId}`
  }

  validateToken(payload) {
    const { sharedSecret } = getAgentRuntimeConfig()

    if (!sharedSecret) {
      return true
    }

    return normalizeString(payload?.token) === sharedSecret
  }

  register(socket, payload) {
    const deviceId = normalizeDeviceId(payload?.deviceId)
    const agentType = normalizeString(payload?.agentType)
    const agentId = normalizeString(payload?.agentId)

    if (!agentType || !agentId) {
      throw createAgentError('AGENT_REGISTER_INVALID', 'agentType and agentId are required', 400)
    }

    if (!this.validateToken(payload)) {
      throw createAgentError('AGENT_AUTH_FAILED', 'agent token is invalid', 401)
    }

    const key = this.makeKey(deviceId, agentType, agentId)
    const existing = this.agents.get(key)

    if (existing && existing.socket !== socket && isOpen(existing.socket)) {
      existing.socket.close(4000, 'AGENT_REPLACED')
    }

    const registeredAt = nowIso()
    const agent = {
      key,
      socket,
      deviceId,
      agentId,
      agentType,
      version: normalizeString(payload?.version, '0.1.0'),
      capabilities: Array.isArray(payload?.capabilities) ? payload.capabilities : [],
      lastHeartbeatAt: registeredAt,
      registeredAt,
      openclawReachable: Boolean(payload?.openclawReachable),
      gatewayBaseUrl: normalizeString(payload?.gatewayBaseUrl),
      model: normalizeString(payload?.model, 'openclaw/default'),
      pendingRequests: new Set(),
    }

    socket.cleanScoutAgentKey = key
    this.agents.set(key, agent)

    return agent
  }

  heartbeat(socket, payload) {
    const agent = this.getBySocket(socket)

    if (!agent) {
      throw createAgentError('AGENT_NOT_REGISTERED', 'agent must register before heartbeat', 400)
    }

    const heartbeatDate = payload?.ts ? new Date(Number(payload.ts)) : null
    agent.lastHeartbeatAt = heartbeatDate && !Number.isNaN(heartbeatDate.getTime())
      ? heartbeatDate.toISOString()
      : nowIso()

    if (payload?.openclawReachable !== undefined) {
      agent.openclawReachable = Boolean(payload.openclawReachable)
    }

    if (payload?.gatewayBaseUrl) {
      agent.gatewayBaseUrl = normalizeString(payload.gatewayBaseUrl)
    }

    if (payload?.model) {
      agent.model = normalizeString(payload.model, agent.model)
    }

    return agent
  }

  unregister(socket) {
    const key = socket.cleanScoutAgentKey

    if (!key) {
      return
    }

    const agent = this.agents.get(key)

    if (agent?.socket === socket) {
      for (const requestId of agent.pendingRequests) {
        const pending = this.pendingRequests.get(requestId)

        if (pending) {
          clearTimeout(pending.timer)
          pending.reject(createAgentError('AGENT_DISCONNECTED', 'pc-openclaw-worker disconnected'))
          this.pendingRequests.delete(requestId)
        }
      }

      this.agents.delete(key)
    }
  }

  getBySocket(socket) {
    const key = socket.cleanScoutAgentKey
    return key ? this.agents.get(key) : null
  }

  isAgentOnline(agent) {
    if (!agent || !isOpen(agent.socket)) {
      return false
    }

    const { heartbeatTimeoutMs } = getAgentRuntimeConfig()
    const lastHeartbeat = new Date(agent.lastHeartbeatAt).getTime()

    return Number.isFinite(lastHeartbeat) && Date.now() - lastHeartbeat <= heartbeatTimeoutMs
  }

  findOpenClawAgent(deviceId) {
    const targetDeviceId = normalizeDeviceId(deviceId)

    for (const agent of this.agents.values()) {
      if (
        agent.deviceId === targetDeviceId &&
        agent.agentType === 'pc-openclaw-worker' &&
        this.isAgentOnline(agent)
      ) {
        return agent
      }
    }

    return null
  }

  getOpenClawStatus(deviceId) {
    const targetDeviceId = normalizeDeviceId(deviceId)
    const agent = this.findOpenClawAgent(targetDeviceId)

    return {
      ok: true,
      deviceId: targetDeviceId,
      pcWorkerOnline: Boolean(agent),
      openclawReachable: Boolean(agent?.openclawReachable),
      gatewayBaseUrl: agent?.gatewayBaseUrl || '',
      model: agent?.model || 'openclaw/default',
      agentId: agent?.agentId || '',
      agentType: agent?.agentType || 'pc-openclaw-worker',
      capabilities: agent?.capabilities || [],
      lastHeartbeatAt: agent?.lastHeartbeatAt || '',
      pendingRequests: agent?.pendingRequests?.size || 0,
    }
  }

  sendOpenClawChat({ deviceId, conversationId, messages, userId, timeoutMs, requestId: providedRequestId }) {
    const agent = this.findOpenClawAgent(deviceId)

    if (!agent) {
      throw createAgentError('PC_OPENCLAW_WORKER_OFFLINE', 'pc-openclaw-worker 当前不在线')
    }

    const requestId = normalizeString(providedRequestId, randomUUID())
    const startedAt = Date.now()
    const requestTimeoutMs = parsePositiveInt(timeoutMs, getAgentRuntimeConfig().chatTimeoutMs)

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        agent.pendingRequests.delete(requestId)
        this.pendingRequests.delete(requestId)
        reject(createAgentError('OPENCLAW_WORKER_TIMEOUT', 'pc-openclaw-worker 响应超时', 504))
      }, requestTimeoutMs)

      this.pendingRequests.set(requestId, {
        requestId,
        agentKey: agent.key,
        startedAt,
        timer,
        resolve,
        reject,
      })
      agent.pendingRequests.add(requestId)

      const sent = safeSend(agent.socket, {
        type: 'OPENCLAW_CHAT_REQUEST',
        requestId,
        conversationId,
        deviceId: agent.deviceId,
        userId,
        messages,
      })

      if (!sent) {
        clearTimeout(timer)
        agent.pendingRequests.delete(requestId)
        this.pendingRequests.delete(requestId)
        reject(createAgentError('AGENT_SOCKET_CLOSED', 'pc-openclaw-worker socket is closed'))
      }
    })
  }

  resolveOpenClawChat(payload) {
    const requestId = normalizeString(payload?.requestId)
    const pending = this.pendingRequests.get(requestId)

    if (!pending) {
      return false
    }

    clearTimeout(pending.timer)
    this.pendingRequests.delete(requestId)

    const agent = this.agents.get(pending.agentKey)

    if (agent) {
      agent.pendingRequests.delete(requestId)
      if (payload?.openclawReachable !== undefined) {
        agent.openclawReachable = Boolean(payload.openclawReachable)
      }
      if (payload?.model) {
        agent.model = normalizeString(payload.model, agent.model)
      }
    }

    pending.resolve({
      ...payload,
      agent,
      latencyMs: Date.now() - pending.startedAt,
    })

    return true
  }
}

export const agentRegistry = new AgentRegistry()
