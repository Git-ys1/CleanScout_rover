<template>
  <view class="detail-page">
    <view class="hero-card">
      <text class="hero-title">OpenMV 前视详情</text>
      <text class="hero-desc">
        当前页面只承载前视画面大图和图传状态，不承载设备控制。
      </text>
      <view class="hero-tags">
        <StatusBadge :value="openmvStatus.status" />
        <StatusBadge :value="openmvStatus.mode" />
      </view>
    </view>

    <view class="frame-card">
      <image v-if="openmvSnapshotUrl" class="detail-frame" :src="openmvSnapshotUrl" mode="aspectFit" @error="handlePreviewError" />
      <view v-else class="empty-panel">
        <text class="empty-text">{{ openmvStatus.message }}</text>
      </view>
    </view>

    <view class="meta-grid">
      <view class="meta-card">
        <text class="meta-label">图传地址</text>
        <text class="meta-value compact">{{ openmvStatus.baseUrl || '--' }}</text>
      </view>
      <view class="meta-card">
        <text class="meta-label">刷新周期</text>
        <text class="meta-value">{{ openmvStatus.previewRefreshMs || '--' }} ms</text>
      </view>
      <view class="meta-card">
        <text class="meta-label">Stream 路径</text>
        <text class="meta-value compact">{{ openmvStatus.streamPath || '--' }}</text>
      </view>
      <view class="meta-card">
        <text class="meta-label">Snapshot 路径</text>
        <text class="meta-value compact">{{ openmvStatus.snapshotPath || '--' }}</text>
      </view>
      <view class="meta-card">
        <text class="meta-label">最近状态</text>
        <text class="meta-value compact">{{ openmvStatus.message }}</text>
      </view>
      <view class="meta-card">
        <text class="meta-label">最近更新时间</text>
        <text class="meta-value compact">{{ formatDate(openmvStatus.lastProbeAt) }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onHide, onShow } from '@dcloudio/uni-app'
import { storeToRefs } from 'pinia'
import StatusBadge from '../../components/StatusBadge.vue'
import { useOpenMvPreview } from '../../composables/useOpenMvPreview.js'
import { useAuthStore } from '../../stores/auth.js'
import { ensureLoggedIn } from '../../utils/auth-guard.js'

const authStore = useAuthStore()
const { token } = storeToRefs(authStore)
const {
  status: openmvStatus,
  snapshotUrl: openmvSnapshotUrl,
  loadStatus: loadOpenMvStatus,
  stopPreviewLoop,
  handlePreviewError,
} = useOpenMvPreview(() => token.value)

onShow(async () => {
  const allowed = await ensureLoggedIn()

  if (!allowed) {
    return
  }

  await Promise.allSettled([
    authStore.fetchMe(),
    loadOpenMvStatus(),
  ])
})

onHide(() => {
  stopPreviewLoop()
})

function formatDate(value) {
  if (!value) {
    return '--'
  }

  return String(value).replace('T', ' ').slice(0, 19)
}
</script>

<style>
.detail-page {
  min-height: 100vh;
  padding: 28rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #f4f8fb 0%, #e6edf4 100%);
}

.hero-card,
.frame-card,
.meta-card {
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 14rpx 38rpx rgba(20, 32, 51, 0.08);
}

.hero-card {
  padding: 28rpx;
}

.hero-title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  color: #17324d;
}

.hero-desc {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #516274;
}

.hero-tags {
  display: flex;
  gap: 10rpx;
  margin-top: 18rpx;
}

.frame-card {
  overflow: hidden;
  margin-top: 22rpx;
  min-height: 560rpx;
}

.detail-frame {
  width: 100%;
  height: 560rpx;
  display: block;
  background: #0f1720;
}

.empty-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 560rpx;
  padding: 36rpx;
  box-sizing: border-box;
}

.empty-text {
  font-size: 26rpx;
  line-height: 1.8;
  text-align: center;
  color: #516274;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 22rpx;
}

.meta-card {
  padding: 22rpx;
}

.meta-label {
  display: block;
  font-size: 22rpx;
  color: #6a7b8b;
}

.meta-value {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: #17324d;
}

.meta-value.compact {
  font-size: 22rpx;
  line-height: 1.7;
}
</style>
