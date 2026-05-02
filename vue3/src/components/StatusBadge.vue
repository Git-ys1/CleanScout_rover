<template>
  <text class="status-badge" :class="resolved.tone">{{ resolved.text }}</text>
</template>

<script setup>
import { computed } from 'vue'
import { getStatusMeta } from '../utils/status-display.js'

const props = defineProps({
  value: {
    type: [String, Number, Boolean],
    default: '',
  },
  fallbackText: {
    type: String,
    default: '--',
  },
})

const resolved = computed(() => getStatusMeta(props.value, props.fallbackText))
</script>

<style>
.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40rpx;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  line-height: 1.2;
  box-sizing: border-box;
}

.status-badge.success {
  background: #ddf1ea;
  color: #1c7c54;
}

.status-badge.warn {
  background: #f8ead1;
  color: #9a6510;
}

.status-badge.danger {
  background: #f4d8d2;
  color: #8b2f20;
}

.status-badge.brand {
  background: #d9eef2;
  color: #205375;
}

.status-badge.neutral {
  background: #e7edf2;
  color: #516274;
}
</style>
