<template>
  <view class="page-shell v-page">
    <view class="hero-card v-fade-in">
      <view class="hero-copy">
        <text class="hero-eyebrow">CleanScout 设备控制</text>
        <text class="hero-title">主控台</text>
        <text class="hero-desc">前视、状态与常用动作集中到首屏，复杂遥测下沉到更多状态。</text>
      </view>
      <view class="identity-panel">
        <view class="identity-avatar">{{ (userInfo?.username || 'U').slice(0, 1).toUpperCase() }}</view>
        <view class="identity-text">
          <text class="identity-name">{{ userInfo?.username || '未登录' }}</text>
          <StatusBadge :value="authStore.role || 'user'" />
        </view>
      </view>
    </view>

    <view class="above-fold">
      <view class="vision-card v-card v-pressable" @tap="openOpenMvDetail">
        <view class="card-topline">
          <view>
            <text class="section-kicker">前方视野</text>
            <text class="card-title">前视画面</text>
          </view>
          <text class="line-icon">VIEW</text>
        </view>
        <view class="preview-frame-shell" v-if="openmvSnapshotUrl">
          <image class="preview-frame" :src="openmvSnapshotUrl" mode="aspectFill" @error="handlePreviewError" />
        </view>
        <view class="preview-empty" v-else>
          <text class="preview-empty-text">{{ openmvStatus.message }}</text>
        </view>
        <view class="compact-status-row">
          <StatusBadge :value="openmvStatus.status" />
          <text class="minor-note">{{ openmvStatus.previewRefreshMs || '--' }} ms 刷新</text>
        </view>
      </view>

      <view class="quick-card v-card">
        <view class="card-topline">
          <view>
            <text class="section-kicker">快捷动作</text>
            <text class="card-title">控制台</text>
          </view>
          <StatusBadge :value="isAdmin ? rosStatus.transport : 'locked'" />
        </view>
        <view v-if="isAdmin" class="control-grid">
          <button
            v-for="preset in rosPresets"
            :key="preset.value"
            class="control-button v-pressable"
            :class="{ danger: preset.value === 'stop' }"
            :loading="rosLoadingStates.command && activePreset === preset.value"
            @tap="handleRosPreset(preset.value)"
          >
            {{ preset.label }}
          </button>
        </view>
        <view v-else class="readonly-panel">
          <text class="readonly-text">控制受限，仅管理员可下发底盘指令。</text>
        </view>
        <view class="last-command">
          <text class="minor-label">最近下发</text>
          <text class="last-command-text">{{ lastCommandLabel }}</text>
        </view>
      </view>
    </view>

    <view class="status-pair">
      <view class="status-card v-card">
        <view class="status-card-head">
          <text class="status-title">设备状态</text>
          <StatusBadge :value="deviceOnline ? 'online' : 'offline'" />
        </view>
        <view class="mini-metrics">
          <view class="mini-metric">
            <text class="mini-value">{{ formatBattery(deviceSummary?.battery) }}</text>
            <text class="mini-label">电量</text>
          </view>
          <view class="mini-metric">
            <text class="mini-value">{{ deviceSummary?.taskStatus || '待同步' }}</text>
            <text class="mini-label">任务</text>
          </view>
        </view>
      </view>

      <view class="status-card v-card">
        <view class="status-card-head">
          <text class="status-title">连接状态</text>
          <StatusBadge :value="rosStatus.connected ? 'connected' : 'disconnected'" />
        </view>
        <view class="mini-metrics">
          <view class="mini-metric">
            <text class="mini-value">{{ rosStatus.edgeDeviceId || '--' }}</text>
            <text class="mini-label">设备 ID</text>
          </view>
          <view class="mini-metric">
            <text class="mini-value compact">{{ formatDate(rosStatus.lastHeartbeatAt) }}</text>
            <text class="mini-label">心跳</text>
          </view>
        </view>
      </view>
    </view>

    <view class="details-shell v-card">
      <view class="details-head">
        <view>
          <text class="section-kicker">更多状态</text>
          <text class="details-title">遥测与执行单元</text>
        </view>
        <StatusBadge :value="rosStatus.transport" />
      </view>

      <view class="details-grid">
        <view class="detail-card">
          <view class="detail-card-head">
            <text class="detail-title">双风机系统</text>
            <view class="status-cluster">
              <StatusBadge :value="fansState.enabled ? 'enabled' : 'disabled'" />
              <StatusBadge :value="fansState.lidOpen ? 'open' : 'closed'" />
            </view>
          </view>

          <view class="fan-state-grid">
            <view class="fan-panel">
              <text class="fan-panel-title">风机 A</text>
              <view class="fan-metrics">
                <view class="metric-block">
                  <text class="metric-label">PWM</text>
                  <text class="metric-value">{{ Number(fansState.fanA.pwm || 0).toFixed(1) }}%</text>
                </view>
                <view class="metric-block">
                  <text class="metric-label">转速</text>
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
                  activeColor="#1F5263"
                  backgroundColor="#D9E3EA"
                  block-color="#1F5263"
                  @changing="handleFanSliderChanging('fanA', $event)"
                  @change="handleFanSliderChange('fanA', $event)"
                />
              </view>
            </view>

            <view class="fan-panel">
              <text class="fan-panel-title">风机 B</text>
              <view class="fan-metrics">
                <view class="metric-block">
                  <text class="metric-label">PWM</text>
                  <text class="metric-value">{{ Number(fansState.fanB.pwm || 0).toFixed(1) }}%</text>
                </view>
                <view class="metric-block">
                  <text class="metric-label">转速</text>
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
                  activeColor="#1F5263"
                  backgroundColor="#D9E3EA"
                  block-color="#1F5263"
                  @changing="handleFanSliderChanging('fanB', $event)"
                  @change="handleFanSliderChange('fanB', $event)"
                />
              </view>
            </view>
          </view>

          <view class="fan-summary-row">
            <text class="summary-text">{{ fanSummaryText }}</text>
            <text class="minor-note">拖动滑条会自动下发，松手立即同步。</text>
          </view>

          <view v-if="isAdmin" class="fan-action-row">
            <button class="primary-action v-pressable" :loading="fansLoadingStates.enable" @tap="handleFanEnableToggle">
              {{ fansState.enabled ? '关闭风机' : '开启风机' }}
            </button>
            <button class="secondary-action v-pressable" :loading="fansLoadingStates.pwm" @tap="applyFanPwm">
              立即同步 PWM
            </button>
          </view>
          <view v-else class="readonly-panel compact-panel">
            <text class="readonly-text">风机开关与 PWM 仅管理员可操作。</text>
          </view>
        </view>

        <view class="detail-card">
          <view class="detail-card-head">
            <text class="detail-title">ROS 遥测摘要</text>
            <view class="status-cluster">
              <StatusBadge :value="telemetrySummary.odomAvailable ? 'available' : 'missing'" />
              <StatusBadge :value="telemetrySummary.imuAvailable ? 'available' : 'missing'" />
              <StatusBadge :value="telemetrySummary.scanAvailable ? 'available' : 'missing'" />
            </view>
          </view>
          <view class="telemetry-grid">
            <view class="metric-block">
              <text class="metric-label">最近遥测</text>
              <text class="metric-value compact">{{ formatDate(rosStatus.lastTelemetryAt) }}</text>
            </view>
            <view class="metric-block">
              <text class="metric-label">执行结果</text>
              <text class="metric-value compact">{{ formatConsoleResult }}</text>
            </view>
            <view class="metric-block">
              <text class="metric-label">计划停止</text>
              <text class="metric-value compact">{{ formatDate(lastCommandResult?.scheduledStopAt) }}</text>
            </view>
            <view class="metric-block">
              <text class="metric-label">线速度 / 角速度</text>
              <text class="metric-value compact">
                {{ Number(telemetrySummary.latestLinearSpeed || 0).toFixed(2) }} /
                {{ Number(telemetrySummary.latestAngularSpeed || 0).toFixed(2) }}
              </text>
            </view>
          </view>
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
  padding: 28rpx 26rpx 48rpx;
  box-sizing: border-box;
}

.hero-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22rpx;
  padding: 34rpx;
  border-radius: 36rpx;
  background:
    radial-gradient(circle at 92% 8%, rgba(213, 138, 58, 0.2), transparent 26%),
    linear-gradient(135deg, #17384a 0%, #1f5263 58%, #5f98a4 100%);
  box-shadow: var(--v-shadow-float);
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
  font-size: 52rpx;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: 0.02em;
}

.hero-desc {
  display: block;
  max-width: 470rpx;
  margin-top: 14rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.86);
}

.identity-panel {
  display: flex;
  align-items: center;
  min-width: 240rpx;
  padding: 18rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.18);
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.12);
}

.identity-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 76rpx;
  height: 76rpx;
  margin-right: 16rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.92);
  color: var(--v-color-primary-deep);
  font-size: 34rpx;
  font-weight: 800;
}

.identity-text {
  flex: 1;
  min-width: 0;
}

.identity-name {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: #ffffff;
  margin-bottom: 10rpx;
}

.above-fold,
.status-pair,
.details-grid,
.fan-state-grid,
.telemetry-grid,
.mini-metrics,
.fan-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 18rpx;
  margin-top: 22rpx;
}

.vision-card,
.quick-card,
.status-card,
.detail-card {
  display: flex;
  flex-direction: column;
  padding: 26rpx;
  box-sizing: border-box;
}

.vision-card {
  flex: 1.25;
  min-width: 360rpx;
  min-height: 520rpx;
}

.quick-card {
  flex: 0.85;
  min-width: 300rpx;
}

.card-topline,
.status-card-head,
.details-head,
.detail-card-head,
.slider-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.section-kicker {
  display: block;
  margin-bottom: 8rpx;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--v-text-muted);
}

.card-title,
.details-title,
.status-title,
.detail-title {
  display: block;
  color: var(--v-text-main);
  font-weight: 800;
}

.card-title {
  font-size: 34rpx;
}

.details-title {
  margin-top: 6rpx;
  font-size: 32rpx;
}

.status-title,
.detail-title {
  font-size: 28rpx;
}

.line-icon {
  min-width: 78rpx;
  padding: 10rpx 14rpx;
  border: 1rpx solid rgba(31, 82, 99, 0.18);
  border-radius: 999rpx;
  color: var(--v-color-primary);
  font-size: 20rpx;
  font-weight: 800;
  text-align: center;
  letter-spacing: 0.08em;
}

.preview-frame-shell {
  overflow: hidden;
  flex: 1;
  margin-top: 24rpx;
  border-radius: 28rpx;
  background: #101a22;
  box-shadow: inset 0 0 0 1rpx rgba(255, 255, 255, 0.08);
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
  min-height: 260rpx;
  margin-top: 24rpx;
  padding: 24rpx;
  border-radius: 28rpx;
  background: var(--v-bg-panel);
  box-sizing: border-box;
}

.preview-empty-text {
  font-size: 24rpx;
  line-height: 1.7;
  color: var(--v-text-muted);
  text-align: center;
}

.compact-status-row,
.status-cluster {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12rpx;
  margin-top: 18rpx;
}

.minor-note,
.minor-label {
  font-size: 22rpx;
  line-height: 1.5;
  color: var(--v-text-muted);
}

.minor-label {
  display: block;
}

.status-card {
  flex: 1;
  min-width: 300rpx;
}

.mini-metric,
.metric-block {
  flex: 1;
  min-width: 180rpx;
  padding: 20rpx;
  border-radius: 22rpx;
  background: var(--v-bg-panel);
}

.mini-value,
.metric-value,
.last-command-text {
  display: block;
  color: var(--v-text-main);
  font-weight: 800;
}

.mini-value {
  font-size: 28rpx;
}

.metric-value {
  margin-top: 10rpx;
  font-size: 26rpx;
}

.mini-value.compact,
.metric-value.compact {
  font-size: 22rpx;
  line-height: 1.6;
}

.mini-label,
.metric-label {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: var(--v-text-muted);
}

.details-shell {
  margin-top: 22rpx;
  padding: 26rpx;
}

.control-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 24rpx;
}

.control-button {
  flex: 1 1 42%;
  min-height: 72rpx;
  border-radius: 999rpx;
  background: #eef5f7;
  color: var(--v-text-main);
  font-size: 26rpx;
  font-weight: 800;
}

.control-button.danger {
  background: rgba(200, 93, 74, 0.16);
  color: var(--v-color-danger);
}

.control-button::after,
.primary-action::after,
.secondary-action::after {
  border: none;
}

.readonly-panel {
  margin-top: 20rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: var(--v-bg-panel);
}

.readonly-text {
  font-size: 24rpx;
  line-height: 1.7;
  color: var(--v-text-secondary);
}

.last-command {
  margin-top: 22rpx;
  padding: 20rpx;
  border-radius: 22rpx;
  background: linear-gradient(135deg, rgba(31, 82, 99, 0.08), rgba(213, 138, 58, 0.09));
}

.last-command-text {
  margin-top: 8rpx;
  font-size: 24rpx;
}

.detail-card {
  flex: 1;
  min-width: 300rpx;
  border-radius: 28rpx;
  background: rgba(246, 250, 252, 0.82);
}

.fan-panel {
  flex: 1;
  min-width: 280rpx;
  padding: 22rpx;
  border-radius: 24rpx;
  background: #ffffff;
}

.fan-panel-title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: var(--v-text-main);
}

.fan-slider-shell {
  margin-top: 16rpx;
}

.slider-label {
  display: block;
  font-size: 22rpx;
  color: var(--v-text-muted);
}

.slider-value {
  font-size: 24rpx;
  font-weight: 800;
  color: var(--v-color-primary);
}

.fan-summary-row {
  margin-top: 18rpx;
  padding: 20rpx;
  border-radius: 22rpx;
  background: rgba(31, 82, 99, 0.06);
}

.summary-text {
  display: block;
  font-size: 24rpx;
  line-height: 1.6;
  color: var(--v-text-main);
}

.fan-action-row {
  display: flex;
  gap: 14rpx;
  margin-top: 18rpx;
}

.primary-action,
.secondary-action {
  flex: 1;
  min-height: 78rpx;
  border-radius: 999rpx;
  font-size: 26rpx;
  font-weight: 800;
}

.primary-action {
  background: var(--v-color-primary);
  color: #ffffff;
}

.secondary-action {
  background: #e8f0f3;
  color: var(--v-text-main);
}

.compact-panel {
  margin-top: 18rpx;
}

@media screen and (max-width: 520px) {
  .hero-card,
  .above-fold,
  .status-pair,
  .details-grid,
  .fan-state-grid,
  .telemetry-grid,
  .fan-action-row {
    flex-direction: column;
  }

  .vision-card,
  .quick-card,
  .status-card,
  .detail-card {
    min-width: 0;
  }

  .identity-panel {
    width: 100%;
    box-sizing: border-box;
  }
}
</style>
