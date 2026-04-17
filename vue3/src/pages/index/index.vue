<template>
  <view class="page-shell">
    <view class="hero-card">
      <text class="hero-eyebrow">V-1.1.0 / Dashboard Shell</text>
      <text class="hero-title">V线前端控制总览</text>
      <text class="hero-desc">
        当前轮只打通登录、角色、mock 摘要和占位控制链，不接真实树莓派或 openclaw。
      </text>
      <view class="identity-row">
        <view class="identity-chip">
          <text class="chip-label">当前用户</text>
          <text class="chip-value">{{ userInfo?.username || '未登录' }}</text>
        </view>
        <view class="identity-chip">
          <text class="chip-label">角色</text>
          <text class="chip-value">{{ roleLabel }}</text>
        </view>
      </view>
    </view>

    <view class="section">
      <text class="section-title">设备摘要</text>
      <view class="summary-grid">
        <view class="summary-card">
          <text class="summary-label">在线状态</text>
          <text class="summary-value">{{ deviceOnline ? '在线' : '离线' }}</text>
        </view>
        <view class="summary-card">
          <text class="summary-label">电量</text>
          <text class="summary-value">{{ deviceSummary?.battery ?? '--' }}%</text>
        </view>
        <view class="summary-card">
          <text class="summary-label">任务状态</text>
          <text class="summary-value">{{ deviceSummary?.taskStatus || '未加载' }}</text>
        </view>
        <view class="summary-card">
          <text class="summary-label">最近更新</text>
          <text class="summary-value compact">{{ deviceSummary?.lastUpdate || '等待后端返回' }}</text>
        </view>
      </view>
    </view>

    <view class="section">
      <text class="section-title">最近消息摘要</text>
      <view class="message-panel" v-if="recentMessages.length">
        <view class="message-row" v-for="message in recentMessages" :key="message.id">
          <text class="message-role">{{ message.role }}</text>
          <text class="message-content">{{ message.content }}</text>
        </view>
      </view>
      <view class="empty-panel" v-else>
        <text class="empty-text">暂无消息，进入对话页后可发起 mock 对话。</text>
      </view>
    </view>

    <view class="section">
      <text class="section-title">快速入口</text>
      <view class="action-grid">
        <button class="action-button primary" @tap="goToPage('/pages/chat/index')">进入对话控制</button>
        <button class="action-button" @tap="goToPage('/pages/profile/index')">进入个人中心</button>
        <button
          v-if="authStore.role === 'admin'"
          class="action-button warning"
          @tap="goToPage('/pages/admin/index')"
        >
          进入管理员页
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '../../stores/auth.js'
import { useAppStore } from '../../stores/app.js'
import { useChatStore } from '../../stores/chat.js'
import { useDeviceStore } from '../../stores/device.js'
import { ensureLoggedIn } from '../../utils/auth-guard.js'

const authStore = useAuthStore()
const appStore = useAppStore()
const chatStore = useChatStore()
const deviceStore = useDeviceStore()

const { userInfo } = storeToRefs(authStore)
const { messages } = storeToRefs(chatStore)
const { deviceOnline, deviceSummary } = storeToRefs(deviceStore)

const roleLabel = computed(() => {
  if (authStore.role === 'admin') {
    return '管理员'
  }

  if (authStore.role === 'user') {
    return '普通用户'
  }

  return '未识别'
})

const recentMessages = computed(() => messages.value.slice(-3).reverse())

onShow(async () => {
  const allowed = await ensureLoggedIn()

  if (!allowed) {
    return
  }

  appStore.markAppReady()
  appStore.setCurrentTab('index')

  await Promise.allSettled([
    authStore.fetchMe(),
    deviceStore.fetchSummary(),
    chatStore.loadHistory(),
  ])
})

function goToPage(url) {
  uni.navigateTo({ url })
}
</script>

<style>
.page-shell {
  min-height: 100vh;
  padding: 32rpx;
  box-sizing: border-box;
  background:
    radial-gradient(circle at top right, rgba(70, 150, 180, 0.16), transparent 36%),
    linear-gradient(180deg, #f4f8fb 0%, #e9eff5 100%);
}

.hero-card {
  padding: 36rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #11324d, #205375 62%, #48a6a7);
  box-shadow: 0 24rpx 56rpx rgba(17, 50, 77, 0.16);
}

.hero-eyebrow {
  font-size: 22rpx;
  letter-spacing: 3rpx;
  color: rgba(255, 255, 255, 0.72);
}

.hero-title {
  display: block;
  margin-top: 18rpx;
  font-size: 48rpx;
  font-weight: 700;
  color: #ffffff;
}

.hero-desc {
  display: block;
  margin-top: 18rpx;
  font-size: 26rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.9);
}

.identity-row {
  display: flex;
  flex-wrap: wrap;
  margin: 28rpx -8rpx 0;
}

.identity-chip {
  min-width: 220rpx;
  margin: 0 8rpx 12rpx;
  padding: 20rpx 24rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.12);
}

.chip-label {
  display: block;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.72);
}

.chip-value {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  font-weight: 600;
  color: #ffffff;
}

.section {
  margin-top: 28rpx;
}

.section-title {
  display: block;
  margin-bottom: 16rpx;
  font-size: 32rpx;
  font-weight: 600;
  color: #17324d;
}

.summary-grid,
.action-grid {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -8rpx;
}

.summary-card {
  width: calc(50% - 16rpx);
  margin: 0 8rpx 16rpx;
  padding: 26rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14rpx 38rpx rgba(20, 32, 51, 0.08);
  box-sizing: border-box;
}

.summary-label {
  display: block;
  font-size: 22rpx;
  color: #6a7b8b;
}

.summary-value {
  display: block;
  margin-top: 12rpx;
  font-size: 32rpx;
  font-weight: 600;
  color: #17324d;
}

.summary-value.compact {
  font-size: 24rpx;
  line-height: 1.5;
}

.message-panel,
.empty-panel {
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14rpx 38rpx rgba(20, 32, 51, 0.08);
}

.message-row + .message-row {
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 2rpx solid rgba(23, 50, 77, 0.06);
}

.message-role {
  display: block;
  font-size: 22rpx;
  font-weight: 600;
  text-transform: uppercase;
  color: #2a6171;
}

.message-content,
.empty-text {
  display: block;
  margin-top: 10rpx;
  font-size: 26rpx;
  line-height: 1.6;
  color: #2b3f51;
}

.action-button {
  width: calc(50% - 16rpx);
  margin: 0 8rpx 16rpx;
  border-radius: 999rpx;
  background: #ffffff;
  color: #17324d;
}

.action-button::after {
  border: none;
}

.action-button.primary {
  background: #205375;
  color: #ffffff;
}

.action-button.warning {
  background: #b8402a;
  color: #ffffff;
}

@media screen and (max-width: 720px) {
  .summary-card,
  .action-button {
    width: calc(100% - 16rpx);
  }
}
</style>
