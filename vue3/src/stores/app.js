import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    appReady: false,
    currentTab: 'index',
    loading: false,
    networkStatus: 'online',
  }),
  actions: {
    markAppReady() {
      this.appReady = true
    },
    setCurrentTab(tab) {
      this.currentTab = tab
    },
    setLoading(loading) {
      this.loading = Boolean(loading)
    },
    setNetworkStatus(status) {
      this.networkStatus = status
    },
  },
})
