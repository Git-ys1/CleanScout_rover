<template>
  <view class="profile-page v-page">
    <view class="profile-card">
      <view class="avatar-block">{{ (userInfo?.username || 'U').slice(0, 1).toUpperCase() }}</view>
      <view class="profile-copy">
        <text class="profile-kicker">账户</text>
        <text class="profile-title">{{ userInfo?.username || '未登录' }}</text>
        <StatusBadge :value="authStore.role || 'user'" />
      </view>
    </view>

    <view class="summary-grid">
      <view class="summary-card v-card">
        <text class="summary-value">{{ isLoggedIn ? '已登录' : '未登录' }}</text>
        <text class="summary-label">登录状态</text>
      </view>
      <view class="summary-card v-card">
        <text class="summary-value">{{ roleLabel }}</text>
        <text class="summary-label">当前权限</text>
      </view>
      <view class="summary-card v-card">
        <text class="summary-value">云端 API</text>
        <text class="summary-label">后端入口</text>
      </view>
      <view class="summary-card v-card">
        <text class="summary-value">边缘中继</text>
        <text class="summary-label">设备链路</text>
      </view>
    </view>

    <view v-if="authStore.role === 'admin'" class="admin-card v-pressable" @tap="goToAdminConsole">
      <view>
        <text class="admin-card-title">管理台</text>
        <text class="admin-card-desc">用户、系统开关与接入状态集中管理。</text>
      </view>
      <text class="admin-arrow">进入</text>
    </view>

    <button class="logout-button v-pressable" @tap="handleLogout">退出登录</button>

    <!-- #ifdef H5 -->
    <H5TabBarFallback current="profile" />
    <!-- #endif -->
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { onShow } from '@dcloudio/uni-app'
import { useAppStore } from '../../stores/app.js'
import { useAuthStore } from '../../stores/auth.js'
import { ensureLoggedIn } from '../../utils/auth-guard.js'
import H5TabBarFallback from '../../components/H5TabBarFallback.vue'
import StatusBadge from '../../components/StatusBadge.vue'

const appStore = useAppStore()
const authStore = useAuthStore()
const { userInfo, isLoggedIn } = storeToRefs(authStore)

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
})

async function handleLogout() {
  await authStore.logout()
  uni.showToast({
    title: '已退出登录',
    icon: 'success',
  })
  setTimeout(() => {
    uni.reLaunch({ url: '/pages/auth/login' })
  }, 160)
}

function goToAdminConsole() {
  uni.navigateTo({ url: '/pages/admin/index' })
}
</script>

<style>
.profile-page {
  min-height: 100vh;
  padding: 28rpx;
  box-sizing: border-box;
}

.profile-card {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 32rpx;
  border-radius: 36rpx;
  background:
    radial-gradient(circle at 96% 0%, rgba(213, 138, 58, 0.18), transparent 28%),
    linear-gradient(135deg, #17384a, #1f5263 64%, #5f98a4);
  box-shadow: var(--v-shadow-float);
}

.avatar-block {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 112rpx;
  height: 112rpx;
  border-radius: 34rpx;
  background: rgba(255, 255, 255, 0.92);
  color: var(--v-color-primary-deep);
  font-size: 48rpx;
  font-weight: 900;
}

.profile-copy {
  flex: 1;
  min-width: 0;
}

.profile-kicker {
  display: block;
  color: rgba(255, 255, 255, 0.7);
  font-size: 22rpx;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.profile-title {
  display: block;
  margin: 8rpx 0 12rpx;
  font-size: 42rpx;
  font-weight: 900;
  color: #ffffff;
}

.summary-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 18rpx;
  margin-top: 22rpx;
}

.summary-card {
  flex: 1 1 40%;
  min-width: 260rpx;
  padding: 26rpx;
  box-sizing: border-box;
}

.summary-value {
  display: block;
  font-size: 30rpx;
  font-weight: 900;
  color: var(--v-text-main);
}

.summary-label {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: var(--v-text-muted);
}

.admin-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  margin-top: 20rpx;
  padding: 30rpx;
  border-radius: 32rpx;
  background:
    radial-gradient(circle at 90% 12%, rgba(255, 255, 255, 0.18), transparent 26%),
    linear-gradient(135deg, var(--v-color-primary-deep), var(--v-color-primary) 68%, var(--v-color-accent));
  box-shadow: var(--v-shadow-card);
}

.admin-card-title {
  display: block;
  font-size: 34rpx;
  font-weight: 900;
  color: #ffffff;
}

.admin-card-desc {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.82);
}

.admin-arrow {
  flex: 0 0 auto;
  padding: 12rpx 22rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.92);
  color: var(--v-color-primary);
  font-size: 24rpx;
  font-weight: 900;
}

.logout-button {
  margin-top: 24rpx;
  border-radius: 999rpx;
  background: rgba(200, 93, 74, 0.14);
  color: var(--v-color-danger);
  font-weight: 800;
}

.logout-button::after {
  border: none;
}
</style>
