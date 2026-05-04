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
  padding: 7rpx 16rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  line-height: 1.2;
  box-sizing: border-box;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.status-badge::before {
  content: '';
  width: 10rpx;
  height: 10rpx;
  margin-right: 8rpx;
  border-radius: 999rpx;
  background: currentColor;
  opacity: 0.72;
}

.status-badge.success {
  background: rgba(40, 121, 90, 0.12);
  color: var(--v-color-success, #28795a);
}

.status-badge.warn {
  background: rgba(213, 138, 58, 0.14);
  color: var(--v-color-warning, #b87320);
}

.status-badge.danger {
  background: rgba(200, 93, 74, 0.14);
  color: var(--v-color-danger, #a64033);
}

.status-badge.brand {
  background: rgba(31, 82, 99, 0.13);
  color: var(--v-color-primary, #1f5263);
}

.status-badge.neutral {
  background: rgba(77, 111, 131, 0.12);
  color: var(--v-color-info, #4d6f83);
}
</style>
