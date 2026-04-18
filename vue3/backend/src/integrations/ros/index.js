import { createHttpError } from '../../utils/response.js'
import { normalizeManualControlCommand } from './dto.js'
import { mapManualPresetToCommand } from './mapper.js'
import { createRosbridgeClient } from './rosbridgeClient.js'
import { createRosStateCache } from './stateCache.js'
import { createMockTransport, createRosbridgeTransport } from './transport.js'

function parseBoolean(value, fallback = false) {
  if (value === undefined) {
    return fallback
  }

  return ['1', 'true', 'yes', 'on'].includes(String(value).trim().toLowerCase())
}

function toPositiveInteger(value, fallback) {
  const parsed = Math.round(Number(value))
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

function getTransportName(value) {
  const normalized = String(value || 'mock').trim().toLowerCase()
  return normalized === 'rosbridge' ? 'rosbridge' : 'mock'
}

export function getRosRuntimeConfig() {
  return {
    enabled: parseBoolean(process.env.ROS_ENABLED, true),
    transport: getTransportName(process.env.ROS_TRANSPORT),
    rosbridgeUrl: String(process.env.ROSBRIDGE_URL || 'ws://127.0.0.1:9090').trim(),
    cmdVelTopic: String(process.env.ROS_CMD_VEL_TOPIC || '/cmd_vel').trim(),
    odomTopic: String(process.env.ROS_ODOM_TOPIC || '/odom').trim(),
    imuTopic: String(process.env.ROS_IMU_TOPIC || '/imu/data').trim(),
    scanTopic: String(process.env.ROS_SCAN_TOPIC || '/scan').trim(),
    repeatHz: toPositiveInteger(process.env.ROS_CMD_REPEAT_HZ, 10),
    defaultHoldMs: toPositiveInteger(process.env.ROS_CMD_DEFAULT_HOLD_MS, 400),
    reconnectDelayMs: toPositiveInteger(process.env.ROS_RECONNECT_DELAY_MS, 1000),
  }
}

const rosConfig = getRosRuntimeConfig()
const rosStateCache = createRosStateCache(rosConfig)
const rosbridgeClient = createRosbridgeClient(rosConfig, rosStateCache)

const rosTransport =
  rosConfig.transport === 'rosbridge'
    ? createRosbridgeTransport(rosConfig, rosStateCache, rosbridgeClient)
    : createMockTransport(rosConfig, rosStateCache)

function ensureRosEnabled() {
  if (!rosConfig.enabled) {
    throw createHttpError(503, 'ROS adapter 当前未启用', 'ROS_DISABLED')
  }
}

export async function getRosStatus() {
  if (!rosConfig.enabled) {
    return {
      ...rosStateCache.getStatusSnapshot(),
      enabled: false,
      connected: false,
      lastError: 'ROS_ENABLED=false，backend 当前不接 ROS transport。',
    }
  }

  return rosTransport.getStatus()
}

export async function getRosTelemetrySummary() {
  ensureRosEnabled()
  return rosTransport.getTelemetrySummary()
}

export async function sendRosCmdVel(input, source = 'admin') {
  ensureRosEnabled()
  const command = normalizeManualControlCommand(input, {
    source,
    holdMs: input?.holdMs ?? rosConfig.defaultHoldMs,
    metadata: {
      ...(input?.metadata || {}),
    },
  })

  return rosTransport.sendCommand(command)
}

export async function sendRosManualPreset({ preset, holdMs }, source = 'admin') {
  ensureRosEnabled()
  const command = mapManualPresetToCommand(preset, {
    source,
    holdMs: holdMs ?? rosConfig.defaultHoldMs,
  })

  return rosTransport.sendCommand(command)
}
