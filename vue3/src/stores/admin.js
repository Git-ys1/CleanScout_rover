import { defineStore } from 'pinia'
import {
  requestAdminUsers,
  requestCreateAdminUser,
  requestDeleteAdminUser,
  requestSystemConfig,
  requestUpdateAdminUser,
  requestUpdateSystemConfig,
} from '../api/admin.js'
import { requestOpenClawStatus } from '../api/integrations.js'

function getDefaultOpenClawStatus() {
  return {
    status: 'disabled',
    activeTransport: 'mock',
    apiMode: 'chat',
    model: 'openclaw/default',
    lastProbeAt: '',
    message: 'OpenClaw backend adapter 尚未探测。',
  }
}

export const useAdminStore = defineStore('admin', {
  state: () => ({
    users: [],
    systemConfig: {
      registrationEnabled: true,
      appEnabled: true,
      maintenanceMessage: '',
      openclawEnabled: false,
    },
    openclawStatus: getDefaultOpenClawStatus(),
    activeSection: 'users',
    loadingStates: {
      users: false,
      systemConfig: false,
      submitUser: false,
      mutateUser: false,
      saveSystemConfig: false,
      openclawStatus: false,
    },
  }),
  actions: {
    setActiveSection(section) {
      this.activeSection = section
    },
    setOpenClawStatus(status) {
      this.openclawStatus = {
        ...getDefaultOpenClawStatus(),
        ...(status || {}),
      }
    },
    async loadOpenClawStatus() {
      this.loadingStates.openclawStatus = true

      try {
        const status = await requestOpenClawStatus()
        this.setOpenClawStatus(status)
        return this.openclawStatus
      } finally {
        this.loadingStates.openclawStatus = false
      }
    },
    async loadUsers() {
      this.loadingStates.users = true

      try {
        const users = await requestAdminUsers()
        this.users = Array.isArray(users) ? users : []
        return this.users
      } finally {
        this.loadingStates.users = false
      }
    },
    async createUser(payload) {
      this.loadingStates.submitUser = true

      try {
        const user = await requestCreateAdminUser(payload)
        await this.loadUsers()
        return user
      } finally {
        this.loadingStates.submitUser = false
      }
    },
    async updateUser(userId, payload) {
      this.loadingStates.mutateUser = true

      try {
        const user = await requestUpdateAdminUser(userId, payload)
        await this.loadUsers()
        return user
      } finally {
        this.loadingStates.mutateUser = false
      }
    },
    async deleteUser(userId) {
      this.loadingStates.mutateUser = true

      try {
        const result = await requestDeleteAdminUser(userId)
        await this.loadUsers()
        return result
      } finally {
        this.loadingStates.mutateUser = false
      }
    },
    async loadSystemConfig() {
      this.loadingStates.systemConfig = true

      try {
        const config = await requestSystemConfig()
        this.systemConfig = {
          registrationEnabled: Boolean(config?.registrationEnabled),
          appEnabled: Boolean(config?.appEnabled),
          maintenanceMessage: config?.maintenanceMessage || '',
          openclawEnabled: Boolean(config?.openclawEnabled),
        }
        return this.systemConfig
      } finally {
        this.loadingStates.systemConfig = false
      }
    },
    async saveSystemConfig(payload) {
      this.loadingStates.saveSystemConfig = true

      try {
        const config = await requestUpdateSystemConfig(payload)
        this.systemConfig = {
          registrationEnabled: Boolean(config?.registrationEnabled),
          appEnabled: Boolean(config?.appEnabled),
          maintenanceMessage: config?.maintenanceMessage || '',
          openclawEnabled: Boolean(config?.openclawEnabled),
        }
        await this.loadOpenClawStatus()
        return this.systemConfig
      } finally {
        this.loadingStates.saveSystemConfig = false
      }
    },
  },
})
