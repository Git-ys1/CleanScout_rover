<template>
  <view v-if="showFallback" class="h5-tabbar-fallback">
    <view class="h5-tabbar-spacer"></view>
    <view class="h5-tabbar-shell">
      <view
        v-for="item in items"
        :key="item.key"
        class="h5-tabbar-item"
        :class="{ active: current === item.key }"
        @tap="switchTo(item.url)"
      >
        <image
          class="h5-tabbar-icon"
          :src="current === item.key ? item.selectedIcon : item.icon"
          mode="aspectFit"
        />
        <text class="h5-tabbar-label">{{ item.label }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

const props = defineProps({
  current: {
    type: String,
    required: true,
  },
})

const showFallback = ref(false)
let checkTimer = null

const items = [
  {
    key: 'index',
    label: '首页',
    url: '/pages/index/index',
    icon: '/static/tabbar/home.png',
    selectedIcon: '/static/tabbar/home-active.png',
  },
  {
    key: 'chat',
    label: '对话',
    url: '/pages/chat/index',
    icon: '/static/tabbar/chat.png',
    selectedIcon: '/static/tabbar/chat-active.png',
  },
  {
    key: 'profile',
    label: '我的',
    url: '/pages/profile/index',
    icon: '/static/tabbar/profile.png',
    selectedIcon: '/static/tabbar/profile-active.png',
  },
]

function hasVisibleNativeTabBar() {
  if (typeof document === 'undefined' || typeof window === 'undefined') {
    return false
  }

  const element = document.querySelector('uni-tabbar')

  if (!element) {
    return false
  }

  const style = window.getComputedStyle(element)
  const rect = element.getBoundingClientRect()

  return style.display !== 'none' && style.visibility !== 'hidden' && rect.height > 0
}

function syncVisibility() {
  clearTimeout(checkTimer)
  checkTimer = setTimeout(() => {
    showFallback.value = !hasVisibleNativeTabBar()
  }, 140)
}

function switchTo(url) {
  uni.switchTab({ url })
}

onMounted(() => {
  syncVisibility()

  if (typeof window !== 'undefined') {
    window.addEventListener('resize', syncVisibility)
  }
})

onShow(() => {
  syncVisibility()
})

onUnmounted(() => {
  clearTimeout(checkTimer)

  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', syncVisibility)
  }
})
</script>

<style>
.h5-tabbar-spacer {
  height: calc(132rpx + env(safe-area-inset-bottom));
}

.h5-tabbar-shell {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  display: flex;
  padding: 10rpx 18rpx calc(10rpx + env(safe-area-inset-bottom));
  border-top: 1rpx solid rgba(31, 82, 99, 0.08);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 -18rpx 48rpx rgba(24, 56, 72, 0.1);
  backdrop-filter: blur(22rpx);
}

.h5-tabbar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10rpx 0 8rpx;
  border-radius: 24rpx;
  transition: background 0.18s ease, transform 0.18s ease;
}

.h5-tabbar-item.active {
  background: rgba(31, 82, 99, 0.07);
}

.h5-tabbar-item:active {
  transform: scale(0.98);
}

.h5-tabbar-item.active .h5-tabbar-label {
  color: var(--v-color-primary, #1f5263);
}

.h5-tabbar-icon {
  width: 44rpx;
  height: 44rpx;
}

.h5-tabbar-label {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: var(--v-text-muted, #6c7f8f);
}
</style>
