import { createHttpError } from '../../utils/response.js'
import { normalizeManualControlCommand } from './dto.js'

export const MANUAL_PRESET_VALUES = {
  forward: {
    linear: { x: 0.08, y: 0, z: 0 },
    angular: { x: 0, y: 0, z: 0 },
  },
  backward: {
    linear: { x: -0.08, y: 0, z: 0 },
    angular: { x: 0, y: 0, z: 0 },
  },
  turn_left: {
    linear: { x: 0, y: 0, z: 0 },
    angular: { x: 0, y: 0, z: 0.2 },
  },
  turn_right: {
    linear: { x: 0, y: 0, z: 0 },
    angular: { x: 0, y: 0, z: -0.2 },
  },
  strafe_left: {
    linear: { x: 0, y: 0.08, z: 0 },
    angular: { x: 0, y: 0, z: 0 },
  },
  strafe_right: {
    linear: { x: 0, y: -0.08, z: 0 },
    angular: { x: 0, y: 0, z: 0 },
  },
  stop: {
    linear: { x: 0, y: 0, z: 0 },
    angular: { x: 0, y: 0, z: 0 },
  },
}

export function mapManualPresetToCommand(preset, options = {}) {
  const normalizedPreset = String(preset || '').trim()

  if (!normalizedPreset || !MANUAL_PRESET_VALUES[normalizedPreset]) {
    throw createHttpError(400, '无效的 ROS 控制预设', 'ROS_PRESET_INVALID')
  }

  return normalizeManualControlCommand(
    {
      source: options.source || 'admin',
      ...MANUAL_PRESET_VALUES[normalizedPreset],
      holdMs: options.holdMs,
      metadata: {
        preset: normalizedPreset,
      },
    },
    {}
  )
}
