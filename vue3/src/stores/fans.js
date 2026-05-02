import { defineStore } from 'pinia'
import { requestFanEnable, requestFanPwm, requestFanState } from '../api/fans.js'

function getDefaultFanState() {
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

export const useFansStore = defineStore('fans', {
  state: () => ({
    state: getDefaultFanState(),
    lastCommandResult: null,
    loadingStates: {
      state: false,
      enable: false,
      pwm: false,
    },
  }),
  actions: {
    setState(payload) {
      this.state = {
        ...getDefaultFanState(),
        ...(payload || {}),
        fanA: {
          ...getDefaultFanState().fanA,
          ...(payload?.fanA || {}),
        },
        fanB: {
          ...getDefaultFanState().fanB,
          ...(payload?.fanB || {}),
        },
      }
    },
    async loadState() {
      this.loadingStates.state = true

      try {
        const state = await requestFanState()
        this.setState(state)
        return this.state
      } finally {
        this.loadingStates.state = false
      }
    },
    async setEnabled(enabled) {
      this.loadingStates.enable = true

      try {
        const result = await requestFanEnable({ enabled })
        this.lastCommandResult = result

        if (result?.state) {
          this.setState(result.state)
        } else {
          await this.loadState()
        }

        return result
      } finally {
        this.loadingStates.enable = false
      }
    },
    async setPwm({ fanA, fanB }) {
      this.loadingStates.pwm = true

      try {
        const result = await requestFanPwm({ fanA, fanB })
        this.lastCommandResult = result

        if (result?.state) {
          this.setState(result.state)
        } else {
          await this.loadState()
        }

        return result
      } finally {
        this.loadingStates.pwm = false
      }
    },
    reset() {
      this.state = getDefaultFanState()
      this.lastCommandResult = null
      this.loadingStates = {
        state: false,
        enable: false,
        pwm: false,
      }
    },
  },
})
