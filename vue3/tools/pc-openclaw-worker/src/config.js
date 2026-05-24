import 'dotenv/config'

function readString(name, fallback = '') {
  const value = String(process.env[name] || '').trim()
  return value || fallback
}

function readPositiveInt(name, fallback) {
  const parsed = Number(process.env[name])
  return Number.isFinite(parsed) && parsed > 0 ? Math.round(parsed) : fallback
}

export function getConfig() {
  return {
    deviceId: readString('DEVICE_ID', 'cleanscout-001'),
    agentId: readString('AGENT_ID', 'pc-yusu-main'),
    agentType: readString('AGENT_TYPE', 'pc-openclaw-worker'),
    cloudWsUrl: readString('CLOUD_WS_URL', 'wss://api.hzhhds.top/ws/agents'),
    cloudAgentToken: readString('CLOUD_AGENT_TOKEN'),
    openclawBaseUrl: readString('OPENCLAW_BASE_URL', 'http://127.0.0.1:18789').replace(/\/+$/, ''),
    openclawGatewayToken: readString('OPENCLAW_GATEWAY_TOKEN'),
    openclawModel: readString('OPENCLAW_MODEL', 'openclaw/default'),
    openclawApiMode: readString('OPENCLAW_API_MODE', 'chat'),
    heartbeatIntervalMs: readPositiveInt('HEARTBEAT_INTERVAL_MS', 10000),
    requestTimeoutMs: readPositiveInt('REQUEST_TIMEOUT_MS', 60000),
    reconnectDelayMs: readPositiveInt('RECONNECT_DELAY_MS', 3000),
  }
}
