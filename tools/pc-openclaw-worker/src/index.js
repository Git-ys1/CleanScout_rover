import { createCloudClient } from './cloudClient.js'
import { getConfig } from './config.js'
import { createOpenClawClient } from './openclawClient.js'

const config = getConfig()

if (!config.cloudAgentToken) {
  console.warn('[pc-openclaw-worker] CLOUD_AGENT_TOKEN is empty; backend must allow empty AGENT_SHARED_SECRET for this to work.')
}

if (!config.openclawGatewayToken) {
  console.warn('[pc-openclaw-worker] OPENCLAW_GATEWAY_TOKEN is empty; only unauthenticated OpenClaw Gateway can work.')
}

console.log(
  `[pc-openclaw-worker] starting device=${config.deviceId} agent=${config.agentId} cloud=${config.cloudWsUrl} gateway=${config.openclawBaseUrl}`
)

const openclawClient = createOpenClawClient(config)
const cloudClient = createCloudClient(config, openclawClient)

cloudClient.connect()
