<template>
  <view class="admin-page">
    <view class="header-card">
      <text class="header-title">管理员控制台</text>
      <text class="header-desc">本页仅管理员可见，当前只联通 mock 指令接口。</text>
    </view>

    <view class="section-card">
      <text class="section-title">快捷命令</text>
      <view class="preset-row">
        <button class="preset-button" @tap="usePreset('START')">启动</button>
        <button class="preset-button" @tap="usePreset('STOP')">停止</button>
        <button class="preset-button" @tap="usePreset('RESET')">复位</button>
        <button class="preset-button" @tap="usePreset('TEST')">测试</button>
      </view>
    </view>

    <view class="section-card">
      <text class="section-title">命令输入</text>
      <textarea v-model="commandText" class="command-input" placeholder="输入管理员命令" />
      <button class="submit-button" :loading="submitting" @tap="submitCommand">发送命令</button>
    </view>

    <view class="section-card">
      <text class="section-title">执行结果</text>
      <view class="result-panel" v-if="adminConsoleResult">
        <text class="result-line">command: {{ adminConsoleResult.command }}</text>
        <text class="result-line">accepted: {{ adminConsoleResult.accepted }}</text>
        <text class="result-line">result: {{ adminConsoleResult.result }}</text>
        <text class="result-line">executedAt: {{ adminConsoleResult.executedAt }}</text>
      </view>
      <view class="result-panel empty" v-else>
        <text class="result-line">尚未发送管理员命令。</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { onShow } from '@dcloudio/uni-app'
import { useAppStore } from '../../stores/app.js'
import { useDeviceStore } from '../../stores/device.js'
import { ensureAdmin } from '../../utils/auth-guard.js'

const appStore = useAppStore()
const deviceStore = useDeviceStore()
const { adminConsoleResult } = storeToRefs(deviceStore)
const commandText = ref('')
const submitting = ref(false)

onShow(async () => {
  const allowed = await ensureAdmin()

  if (!allowed) {
    return
  }

  appStore.setCurrentTab('admin')
})

function usePreset(command) {
  commandText.value = command
}

async function submitCommand() {
  if (!commandText.value.trim()) {
    uni.showToast({
      title: '请输入管理员命令',
      icon: 'none',
    })
    return
  }

  submitting.value = true

  try {
    await deviceStore.runAdminCommand(commandText.value)
    uni.showToast({
      title: '命令已发送',
      icon: 'success',
    })
  } catch (error) {
    uni.showToast({
      title: error.message || '命令发送失败',
      icon: 'none',
    })
  } finally {
    submitting.value = false
  }
}
</script>

<style>
.admin-page {
  min-height: 100vh;
  padding: 28rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #eef3f9 0%, #e5edf4 100%);
}

.header-card,
.section-card {
  padding: 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14rpx 38rpx rgba(20, 32, 51, 0.08);
}

.header-card {
  background: linear-gradient(135deg, #6f1d1b, #a53f2b 68%, #d17f54);
}

.header-title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  color: #ffffff;
}

.header-desc {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.88);
}

.section-card {
  margin-top: 20rpx;
}

.section-title {
  display: block;
  margin-bottom: 16rpx;
  font-size: 30rpx;
  font-weight: 600;
  color: #17324d;
}

.preset-row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -8rpx;
}

.preset-button {
  width: calc(50% - 16rpx);
  margin: 0 8rpx 16rpx;
  border-radius: 999rpx;
  background: #f5d9c9;
  color: #6f1d1b;
}

.preset-button::after {
  border: none;
}

.command-input {
  width: 100%;
  min-height: 180rpx;
  padding: 18rpx 0;
  font-size: 28rpx;
  color: #17324d;
}

.submit-button {
  border-radius: 999rpx;
  background: #a53f2b;
  color: #ffffff;
}

.submit-button::after {
  border: none;
}

.result-panel {
  padding: 20rpx;
  border-radius: 20rpx;
  background: #f7fafc;
}

.result-panel.empty {
  background: #f3f6f9;
}

.result-line {
  display: block;
  font-size: 25rpx;
  line-height: 1.8;
  color: #2b3f51;
}

@media screen and (max-width: 720px) {
  .preset-button {
    width: calc(100% - 16rpx);
  }
}
</style>
