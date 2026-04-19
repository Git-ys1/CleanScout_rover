<template>
  <view class="admin-page">
    <view class="header-card">
      <text class="header-title">管理员工作台</text>
      <text class="header-desc">
        当前轮把管理员页升级成系统管理面板，并在同一页面内并行承载用户管理、系统开关、OpenClaw 接入状态和 ROS 固定控制台。
      </text>
    </view>

    <view class="section-switcher">
      <button
        v-for="section in sections"
        :key="section.value"
        class="section-button"
        :class="{ active: activeSection === section.value }"
        @tap="adminStore.setActiveSection(section.value)"
      >
        {{ section.label }}
      </button>
    </view>

    <view v-if="activeSection === 'users'" class="panel-card">
      <text class="panel-title">用户管理</text>
      <view class="create-form">
        <input v-model="newUserForm.username" class="field" placeholder="用户名" />
        <input v-model="newUserForm.password" class="field" password placeholder="初始密码（至少 6 位）" />
        <picker class="picker" :range="roleOptions" @change="handleRoleChange">
          <view class="picker-value">角色：{{ newUserForm.role }}</view>
        </picker>
        <label class="switch-row">
          <text class="switch-label">新增后立即启用</text>
          <switch :checked="newUserForm.isEnabled" @change="handleCreateEnabledChange" color="#205375" />
        </label>
        <button class="primary-button" :loading="loadingStates.submitUser" @tap="submitNewUser">新增用户</button>
      </view>

      <view class="user-list">
        <view class="user-card" v-for="user in users" :key="user.id">
          <view class="user-meta">
            <text class="user-name">{{ user.username }}</text>
            <text class="user-tag" :class="user.role">{{ user.role }}</text>
            <text class="user-status" :class="{ disabled: !user.isEnabled }">
              {{ user.isEnabled ? '启用中' : '已停用' }}
            </text>
          </view>
          <text class="user-time">创建时间：{{ formatDate(user.createdAt) }}</text>
          <view class="user-actions">
            <button class="inline-button" @tap="toggleUserEnabled(user)">
              {{ user.isEnabled ? '停用' : '启用' }}
            </button>
            <button class="inline-button" @tap="toggleUserRole(user)">
              改为{{ user.role === 'admin' ? 'user' : 'admin' }}
            </button>
            <button class="inline-button danger" @tap="removeUser(user)">删除</button>
          </view>
        </view>
      </view>
    </view>

    <view v-if="activeSection === 'system'" class="panel-card">
      <text class="panel-title">系统开关</text>
      <label class="switch-row">
        <text class="switch-label">允许新用户注册</text>
        <switch :checked="systemConfig.registrationEnabled" color="#205375" @change="handleRegistrationChange" />
      </label>
      <label class="switch-row">
        <text class="switch-label">软件总开关</text>
        <switch :checked="systemConfig.appEnabled" color="#205375" @change="handleAppEnabledChange" />
      </label>
      <label class="switch-row">
        <text class="switch-label">OpenClaw 接入软开关</text>
        <switch :checked="systemConfig.openclawEnabled" color="#205375" @change="handleOpenClawToggle" />
      </label>
      <textarea
        v-model="systemConfig.maintenanceMessage"
        class="maintenance-input"
        maxlength="120"
        placeholder="维护提示语，普通用户在维护模式下会看到这里的文本"
      />
      <button class="primary-button" :loading="loadingStates.saveSystemConfig" @tap="saveSystemConfig">
        保存系统配置
      </button>
    </view>

    <view v-if="activeSection === 'gateway'" class="panel-card">
      <text class="panel-title">接入状态 / ROS 控制</text>

      <view class="sub-panel">
        <text class="sub-panel-title">OpenClaw 接入状态</text>
        <view class="status-grid">
          <view class="status-item">
            <text class="status-label">当前 transport</text>
            <text class="status-value">{{ openclawStatus.activeTransport }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">OpenClaw 状态</text>
            <text class="status-value">{{ openclawStatus.status }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">API 模式</text>
            <text class="status-value">{{ openclawStatus.apiMode }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">目标模型</text>
            <text class="status-value">{{ openclawStatus.model }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">最近探测</text>
            <text class="status-value compact">{{ formatDate(openclawStatus.lastProbeAt) }}</text>
          </view>
        </view>
        <view class="status-note">
          <text class="status-note-text">{{ openclawStatus.message }}</text>
        </view>
      </view>

      <view class="sub-panel">
        <text class="sub-panel-title">ROS 状态</text>
        <view class="status-grid">
          <view class="status-item">
            <text class="status-label">当前 transport</text>
            <text class="status-value">{{ rosStatus.transport }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">连接状态</text>
            <text class="status-value">{{ rosStatus.connected ? 'connected' : 'disconnected' }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">edge-relay 在线</text>
            <text class="status-value">{{ rosStatus.edgeRelayConnected ? 'online' : 'offline' }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">edge deviceId</text>
            <text class="status-value compact">{{ rosStatus.edgeDeviceId || '--' }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">最近心跳</text>
            <text class="status-value compact">{{ formatDate(rosStatus.lastHeartbeatAt) }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">最近 edge 遥测</text>
            <text class="status-value compact">{{ formatDate(rosStatus.lastTelemetryAt) }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">rosbridge</text>
            <text class="status-value compact">{{ rosStatus.rosbridgeUrl }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">cmd_vel topic</text>
            <text class="status-value compact">{{ rosStatus.cmdVelTopic }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">最近错误</text>
            <text class="status-value compact">{{ rosStatus.lastRelayError || rosStatus.lastError || '--' }}</text>
          </view>
        </view>
      </view>

      <view class="sub-panel">
        <text class="sub-panel-title">ROS 控制台</text>
        <view class="control-grid">
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
        <view class="status-grid">
          <view class="status-item">
            <text class="status-label">odom</text>
            <text class="status-value">{{ telemetrySummary.odomAvailable ? 'available' : 'missing' }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">imu</text>
            <text class="status-value">{{ telemetrySummary.imuAvailable ? 'available' : 'missing' }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">scan</text>
            <text class="status-value">{{ telemetrySummary.scanAvailable ? 'available' : 'missing' }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">线速度</text>
            <text class="status-value">{{ Number(telemetrySummary.latestLinearSpeed || 0).toFixed(2) }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">角速度</text>
            <text class="status-value">{{ Number(telemetrySummary.latestAngularSpeed || 0).toFixed(2) }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">最后 odom</text>
            <text class="status-value compact">{{ formatDate(telemetrySummary.lastOdomAt) }}</text>
          </view>
        </view>
        <view class="status-note">
          <text class="status-note-text">
            下一轮对接树莓派 + OpenClaw 实机链路；当前固定控制平面先走 backend ROS adapter，natural language 仍走 OpenClaw 平面。
          </text>
        </view>
        <view class="status-note" v-if="lastCommandResult">
          <text class="status-note-text">
            最近下发：{{ lastCommandResult.command?.metadata?.preset || 'cmd_vel' }} / transport:
            {{ lastCommandResult.transport }} / stop at: {{ formatDate(lastCommandResult.scheduledStopAt) }}
          </text>
        </view>
      </view>

      <button
        class="primary-button"
        :loading="loadingStates.openclawStatus || rosLoadingStates.status || rosLoadingStates.telemetry"
        @tap="refreshGatewayStatus"
      >
        刷新接入状态
      </button>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { onShow } from '@dcloudio/uni-app'
import { useAdminStore } from '../../stores/admin.js'
import { useAppStore } from '../../stores/app.js'
import { useRosStore } from '../../stores/ros.js'
import { ensureAdmin } from '../../utils/auth-guard.js'

const appStore = useAppStore()
const adminStore = useAdminStore()
const rosStore = useRosStore()
const { users, systemConfig, openclawStatus, activeSection, loadingStates } = storeToRefs(adminStore)
const {
  status: rosStatus,
  telemetrySummary,
  lastCommandResult,
  loadingStates: rosLoadingStates,
} = storeToRefs(rosStore)

const sections = [
  { label: '用户管理', value: 'users' },
  { label: '系统开关', value: 'system' },
  { label: '接入状态 / ROS', value: 'gateway' },
]

const roleOptions = ['user', 'admin']
const rosPresets = [
  { label: '前进', value: 'forward' },
  { label: '后退', value: 'backward' },
  { label: '左转', value: 'turn_left' },
  { label: '右转', value: 'turn_right' },
  { label: '左平移', value: 'strafe_left' },
  { label: '右平移', value: 'strafe_right' },
  { label: '停止', value: 'stop' },
]

const activePreset = ref('')
const newUserForm = reactive({
  username: '',
  password: '',
  role: 'user',
  isEnabled: true,
})

onShow(async () => {
  const allowed = await ensureAdmin()

  if (!allowed) {
    return
  }

  appStore.setCurrentTab('admin')

  await Promise.allSettled([
    adminStore.loadUsers(),
    adminStore.loadSystemConfig(),
    adminStore.loadOpenClawStatus(),
    rosStore.loadStatus(),
    rosStore.loadTelemetrySummary(),
  ])
})

function handleRoleChange(event) {
  newUserForm.role = roleOptions[event.detail.value] || 'user'
}

function handleCreateEnabledChange(event) {
  newUserForm.isEnabled = Boolean(event.detail.value)
}

function handleRegistrationChange(event) {
  systemConfig.value.registrationEnabled = Boolean(event.detail.value)
}

function handleAppEnabledChange(event) {
  systemConfig.value.appEnabled = Boolean(event.detail.value)
}

function handleOpenClawToggle(event) {
  systemConfig.value.openclawEnabled = Boolean(event.detail.value)
}

async function submitNewUser() {
  if (!newUserForm.username.trim() || !newUserForm.password.trim()) {
    uni.showToast({
      title: '请填写用户名和初始密码',
      icon: 'none',
    })
    return
  }

  try {
    await adminStore.createUser({
      username: newUserForm.username,
      password: newUserForm.password,
      role: newUserForm.role,
      isEnabled: newUserForm.isEnabled,
    })
    Object.assign(newUserForm, {
      username: '',
      password: '',
      role: 'user',
      isEnabled: true,
    })
    uni.showToast({
      title: '用户已创建',
      icon: 'success',
    })
  } catch (error) {
    uni.showToast({
      title: error.message || '创建用户失败',
      icon: 'none',
    })
  }
}

async function toggleUserEnabled(user) {
  try {
    await adminStore.updateUser(user.id, {
      isEnabled: !user.isEnabled,
    })
    uni.showToast({
      title: user.isEnabled ? '用户已停用' : '用户已启用',
      icon: 'success',
    })
  } catch (error) {
    uni.showToast({
      title: error.message || '更新用户失败',
      icon: 'none',
    })
  }
}

async function toggleUserRole(user) {
  try {
    await adminStore.updateUser(user.id, {
      role: user.role === 'admin' ? 'user' : 'admin',
    })
    uni.showToast({
      title: '角色已更新',
      icon: 'success',
    })
  } catch (error) {
    uni.showToast({
      title: error.message || '角色更新失败',
      icon: 'none',
    })
  }
}

function removeUser(user) {
  uni.showModal({
    title: '删除确认',
    content: `确认删除用户 ${user.username} 吗？`,
    success: async (result) => {
      if (!result.confirm) {
        return
      }

      try {
        await adminStore.deleteUser(user.id)
        uni.showToast({
          title: '用户已删除',
          icon: 'success',
        })
      } catch (error) {
        uni.showToast({
          title: error.message || '删除用户失败',
          icon: 'none',
        })
      }
    },
  })
}

async function saveSystemConfig() {
  try {
    await adminStore.saveSystemConfig(systemConfig.value)
    uni.showToast({
      title: '系统配置已保存',
      icon: 'success',
    })
  } catch (error) {
    uni.showToast({
      title: error.message || '保存系统配置失败',
      icon: 'none',
    })
  }
}

async function refreshGatewayStatus() {
  try {
    await Promise.allSettled([
      adminStore.loadOpenClawStatus(),
      rosStore.loadStatus(),
      rosStore.loadTelemetrySummary(),
    ])
    uni.showToast({
      title: '接入状态已刷新',
      icon: 'success',
    })
  } catch (error) {
    uni.showToast({
      title: error.message || '刷新接入状态失败',
      icon: 'none',
    })
  }
}

async function handleRosPreset(preset) {
  activePreset.value = preset

  try {
    await rosStore.sendManualPreset({ preset })
    uni.showToast({
      title: 'ROS 控制已发送',
      icon: 'success',
    })
  } catch (error) {
    uni.showToast({
      title: error.message || 'ROS 控制发送失败',
      icon: 'none',
    })
  } finally {
    activePreset.value = ''
  }
}

function formatDate(value) {
  if (!value) {
    return '--'
  }

  return String(value).replace('T', ' ').slice(0, 19)
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
.panel-card {
  padding: 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 14rpx 38rpx rgba(20, 32, 51, 0.08);
}

.header-card {
  background: linear-gradient(135deg, #17324d, #205375 62%, #4e8ca5);
}

.header-title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  color: #ffffff;
}

.header-desc {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.88);
}

.section-switcher {
  display: flex;
  margin: 20rpx -8rpx 0;
  flex-wrap: wrap;
}

.section-button {
  width: calc(33.3333% - 16rpx);
  margin: 0 8rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.88);
  color: #445868;
}

.section-button.active {
  background: #205375;
  color: #ffffff;
}

.section-button::after,
.primary-button::after,
.inline-button::after,
.control-button::after {
  border: none;
}

.panel-card {
  margin-top: 4rpx;
}

.panel-title {
  display: block;
  margin-bottom: 18rpx;
  font-size: 32rpx;
  font-weight: 700;
  color: #17324d;
}

.sub-panel + .sub-panel {
  margin-top: 22rpx;
}

.sub-panel-title {
  display: block;
  margin-bottom: 14rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: #205375;
}

.create-form {
  padding: 24rpx;
  border-radius: 22rpx;
  background: #f4f8fb;
}

.field,
.picker,
.maintenance-input {
  width: 100%;
  margin-bottom: 16rpx;
  padding: 0 24rpx;
  box-sizing: border-box;
  border-radius: 18rpx;
  background: #ffffff;
  color: #17324d;
  font-size: 28rpx;
}

.field,
.picker {
  height: 88rpx;
  line-height: 88rpx;
}

.picker-value {
  line-height: 88rpx;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 10rpx 0 22rpx;
}

.switch-label {
  font-size: 26rpx;
  color: #3d5061;
}

.primary-button {
  border-radius: 999rpx;
  background: #205375;
  color: #ffffff;
}

.user-list {
  margin-top: 18rpx;
}

.user-card {
  margin-top: 16rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: #ffffff;
  box-shadow: 0 12rpx 30rpx rgba(20, 32, 51, 0.06);
}

.user-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10rpx;
}

.user-name {
  font-size: 30rpx;
  font-weight: 700;
  color: #17324d;
}

.user-tag,
.user-status {
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
}

.user-tag {
  background: #e3eef6;
  color: #205375;
}

.user-tag.admin {
  background: #f7d9ce;
  color: #8b2f20;
}

.user-status {
  background: #ddf1ea;
  color: #1c7c54;
}

.user-status.disabled {
  background: #f1e2df;
  color: #8b2f20;
}

.user-time {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #6a7b8b;
}

.user-actions,
.control-grid {
  display: flex;
  flex-wrap: wrap;
  margin: 16rpx -8rpx 0;
}

.inline-button,
.control-button {
  width: calc(50% - 16rpx);
  margin: 0 8rpx 14rpx;
  border-radius: 999rpx;
  background: #eff5f9;
  color: #17324d;
}

.inline-button.danger,
.control-button.danger {
  background: #f4d8d2;
  color: #8b2f20;
}

.maintenance-input {
  min-height: 180rpx;
  padding-top: 20rpx;
}

.status-grid {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -8rpx;
}

.status-item {
  width: calc(50% - 16rpx);
  margin: 0 8rpx 16rpx;
  padding: 22rpx;
  border-radius: 20rpx;
  background: #f7fafc;
  box-sizing: border-box;
}

.status-label {
  display: block;
  font-size: 22rpx;
  color: #6a7b8b;
}

.status-value {
  display: block;
  margin-top: 10rpx;
  font-size: 30rpx;
  font-weight: 700;
  color: #17324d;
}

.status-value.compact {
  font-size: 22rpx;
  line-height: 1.6;
}

.status-note {
  margin-top: 8rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f7fafc;
}

.status-note-text {
  font-size: 26rpx;
  line-height: 1.7;
  color: #314454;
}

@media screen and (max-width: 720px) {
  .section-button,
  .inline-button,
  .control-button,
  .status-item {
    width: calc(100% - 16rpx);
  }
}
</style>
