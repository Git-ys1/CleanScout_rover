import { defineStore } from 'pinia'
import {
  requestCurrentUser,
  requestLogin,
  requestLogout,
  requestRegister,
} from '../api/auth.js'
import { AUTH_TOKEN_STORAGE_KEY, AUTH_USER_STORAGE_KEY } from '../utils/constants.js'

function normalizeStoredUser(storedUser) {
  if (!storedUser) {
    return null
  }

  if (typeof storedUser === 'string') {
    try {
      return JSON.parse(storedUser)
    } catch (_error) {
      return null
    }
  }

  return storedUser
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: '',
    userInfo: null,
    role: '',
    isLoggedIn: false,
  }),
  actions: {
    syncStorage() {
      if (this.token) {
        uni.setStorageSync(AUTH_TOKEN_STORAGE_KEY, this.token)
      } else {
        uni.removeStorageSync(AUTH_TOKEN_STORAGE_KEY)
      }

      if (this.userInfo) {
        uni.setStorageSync(AUTH_USER_STORAGE_KEY, this.userInfo)
      } else {
        uni.removeStorageSync(AUTH_USER_STORAGE_KEY)
      }
    },
    applySession(token, userInfo) {
      this.token = token || ''
      this.userInfo = userInfo || null
      this.role = userInfo?.role || ''
      this.isLoggedIn = Boolean(this.token && this.userInfo)
      this.syncStorage()
    },
    setToken(token) {
      this.applySession(token, this.userInfo)
    },
    clearSession() {
      this.token = ''
      this.userInfo = null
      this.role = ''
      this.isLoggedIn = false
      this.syncStorage()
    },
    async login(payload) {
      const result = await requestLogin(payload)
      this.applySession(result.token, result.user)
      return result.user
    },
    async register(payload) {
      return requestRegister(payload)
    },
    async fetchMe() {
      const user = await requestCurrentUser()
      this.applySession(this.token, user)
      return user
    },
    async restoreSession() {
      const token = uni.getStorageSync(AUTH_TOKEN_STORAGE_KEY) || ''
      const userInfo = normalizeStoredUser(uni.getStorageSync(AUTH_USER_STORAGE_KEY))

      if (!token) {
        this.clearSession()
        return false
      }

      this.applySession(token, userInfo)

      try {
        await this.fetchMe()
        return true
      } catch (_error) {
        this.clearSession()
        return false
      }
    },
    async logout(shouldNotify = true) {
      try {
        if (shouldNotify && this.token) {
          await requestLogout()
        }
      } finally {
        this.clearSession()
      }
    },
  },
})
