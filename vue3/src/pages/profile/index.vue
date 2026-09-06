<template>
  <view class="account-page">
    <view class="account-content">
      <view class="account-header">
        <view class="avatar">{{ (userInfo?.username || 'U').slice(0, 1).toUpperCase() }}</view>
        <view class="identity"><text class="username">{{ userInfo?.username || '未获取账号' }}</text><text class="muted">{{ roleLabel }}</text></view>
      </view>
      <view class="group">
        <view class="row"><text class="row-label">账号权限</text><text class="row-value">{{ authStore.role === 'admin' ? '可查看状态、控制移动与风机，并使用管理台' : '可查看设备状态，控制操作需管理员权限' }}</text></view>
        <button class="row connection-toggle" @tap="showConnection = !showConnection"><text class="row-label">连接信息</text><text class="row-value">查看接入方式 {{ showConnection ? '⌃' : '⌄' }}</text></button>
        <view v-if="showConnection" class="connection-details">
          <view class="row"><text class="row-label">服务入口</text><text class="row-value">应用后台服务（API）</text></view>
          <view class="row"><text class="row-label">接口地址</text><text class="row-value">{{ API_BASE_URL }}</text></view>
          <view class="row"><text class="row-label">设备接入方式</text><text class="row-value">{{ connectionMode }}</text></view>
          <text class="muted explanation">设备实际连接方式和在线状态请查看首页的“连接信息”。此处展示配置地址，不代表连接正常。</text>
        </view>
      </view>
      <view v-if="authStore.role === 'admin'" class="group">
        <button class="row" @tap="goToAdminConsole"><text>管理台</text><text class="row-value">用户与系统管理 ›</text></button>
      </view>
      <view class="group"><button class="logout" :disabled="loggingOut" :loading="loggingOut" @tap="handleLogout">退出登录</button></view>
    </view>
    <!-- #ifdef H5 -->
    <H5TabBarFallback current="profile" />
    <!-- #endif -->
  </view>
</template>
<script setup>
import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { onShow } from '@dcloudio/uni-app'
import { useAppStore } from '../../stores/app.js'
import { useAuthStore } from '../../stores/auth.js'
import { ensureLoggedIn } from '../../utils/auth-guard.js'
import H5TabBarFallback from '../../components/H5TabBarFallback.vue'
import { API_BASE_URL } from '../../api/config.js'
import { requestRosStatus } from '../../api/integrations.js'
const showConnection = ref(false)
const loggingOut = ref(false)
const connectionMode = ref('暂未获取')

const appStore = useAppStore()
const authStore = useAuthStore()
const { userInfo } = storeToRefs(authStore)

const roleLabel = computed(() => {
  if (authStore.role === 'admin') {
    return '管理员'
  }

  if (authStore.role === 'user') {
    return '普通用户'
  }

  return '未识别'
})

onShow(async () => {
  const allowed = await ensureLoggedIn()

  if (!allowed) {
    return
  }

  appStore.setCurrentTab('profile')
  await authStore.fetchMe()
  try {
    const status = await requestRosStatus()
    connectionMode.value = ({ 'edge-relay': '设备中继（边缘中继）', rosbridge: '机器人直连', mock: '演示链路' })[status.transport] || '状态未知'
  } catch { connectionMode.value = '暂未获取' }
})

async function handleLogout() {
  if (loggingOut.value) return
  const confirmed = await new Promise(resolve => uni.showModal({ title: '退出登录', content: '确定退出当前账号？', confirmText: '退出', cancelText: '取消', success: result => resolve(result.confirm), fail: () => resolve(false) }))
  if (!confirmed) return
  loggingOut.value = true
  try {
  await authStore.logout()
  uni.showToast({
    title: '已退出登录',
    icon: 'success',
  })
  setTimeout(() => {
    uni.reLaunch({ url: '/pages/auth/login' })
  }, 160)
  } catch (error) { uni.showToast({ title: error.message || '退出失败，请重试', icon: 'none' }) }
  finally { loggingOut.value = false }
}

function goToAdminConsole() {
  uni.navigateTo({ url: '/pages/admin/index' })
}
</script>
<style scoped>
.account-page { min-height: 100vh; padding: 16px 16px calc(80px + env(safe-area-inset-bottom)); box-sizing: border-box; background: #f5f5f5; color: #1f2329; font: 15px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; }
.account-content { max-width: 700px; margin: auto; }
.account-header { display: flex; align-items: center; gap: 16px; background: white; padding: 24px 20px; border-radius: 12px; }
.avatar { display: flex; justify-content: center; align-items: center; flex: 0 0 56px; height: 56px; border-radius: 12px; background: #e8f5ed; color: #07a35a; font-size: 26px; font-weight: 600; }
.identity { min-width: 0; }
.username { display: block; font-size: 20px; font-weight: 600; overflow-wrap: anywhere; }
.muted { display: block; font-size: 14px; color: #667085; }
.group { margin-top: 16px; padding: 0 18px; background: white; border-radius: 12px; }
.row { display: flex; align-items: center; justify-content: space-between; gap: 20px; min-height: 56px; padding: 14px 0; box-sizing: border-box; border-bottom: 1px solid #f0f1f2; }
.row:last-child { border-bottom: 0; }
.row-label { flex: 0 0 80px; }
.row-value { color: #667085; font-size: 14px; text-align: right; overflow-wrap: anywhere; min-width: 0; }
button { width: 100%; margin: 0; background: white; border-radius: 0; text-align: left; font: inherit; color: inherit; }
button::after { border: 0; }
.connection-details { padding-bottom: 16px; }
.explanation { margin-top: 8px; }
.logout { min-height: 52px; padding: 12px 0; text-align: center; color: #c43232; }
</style>
