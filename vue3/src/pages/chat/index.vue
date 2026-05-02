<template>
  <view class="chat-page">
    <view class="page-header">
      <text class="page-title">对话控制</text>
      <text class="page-subtitle">
        当前页面已按 OpenClaw 接入预留为流式消息界面，本轮后端协议仍保持一次性返回，前端先使用伪流式展示。
      </text>
      <view class="transport-row">
        <StatusBadge :value="transport.mode" />
        <StatusBadge :value="transport.status" />
        <StatusBadge :value="transport.apiMode" />
      </view>
      <view class="transport-banner" :class="{ warn: transport.fallback, error: transport.status === 'error' }">
        <text class="transport-label">{{ transportBannerText }}</text>
      </view>
    </view>

    <scroll-view
      class="chat-list"
      scroll-y
      :scroll-into-view="scrollAnchorId"
      scroll-with-animation
      :style="{ paddingBottom: composerSpacerHeight }"
    >
      <view
        v-for="message in messages"
        :key="message.id"
        class="message-row"
        :class="[message.kind]"
      >
        <view v-if="message.kind === 'system'" class="system-message">
          <text class="system-message-text">{{ message.displayText || message.content }}</text>
        </view>

        <view v-else class="bubble-shell" :class="message.kind">
          <view class="bubble-card" :class="message.kind">
            <text class="bubble-role">{{ message.kind === 'user' ? '你' : '系统助手' }}</text>
            <text class="bubble-text">{{ message.displayText || message.content }}</text>
            <text v-if="message.streaming" class="bubble-streaming">生成中…</text>
            <text class="bubble-time">{{ formatDate(message.createdAt) }}</text>
          </view>
        </view>
      </view>
      <view :id="scrollAnchorId" class="scroll-anchor"></view>
    </scroll-view>

    <view class="composer-spacer" :style="{ height: composerSpacerHeight }"></view>

    <view class="composer-card" :style="{ bottom: composerBottomOffset }">
      <view class="voice-meta-row">
        <view class="voice-meta-left">
          <StatusBadge :value="voiceBadgeValue" />
          <StatusBadge :value="asrBadgeValue" />
        </view>
        <text class="voice-meta-text">{{ voiceHintText }}</text>
      </view>

      <textarea
        v-model="draftText"
        class="composer-input"
        maxlength="240"
        placeholder="输入任务描述、自然语言控制意图，或先点语音录入后再确认发送"
      />

      <view class="composer-actions">
        <button
          class="composer-secondary-button"
          :disabled="!canUseVoiceAction"
          @tap="handleVoiceAction"
        >
          {{ voiceButtonText }}
        </button>
        <button
          class="composer-button"
          :loading="sending"
          :disabled="sending || voiceState === 'recording' || voiceState === 'transcribing'"
          @tap="handleSend"
        >
          发送消息
        </button>
      </view>
    </view>

    <!-- #ifdef H5 -->
    <H5TabBarFallback current="chat" />
    <!-- #endif -->
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { onHide, onShow, onUnload } from '@dcloudio/uni-app'
import H5TabBarFallback from '../../components/H5TabBarFallback.vue'
import StatusBadge from '../../components/StatusBadge.vue'
import { requestAsrStatus, uploadAsrRecording } from '../../api/asr.js'
import { useSpeechRecorder } from '../../composables/useSpeechRecorder.js'
import { useAppStore } from '../../stores/app.js'
import { useChatStore } from '../../stores/chat.js'
import { ensureLoggedIn } from '../../utils/auth-guard.js'
import { formatStatusText } from '../../utils/status-display.js'

const appStore = useAppStore()
const chatStore = useChatStore()
const { messages, draftText, sending, transport } = storeToRefs(chatStore)
const recorder = useSpeechRecorder()

const scrollAnchorId = ref(`chat-bottom-${Date.now()}`)
const isH5 = typeof window !== 'undefined'
const asrStatus = ref({
  enabled: false,
  provider: 'funasr',
  language: 'zh',
  status: 'disabled',
  message: '语音识别未启用',
  model: '',
})
const voiceState = ref('idle')

const composerBottomOffset = computed(() =>
  isH5 ? 'calc(136rpx + env(safe-area-inset-bottom))' : 'calc(20rpx + env(safe-area-inset-bottom))'
)
const composerSpacerHeight = computed(() => (isH5 ? '320rpx' : '280rpx'))

const transportBannerText = computed(() => {
  const modeText = formatStatusText(transport.value.mode, '未知链路')
  const statusText = formatStatusText(transport.value.status, '未知状态')

  if (transport.value.fallback) {
    return `当前回复已回退到${modeText}，链路状态为${statusText}。`
  }

  return transport.value.message || `当前链路为${modeText}，状态为${statusText}。`
})

const asrReady = computed(() => asrStatus.value.enabled && asrStatus.value.status === 'healthy')
const voiceBadgeValue = computed(() => voiceState.value)
const asrBadgeValue = computed(() => {
  if (!recorder.isSupported.value) {
    return 'disabled'
  }

  return asrStatus.value.status || 'disabled'
})

const voiceButtonText = computed(() => {
  if (voiceState.value === 'recording') {
    return '结束录音'
  }

  if (voiceState.value === 'transcribing') {
    return '识别中'
  }

  return '语音录入'
})

const canUseVoiceAction = computed(() => {
  if (voiceState.value === 'transcribing') {
    return false
  }

  if (voiceState.value === 'recording') {
    return true
  }

  return recorder.isSupported.value && asrReady.value && !sending.value
})

const voiceHintText = computed(() => {
  if (!recorder.isSupported.value) {
    return '当前平台不支持语音录入'
  }

  if (!asrReady.value) {
    return asrStatus.value.message || '语音识别服务未就绪'
  }

  if (voiceState.value === 'recording') {
    return `录音中，已录 ${formatDuration(recorder.durationMs.value)}`
  }

  if (voiceState.value === 'transcribing') {
    return '正在识别语音，请稍候…'
  }

  if (voiceState.value === 'error') {
    return recorder.errorMessage.value || '语音录入失败，请重试'
  }

  return '点击语音录入，识别结果会先回填输入框，再由你确认发送'
})

watch(
  () => messages.value.length,
  () => {
    scrollAnchorId.value = `chat-bottom-${Date.now()}`
  }
)

watch(
  () => recorder.status.value,
  (nextStatus) => {
    if (voiceState.value !== 'transcribing') {
      voiceState.value = nextStatus
    }
  }
)

onShow(async () => {
  const allowed = await ensureLoggedIn()

  if (!allowed) {
    return
  }

  appStore.setCurrentTab('chat')
  await Promise.allSettled([
    chatStore.loadHistory(),
    chatStore.syncTransportStatus(),
    refreshAsrStatus(),
  ])
})

onHide(() => {
  if (voiceState.value === 'recording') {
    recorder.cancelRecording()
    voiceState.value = 'idle'
  }
})

onUnload(() => {
  if (voiceState.value === 'recording') {
    recorder.cancelRecording()
  }
})

async function refreshAsrStatus() {
  try {
    asrStatus.value = await requestAsrStatus()
  } catch (error) {
    asrStatus.value = {
      enabled: false,
      provider: 'funasr',
      language: 'zh',
      status: 'error',
      message: error.message || '语音识别状态获取失败',
      model: '',
    }
  }
}

async function handleVoiceAction() {
  if (voiceState.value === 'recording') {
    await stopAndTranscribe()
    return
  }

  if (!recorder.isSupported.value) {
    uni.showToast({
      title: '当前平台不支持语音录入',
      icon: 'none',
    })
    return
  }

  if (!asrReady.value) {
    uni.showToast({
      title: asrStatus.value.message || '语音识别服务未就绪',
      icon: 'none',
    })
    return
  }

  try {
    await recorder.startRecording()
    voiceState.value = 'recording'
  } catch (error) {
    voiceState.value = 'error'
    uni.showToast({
      title: error.message || '录音启动失败',
      icon: 'none',
    })
  }
}

async function stopAndTranscribe() {
  try {
    const recording = await recorder.stopRecording()
    voiceState.value = 'transcribing'

    const result = await uploadAsrRecording({
      tempFilePath: recording.tempFilePath,
      file: recording.file,
      fileName: recording.fileName,
      lang: 'zh',
    })

    const recognizedText = String(result.text || '').trim()

    if (!recognizedText) {
      throw new Error('语音识别未返回有效文本')
    }

    const nextDraft = String(draftText.value || '').trim()
      ? `${draftText.value}\n${recognizedText}`
      : recognizedText

    chatStore.setDraftText(nextDraft)
    chatStore.appendSystemMessage('语音识别结果已回填输入框，请确认后发送。', 'asr-filled')
    voiceState.value = 'idle'

    uni.showToast({
      title: '识别结果已回填',
      icon: 'success',
    })
  } catch (error) {
    voiceState.value = 'error'
    uni.showToast({
      title: error.message || '语音识别失败',
      icon: 'none',
    })
  }
}

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

function formatDate(value) {
  if (!value) {
    return '--'
  }

  return String(value).replace('T', ' ').slice(11, 19)
}

function formatDuration(value) {
  const totalSeconds = Math.max(0, Math.floor(Number(value || 0) / 1000))
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0')
  const seconds = String(totalSeconds % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
}
</script>

<style>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 28rpx;
  box-sizing: border-box;
  overflow: hidden;
  background:
    radial-gradient(circle at top right, rgba(70, 150, 180, 0.16), transparent 34%),
    linear-gradient(180deg, #eef3f9 0%, #e5edf4 100%);
}

.page-header {
  padding: 28rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #17324d, #205375 62%, #4e8ca5);
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

.transport-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 18rpx;
}

.transport-banner {
  margin-top: 18rpx;
  padding: 18rpx 20rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.14);
}

.transport-banner.warn {
  background: rgba(248, 234, 209, 0.22);
}

.transport-banner.error {
  background: rgba(244, 216, 210, 0.22);
}

.transport-label {
  font-size: 24rpx;
  line-height: 1.6;
  color: #ffffff;
}

.chat-list {
  flex: 1;
  min-height: 0;
  margin-top: 22rpx;
  padding-top: 8rpx;
  box-sizing: border-box;
}

.message-row + .message-row {
  margin-top: 14rpx;
}

.bubble-shell {
  display: flex;
}

.bubble-shell.user {
  justify-content: flex-end;
}

.bubble-shell.assistant {
  justify-content: flex-start;
}

.bubble-card {
  max-width: 78%;
  padding: 20rpx 22rpx;
  border-radius: 24rpx;
  box-shadow: 0 12rpx 34rpx rgba(20, 32, 51, 0.08);
}

.bubble-card.user {
  border-bottom-right-radius: 10rpx;
  background: #d9eef2;
}

.bubble-card.assistant {
  border-bottom-left-radius: 10rpx;
  background: rgba(255, 255, 255, 0.96);
}

.bubble-role {
  display: block;
  font-size: 22rpx;
  font-weight: 700;
  color: #205375;
}

.bubble-text {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  line-height: 1.7;
  color: #17324d;
  white-space: pre-wrap;
  word-break: break-word;
}

.bubble-streaming {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #9a6510;
}

.bubble-time {
  display: block;
  margin-top: 12rpx;
  font-size: 20rpx;
  color: #6a7b8b;
}

.system-message {
  display: flex;
  justify-content: center;
}

.system-message-text {
  max-width: 80%;
  padding: 8rpx 18rpx;
  font-size: 22rpx;
  line-height: 1.7;
  text-align: center;
  color: #6a7b8b;
}

.scroll-anchor {
  height: 2rpx;
}

.composer-spacer {
  flex: 0 0 auto;
}

.composer-card {
  position: fixed;
  left: 28rpx;
  right: 28rpx;
  padding: 18rpx 22rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 12rpx 34rpx rgba(20, 32, 51, 0.08);
  box-sizing: border-box;
  z-index: 40;
}

.voice-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.voice-meta-left {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}

.voice-meta-text {
  flex: 1;
  font-size: 22rpx;
  line-height: 1.6;
  color: #6a7b8b;
  text-align: right;
}

.composer-input {
  width: 100%;
  height: 84rpx;
  min-height: 84rpx;
  margin-top: 12rpx;
  padding: 8rpx 0;
  font-size: 28rpx;
  line-height: 1.6;
  color: #17324d;
}

.composer-actions {
  display: flex;
  gap: 14rpx;
  margin-top: 12rpx;
}

.composer-secondary-button,
.composer-button {
  flex: 1;
  border-radius: 999rpx;
}

.composer-secondary-button {
  background: #d9eef2;
  color: #205375;
}

.composer-button {
  background: #205375;
  color: #ffffff;
}

.composer-secondary-button[disabled],
.composer-button[disabled] {
  opacity: 0.58;
}

.composer-secondary-button::after,
.composer-button::after {
  border: none;
}
</style>
