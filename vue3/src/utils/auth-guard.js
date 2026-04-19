import { useAuthStore } from '../stores/auth.js'

const LOGIN_PAGE_URL = '/pages/auth/login'
const HOME_PAGE_URL = '/pages/index/index'
const CHAT_PAGE_URL = '/pages/chat/index'
const PROFILE_PAGE_URL = '/pages/profile/index'
const TAB_BAR_PAGES = new Set([HOME_PAGE_URL, CHAT_PAGE_URL, PROFILE_PAGE_URL])

function jump(url) {
  if (TAB_BAR_PAGES.has(url)) {
    uni.switchTab({ url })
    return
  }

  uni.reLaunch({ url })
}

export async function ensureLoggedIn({ redirect = true } = {}) {
  const authStore = useAuthStore()
  const restored = await authStore.restoreSession()

  if (restored && authStore.isLoggedIn) {
    return true
  }

  if (redirect) {
    uni.showToast({
      title: '请先登录',
      icon: 'none',
    })

    setTimeout(() => {
      jump(LOGIN_PAGE_URL)
    }, 120)
  }

  return false
}

export async function ensureAdmin() {
  const isLoggedIn = await ensureLoggedIn()

  if (!isLoggedIn) {
    return false
  }

  const authStore = useAuthStore()

  if (authStore.role === 'admin') {
    return true
  }

  uni.showToast({
    title: '当前账号没有管理员权限',
    icon: 'none',
  })

  setTimeout(() => {
    jump(HOME_PAGE_URL)
  }, 120)

  return false
}

export async function redirectIfLoggedIn() {
  const authStore = useAuthStore()
  const restored = await authStore.restoreSession()

  if (restored && authStore.isLoggedIn) {
    jump(HOME_PAGE_URL)
    return true
  }

  return false
}

export function switchToHomeTab() {
  jump(HOME_PAGE_URL)
}
