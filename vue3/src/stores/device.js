import { defineStore } from 'pinia'
import { requestAdminCommand } from '../api/admin.js'
import { requestDeviceSummary } from '../api/device.js'

export const useDeviceStore = defineStore('device', {
  state: () => ({
    deviceOnline: false,
    deviceSummary: null,
    lastTelemetry: null,
    adminConsoleResult: null,
  }),
  actions: {
    async fetchSummary() {
      const summary = await requestDeviceSummary()
      this.deviceSummary = summary
      this.deviceOnline = Boolean(summary?.online)
      this.lastTelemetry = summary
      return summary
    },
    async runAdminCommand(command) {
      const result = await requestAdminCommand(command)
      this.adminConsoleResult = result
      return result
    },
    clearAdminConsoleResult() {
      this.adminConsoleResult = null
    },
  },
})
