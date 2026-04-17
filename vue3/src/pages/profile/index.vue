<template>
  <view class="profile-page">
    <view class="profile-card">
      <text class="profile-title">个人中心</text>
      <text class="profile-subtitle">当前联调仅保留登录态、角色展示和退出登录。</text>
    </view>

    <view class="detail-card">
      <view class="detail-row">
        <text class="detail-label">用户名</text>
        <text class="detail-value">{{ userInfo?.username || '--' }}</text>
      </view>
      <view class="detail-row">
        <text class="detail-label">角色</text>
        <text class="detail-value">{{ roleLabel }}</text>
      </view>
      <view class="detail-row">
        <text class="detail-label">登录态</text>
        <text class="detail-value">{{ isLoggedIn ? '已登录' : '未登录' }}</text>
      </view>
      <view class="detail-row">
        <text class="detail-label">Token 摘要</text>
        <text class="detail-value token">{{ tokenPreview }}</text>
      </view>
    </view>

    <button class="logout-button" @tap="handleLogout">退出登录</button>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { onShow } from '@dcloudio/uni-app'
import { useAppStore } from '../../stores/app.js'
import { useAuthStore } from '../../stores/auth.js'
import { ensureLoggedIn } from '../../utils/auth-guard.js'

const appStore = useAppStore()
const authStore = useAuthStore()
const { userInfo, token, isLoggedIn } = storeToRefs(authStore)

const roleLabel = computed(() => {
  if (authStore.role === 'admin') {
    return '管理员'
  }

  if (authStore.role === 'user') {
    return '普通用户'
  }

  return '未识别'
})

const tokenPreview = computed(() => {
  if (!token.value) {
    return '--'
  }

  if (token.value.length <= 24) {
    return token.value
  }

  return `${token.value.slice(0, 24)}...`
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
</script>

<style>
.profile-page {
  min-height: 100vh;
  padding: 28rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #eef3f9 0%, #e7eef4 100%);
}

.profile-card,
.detail-card {
  padding: 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14rpx 38rpx rgba(20, 32, 51, 0.08);
}

.profile-card {
  background: linear-gradient(135deg, #17324d, #205375 64%, #5ca4a9);
}

.profile-title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  color: #ffffff;
}

.profile-subtitle {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.88);
}

.detail-card {
  margin-top: 20rpx;
}

.detail-row + .detail-row {
  margin-top: 18rpx;
  padding-top: 18rpx;
  border-top: 2rpx solid rgba(23, 50, 77, 0.06);
}

.detail-label {
  display: block;
  font-size: 22rpx;
  color: #6a7b8b;
}

.detail-value {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  line-height: 1.6;
  color: #17324d;
}

.detail-value.token {
  word-break: break-all;
}

.logout-button {
  margin-top: 24rpx;
  border-radius: 999rpx;
  background: #a53f2b;
  color: #ffffff;
}

.logout-button::after {
  border: none;
}
</style>
