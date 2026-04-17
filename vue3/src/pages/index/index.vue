<template>
  <view class="shell-page">
    <view class="hero">
      <text class="eyebrow">V-1.0.0 / Freeze Baseline</text>
      <text class="title">V Line Control Shell</text>
      <text class="subtitle">
        This screen freezes project scope, system boundaries, and planned entry points before business development starts.
      </text>
    </view>

    <view class="status-panel">
      <view class="status-item" v-for="item in statusItems" :key="item.label">
        <text class="status-label">{{ item.label }}</text>
        <text class="status-value">{{ item.value }}</text>
      </view>
    </view>

    <view class="section-header">
      <text class="section-title">Phase One Shell Areas</text>
      <text class="section-hint">Only responsibilities are frozen in V-1.0.0</text>
    </view>

    <view class="card-grid">
      <view class="card" v-for="card in cards" :key="card.title">
        <text class="card-tag">{{ card.tag }}</text>
        <text class="card-title">{{ card.title }}</text>
        <text class="card-desc">{{ card.description }}</text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      statusItems: [
        { label: 'Device Status', value: 'Waiting for Raspberry Pi link' },
        { label: 'Task Status', value: 'Waiting for task model freeze' },
        { label: 'Connection State', value: 'No transport bound yet' },
        { label: 'Recent Message', value: 'Placeholder shell only' },
      ],
      cards: [
        {
          tag: '01',
          title: 'Device Home',
          description: 'Online state, task state, connection state, and recent message summary.',
        },
        {
          tag: '02',
          title: 'Conversation Control',
          description: 'Natural language input, device replies, and the base chat flow.',
        },
        {
          tag: '03',
          title: 'Admin Control',
          description: 'Direct commands, manual control, debug actions, and emergency stop.',
        },
        {
          tag: '04',
          title: 'State / Logs',
          description: 'Status feedback, execution logs, and key event visibility.',
        },
      ],
    }
  },
}
</script>

<style>
.shell-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding: 48rpx 32rpx 72rpx;
  box-sizing: border-box;
}

.hero {
  padding: 40rpx 36rpx;
  border-radius: 32rpx;
  background: linear-gradient(135deg, #102a43, #1f4f7a 60%, #4fb0c6);
  box-shadow: 0 24rpx 60rpx rgba(16, 42, 67, 0.18);
}

.eyebrow {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.72);
  letter-spacing: 4rpx;
}

.title {
  display: flex;
  margin-top: 20rpx;
  font-size: 52rpx;
  font-weight: 600;
  line-height: 1.2;
  color: #ffffff;
}

.subtitle {
  margin-top: 20rpx;
  font-size: 28rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.84);
}

.status-panel {
  display: flex;
  flex-wrap: wrap;
  margin: 28rpx -10rpx 0;
}

.status-item {
  display: flex;
  flex-direction: column;
  width: calc(50% - 20rpx);
  margin: 0 10rpx 20rpx;
  padding: 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 16rpx 40rpx rgba(20, 32, 51, 0.08);
  box-sizing: border-box;
}

.status-label {
  font-size: 24rpx;
  color: #52606d;
}

.status-value {
  margin-top: 12rpx;
  font-size: 30rpx;
  font-weight: 600;
  color: #102a43;
}

.section-header {
  display: flex;
  flex-direction: column;
  margin-top: 36rpx;
}

.section-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #102a43;
}

.section-hint {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #52606d;
}

.card-grid {
  display: flex;
  flex-wrap: wrap;
  margin: 20rpx -10rpx 0;
}

.card {
  display: flex;
  flex-direction: column;
  width: calc(50% - 20rpx);
  min-height: 220rpx;
  margin: 0 10rpx 20rpx;
  padding: 28rpx;
  border: 2rpx solid rgba(16, 42, 67, 0.08);
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 16rpx 36rpx rgba(20, 32, 51, 0.06);
  box-sizing: border-box;
}

.card-tag {
  font-size: 22rpx;
  font-weight: 600;
  color: #1f4f7a;
}

.card-title {
  margin-top: 18rpx;
  font-size: 32rpx;
  font-weight: 600;
  color: #102a43;
}

.card-desc {
  margin-top: 16rpx;
  font-size: 26rpx;
  line-height: 1.7;
  color: #52606d;
}

@media screen and (max-width: 640px) {
  .status-panel,
  .card-grid {
    display: block;
    margin-left: 0;
    margin-right: 0;
  }

  .status-item,
  .card {
    width: auto;
    margin-left: 0;
    margin-right: 0;
  }
}
</style>
