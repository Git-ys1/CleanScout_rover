import { buildStopCommand, isZeroCommand } from './dto.js'

function clearTimers(timers) {
  if (timers.intervalId) {
    clearInterval(timers.intervalId)
    timers.intervalId = null
  }

  if (timers.stopTimeoutId) {
    clearTimeout(timers.stopTimeoutId)
    timers.stopTimeoutId = null
  }
}

function scheduleRepeatedCommand({ command, repeatHz, publishCommand, timers }) {
  clearTimers(timers)

  if (isZeroCommand(command) || command.holdMs <= 0) {
    return null
  }

  const intervalMs = Math.max(50, Math.round(1000 / repeatHz))
  const scheduledStopAt = new Date(Date.now() + command.holdMs).toISOString()

  timers.intervalId = setInterval(() => {
    publishCommand(command).catch(() => {})
  }, intervalMs)

  timers.stopTimeoutId = setTimeout(() => {
    clearTimers(timers)
    publishCommand(
      buildStopCommand(command.source, {
        reason: 'hold-expired',
      })
    ).catch(() => {})
  }, command.holdMs)

  return scheduledStopAt
}

function createBaseResult(command, transport, scheduledStopAt) {
  return {
    accepted: true,
    transport,
    command,
    scheduledStopAt,
  }
}

export function createMockTransport(config, cache) {
  const timers = {
    intervalId: null,
    stopTimeoutId: null,
  }

  async function publishCommand(command) {
    cache.setConnected(Boolean(config.enabled))
    cache.applyCommand(command)
  }

  return {
    async getStatus() {
      cache.setConnected(Boolean(config.enabled))
      return cache.getStatusSnapshot()
    },
    async getTelemetrySummary() {
      return cache.getTelemetrySummary()
    },
    async getFanState() {
      return cache.getFanState()
    },
    async sendCommand(command) {
      await publishCommand(command)
      const scheduledStopAt = scheduleRepeatedCommand({
        command,
        repeatHz: config.repeatHz,
        publishCommand,
        timers,
      })

      return createBaseResult(command, 'mock', scheduledStopAt)
    },
    async sendFanEnable({ enabled }) {
      cache.updateFanEnable(enabled)
      return {
        accepted: true,
        transport: 'mock',
        state: cache.getFanState(),
        command: {
          type: 'fan_enable',
          enabled: Boolean(enabled),
        },
      }
    },
    async sendFanPwm({ fanA, fanB }) {
      cache.updateFanPwm({ fanA, fanB })
      return {
        accepted: true,
        transport: 'mock',
        state: cache.getFanState(),
        command: {
          type: 'fan_pwm',
          fanA,
          fanB,
        },
      }
    },
  }
}

export function createRosbridgeTransport(config, cache, client) {
  const timers = {
    intervalId: null,
    stopTimeoutId: null,
  }

  async function publishCommand(command) {
    await client.publishCmdVel(command)
  }

  return {
    async getStatus() {
      try {
        await client.ensureConnected()
      } catch (_error) {
        cache.setConnected(false)
      }

      return cache.getStatusSnapshot()
    },
    async getTelemetrySummary() {
      return cache.getTelemetrySummary()
    },
    async getFanState() {
      return cache.getFanState()
    },
    async sendCommand(command) {
      await publishCommand(command)
      const scheduledStopAt = scheduleRepeatedCommand({
        command,
        repeatHz: config.repeatHz,
        publishCommand,
        timers,
      })

      return createBaseResult(command, 'rosbridge', scheduledStopAt)
    },
    async sendFanEnable({ enabled }) {
      await client.publishFanEnable(enabled)
      return {
        accepted: true,
        transport: 'rosbridge',
        state: cache.getFanState(),
        command: {
          type: 'fan_enable',
          enabled: Boolean(enabled),
        },
      }
    },
    async sendFanPwm({ fanA, fanB }) {
      await client.publishFanPwm({ fanA, fanB })
      return {
        accepted: true,
        transport: 'rosbridge',
        state: cache.getFanState(),
        command: {
          type: 'fan_pwm',
          fanA,
          fanB,
        },
      }
    },
  }
}

export function createEdgeRelayTransport(config, cache, hub) {
  const timers = {
    intervalId: null,
    stopTimeoutId: null,
  }

  async function publishCommand(command) {
    await hub.sendCommand(command)
  }

  return {
    async getStatus() {
      return hub.getStatus()
    },
    async getTelemetrySummary() {
      return cache.getTelemetrySummary()
    },
    async getFanState() {
      return cache.getFanState()
    },
    async sendCommand(command) {
      await publishCommand(command)
      const scheduledStopAt = scheduleRepeatedCommand({
        command,
        repeatHz: config.repeatHz,
        publishCommand,
        timers,
      })

      return createBaseResult(command, 'edge-relay', scheduledStopAt)
    },
    async sendFanEnable({ enabled }) {
      const result = await hub.sendFanEnable({ enabled })
      return {
        accepted: true,
        transport: 'edge-relay',
        state: cache.getFanState(),
        command: {
          type: 'fan_enable',
          enabled: Boolean(enabled),
          seq: result.seq,
        },
      }
    },
    async sendFanPwm({ fanA, fanB }) {
      const result = await hub.sendFanPwm({ fanA, fanB })
      return {
        accepted: true,
        transport: 'edge-relay',
        state: cache.getFanState(),
        command: {
          type: 'fan_pwm',
          fanA,
          fanB,
          seq: result.seq,
        },
      }
    },
  }
}
