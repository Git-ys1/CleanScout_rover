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
  }
}
