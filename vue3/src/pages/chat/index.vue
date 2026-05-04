<template>
  <view class="chat-page v-page">
    <view class="page-header v-card">
      <view class="header-main">
        <view>
          <text class="page-kicker">智能控制入口</text>
          <text class="page-title">对话</text>
        </view>
        <view class="transport-row">
          <StatusBadge :value="transport.mode" />
          <StatusBadge :value="transport.status" />
        </view>
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
      <view class="suggestion-row">
        <button
          v-for="item in suggestions"
          :key="item"
          class="suggestion-chip v-pressable"
          @tap="applySuggestion(item)"
        >
          {{ item }}
        </button>
      </view>

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
        placeholder="输入任务，或先语音识别后确认发送"
      />

      <view class="composer-actions">
        <button
          class="voice-button v-pressable"
          :disabled="!canUseVoiceAction"
          @tap="handleVoiceAction"
        >
          {{ voiceButtonText }}
        </button>
        <button
          class="composer-button v-pressable"
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
const suggestions = ['前进', '停止', '查看状态', '打开风机']

const composerBottomOffset = computed(() =>
  isH5 ? 'calc(136rpx + env(safe-area-inset-bottom))' : 'calc(20rpx + env(safe-area-inset-bottom))'
)
const composerSpacerHeight = computed(() => (isH5 ? '250rpx' : '220rpx'))

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

function applySuggestion(text) {
  chatStore.setDraftText(text)
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
  padding: 24rpx;
  box-sizing: border-box;
  overflow: hidden;
}

.page-header {
  padding: 24rpx;
}

.header-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.page-kicker {
  display: block;
  margin-bottom: 8rpx;
  color: var(--v-text-muted);
  font-size: 22rpx;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.page-title {
  display: block;
  color: var(--v-text-main);
  font-size: 42rpx;
  font-weight: 900;
}

.transport-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.transport-banner {
  margin-top: 16rpx;
  padding: 16rpx 18rpx;
  border-radius: 20rpx;
  background: rgba(31, 82, 99, 0.08);
}

.transport-banner.warn {
  background: rgba(213, 138, 58, 0.13);
}

.transport-banner.error {
  background: rgba(200, 93, 74, 0.13);
}

.transport-label {
  font-size: 22rpx;
  line-height: 1.6;
  color: var(--v-text-secondary);
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
  padding: 20rpx 24rpx;
  border-radius: 28rpx;
  box-shadow: var(--v-shadow-card);
}

.bubble-card.user {
  border-bottom-right-radius: 10rpx;
  background: linear-gradient(135deg, #dbecef, #cfe4e8);
}

.bubble-card.assistant {
  border-bottom-left-radius: 10rpx;
  background: rgba(255, 255, 255, 0.95);
}

.bubble-role {
  display: block;
  font-size: 22rpx;
  font-weight: 800;
  color: var(--v-color-primary);
}

.bubble-text {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  line-height: 1.7;
  color: var(--v-text-main);
  white-space: pre-wrap;
  word-break: break-word;
}

.bubble-streaming {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: var(--v-color-warning);
}

.bubble-time {
  display: block;
  margin-top: 12rpx;
  font-size: 20rpx;
  color: var(--v-text-muted);
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
  color: var(--v-text-muted);
}

.scroll-anchor {
  height: 2rpx;
}

.composer-spacer {
  flex: 0 0 auto;
}

.composer-card {
  position: fixed;
  left: 24rpx;
  right: 24rpx;
  padding: 16rpx 18rpx 18rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.72);
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: var(--v-shadow-float);
  backdrop-filter: blur(20rpx);
  box-sizing: border-box;
  z-index: 40;
}

.suggestion-row {
  display: flex;
  gap: 10rpx;
  overflow-x: auto;
  padding-bottom: 10rpx;
  white-space: nowrap;
}

.suggestion-chip {
  flex: 0 0 auto;
  min-height: 52rpx;
  padding: 0 22rpx;
  border-radius: 999rpx;
  background: rgba(31, 82, 99, 0.08);
  color: var(--v-color-primary);
  font-size: 22rpx;
  font-weight: 800;
}

.suggestion-chip::after {
  border: none;
}

.voice-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.voice-meta-left {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}

.voice-meta-text {
  flex: 1;
  font-size: 20rpx;
  line-height: 1.6;
  color: var(--v-text-muted);
  text-align: right;
}

.composer-input {
  width: 100%;
  height: 62rpx;
  min-height: 62rpx;
  margin-top: 8rpx;
  padding: 6rpx 0;
  font-size: 26rpx;
  line-height: 1.45;
  color: var(--v-text-main);
}

.composer-actions {
  display: flex;
  gap: 12rpx;
  margin-top: 10rpx;
}

.voice-button,
.composer-button {
  flex: 1;
  min-height: 68rpx;
  border-radius: 999rpx;
  font-size: 26rpx;
  font-weight: 800;
}

.voice-button {
  flex: 0.72;
  background: rgba(213, 138, 58, 0.14);
  color: var(--v-color-warning);
}

.composer-button {
  background: var(--v-color-primary);
  color: #ffffff;
}

.voice-button[disabled],
.composer-button[disabled] {
  opacity: 0.58;
}

.voice-button::after,
.composer-button::after {
  border: none;
}
</style>
