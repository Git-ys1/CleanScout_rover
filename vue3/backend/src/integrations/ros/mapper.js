import { createHttpError } from '../../utils/response.js'
import { normalizeManualControlCommand } from './dto.js'

function toPositiveNumber(value, fallback) {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

function getManualSpeedConfig() {
  return {
    linearSpeed: toPositiveNumber(process.env.ROS_MANUAL_LINEAR_SPEED, 0.5),
    strafeSpeed: toPositiveNumber(process.env.ROS_MANUAL_STRAFE_SPEED, 0.5),
    angularSpeed: toPositiveNumber(process.env.ROS_MANUAL_ANGULAR_SPEED, 0.8),
  }
}

export function getManualPresetValues() {
  const { linearSpeed, strafeSpeed, angularSpeed } = getManualSpeedConfig()

  return {
    forward: {
      linear: { x: linearSpeed, y: 0, z: 0 },
      angular: { x: 0, y: 0, z: 0 },
    },
    backward: {
      linear: { x: -linearSpeed, y: 0, z: 0 },
      angular: { x: 0, y: 0, z: 0 },
    },
    turn_left: {
      linear: { x: 0, y: 0, z: 0 },
      angular: { x: 0, y: 0, z: angularSpeed },
    },
    turn_right: {
      linear: { x: 0, y: 0, z: 0 },
      angular: { x: 0, y: 0, z: -angularSpeed },
    },
    strafe_left: {
      linear: { x: 0, y: strafeSpeed, z: 0 },
      angular: { x: 0, y: 0, z: 0 },
    },
    strafe_right: {
      linear: { x: 0, y: -strafeSpeed, z: 0 },
      angular: { x: 0, y: 0, z: 0 },
    },
    stop: {
      linear: { x: 0, y: 0, z: 0 },
      angular: { x: 0, y: 0, z: 0 },
    },
  }
}

export const MANUAL_PRESET_VALUES = getManualPresetValues()

export function mapManualPresetToCommand(preset, options = {}) {
  const normalizedPreset = String(preset || '').trim()
  const presetValues = getManualPresetValues()

  if (!normalizedPreset || !presetValues[normalizedPreset]) {
    throw createHttpError(400, '无效的 ROS 控制预设', 'ROS_PRESET_INVALID')
  }

  return normalizeManualControlCommand(
    {
      source: options.source || 'admin',
      ...presetValues[normalizedPreset],
      holdMs: options.holdMs,
      metadata: {
        preset: normalizedPreset,
      },
    },
    {}
  )
}
