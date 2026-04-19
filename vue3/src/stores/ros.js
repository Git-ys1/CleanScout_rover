import { defineStore } from 'pinia'
import { requestRosStatus } from '../api/integrations.js'
import { requestRosCmdVel, requestRosManualPreset, requestRosTelemetrySummary } from '../api/ros.js'

function getDefaultStatus() {
  return {
    enabled: false,
    transport: 'mock',
    connected: false,
    rosbridgeUrl: 'ws://127.0.0.1:9090',
    lastHeartbeatAt: '',
    lastError: '',
    edgeRelayConnected: false,
    edgeDeviceId: '',
    lastTelemetryAt: '',
    lastRelayError: '',
    cmdVelTopic: '/cmd_vel',
    odomTopic: '/odom',
    imuTopic: '/imu/data',
    scanTopic: '/scan',
  }
}

function getDefaultTelemetry() {
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

export const useRosStore = defineStore('ros', {
  state: () => ({
    status: getDefaultStatus(),
    telemetrySummary: getDefaultTelemetry(),
    lastCommandResult: null,
    loadingStates: {
      status: false,
      telemetry: false,
      command: false,
    },
  }),
  actions: {
    setStatus(status) {
      this.status = {
        ...getDefaultStatus(),
        ...(status || {}),
      }
    },
    setTelemetrySummary(summary) {
      this.telemetrySummary = {
        ...getDefaultTelemetry(),
        ...(summary || {}),
      }
    },
    async loadStatus() {
      this.loadingStates.status = true

      try {
        const status = await requestRosStatus()
        this.setStatus(status)
        return this.status
      } finally {
        this.loadingStates.status = false
      }
    },
    async loadTelemetrySummary() {
      this.loadingStates.telemetry = true

      try {
        const summary = await requestRosTelemetrySummary()
        this.setTelemetrySummary(summary)
        return this.telemetrySummary
      } finally {
        this.loadingStates.telemetry = false
      }
    },
    async sendCmdVel(payload) {
      this.loadingStates.command = true

      try {
        const result = await requestRosCmdVel(payload)
        this.lastCommandResult = result
        await Promise.allSettled([this.loadStatus(), this.loadTelemetrySummary()])
        return result
      } finally {
        this.loadingStates.command = false
      }
    },
    async sendManualPreset(payload) {
      this.loadingStates.command = true

      try {
        const result = await requestRosManualPreset(payload)
        this.lastCommandResult = result
        await Promise.allSettled([this.loadStatus(), this.loadTelemetrySummary()])
        return result
      } finally {
        this.loadingStates.command = false
      }
    },
    reset() {
      this.status = getDefaultStatus()
      this.telemetrySummary = getDefaultTelemetry()
      this.lastCommandResult = null
      this.loadingStates = {
        status: false,
        telemetry: false,
        command: false,
      }
    },
  },
})
