function getBaseTelemetryState() {
  return {
    odomAvailable: false,
    imuAvailable: false,
    scanAvailable: false,
    lastOdomAt: '',
    lastImuAt: '',
    lastScanAt: '',
    latestLinearSpeed: 0,
    latestAngularSpeed: 0,
    latestPose2D: null,
  }
}

function getBaseFanState() {
  return {
    enabled: false,
    fanA: {
      pwm: 0,
      rpm: 0,
    },
    fanB: {
      pwm: 0,
      rpm: 0,
    },
    lidOpen: false,
    summary: '',
    lastUpdate: '',
  }
}

function normalizeIsoTime(value) {
  if (!value) {
    return new Date().toISOString()
  }

  const numericValue = Number(value)
  const date = Number.isFinite(numericValue) ? new Date(numericValue) : new Date(value)

  if (Number.isNaN(date.getTime())) {
    return new Date().toISOString()
  }

  return date.toISOString()
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function toBoolean(value, fallback = false) {
  if (value === undefined || value === null || value === '') {
    return fallback
  }

  if (typeof value === 'boolean') {
    return value
  }

  const normalized = String(value).trim().toLowerCase()

  if (['1', 'true', 'yes', 'on', 'open', 'enabled'].includes(normalized)) {
    return true
  }

  if (['0', 'false', 'no', 'off', 'closed', 'disabled'].includes(normalized)) {
    return false
  }

  return fallback
}

function getSummaryFlag(summary, key) {
  const matched = String(summary || '').match(new RegExp(`${key}=([^\\s]+)`, 'i'))
  return matched?.[1]
}

function getSummaryNumber(summary, key) {
  const matched = String(summary || '').match(new RegExp(`${key}=(-?\\d+(?:\\.\\d+)?)`, 'i'))
  return matched ? Number(matched[1]) : undefined
}

function getFanEntry(payload, primaryKey, secondaryKey) {
  if (payload?.[primaryKey] && typeof payload[primaryKey] === 'object') {
    return payload[primaryKey]
  }

  if (payload?.[secondaryKey] && typeof payload[secondaryKey] === 'object') {
    return payload[secondaryKey]
  }

  return {}
}

function extractFanPayload(payload = {}) {
  if (payload.fans && typeof payload.fans === 'object') {
    return payload.fans
  }

  if (payload.fanState && typeof payload.fanState === 'object') {
    return payload.fanState
  }

  if (payload.fanTelemetry && typeof payload.fanTelemetry === 'object') {
    return payload.fanTelemetry
  }

  const hasTopLevelFanFields =
    payload.fanA ||
    payload.fanB ||
    payload.fan_a ||
    payload.fan_b ||
    payload.fansEnabled !== undefined ||
    payload.enabled !== undefined ||
    payload.lidOpen !== undefined ||
    payload.summary !== undefined

  return hasTopLevelFanFields ? payload : null
}

export function createRosStateCache(config) {
  const state = {
    enabled: Boolean(config.enabled),
    transport: config.transport,
    connected: Boolean(config.enabled && config.transport === 'mock'),
    rosbridgeUrl: config.rosbridgeUrl,
    lastHeartbeatAt: config.enabled && config.transport === 'mock' ? new Date().toISOString() : '',
    lastError: '',
    edgeRelayConnected: false,
    edgeDeviceId: '',
    lastTelemetryAt: '',
    lastRelayError: '',
    cmdVelTopic: config.cmdVelTopic,
    odomTopic: config.odomTopic,
    imuTopic: config.imuTopic,
    scanTopic: config.scanTopic,
    ...getBaseTelemetryState(),
    fanState: getBaseFanState(),
  }

  function getStatusSnapshot() {
    return {
      enabled: state.enabled,
      transport: state.transport,
      connected: state.connected,
      rosbridgeUrl: state.rosbridgeUrl,
      lastHeartbeatAt: state.lastHeartbeatAt,
      lastError: state.lastError,
      edgeRelayConnected: state.edgeRelayConnected,
      edgeDeviceId: state.edgeDeviceId,
      lastTelemetryAt: state.lastTelemetryAt,
      lastRelayError: state.lastRelayError,
      cmdVelTopic: state.cmdVelTopic,
      odomTopic: state.odomTopic,
      imuTopic: state.imuTopic,
      scanTopic: state.scanTopic,
    }
  }

  function getTelemetrySummary() {
    return {
      odomAvailable: state.odomAvailable,
      imuAvailable: state.imuAvailable,
      scanAvailable: state.scanAvailable,
      lastOdomAt: state.lastOdomAt,
      lastImuAt: state.lastImuAt,
      lastScanAt: state.lastScanAt,
      latestLinearSpeed: state.latestLinearSpeed,
      latestAngularSpeed: state.latestAngularSpeed,
      latestPose2D: state.latestPose2D,
    }
  }

  function getFanState() {
    return {
      enabled: state.fanState.enabled,
      fanA: {
        pwm: state.fanState.fanA.pwm,
        rpm: state.fanState.fanA.rpm,
      },
      fanB: {
        pwm: state.fanState.fanB.pwm,
        rpm: state.fanState.fanB.rpm,
      },
      lidOpen: state.fanState.lidOpen,
      summary: state.fanState.summary,
      lastUpdate: state.fanState.lastUpdate,
    }
  }

  function markHeartbeat(at = new Date().toISOString()) {
    state.lastHeartbeatAt = at
  }

  function setConnected(connected) {
    state.connected = Boolean(connected)

    if (state.connected) {
      markHeartbeat()
      state.lastError = ''
    }
  }

  function setLastError(message) {
    state.lastError = String(message || '').trim()
  }

  function setRelayError(message) {
    state.lastRelayError = String(message || '').trim()
    state.lastError = state.lastRelayError
  }

  function setEdgeRelayConnected({ connected, deviceId = '', at = new Date().toISOString() } = {}) {
    state.edgeRelayConnected = Boolean(connected)
    state.edgeDeviceId = state.edgeRelayConnected ? String(deviceId || state.edgeDeviceId || '').trim() : ''
    state.connected = state.transport === 'edge-relay' ? state.edgeRelayConnected : state.connected

    if (state.edgeRelayConnected) {
      markHeartbeat(at)
      state.lastRelayError = ''
      state.lastError = ''
    }
  }

  function updateOdom(message = {}) {
    const timestamp = new Date().toISOString()
    const twist = message?.twist?.twist || message?.twist || {}
    const pose = message?.pose?.pose || message?.pose || {}
    const position = pose?.position || {}
    const orientation = pose?.orientation || {}

    state.odomAvailable = true
    state.lastOdomAt = timestamp
    state.latestLinearSpeed = Number(twist?.linear?.x || 0)
    state.latestAngularSpeed = Number(twist?.angular?.z || 0)
    state.latestPose2D = {
      x: Number(position?.x || 0),
      y: Number(position?.y || 0),
      yawHint: Number(orientation?.z || 0),
    }
    markHeartbeat(timestamp)
  }

  function updateImu(_message = {}) {
    const timestamp = new Date().toISOString()
    state.imuAvailable = true
    state.lastImuAt = timestamp
    markHeartbeat(timestamp)
  }

  function updateScan(_message = {}) {
    const timestamp = new Date().toISOString()
    state.scanAvailable = true
    state.lastScanAt = timestamp
    markHeartbeat(timestamp)
  }

  function updateFanEnable(enabled, at = new Date().toISOString()) {
    state.fanState.enabled = Boolean(enabled)
    state.fanState.lastUpdate = at

    if (!state.fanState.enabled) {
      state.fanState.fanA.pwm = 0
      state.fanState.fanB.pwm = 0
    }

    markHeartbeat(at)
  }

  function updateFanPwm({ fanA, fanB } = {}, at = new Date().toISOString()) {
    if (fanA !== undefined) {
      state.fanState.fanA.pwm = toNumber(fanA, state.fanState.fanA.pwm)
    }

    if (fanB !== undefined) {
      state.fanState.fanB.pwm = toNumber(fanB, state.fanState.fanB.pwm)
    }

    state.fanState.lastUpdate = at
    markHeartbeat(at)
  }

  function updateFanRpm(fanKey, rpm, at = new Date().toISOString()) {
    if (fanKey === 'fanA') {
      state.fanState.fanA.rpm = toNumber(rpm, state.fanState.fanA.rpm)
    }

    if (fanKey === 'fanB') {
      state.fanState.fanB.rpm = toNumber(rpm, state.fanState.fanB.rpm)
    }

    state.fanState.lastUpdate = at
    markHeartbeat(at)
  }

  function updateFanLidState(lidOpen, at = new Date().toISOString()) {
    state.fanState.lidOpen = Boolean(lidOpen)
    state.fanState.lastUpdate = at
    markHeartbeat(at)
  }

  function updateFanSummary(summary, at = new Date().toISOString()) {
    const text = String(summary || '').trim()
    state.fanState.summary = text

    const enabledFlag = getSummaryFlag(text, 'enabled')
    const lidFlag = getSummaryFlag(text, 'lid_open')
    const fanAPwm = getSummaryNumber(text, 'fan_a_pwm')
    const fanBPwm = getSummaryNumber(text, 'fan_b_pwm')
    const fanARpm = getSummaryNumber(text, 'fan_a_rpm')
    const fanBRpm = getSummaryNumber(text, 'fan_b_rpm')

    if (enabledFlag !== undefined) {
      state.fanState.enabled = toBoolean(enabledFlag, state.fanState.enabled)
    }

    if (lidFlag !== undefined) {
      state.fanState.lidOpen = toBoolean(lidFlag, state.fanState.lidOpen)
    }

    if (fanAPwm !== undefined) {
      state.fanState.fanA.pwm = fanAPwm
    }

    if (fanBPwm !== undefined) {
      state.fanState.fanB.pwm = fanBPwm
    }

    if (fanARpm !== undefined) {
      state.fanState.fanA.rpm = fanARpm
    }

    if (fanBRpm !== undefined) {
      state.fanState.fanB.rpm = fanBRpm
    }

    state.fanState.lastUpdate = at
    markHeartbeat(at)
  }

  function updateEdgeFanTelemetry(payload = {}, at = new Date().toISOString()) {
    const normalizedPayload = extractFanPayload(payload)

    if (!normalizedPayload) {
      return
    }

    const fanA = getFanEntry(normalizedPayload, 'fanA', 'fan_a')
    const fanB = getFanEntry(normalizedPayload, 'fanB', 'fan_b')

    if (normalizedPayload.enabled !== undefined || normalizedPayload.fansEnabled !== undefined) {
      updateFanEnable(normalizedPayload.enabled ?? normalizedPayload.fansEnabled, at)
    }

    if (
      fanA.pwm !== undefined ||
      fanA.pwmPercent !== undefined ||
      normalizedPayload.fanAPwm !== undefined ||
      normalizedPayload.fan_a_pwm !== undefined ||
      fanB.pwm !== undefined ||
      fanB.pwmPercent !== undefined ||
      normalizedPayload.fanBPwm !== undefined ||
      normalizedPayload.fan_b_pwm !== undefined
    ) {
      updateFanPwm(
        {
          fanA: fanA.pwm ?? fanA.pwmPercent ?? normalizedPayload.fanAPwm ?? normalizedPayload.fan_a_pwm,
          fanB: fanB.pwm ?? fanB.pwmPercent ?? normalizedPayload.fanBPwm ?? normalizedPayload.fan_b_pwm,
        },
        at
      )
    }

    if (fanA.rpm !== undefined || normalizedPayload.fanARpm !== undefined || normalizedPayload.fan_a_rpm !== undefined) {
      updateFanRpm('fanA', fanA.rpm ?? normalizedPayload.fanARpm ?? normalizedPayload.fan_a_rpm, at)
    }

    if (fanB.rpm !== undefined || normalizedPayload.fanBRpm !== undefined || normalizedPayload.fan_b_rpm !== undefined) {
      updateFanRpm('fanB', fanB.rpm ?? normalizedPayload.fanBRpm ?? normalizedPayload.fan_b_rpm, at)
    }

    if (normalizedPayload.lidOpen !== undefined || normalizedPayload.lid_open !== undefined) {
      updateFanLidState(normalizedPayload.lidOpen ?? normalizedPayload.lid_open, at)
    }

    if (normalizedPayload.summary !== undefined || normalizedPayload.stateSummary !== undefined) {
      updateFanSummary(normalizedPayload.summary ?? normalizedPayload.stateSummary, at)
    }

    state.fanState.lastUpdate = at
    markHeartbeat(at)
  }

  function updateEdgeTelemetry(payload = {}) {
    const timestamp = normalizeIsoTime(payload.ts)

    if (payload.odom) {
      updateOdom(payload.odom)
      state.lastOdomAt = timestamp
    }

    if (payload.imu) {
      updateImu(payload.imu)
      state.lastImuAt = timestamp
    }

    if (payload.scanSummary) {
      updateScan(payload.scanSummary)
      state.lastScanAt = timestamp
    }

    updateEdgeFanTelemetry(payload, timestamp)

    state.lastTelemetryAt = timestamp
    markHeartbeat(timestamp)
  }

  function applyCommand(command) {
    const timestamp = new Date().toISOString()
    state.latestLinearSpeed = Number(command?.linear?.x || 0)
    state.latestAngularSpeed = Number(command?.angular?.z || 0)
    state.lastOdomAt = timestamp
    state.latestPose2D = state.latestPose2D || {
      x: 0,
      y: 0,
      yawHint: 0,
    }
    markHeartbeat(timestamp)
  }

  return {
    getStatusSnapshot,
    getTelemetrySummary,
    getFanState,
    markHeartbeat,
    setConnected,
    setLastError,
    setRelayError,
    setEdgeRelayConnected,
    updateOdom,
    updateImu,
    updateScan,
    updateFanEnable,
    updateFanPwm,
    updateFanRpm,
    updateFanLidState,
    updateFanSummary,
    updateEdgeFanTelemetry,
    updateEdgeTelemetry,
    applyCommand,
  }
}
