<template>
  <view class="admin-page">
    <view class="header-card">
      <text class="header-title">管理后台</text>
      <text class="header-desc">
        本轮管理员页收口为后台管理职责：用户管理、系统开关、接入状态只读监看。设备控制已迁到首页快捷控制台。
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
          <view class="picker-value">角色：{{ roleLabelMap[newUserForm.role] }}</view>
        </picker>
        <label class="switch-row">
          <text class="switch-label">新增后立即启用</text>
          <switch :checked="newUserForm.isEnabled" @change="handleCreateEnabledChange" color="#205375" />
        </label>
        <button class="primary-button" :loading="loadingStates.submitUser" @tap="submitNewUser">新增用户</button>
      </view>

      <view class="user-list">
        <view class="user-card" v-for="user in users" :key="user.id">
          <view class="user-head">
            <text class="user-name">{{ user.username }}</text>
            <view class="user-tags">
              <StatusBadge :value="user.role" />
              <StatusBadge :value="user.isEnabled ? 'online' : 'offline'" />
            </view>
          </view>
          <text class="user-time">创建时间：{{ formatDate(user.createdAt) }}</text>
          <view class="user-actions">
            <button class="inline-button" @tap="toggleUserEnabled(user)">
              {{ user.isEnabled ? '停用' : '启用' }}
            </button>
            <button class="inline-button" @tap="toggleUserRole(user)">
              改为{{ user.role === 'admin' ? '普通用户' : '管理员' }}
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
      <text class="panel-title">接入状态</text>

      <view class="sub-panel">
        <text class="sub-panel-title">OpenClaw 接入状态</text>
        <view class="status-grid">
          <view class="status-item">
            <text class="status-label">当前链路</text>
            <StatusBadge :value="openclawStatus.activeTransport" />
          </view>
          <view class="status-item">
            <text class="status-label">链路状态</text>
            <StatusBadge :value="openclawStatus.status" />
          </view>
          <view class="status-item">
            <text class="status-label">接口模式</text>
            <StatusBadge :value="openclawStatus.apiMode" />
          </view>
          <view class="status-item">
            <text class="status-label">目标模型</text>
            <text class="status-value compact">{{ openclawStatus.model }}</text>
          </view>
          <view class="status-item wide">
            <text class="status-label">最近探测</text>
            <text class="status-value compact">{{ formatDate(openclawStatus.lastProbeAt) }}</text>
          </view>
          <view class="status-item wide">
            <text class="status-label">状态说明</text>
            <text class="status-value compact">{{ openclawStatus.message }}</text>
          </view>
        </view>
      </view>

      <view class="sub-panel">
        <text class="sub-panel-title">ROS 接入状态</text>
        <view class="status-grid">
          <view class="status-item">
            <text class="status-label">当前链路</text>
            <StatusBadge :value="rosStatus.transport" />
          </view>
          <view class="status-item">
            <text class="status-label">连接状态</text>
            <StatusBadge :value="rosStatus.connected ? 'connected' : 'disconnected'" />
          </view>
          <view class="status-item">
            <text class="status-label">边缘在线</text>
            <StatusBadge :value="rosStatus.edgeRelayConnected ? 'online' : 'offline'" />
          </view>
          <view class="status-item">
            <text class="status-label">设备 ID</text>
            <text class="status-value compact">{{ rosStatus.edgeDeviceId || '--' }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">最近心跳</text>
            <text class="status-value compact">{{ formatDate(rosStatus.lastHeartbeatAt) }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">最近遥测</text>
            <text class="status-value compact">{{ formatDate(rosStatus.lastTelemetryAt) }}</text>
          </view>
          <view class="status-item">
            <text class="status-label">odom</text>
            <StatusBadge :value="telemetrySummary.odomAvailable ? 'available' : 'missing'" />
          </view>
          <view class="status-item">
            <text class="status-label">imu</text>
            <StatusBadge :value="telemetrySummary.imuAvailable ? 'available' : 'missing'" />
          </view>
          <view class="status-item">
            <text class="status-label">scan</text>
            <StatusBadge :value="telemetrySummary.scanAvailable ? 'available' : 'missing'" />
          </view>
          <view class="status-item">
            <text class="status-label">最近错误</text>
            <text class="status-value compact">{{ rosStatus.lastRelayError || rosStatus.lastError || '--' }}</text>
          </view>
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
import { reactive } from 'vue'
import { storeToRefs } from 'pinia'
import { onShow } from '@dcloudio/uni-app'
import StatusBadge from '../../components/StatusBadge.vue'
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
  loadingStates: rosLoadingStates,
} = storeToRefs(rosStore)

const sections = [
  { label: '用户管理', value: 'users' },
  { label: '系统开关', value: 'system' },
  { label: '接入状态', value: 'gateway' },
]

const roleOptions = ['user', 'admin']
const roleLabelMap = {
  user: '普通用户',
  admin: '管理员',
}

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
.inline-button::after {
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

.user-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.user-name {
  font-size: 30rpx;
  font-weight: 700;
  color: #17324d;
}

.user-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  justify-content: flex-end;
}

.user-time {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #6a7b8b;
}

.user-actions {
  display: flex;
  flex-wrap: wrap;
  margin: 16rpx -8rpx 0;
}

.inline-button {
  width: calc(33.3333% - 16rpx);
  margin: 0 8rpx 14rpx;
  border-radius: 999rpx;
  background: #eff5f9;
  color: #17324d;
}

.inline-button.danger {
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

.status-item.wide {
  width: calc(100% - 16rpx);
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

@media screen and (max-width: 720px) {
  .section-button,
  .inline-button,
  .status-item {
    width: calc(100% - 16rpx);
  }
}
</style>
