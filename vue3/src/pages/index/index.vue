<template>
  <view class="page-shell">
    <view class="hero-card">
      <view class="hero-main">
        <view>
          <text class="hero-eyebrow">V-1.7.14 / 主控制台</text>
          <text class="hero-title">V 线交互总览</text>
          <text class="hero-desc">
            首页当前收口为块状总览与快捷交互入口：前视画面、设备状态、ROS 接入状态、双风机系统、快捷控制台。
          </text>
        </view>
        <view class="identity-panel">
          <view class="identity-chip">
            <text class="chip-label">当前用户</text>
            <text class="chip-value">{{ userInfo?.username || '未登录' }}</text>
          </view>
          <view class="identity-chip">
            <text class="chip-label">当前角色</text>
            <StatusBadge :value="authStore.role || 'user'" />
          </view>
        </view>
      </view>
    </view>

    <view class="module-grid">
      <view class="module-card preview-card" @tap="openOpenMvDetail">
        <view class="module-head">
          <text class="module-title">前视画面</text>
          <text class="module-action">点击查看大图</text>
        </view>
        <view class="module-tags">
          <StatusBadge :value="openmvStatus.status" />
          <StatusBadge :value="openmvStatus.mode" />
        </view>
        <view class="preview-frame-shell" v-if="openmvSnapshotUrl">
          <image class="preview-frame" :src="openmvSnapshotUrl" mode="aspectFill" @error="handlePreviewError" />
        </view>
        <view class="preview-empty" v-else>
          <text class="preview-empty-text">{{ openmvStatus.message }}</text>
        </view>
        <view class="module-meta-grid">
          <view class="meta-item">
            <text class="meta-label">刷新周期</text>
            <text class="meta-value">{{ openmvStatus.previewRefreshMs || '--' }} ms</text>
          </view>
          <view class="meta-item">
            <text class="meta-label">图传地址</text>
            <text class="meta-value compact">{{ openmvStatus.baseUrl || '--' }}</text>
          </view>
        </view>
      </view>

      <view class="module-card">
        <view class="module-head">
          <text class="module-title">设备状态</text>
          <StatusBadge :value="deviceOnline ? 'online' : 'offline'" />
        </view>
        <view class="module-metric-grid">
          <view class="metric-block">
            <text class="metric-label">电量</text>
            <text class="metric-value">{{ formatBattery(deviceSummary?.battery) }}</text>
          </view>
          <view class="metric-block">
            <text class="metric-label">任务状态</text>
            <text class="metric-value compact">{{ deviceSummary?.taskStatus || '待同步' }}</text>
          </view>
          <view class="metric-block">
            <text class="metric-label">最近更新</text>
            <text class="metric-value compact">{{ formatDate(deviceSummary?.lastUpdate) }}</text>
          </view>
          <view class="metric-block">
            <text class="metric-label">执行结果</text>
            <text class="metric-value compact">{{ formatConsoleResult }}</text>
          </view>
        </view>
      </view>

      <view class="module-card">
        <view class="module-head">
          <text class="module-title">ROS 接入状态</text>
          <StatusBadge :value="rosStatus.connected ? 'connected' : 'disconnected'" />
        </view>
        <view class="module-tags">
          <StatusBadge :value="rosStatus.transport" />
          <StatusBadge :value="rosStatus.edgeRelayConnected ? 'online' : 'offline'" />
        </view>
        <view class="module-meta-grid">
          <view class="meta-item">
            <text class="meta-label">设备 ID</text>
            <text class="meta-value compact">{{ rosStatus.edgeDeviceId || '--' }}</text>
          </view>
          <view class="meta-item">
            <text class="meta-label">最近心跳</text>
            <text class="meta-value compact">{{ formatDate(rosStatus.lastHeartbeatAt) }}</text>
          </view>
          <view class="meta-item">
            <text class="meta-label">最近遥测</text>
            <text class="meta-value compact">{{ formatDate(rosStatus.lastTelemetryAt) }}</text>
          </view>
          <view class="meta-item">
            <text class="meta-label">遥测健康</text>
            <view class="meta-status-row">
              <StatusBadge :value="telemetrySummary.odomAvailable ? 'available' : 'missing'" />
              <StatusBadge :value="telemetrySummary.imuAvailable ? 'available' : 'missing'" />
              <StatusBadge :value="telemetrySummary.scanAvailable ? 'available' : 'missing'" />
            </view>
          </view>
        </view>
      </view>

      <view class="module-card control-card">
        <view class="module-head">
          <text class="module-title">快捷控制台</text>
          <StatusBadge :value="isAdmin ? rosStatus.transport : 'locked'" />
        </view>

        <view v-if="isAdmin" class="control-grid">
          <button
            v-for="preset in rosPresets"
            :key="preset.value"
            class="control-button"
            :class="{ danger: preset.value === 'stop' }"
            :loading="rosLoadingStates.command && activePreset === preset.value"
            @tap="handleRosPreset(preset.value)"
          >
            {{ preset.label }}
          </button>
        </view>
        <view v-else class="readonly-panel">
          <text class="readonly-text">当前账号可查看状态，但只有管理员可以在首页直接下发控制指令。</text>
        </view>

        <view class="module-meta-grid compact-top">
          <view class="meta-item">
            <text class="meta-label">当前下行</text>
            <StatusBadge :value="rosStatus.transport" />
          </view>
          <view class="meta-item">
            <text class="meta-label">最近下发</text>
            <text class="meta-value compact">{{ lastCommandLabel }}</text>
          </view>
          <view class="meta-item">
            <text class="meta-label">计划停止</text>
            <text class="meta-value compact">{{ formatDate(lastCommandResult?.scheduledStopAt) }}</text>
          </view>
          <view class="meta-item">
            <text class="meta-label">线速度 / 角速度</text>
            <text class="meta-value compact">
              {{ Number(telemetrySummary.latestLinearSpeed || 0).toFixed(2) }} /
              {{ Number(telemetrySummary.latestAngularSpeed || 0).toFixed(2) }}
            </text>
          </view>
        </view>
      </view>

      <view class="module-card wide-card fan-card">
        <view class="module-head">
          <text class="module-title">双风机系统</text>
          <view class="module-tags">
            <StatusBadge :value="fansState.enabled ? 'enabled' : 'disabled'" />
            <StatusBadge :value="fansState.lidOpen ? 'open' : 'closed'" />
            <StatusBadge :value="rosStatus.transport" />
          </view>
        </view>

        <view class="fan-state-grid">
          <view class="fan-panel">
            <text class="fan-panel-title">风机 A</text>
            <view class="fan-metrics">
              <view class="metric-block">
                <text class="metric-label">当前 PWM</text>
                <text class="metric-value">{{ Number(fansState.fanA.pwm || 0).toFixed(1) }}%</text>
              </view>
              <view class="metric-block">
                <text class="metric-label">回传转速</text>
                <text class="metric-value">{{ Number(fansState.fanA.rpm || 0).toFixed(0) }} RPM</text>
              </view>
            </view>
            <view v-if="isAdmin" class="fan-slider-shell">
              <view class="slider-head">
                <text class="slider-label">目标 PWM</text>
                <text class="slider-value">{{ Number(fanPwmDraft.fanA).toFixed(0) }}%</text>
              </view>
              <slider
                :value="fanPwmDraft.fanA"
                :min="0"
                :max="100"
                :step="1"
                activeColor="#205375"
                backgroundColor="#d7e2eb"
                block-color="#205375"
                @changing="handleFanSliderChanging('fanA', $event)"
                @change="handleFanSliderChange('fanA', $event)"
              />
            </view>
          </view>

          <view class="fan-panel">
            <text class="fan-panel-title">风机 B</text>
            <view class="fan-metrics">
              <view class="metric-block">
                <text class="metric-label">当前 PWM</text>
                <text class="metric-value">{{ Number(fansState.fanB.pwm || 0).toFixed(1) }}%</text>
              </view>
              <view class="metric-block">
                <text class="metric-label">回传转速</text>
                <text class="metric-value">{{ Number(fansState.fanB.rpm || 0).toFixed(0) }} RPM</text>
              </view>
            </view>
            <view v-if="isAdmin" class="fan-slider-shell">
              <view class="slider-head">
                <text class="slider-label">目标 PWM</text>
                <text class="slider-value">{{ Number(fanPwmDraft.fanB).toFixed(0) }}%</text>
              </view>
              <slider
                :value="fanPwmDraft.fanB"
                :min="0"
                :max="100"
                :step="1"
                activeColor="#205375"
                backgroundColor="#d7e2eb"
                block-color="#205375"
                @changing="handleFanSliderChanging('fanB', $event)"
                @change="handleFanSliderChange('fanB', $event)"
              />
            </view>
          </view>
        </view>

        <view class="fan-summary-row">
          <view class="summary-box">
            <text class="summary-label">最近摘要</text>
            <text class="summary-text">{{ fanSummaryText }}</text>
          </view>
          <view class="summary-box">
            <text class="summary-label">最近更新</text>
            <text class="summary-text">{{ formatDate(fansState.lastUpdate) }}</text>
          </view>
        </view>

        <view v-if="isAdmin" class="fan-action-row">
          <button class="primary-action" :loading="fansLoadingStates.enable" @tap="handleFanEnableToggle">
            {{ fansState.enabled ? '关闭风机系统' : '开启风机系统' }}
          </button>
          <button class="secondary-action" :loading="fansLoadingStates.pwm" @tap="applyFanPwm">
            应用双风机 PWM
          </button>
        </view>
        <view v-else class="readonly-panel compact-panel">
          <text class="readonly-text">当前仅开放风机状态查看，开启/关闭与 PWM 调节仅管理员可操作。</text>
        </view>
      </view>
    </view>

    <!-- #ifdef H5 -->
    <H5TabBarFallback current="index" />
    <!-- #endif -->
  </view>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { onHide, onShow } from '@dcloudio/uni-app'
import H5TabBarFallback from '../../components/H5TabBarFallback.vue'
import StatusBadge from '../../components/StatusBadge.vue'
import { useOpenMvPreview } from '../../composables/useOpenMvPreview.js'
import { useAppStore } from '../../stores/app.js'
import { useAuthStore } from '../../stores/auth.js'
import { useDeviceStore } from '../../stores/device.js'
import { useFansStore } from '../../stores/fans.js'
import { useRosStore } from '../../stores/ros.js'
import { ensureLoggedIn } from '../../utils/auth-guard.js'

const appStore = useAppStore()
const authStore = useAuthStore()
const deviceStore = useDeviceStore()
const rosStore = useRosStore()
const fansStore = useFansStore()

const { userInfo } = storeToRefs(authStore)
const { deviceOnline, deviceSummary, adminConsoleResult } = storeToRefs(deviceStore)
const {
  status: rosStatus,
  telemetrySummary,
  lastCommandResult,
  loadingStates: rosLoadingStates,
} = storeToRefs(rosStore)
const {
  state: fansState,
  loadingStates: fansLoadingStates,
} = storeToRefs(fansStore)

const {
  status: openmvStatus,
  snapshotUrl: openmvSnapshotUrl,
  loadStatus: loadOpenMvStatus,
  stopPreviewLoop,
  handlePreviewError,
} = useOpenMvPreview(() => authStore.token)

const activePreset = ref('')
const fanPwmDirty = ref(false)
const fanPwmDraft = reactive({
  fanA: 0,
  fanB: 0,
})

let fanRefreshTimer = null
let fanPwmApplyTimer = null
let fanPwmApplying = false

const rosPresets = [
  { label: '前进', value: 'forward' },
  { label: '后退', value: 'backward' },
  { label: '左转', value: 'turn_left' },
  { label: '右转', value: 'turn_right' },
  { label: '左平移', value: 'strafe_left' },
  { label: '右平移', value: 'strafe_right' },
  { label: '停止', value: 'stop' },
]

const isAdmin = computed(() => authStore.role === 'admin')
const lastCommandLabel = computed(() => {
  if (!lastCommandResult.value?.command) {
    return '暂无控制记录'
  }

  return lastCommandResult.value.command.metadata?.preset || '手动速度控制'
})
const formatConsoleResult = computed(() => {
  if (!adminConsoleResult.value) {
    return '暂无'
  }

  return adminConsoleResult.value.result || adminConsoleResult.value.command || '已返回'
})
const fanSummaryText = computed(() => fansState.value.summary || '等待风机状态回传')

watch(
  () => [fansState.value.fanA.pwm, fansState.value.fanB.pwm],
  ([fanA, fanB]) => {
    if (fanPwmDirty.value) {
      return
    }

    fanPwmDraft.fanA = Number(fanA || 0)
    fanPwmDraft.fanB = Number(fanB || 0)
  },
  {
    immediate: true,
  }
)

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
    rosStore.loadStatus(),
    rosStore.loadTelemetrySummary(),
    fansStore.loadState(),
    loadOpenMvStatus(),
  ])

  startFanRefreshLoop()
})

onHide(() => {
  stopPreviewLoop()
  stopFanRefreshLoop()
  clearFanPwmApplyTimer()
})

function startFanRefreshLoop() {
  stopFanRefreshLoop()
  fanRefreshTimer = setInterval(() => {
    fansStore.loadState().catch(() => {})
  }, 3000)
}

function stopFanRefreshLoop() {
  if (fanRefreshTimer) {
    clearInterval(fanRefreshTimer)
    fanRefreshTimer = null
  }
}

function openOpenMvDetail() {
  uni.navigateTo({
    url: '/pages/openmv/index',
  })
}

async function handleRosPreset(preset) {
  activePreset.value = preset

  try {
    await rosStore.sendManualPreset({ preset })
    uni.showToast({
      title: '控制指令已发送',
      icon: 'success',
    })
  } catch (error) {
    uni.showToast({
      title: error.message || '控制发送失败',
      icon: 'none',
    })
  } finally {
    activePreset.value = ''
  }
}

function handleFanSliderChange(key, event) {
  fanPwmDirty.value = true
  fanPwmDraft[key] = Number(event.detail.value || 0)
  queueFanPwmApply(0)
}

function handleFanSliderChanging(key, event) {
  fanPwmDirty.value = true
  fanPwmDraft[key] = Number(event.detail.value || 0)
  queueFanPwmApply(220)
}

function clearFanPwmApplyTimer() {
  if (fanPwmApplyTimer) {
    clearTimeout(fanPwmApplyTimer)
    fanPwmApplyTimer = null
  }
}

function queueFanPwmApply(delayMs) {
  if (!isAdmin.value) {
    return
  }

  clearFanPwmApplyTimer()
  fanPwmApplyTimer = setTimeout(() => {
    applyFanPwm({ silent: true }).catch(() => {})
  }, delayMs)
}

async function handleFanEnableToggle() {
  try {
    await fansStore.setEnabled(!fansState.value.enabled)
    await fansStore.loadState()
    fanPwmDirty.value = false
    uni.showToast({
      title: fansState.value.enabled ? '风机系统已开启' : '风机系统已关闭',
      icon: 'success',
    })
  } catch (error) {
    uni.showToast({
      title: error.message || '风机总开关更新失败',
      icon: 'none',
    })
  }
}

async function applyFanPwm(options = {}) {
  if (fanPwmApplying) {
    return null
  }

  fanPwmApplying = true

  try {
    const result = await fansStore.setPwm({
      fanA: fanPwmDraft.fanA,
      fanB: fanPwmDraft.fanB,
    })
    fanPwmDirty.value = false

    if (!options.silent) {
      uni.showToast({
        title: '双风机 PWM 已下发',
        icon: 'success',
      })
    }

    return result
  } catch (error) {
    if (!options.silent) {
      uni.showToast({
        title: error.message || '风机 PWM 下发失败',
        icon: 'none',
      })
    }

    throw error
  } finally {
    fanPwmApplying = false
  }
}

function formatBattery(value) {
  return value === 0 || value ? `${value}%` : '--'
}

function formatDate(value) {
  if (!value) {
    return '--'
  }

  return String(value).replace('T', ' ').slice(0, 19)
}
</script>

<style>
.page-shell {
  min-height: 100vh;
  padding: 28rpx;
  box-sizing: border-box;
  background:
    radial-gradient(circle at top right, rgba(70, 150, 180, 0.16), transparent 34%),
    linear-gradient(180deg, #f4f8fb 0%, #e6edf4 100%);
}

.hero-card {
  padding: 30rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #11324d, #205375 62%, #48a6a7);
  box-shadow: 0 24rpx 56rpx rgba(17, 50, 77, 0.16);
}

.hero-main {
  display: flex;
  gap: 20rpx;
  align-items: flex-start;
  justify-content: space-between;
}

.hero-eyebrow {
  display: block;
  font-size: 22rpx;
  letter-spacing: 3rpx;
  color: rgba(255, 255, 255, 0.72);
}

.hero-title {
  display: block;
  margin-top: 14rpx;
  font-size: 46rpx;
  font-weight: 700;
  color: #ffffff;
}

.hero-desc {
  display: block;
  margin-top: 16rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.9);
}

.identity-panel {
  min-width: 220rpx;
}

.identity-chip + .identity-chip {
  margin-top: 14rpx;
}

.identity-chip {
  padding: 18rpx 20rpx;
  border-radius: 20rpx;
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

.module-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
  margin-top: 24rpx;
}

.module-card {
  display: flex;
  flex-direction: column;
  min-height: 360rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14rpx 38rpx rgba(20, 32, 51, 0.08);
  box-sizing: border-box;
}

.wide-card {
  grid-column: 1 / -1;
}

.preview-card {
  cursor: pointer;
}

.module-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.module-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #17324d;
}

.module-action {
  font-size: 22rpx;
  color: #205375;
}

.module-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 14rpx;
}

.preview-frame-shell {
  overflow: hidden;
  flex: 1;
  margin-top: 16rpx;
  border-radius: 18rpx;
  background: #0f1720;
}

.preview-frame {
  width: 100%;
  height: 100%;
  min-height: 200rpx;
  display: block;
}

.preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 200rpx;
  margin-top: 16rpx;
  padding: 24rpx;
  border-radius: 18rpx;
  background: #edf3f7;
  box-sizing: border-box;
}

.preview-empty-text {
  font-size: 24rpx;
  line-height: 1.7;
  color: #516274;
  text-align: center;
}

.module-metric-grid,
.module-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 16rpx;
}

.meta-item,
.metric-block {
  padding: 18rpx;
  border-radius: 18rpx;
  background: #f7fafc;
}

.meta-label,
.metric-label {
  display: block;
  font-size: 22rpx;
  color: #6a7b8b;
}

.meta-value,
.metric-value {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: #17324d;
}

.meta-value.compact,
.metric-value.compact {
  font-size: 22rpx;
  line-height: 1.6;
}

.meta-status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  margin-top: 10rpx;
}

.control-card {
  justify-content: flex-start;
}

.control-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
  margin-top: 16rpx;
}

.control-button {
  border-radius: 999rpx;
  background: #eff5f9;
  color: #17324d;
}

.control-button.danger {
  background: #f4d8d2;
  color: #8b2f20;
}

.control-button::after,
.primary-action::after,
.secondary-action::after {
  border: none;
}

.readonly-panel {
  margin-top: 16rpx;
  padding: 22rpx;
  border-radius: 20rpx;
  background: #f7fafc;
}

.readonly-text {
  font-size: 24rpx;
  line-height: 1.7;
  color: #516274;
}

.compact-top {
  margin-top: 18rpx;
}

.fan-card {
  min-height: 0;
}

.fan-state-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 18rpx;
}

.fan-panel {
  padding: 20rpx;
  border-radius: 20rpx;
  background: #f7fafc;
}

.fan-panel-title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: #17324d;
}

.fan-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
  margin-top: 14rpx;
}

.fan-slider-shell {
  margin-top: 16rpx;
}

.slider-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.slider-label,
.summary-label {
  display: block;
  font-size: 22rpx;
  color: #6a7b8b;
}

.slider-value {
  font-size: 24rpx;
  font-weight: 700;
  color: #205375;
}

.fan-summary-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 18rpx;
}

.summary-box {
  padding: 20rpx;
  border-radius: 20rpx;
  background: #f7fafc;
}

.summary-text {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #17324d;
}

.fan-action-row {
  display: flex;
  gap: 14rpx;
  margin-top: 18rpx;
}

.primary-action,
.secondary-action {
  flex: 1;
  border-radius: 999rpx;
}

.primary-action {
  background: #205375;
  color: #ffffff;
}

.secondary-action {
  background: #e8f0f6;
  color: #17324d;
}

.compact-panel {
  margin-top: 18rpx;
}

@media screen and (max-width: 720px) {
  .hero-main,
  .module-grid,
  .module-metric-grid,
  .module-meta-grid,
  .fan-state-grid,
  .fan-summary-row,
  .fan-metrics,
  .control-grid,
  .fan-action-row {
    grid-template-columns: repeat(1, minmax(0, 1fr));
    flex-direction: column;
  }

  .identity-panel {
    width: 100%;
  }
}
</style>
