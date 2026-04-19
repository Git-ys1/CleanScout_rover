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

    <view v-if="authStore.role === 'admin'" class="admin-card">
      <text class="admin-card-title">管理员入口</text>
      <text class="admin-card-desc">
        当前账号具备管理员权限。管理台已从一级导航移出，请从这里进入用户管理、系统开关和接入状态工作台。
      </text>
      <button class="admin-entry-button" @tap="goToAdminConsole">进入管理台</button>
    </view>

    <button class="logout-button" @tap="handleLogout">退出登录</button>

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

function goToAdminConsole() {
  uni.navigateTo({ url: '/pages/admin/index' })
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

.admin-card {
  margin-top: 20rpx;
  padding: 28rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #6f1d1b, #a53f2b 68%, #d17f54);
  box-shadow: 0 14rpx 38rpx rgba(20, 32, 51, 0.08);
}

.admin-card-title {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  color: #ffffff;
}

.admin-card-desc {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.88);
}

.admin-entry-button {
  margin-top: 18rpx;
  border-radius: 999rpx;
  background: #ffffff;
  color: #8b2f20;
}

.admin-entry-button::after {
  border: none;
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
