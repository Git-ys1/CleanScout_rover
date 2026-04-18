function toNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function normalizeAxis(value) {
  return toNumber(value, 0)
}

function normalizeVector(input = {}) {
  return {
    x: normalizeAxis(input?.x),
    y: normalizeAxis(input?.y),
    z: normalizeAxis(input?.z),
  }
}

function normalizeHoldMs(value, fallback) {
  const parsed = Math.round(toNumber(value, fallback))
  return parsed >= 0 ? parsed : fallback
}

export function getDefaultHoldMs() {
  return normalizeHoldMs(process.env.ROS_CMD_DEFAULT_HOLD_MS, 400)
}

export function createZeroTwist() {
  return {
    linear: { x: 0, y: 0, z: 0 },
    angular: { x: 0, y: 0, z: 0 },
  }
}

export function normalizeManualControlCommand(input = {}, overrides = {}) {
  const fallbackHoldMs = getDefaultHoldMs()
  const command = {
    source: String(overrides.source || input?.source || 'admin').trim() || 'admin',
    linear: normalizeVector(overrides.linear || input?.linear),
    angular: normalizeVector(overrides.angular || input?.angular),
    holdMs: normalizeHoldMs(overrides.holdMs ?? input?.holdMs, fallbackHoldMs),
    metadata:
      overrides.metadata !== undefined
        ? { ...(overrides.metadata || {}) }
        : { ...(input?.metadata || {}) },
  }

  return command
}

export function buildStopCommand(source = 'ros', metadata = {}) {
  return normalizeManualControlCommand(
    {
      source,
      ...createZeroTwist(),
      holdMs: 0,
      metadata,
    },
    {}
  )
}

export function isZeroCommand(command) {
  const safeCommand = normalizeManualControlCommand(command)

  return (
    safeCommand.linear.x === 0 &&
    safeCommand.linear.y === 0 &&
    safeCommand.linear.z === 0 &&
    safeCommand.angular.x === 0 &&
    safeCommand.angular.y === 0 &&
    safeCommand.angular.z === 0
  )
}
