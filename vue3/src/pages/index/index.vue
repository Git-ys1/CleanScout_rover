<template>
  <view class="dashboard">
    <view class="content">
      <view class="panel overview">
        <view class="heading"><text class="title">{{ deviceSummary?.name || deviceSummary?.deviceName || '清扫机器人' }}</text><text v-if="isDemo" class="demo">ⓘ 演示模式</text></view>
        <view class="overview-metrics">
          <view><text class="label">设备连接</text><text class="value">○ {{ connectionText }}</text></view>
          <view><text class="label">当前任务</text><text class="value">{{ taskLabel(deviceSummary?.taskStatus) }}</text></view>
          <view><text class="label">电量</text><text class="value">▱ {{ formatBattery(deviceSummary?.battery) }}</text></view>
        </view>
        <text class="note">{{ ageText(updateAt, now) }}{{ outdated ? ' · 数据可能已过期' : '' }}</text>
        <text v-if="isDemo" class="note">概况或控制链路包含演示数据，不代表真实设备状态。</text>
      </view>
      <view v-for="item in alerts" :key="item.text" class="notice" :class="item.tone"><text>ⓘ {{ item.text }}</text></view>
      <view class="main-grid">
        <view class="panel">
          <text class="section-title">常用操作</text>
          <text v-if="!isAdmin" class="note">当前账号可查看设备状态，控制操作需管理员权限。</text>
          <template v-else>
            <text class="note">手动移动设备；停止按钮可随时下发停止指令。</text>
            <view class="actions"><button v-for="preset in rosPresets" :key="preset.value" :class="{ primary: preset.value === 'forward', stop: preset.value === 'stop' }" :disabled="preset.value !== 'stop' && (!!controlReason || commandPending)" :loading="commandPending && activePreset === preset.value" @tap="handleRosPreset(preset.value)">{{ preset.label }}</button></view>
            <text v-if="controlReason" class="note">{{ controlReason }}，移动操作暂不可用。停止指令仍可尝试发送。</text>
          </template>
          <text v-if="commandNotice" class="note" role="status">{{ commandNotice }}</text>
          <view class="list-row"><text>最近操作</text><text>{{ lastCommandLabel }}</text></view>
        </view>
        <view class="panel">
          <view class="heading"><text class="section-title">前方画面</text><button class="link" @tap="openOpenMvDetail">查看详情 ›</button></view>
          <template v-if="openmvStreamUrl || openmvSnapshotUrl">
            <!-- #ifdef H5 -->
            <img v-if="openmvStreamUrl" class="preview" :src="openmvStreamUrl" alt="机器人前方画面" @error="handlePreviewError" />
            <image v-else class="preview" :src="openmvSnapshotUrl" mode="widthFix" @error="handlePreviewError" />
            <!-- #endif -->
            <!-- #ifndef H5 -->
            <image class="preview" :src="openmvSnapshotUrl" mode="widthFix" @error="handlePreviewError" />
            <!-- #endif -->
          </template>
          <text v-else class="empty">ⓘ {{ cameraEmpty }}</text>
        </view>
      </view>
      <text class="section-title outside">设备详情</text>
      <view class="panel details">
        <button class="group-toggle" @tap="expanded.connection = !expanded.connection"><text>连接信息</text><text>{{ connectionText }} {{ expanded.connection ? '⌃' : '⌄' }}</text></button>
        <view v-if="expanded.connection" class="group-content">
          <view class="list-row"><text>设备编号</text><text>{{ deviceSummary?.deviceId || rosStatus.edgeDeviceId || '暂未获取' }}</text></view>
          <view class="list-row"><text>连接方式</text><text>{{ !loaded.ros ? '暂未获取' : ({mock:'演示链路', 'edge-relay':'设备中继', rosbridge:'机器人直连'})[rosStatus.transport] || '状态未知' }}</text></view>
          <view class="list-row"><text>最近通信时间</text><text>{{ formatDate(rosStatus.lastHeartbeatAt) }}</text></view>
          <view class="list-row"><text>数据更新时间</text><text>{{ formatDate(updateAt) }}</text></view>
          <view class="list-row"><text>画面刷新间隔</text><text>{{ loaded.camera ? numberText(openmvStatus.previewRefreshMs, ' ms') : '暂未获取' }}</text></view>
          <text class="note">超过 30 秒未更新时提示数据过期，不据此推断设备故障。</text>
        </view>
        <button class="group-toggle" @tap="expanded.fans = !expanded.fans"><text>清扫风机</text><text>{{ fanReceived ? '查看最近记录' : '暂未收到风机状态' }} {{ expanded.fans ? '⌃' : '⌄' }}</text></button>
        <view v-if="expanded.fans" class="group-content">
          <text class="note">接口提供合并状态缓存，没有逐项确认标记；数值为接口缓存值，不能视为执行确认。</text>
          <view v-for="(name, key) in { fanA: '风机 A', fanB: '风机 B' }" :key="key">
            <view class="list-row"><text>{{ name }}</text><text>{{ fanRun(key) }}</text></view>
            <view class="list-row"><text>风机输出（PWM 占空比）</text><text>{{ fanValue(key, 'pwm', '%') }}</text></view>
            <view class="list-row"><text>转速</text><text>{{ fanValue(key, 'rpm', ' RPM') }}</text></view>
            <template v-if="isAdmin">
              <view class="list-row"><text>{{ name }} 输出设定值</text><text>{{ fanPwmDraft[key] }}%</text></view>
              <slider :value="fanPwmDraft[key]" :min="0" :max="100" :step="1" :disabled="!!controlReason" activeColor="#07A35A" @changing="handleFanSliderChanging(key, $event)" @change="handleFanSliderChange(key, $event)" />
            </template>
          </view>
          <text class="note">最近风机记录：{{ formatDate(fansState.lastUpdate) }}</text>
          <template v-if="isAdmin">
            <text class="note">调节时自动下发，松手立即同步。设定值与上方接口回传值分开显示。</text>
            <view class="actions"><button :disabled="!!controlReason || fanPending" :loading="fanPending" @tap="handleFanEnableToggle(true)">发送开启指令</button><button :disabled="!!controlReason || fanPending" @tap="handleFanEnableToggle(false)">发送关闭指令</button><button :disabled="!!controlReason || fansLoadingStates.pwm" :loading="fansLoadingStates.pwm" @tap="applyFanPwm">发送输出设定</button></view>
            <text v-if="controlReason" class="note">{{ controlReason }}</text>
            <text v-if="fanNotice" class="note" role="status">{{ fanNotice }}</text>
          </template>
        </view>
        <button class="group-toggle" @tap="expanded.telemetry = !expanded.telemetry"><text>运行数据</text><text>{{ loaded.telemetry ? '查看各项数据' : '暂未收到数据' }} {{ expanded.telemetry ? '⌃' : '⌄' }}</text></button>
        <view v-if="expanded.telemetry" class="group-content">
          <view v-for="(label, key) in { odom: '位置与速度', imu: '姿态传感器', scan: '障碍扫描' }" :key="key" class="list-row"><text>{{ label }}</text><text>{{ loaded.telemetry && telemetrySummary[key + 'Available'] ? '已有记录' : '暂未收到数据' }}</text></view>
          <view class="list-row"><text>前后移动速度</text><text>{{ loaded.telemetry && telemetrySummary.odomAvailable ? numberText(telemetrySummary.latestLinearSpeed, ' m/s') : '暂未收到速度数据' }}</text></view>
          <view class="list-row"><text>转向角速度</text><text>{{ loaded.telemetry && telemetrySummary.odomAvailable ? numberText(telemetrySummary.latestAngularSpeed, ' rad/s') : '暂未收到速度数据' }}</text></view>
          <view class="list-row"><text>最近运行数据</text><text>{{ formatDate(rosStatus.lastTelemetryAt) }}</text></view>
          <view class="list-row"><text>计划停止时间</text><text>{{ formatDate(lastCommandResult?.scheduledStopAt) }}</text></view>
          <text class="note">速度来自 ROS 里程计 linear.x 与 angular.z；有记录不表示数据仍然实时有效。</text>
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
import { onlineLabel, taskLabel, numberText, ageText, isStale } from './presentation.js'
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


const { deviceSummary } = storeToRefs(deviceStore)
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
  streamUrl: openmvStreamUrl,
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

let refreshRunning = false
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
const expanded = reactive({ connection: false, fans: false, telemetry: false })
const loaded = reactive({ device: false, ros: false, fans: false, telemetry: false, camera: false })
const now = ref(Date.now())
const refreshFailed = ref(false)
const commandNotice = ref('')
const fanNotice = ref('')
const commandPending = ref(false)
let pendingCommands = 0
let commandSequence = 0
const fanPending = ref(false)
const isDemo = computed(() => (loaded.device && deviceSummary.value?.deviceId === 'mock-rover-001') || (loaded.ros && rosStatus.value.transport === 'mock'))
const connectionText = computed(() => onlineLabel(loaded.ros ? rosStatus.value : null, loaded.device ? deviceSummary.value : null, rosLoadingStates.value.status))
const updateAt = computed(() => deviceSummary.value?.lastUpdate || rosStatus.value.lastTelemetryAt)
const outdated = computed(() => isStale(updateAt.value, now.value))
const controlReason = computed(() => !loaded.ros ? '暂未获取连接状态' : !rosStatus.value.enabled ? '设备控制功能未开启' : !rosStatus.value.connected ? '设备连接未建立' : '')
const fanReceived = computed(() => loaded.fans && Boolean(fansState.value.lastUpdate))
const cameraEmpty = computed(() => !loaded.camera ? '正在读取摄像头状态' : openmvStatus.value.status === 'error' ? '画面加载失败' : !openmvStatus.value.enabled ? '摄像头未开启' : '暂未收到画面')
const alerts = computed(() => {
  const items = []
  if (deviceSummary.value?.taskStatus === 'error') items.push({ tone: 'fault', text: '设备上报任务异常，请停止操作并联系管理员检查设备。' })
  if (refreshFailed.value) items.push({ tone: 'warning', text: '状态更新失败，当前可能是旧数据。请检查网络，稍后将自动重试。' })
  if (outdated.value) items.push({ tone: 'warning', text: '设备数据超过 30 秒未更新，请检查设备连接；下方数值为最近记录。' })
  if (loaded.ros && rosStatus.value.enabled && !rosStatus.value.connected) items.push({ tone: 'warning', text: '设备连接中断或尚未建立，请确认设备已开机并连接网络。' })
  if (loaded.ros && !rosStatus.value.enabled) items.push({ tone: 'neutral', text: '设备控制功能未开启，可联系管理员确认配置。' })
  return items
})
const lastCommandLabel = computed(() => {
  const result = lastCommandResult.value
  if (!result?.command) return '暂无操作记录'
  const name = rosPresets.find(p => p.value === result.command.metadata?.preset)?.label || '移动控制'
  return name + ' · ' + (result.transport === 'mock' ? '演示指令已接收，未控制真实设备' : result.accepted === true ? '指令已发送，尚无设备执行确认' : '状态未知')
})
function fanValue(key, field, unit) {
  if (!fanReceived.value) return '暂未收到数据'
  const value = fansState.value[key]?.[field]
  // The existing backend substitutes zero for missing individual fields.
  if (value === 0) return '暂未确认（接口缓存为 0）'
  return numberText(value, unit)
}
function fanRun(key) {
  if (!fanReceived.value) return '暂未收到风机状态'
  return '运行状态未单独上报'
}
async function refreshDashboard() {
  const jobs = [['device', () => deviceStore.fetchSummary()], ['ros', () => rosStore.loadStatus()], ['telemetry', () => rosStore.loadTelemetrySummary()], ['fans', () => fansStore.loadState()]]
  const results = await Promise.allSettled(jobs.map(async ([key, run]) => { await run(); loaded[key] = true }))
  refreshFailed.value = results.some(r => r.status === 'rejected')
  now.value = Date.now()
}

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

  await Promise.allSettled([authStore.fetchMe(), refreshDashboard(), loadOpenMvStatus().then(() => { loaded.camera = true })])

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
    if (!refreshRunning) { refreshRunning = true; refreshDashboard().finally(() => { refreshRunning = false }) }
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
  if (!isAdmin.value || (preset !== 'stop' && (commandPending.value || controlReason.value))) return
  const sequence = ++commandSequence
  pendingCommands++
  commandPending.value = true
  commandNotice.value = '正在发送指令…'
  activePreset.value = preset

  try {
    const result = await rosStore.sendManualPreset({ preset })
    if (sequence !== commandSequence) return
    commandNotice.value = result.transport === 'mock' ? '演示指令已接收，未控制真实设备' : result.accepted === true ? '指令已发送，等待设备执行确认（当前接口不提供确认）' : '指令结果未知'
    uni.showToast({
      title: commandNotice.value,
      icon: 'none',
    })
  } catch (error) {
    if (sequence !== commandSequence) return
    commandNotice.value = '指令发送失败：' + (error.message || '请重试')
    uni.showToast({
      title: error.message || '控制发送失败',
      icon: 'none',
    })
  } finally {
    if (sequence === commandSequence) activePreset.value = ''
    pendingCommands--
    commandPending.value = pendingCommands > 0
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

async function handleFanEnableToggle(enabled) {
  if (!isAdmin.value || fanPending.value || controlReason.value) return
  fanPending.value = true
  fanNotice.value = '正在发送风机指令…'
  try {
    const result = await fansStore.setEnabled(enabled)
    fanNotice.value = result.transport === 'mock' ? '演示风机指令已接收' : '风机指令已发送，尚无设备执行确认'
    await fansStore.loadState()
    fanPwmDirty.value = false
    uni.showToast({
      title: fanNotice.value,
      icon: 'none',
    })
  } catch (error) {
    fanNotice.value = '风机指令发送失败'
    uni.showToast({
      title: error.message || '风机总开关更新失败',
      icon: 'none',
    })
  }
  finally { fanPending.value = false }
}

async function applyFanPwm(options = {}) {
  if (!isAdmin.value || controlReason.value) return null
  if (fanPwmApplying) {
    return null
  }

  fanPwmApplying = true
  fanNotice.value = '正在发送风机输出设定…'

  try {
    const result = await fansStore.setPwm({
      fanA: fanPwmDraft.fanA,
      fanB: fanPwmDraft.fanB,
    })
    fanPwmDirty.value = false
    fanNotice.value = result.transport === 'mock' ? '演示输出设定已接收' : '输出设定已发送，尚无设备执行确认'

    if (!options.silent) {
      uni.showToast({
        title: '风机输出设定已发送',
        icon: 'success',
      })
    }

    return result
  } catch (error) {
    fanNotice.value = '风机输出设定发送失败'
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
  return numberText(value, '%')
}

function formatDate(value) {
  if (!value) {
    return '暂未获取'
  }

  return String(value).replace('T', ' ').slice(0, 19)
}
</script>
<style scoped>
.dashboard { min-height: 100vh; background: #f5f5f5; color: #1f2329; padding: 16px 16px calc(80px + env(safe-area-inset-bottom)); box-sizing: border-box; font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; }
.content { max-width: 1200px; margin: auto; }
.panel { background: white; border-radius: 12px; padding: 18px; min-width: 0; }
.heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.title { font-size: 20px; font-weight: 600; overflow-wrap: anywhere; }
.section-title { font-size: 17px; font-weight: 600; }
.overview-metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 16px 0 10px; }
.label, .value, .note { display: block; }
.label, .note { color: #667085; font-size: 14px; }
.value { margin-top: 4px; font-size: 16px; font-weight: 600; overflow-wrap: anywhere; }
.note { margin-top: 8px; }
.demo { color: #995600; background: #fff5df; border-radius: 6px; padding: 3px 8px; font-size: 13px; }
.notice { padding: 12px 16px; margin-top: 12px; border-radius: 12px; font-size: 14px; }
.warning { background: #fff3df; color: #8a520b; }
.neutral { background: #edf0f3; color: #667085; }
.fault { background: #fff0ee; color: #b42318; }
.main-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; margin-top: 16px; }
.actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
button { font: inherit; box-sizing: border-box; }
.actions button { flex: 1 1 100px; min-height: 44px; padding: 7px 12px; margin: 0; font-size: 14px; line-height: 30px; color: #1f2329; background: #f0f3f1; border-radius: 8px; }
button::after { border: 0; }
.actions .primary { background: #07a35a; color: white; }
.actions .stop { color: #b42318; background: #fff0ee; border: 1px solid #edc0b9; }
.actions button[disabled] { color: #828991; background: #f3f4f5; }
.list-row { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; padding: 12px 0; border-bottom: 1px solid #f0f1f2; font-size: 14px; }
.list-row > text:first-child { flex: 0 0 42%; color: #667085; }
.list-row > text:last-child { text-align: right; min-width: 0; overflow-wrap: anywhere; }
.preview { display: block; width: 100%; height: auto; object-fit: contain; margin-top: 12px; border-radius: 8px; }
.empty { display: block; padding: 18px 0 6px; color: #667085; }
.link { background: transparent; color: #07a35a; margin: 0; padding: 0 4px; line-height: 44px; font-size: 14px; }
.outside { display: block; margin: 22px 0 10px; }
.details { padding: 0 18px; }
.group-toggle { display: flex; justify-content: space-between; align-items: center; gap: 10px; text-align: left; width: 100%; min-height: 60px; padding: 10px 0; border-radius: 0; background: white; border-bottom: 1px solid #eee; line-height: 1.5; }
.group-toggle > text:last-child { font-size: 13px; color: #667085; text-align: right; }
.group-content { padding-bottom: 16px; }
@media (max-width: 700px) { .main-grid { grid-template-columns: minmax(0, 1fr); } .panel { padding: 16px; } .details { padding: 0 16px; } .overview-metrics { gap: 8px; } .value { font-size: 15px; } }
</style>
