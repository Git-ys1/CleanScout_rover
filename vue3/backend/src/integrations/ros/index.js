import { createHttpError } from '../../utils/response.js'
import { normalizeManualControlCommand } from './dto.js'
import { createEdgeRelayHub } from './edgeRelayHub.js'
import { mapManualPresetToCommand } from './mapper.js'
import { createRosbridgeClient } from './rosbridgeClient.js'
import { createRosStateCache } from './stateCache.js'
import { createEdgeRelayTransport, createMockTransport, createRosbridgeTransport } from './transport.js'

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
  if (normalized === 'rosbridge') {
    return 'rosbridge'
  }

  if (normalized === 'edge-relay') {
    return 'edge-relay'
  }

  return 'mock'
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
    fanEnableTopic: String(process.env.ROS_FAN_ENABLE_TOPIC || '/fans/enable').trim(),
    fanAPwmTopic: String(process.env.ROS_FAN_A_PWM_TOPIC || '/fan_a/pwm_percent').trim(),
    fanBPwmTopic: String(process.env.ROS_FAN_B_PWM_TOPIC || '/fan_b/pwm_percent').trim(),
    fanARpmTopic: String(process.env.ROS_FAN_A_RPM_TOPIC || '/fan_a/rpm').trim(),
    fanBRpmTopic: String(process.env.ROS_FAN_B_RPM_TOPIC || '/fan_b/rpm').trim(),
    fanLidStateTopic: String(process.env.ROS_FAN_LID_STATE_TOPIC || '/fan_lid/state').trim(),
    fanSummaryTopic: String(process.env.ROS_FAN_SUMMARY_TOPIC || '/fans/state_summary').trim(),
    repeatHz: toPositiveInteger(process.env.ROS_CMD_REPEAT_HZ, 10),
    defaultHoldMs: toPositiveInteger(process.env.ROS_CMD_DEFAULT_HOLD_MS, 400),
    reconnectDelayMs: toPositiveInteger(process.env.ROS_RECONNECT_DELAY_MS, 1000),
    edgeRelayEnabled: parseBoolean(process.env.EDGE_RELAY_ENABLED, false),
    edgeRelayPath: String(process.env.EDGE_RELAY_PATH || '/edge/ros').trim(),
    edgeDeviceAuthRequired: parseBoolean(process.env.EDGE_DEVICE_AUTH_REQUIRED, true),
    edgeHelloTimeoutMs: toPositiveInteger(process.env.EDGE_HELLO_TIMEOUT_MS, 5000),
    edgeHeartbeatTimeoutMs: toPositiveInteger(process.env.EDGE_HEARTBEAT_TIMEOUT_MS, 15000),
    edgeServerPingIntervalMs: toPositiveInteger(process.env.EDGE_SERVER_PING_INTERVAL_MS, 25000),
    edgeAllowedDeviceIds: String(process.env.EDGE_ALLOWED_DEVICE_IDS || '').trim(),
  }
}

const rosConfig = getRosRuntimeConfig()
const rosStateCache = createRosStateCache(rosConfig)
const rosbridgeClient = createRosbridgeClient(rosConfig, rosStateCache)
const edgeRelayHub = createEdgeRelayHub(rosConfig, rosStateCache)

const rosTransport =
  rosConfig.transport === 'rosbridge'
    ? createRosbridgeTransport(rosConfig, rosStateCache, rosbridgeClient)
    : rosConfig.transport === 'edge-relay'
      ? createEdgeRelayTransport(rosConfig, rosStateCache, edgeRelayHub)
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

export function attachRosEdgeRelayServer(server) {
  edgeRelayHub.attach(server)
}

export async function getRosTelemetrySummary() {
  ensureRosEnabled()
  return rosTransport.getTelemetrySummary()
}

function normalizeFanEnabledInput(input) {
  if (input?.enabled === undefined) {
    throw createHttpError(400, '风机总开关字段 enabled 必填', 'ROS_FAN_ENABLE_REQUIRED')
  }

  return {
    enabled: Boolean(input.enabled),
  }
}

function normalizeFanPwmInput(input) {
  const fanA = Number(input?.fanA)
  const fanB = Number(input?.fanB)

  if (!Number.isFinite(fanA) || !Number.isFinite(fanB)) {
    throw createHttpError(400, '风机 PWM 需要同时提供 fanA 和 fanB 数值', 'ROS_FAN_PWM_INVALID')
  }

  if (fanA < 0 || fanA > 100 || fanB < 0 || fanB > 100) {
    throw createHttpError(400, '风机 PWM 范围必须在 0 到 100 之间', 'ROS_FAN_PWM_RANGE_INVALID')
  }

  return {
    fanA,
    fanB,
  }
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

export async function getRosFanState() {
  ensureRosEnabled()
  return rosTransport.getFanState()
}

export async function sendRosFanEnable(input) {
  ensureRosEnabled()
  return rosTransport.sendFanEnable(normalizeFanEnabledInput(input))
}

export async function sendRosFanPwm(input) {
  ensureRosEnabled()
  return rosTransport.sendFanPwm(normalizeFanPwmInput(input))
}
