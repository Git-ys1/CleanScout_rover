<template>
  <view class="chat-page">
    <view class="page-header">
      <text class="page-title">对话控制</text>
      <text class="page-subtitle">
        当前 transport：{{ transport.mode }} / 状态：{{ transport.status }} / API：{{ transport.apiMode }}
      </text>
      <view class="transport-banner" :class="[transport.mode, transport.status]">
        <text class="transport-label">
          {{ transport.fallback ? '当前不是实车链路，OpenClaw 已回退到 mock。' : transport.message }}
        </text>
      </view>
    </view>

    <scroll-view class="chat-list" scroll-y>
      <view class="message-card" v-for="message in messages" :key="message.id" :class="message.role">
        <text class="message-role">{{ message.role }}</text>
        <text class="message-text">{{ message.content }}</text>
        <text class="message-time">{{ message.createdAt }}</text>
      </view>
    </scroll-view>

    <view class="composer-card">
      <textarea
        v-model="draftText"
        class="composer-input"
        maxlength="240"
        placeholder="输入任务描述或调试消息"
      />
      <button class="composer-button" :loading="sending" @tap="handleSend">发送消息</button>
    </view>
  </view>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { onShow } from '@dcloudio/uni-app'
import { useAppStore } from '../../stores/app.js'
import { useChatStore } from '../../stores/chat.js'
import { ensureLoggedIn } from '../../utils/auth-guard.js'

const appStore = useAppStore()
const chatStore = useChatStore()
const { messages, draftText, sending, transport } = storeToRefs(chatStore)

onShow(async () => {
  const allowed = await ensureLoggedIn()

  if (!allowed) {
    return
  }

  appStore.setCurrentTab('chat')
  await Promise.allSettled([
    chatStore.loadHistory(),
    chatStore.syncTransportStatus(),
  ])
})

async function handleSend() {
  try {
    await chatStore.sendMessage()
  } catch (error) {
    uni.showToast({
      title: error.message || '发送失败',
      icon: 'none',
    })
  }
}
</script>

<style>
.chat-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding: 28rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #eef3f9 0%, #e3ebf2 100%);
}

.page-header {
  padding: 28rpx;
  border-radius: 24rpx;
  background: #17324d;
  box-shadow: 0 16rpx 44rpx rgba(23, 50, 77, 0.12);
}

.page-title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  color: #ffffff;
}

.page-subtitle {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.84);
}

.transport-banner {
  margin-top: 18rpx;
  padding: 18rpx 20rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.12);
}

.transport-banner.mock {
  background: rgba(255, 255, 255, 0.14);
}

.transport-banner.openclaw.healthy {
  background: rgba(93, 173, 122, 0.18);
}

.transport-label {
  font-size: 24rpx;
  line-height: 1.6;
  color: #ffffff;
}

.chat-list {
  flex: 1;
  min-height: 720rpx;
  margin-top: 24rpx;
  padding: 8rpx 0;
}

.message-card {
  margin-bottom: 18rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 12rpx 34rpx rgba(20, 32, 51, 0.08);
}

.message-card.user {
  background: #d9eef2;
}

.message-card.assistant {
  background: #ffffff;
}

.message-role {
  display: block;
  font-size: 22rpx;
  font-weight: 600;
  text-transform: uppercase;
  color: #205375;
}

.message-text {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  line-height: 1.6;
  color: #17324d;
}

.message-time {
  display: block;
  margin-top: 12rpx;
  font-size: 22rpx;
  color: #6a7b8b;
}

.composer-card {
  margin-top: 16rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 12rpx 34rpx rgba(20, 32, 51, 0.08);
}

.composer-input {
  width: 100%;
  min-height: 180rpx;
  padding: 16rpx 0;
  font-size: 28rpx;
  color: #17324d;
}

.composer-button {
  margin-top: 12rpx;
  border-radius: 999rpx;
  background: #205375;
  color: #ffffff;
}

.composer-button::after {
  border: none;
}
</style>
