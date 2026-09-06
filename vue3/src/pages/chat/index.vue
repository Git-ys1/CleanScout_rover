<template>
  <view class="chat-page v-page">
    <view class="page-header v-card">
      <view class="header-main">
        <view>
          <text class="page-title">智能助手</text>
        </view>
        <view class="transport-row">
          <StatusBadge :value="transport.mode" />
          <StatusBadge :value="transport.status" />
          <button class="detail-toggle" @tap="showDetails = !showDetails">{{ showDetails ? '收起' : '详情' }}</button>
        </view>
      </view>
      <view v-if="showDetails || transport.status === 'error' || transport.fallback" class="transport-banner" :class="{ warn: transport.fallback, error: transport.status === 'error' }">
        <text class="transport-label">{{ transportBannerText }}</text>
      </view>
      <view v-if="showDetails && transport.mode === 'openclaw'" class="agent-meta">
        <text>设备：{{ transport.deviceId || 'cleanscout-001' }}</text>
        <text>Worker：{{ transport.agentId || 'pc-yusu-main' }}</text>
        <text>{{ transport.pcWorkerOnline ? 'Worker 在线' : 'Worker 离线' }}</text>
        <text>{{ streamingModeText }}</text>
        <text v-if="transport.pendingRequests">处理中：{{ transport.pendingRequests }}</text>
      </view>
      <view v-else-if="showDetails" class="agent-meta"><text v-if="transport.model">模型：{{ transport.model }}</text><text>{{ streamingModeText }}</text></view>
    </view>

    <scroll-view
      class="chat-list"
      scroll-y
      :scroll-into-view="scrollAnchorId"
      scroll-with-animation
    >
      <view v-if="!messages.length" class="empty-chat">发送文字或选择图片，开始对话</view>
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
            <image
              v-if="message.type === 'image' && message.imageUrl"
              class="bubble-image"
              :src="message.imageUrl"
              mode="widthFix"
              @tap="previewImage(message.imageUrl)"
            />
            <text class="bubble-text">{{ message.displayText || message.content }}</text>
            <text v-if="message.imageError" class="chat-error">{{ message.imageError }}</text>
            <text v-if="message.type === 'image'" class="bubble-image-name">{{ message.imageName || message.content }}</text>
            <text v-if="message.streaming" class="bubble-streaming">生成中…</text>
            <text class="bubble-time">{{ formatDate(message.createdAt) }}</text>
          </view>
        </view>
      </view>
      <view :id="scrollAnchorId" class="scroll-anchor"></view>
    </scroll-view>

    <view class="composer-card">
      <view v-if="showTools" class="suggestion-row">
        <button
          v-for="item in suggestions"
          :key="item"
          class="suggestion-chip v-pressable"
          :disabled="sending"
          @tap="applySuggestion(item)"
        >
          {{ item }}
        </button>
      </view>

      <view v-if="showTools || voiceState === 'recording' || voiceState === 'transcribing'" class="voice-meta-row">
        <view class="voice-meta-left">
          <StatusBadge :value="voiceBadgeValue" />
          <StatusBadge :value="asrBadgeValue" />
        </view>
        <text class="voice-meta-text">{{ voiceHintText }}</text>
      </view>

      <view v-if="pendingImage" class="pending-image-row">
        <image class="pending-image" :src="pendingImage" mode="aspectFit" @tap="previewImage(pendingImage)" />
        <button :disabled="sending" @tap="chatStore.setImage('')">移除图片</button>
      </view>
      <text v-if="sending" class="chat-notice">正在发送并等待回复，请勿重复点击…（最长约 150 秒）</text>
      <text v-if="errorText" class="chat-error" role="alert">{{ errorText }}</text>
      <view class="input-row">
      <button class="tool-toggle" :aria-label="showTools ? '收起工具' : '图片和语音工具'" @tap="showTools = !showTools">{{ showTools ? '−' : '+' }}</button>
      <textarea
        v-model="draftText"
        class="composer-input"
        maxlength="12000"
        :disabled="sending"
        placeholder="输入消息…"
      />
      <button class="composer-button" :loading="sending" :disabled="sending || voiceState === 'recording' || voiceState === 'transcribing'" @tap="handleSend">{{ errorText ? '重试' : '发送' }}</button>
      </view>
      <view v-if="showTools" class="composer-actions">
        <button
          class="image-button v-pressable"
          :disabled="sending || voiceState === 'recording' || voiceState === 'transcribing'"
          @tap="handleChooseImage"
        >
          选择图片
        </button>
        <button
          class="voice-button v-pressable"
          :disabled="!canUseVoiceAction"
          @tap="handleVoiceAction"
        >
          {{ voiceButtonText }}
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
const { messages, draftText, sending, transport, pendingImage, errorText } = storeToRefs(chatStore)
const recorder = useSpeechRecorder()

const scrollAnchorId = ref(`chat-bottom-${Date.now()}`)
const showDetails = ref(false)
const showTools = ref(false)
const asrStatus = ref({
  enabled: false,
  provider: 'funasr',
  language: 'zh',
  status: 'disabled',
  message: '语音识别未启用',
  model: '',
})
const voiceState = ref('idle')
const suggestions = computed(() => transport.value.mode === 'openclaw'
  ? ['前进', '停止', '查看状态', '打开风机']
  : ['描述这张图片', '有哪些值得注意的细节？', '请简要总结'])

const transportBannerText = computed(() => {
  const modeText = formatStatusText(transport.value.mode, '未知链路')
  const statusText = formatStatusText(transport.value.status, '未知状态')
  const heartbeatText = formatHeartbeatAge(transport.value.lastHeartbeatAgeMs)

  if (transport.value.fallback) {
    return `当前回复已回退到${modeText}，链路状态为${statusText}。${heartbeatText}`
  }

  const baseText = transport.value.message || `当前链路为${modeText}，状态为${statusText}。`

  return `${baseText}${heartbeatText}`
})

const streamingModeText = computed(() => {
  if (transport.value.realtimeStreaming) {
    return '真流式'
  }

  if (transport.value.displayStreaming === 'frontend-typewriter') {
    return '伪流式展示'
  }

  return '一次性回复'
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

function handleChooseImage() {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album'],
    async success(result) {
      try {
        chatStore.setImage(result.tempFilePaths?.[0])
        showTools.value = false
      } catch (error) {
        uni.showToast({
          title: error.message || '图片发送失败',
          icon: 'none',
        })
      }
    },
  })
}

function previewImage(url) {
  if (!url) {
    return
  }

  uni.previewImage({
    current: url,
    urls: [url],
  })
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

function formatHeartbeatAge(value) {
  if (value === null || value === undefined || value === '') {
    return ''
  }

  const seconds = Math.max(0, Math.round(Number(value || 0) / 1000))

  if (!Number.isFinite(seconds)) {
    return ''
  }

  return ` 最近心跳 ${seconds}s 前。`
}
</script>

<style scoped>
.pending-image-row { display: flex; align-items: center; gap: 20rpx; }
.pending-image { width: 130rpx; height: 130rpx; }
.chat-notice, .chat-error { display: block; font-size: 24rpx; margin-top: 8rpx; }
.chat-error { color: #ad342d; }
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

.agent-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 14rpx;
  color: var(--v-text-muted);
  font-size: 20rpx;
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

.bubble-image {
  display: block;
  width: 360rpx;
  max-width: 100%;
  margin-top: 10rpx;
  border-radius: 18rpx;
  background: rgba(31, 82, 99, 0.08);
}

.bubble-image-name {
  display: block;
  margin-top: 8rpx;
  color: var(--v-text-muted);
  font-size: 20rpx;
  word-break: break-all;
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

.image-button,
.voice-button,
.composer-button {
  flex: 1;
  min-height: 68rpx;
  border-radius: 999rpx;
  font-size: 26rpx;
  font-weight: 800;
}

.image-button {
  flex: 0.72;
  background: rgba(31, 82, 99, 0.1);
  color: var(--v-color-primary);
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

.image-button[disabled],
.voice-button[disabled],
.composer-button[disabled] {
  opacity: 0.58;
}

.image-button::after,
.voice-button::after,
.composer-button::after {
  border: none;
}

/* Keep the header and composer in flow: only the message pane scrolls. */
.chat-page {
  height: calc(100vh - var(--window-top, 0px) - var(--window-bottom, 0px));
  height: calc(100dvh - var(--window-top, 0px) - var(--window-bottom, 0px));
  min-height: 0;
  padding: 0;
  background: #ededed;
}
.page-header, .composer-card {
  width: 100%;
  max-width: 980px;
  margin: 0 auto;
  flex: 0 0 auto;
  border-radius: 0;
  box-shadow: none;
  box-sizing: border-box;
  background: #f7f7f7;
}
.page-header { padding: 10px 16px; border-bottom: 1px solid #dedede; }
.page-title { font-size: 16px; font-weight: 600; }
.header-main { gap: 8px; }
.transport-row { gap: 6px; align-items: center; }
.detail-toggle { margin: 0; padding: 0 5px; font-size: 12px; line-height: 28px; background: transparent; color: #66766c; }
.detail-toggle::after, .tool-toggle::after { border: 0; }
.transport-banner { margin-top: 8px; padding: 8px; border-radius: 6px; max-height: 90px; overflow-y: auto; }
.transport-label, .agent-meta { font-size: 12px; }
.agent-meta { margin-top: 6px; }
.chat-list { height: 0; flex: 1 1 0; width: 100%; max-width: 980px; margin: 0 auto; padding: 0; }
.message-row { padding: 0 18px; margin-top: 18px; }
.message-row + .message-row { margin-top: 16px; }
.bubble-card { max-width: 82%; padding: 10px 13px; border-radius: 7px; box-shadow: none; }
.bubble-card.user { background: #a9e97a; border-radius: 7px 2px 7px 7px; }
.bubble-card.assistant { background: #fff; border-radius: 2px 7px 7px 7px; }
.bubble-role { font-size: 11px; font-weight: 400; color: #627166; }
.bubble-text { font-size: 15px; line-height: 1.65; margin-top: 3px; color: #222; user-select: text; }
.bubble-image { width: 240px; max-width: 100%; margin-top: 6px; border-radius: 5px; }
.bubble-image-name { font-size: 11px; margin-top: 5px; }
.bubble-time { font-size: 10px; margin-top: 5px; color: #78867c; text-align: right; }
.scroll-anchor { height: 18px; }
.empty-chat { padding: 40px 20px; text-align: center; color: #88918b; font-size: 14px; }
.composer-card { position: static; padding: 9px 14px; border: 0; border-top: 1px solid #dedede; backdrop-filter: none; max-height: 45%; overflow-y: auto; }
.input-row { display: flex; align-items: center; gap: 9px; }
.tool-toggle { flex: 0 0 32px; width: 32px; height: 36px; padding: 0; margin: 0; background: transparent; font-size: 28px; line-height: 34px; color: #52635a; }
.composer-input { flex: 1; width: 0; min-width: 0; height: 42px; min-height: 42px; margin: 0; padding: 9px 10px; box-sizing: border-box; border-radius: 6px; background: white; font-size: 15px; line-height: 24px; }
.composer-button { flex: 0 0 auto; min-height: 36px; margin: 0; padding: 0 16px; border-radius: 5px; background: #07a653; font-size: 14px; line-height: 36px; }
.suggestion-row { gap: 7px; padding-bottom: 8px; }
.suggestion-chip { margin: 0; min-height: 28px; padding: 0 10px; font-size: 12px; line-height: 28px; font-weight: 400; }
.voice-meta-row { margin-bottom: 8px; }
.voice-meta-text { font-size: 11px; }
.composer-actions { margin-top: 8px; gap: 8px; }
.image-button, .voice-button { flex: 0 1 130px; min-height: 34px; margin: 0; font-size: 13px; line-height: 34px; border-radius: 5px; font-weight: 400; }
.pending-image-row { gap: 10px; margin-bottom: 8px; }
.pending-image { width: 52px; height: 52px; }
.pending-image-row button { margin: 0; font-size: 12px; line-height: 28px; }
.chat-notice, .chat-error { font-size: 12px; margin: 0 0 7px; line-height: 1.5; }
.chat-page :deep(.h5-tabbar-fallback) { flex: 0 0 auto; }
.chat-page :deep(.h5-tabbar-spacer) { height: calc(62px + env(safe-area-inset-bottom)); }
.chat-page :deep(.h5-tabbar-shell) { height: calc(62px + env(safe-area-inset-bottom)); padding: 4px 12px env(safe-area-inset-bottom); box-sizing: border-box; box-shadow: none; }
.chat-page :deep(.h5-tabbar-item) { padding: 3px 0; }
.chat-page :deep(.h5-tabbar-icon) { width: 22px; height: 22px; }
.chat-page :deep(.h5-tabbar-label) { margin-top: 2px; font-size: 11px; }
@media (max-width: 480px) {
  .page-header { padding: 8px 10px; }
  .message-row { padding: 0 12px; }
  .composer-card { padding: 8px; }
  .input-row { gap: 6px; }
  .bubble-card { max-width: 86%; }
}
</style>
