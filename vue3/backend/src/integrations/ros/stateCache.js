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

export function createRosStateCache(config) {
  const state = {
    enabled: Boolean(config.enabled),
    transport: config.transport,
    connected: Boolean(config.enabled && config.transport === 'mock'),
    rosbridgeUrl: config.rosbridgeUrl,
    lastHeartbeatAt: config.enabled && config.transport === 'mock' ? new Date().toISOString() : '',
    lastError: '',
    cmdVelTopic: config.cmdVelTopic,
    odomTopic: config.odomTopic,
    imuTopic: config.imuTopic,
    scanTopic: config.scanTopic,
    ...getBaseTelemetryState(),
  }

  function getStatusSnapshot() {
    return {
      enabled: state.enabled,
      transport: state.transport,
      connected: state.connected,
      rosbridgeUrl: state.rosbridgeUrl,
      lastHeartbeatAt: state.lastHeartbeatAt,
      lastError: state.lastError,
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
    markHeartbeat,
    setConnected,
    setLastError,
    updateOdom,
    updateImu,
    updateScan,
    applyCommand,
  }
}
