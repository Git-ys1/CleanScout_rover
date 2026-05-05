<script>
export default {
  onLaunch() {
    console.log('V line control shell launched')
  },
  onShow() {
    console.log('V line control shell visible')
  },
  onHide() {
    console.log('V line control shell hidden')
  },
}
</script>

<style>
page {
  --v-color-primary: #1f5263;
  --v-color-primary-deep: #17384a;
  --v-color-primary-soft: #d9e9ec;
  --v-color-accent: #d58a3a;
  --v-color-coral: #c85d4a;
  --v-color-success: #28795a;
  --v-color-warning: #b87320;
  --v-color-danger: #a64033;
  --v-color-info: #4d6f83;
  --v-text-main: #142433;
  --v-text-secondary: #33495c;
  --v-text-muted: #6c7f8f;
  --v-border: #d9e3ea;
  --v-bg-page: #edf3f6;
  --v-bg-page-deep: #dfe9ee;
  --v-bg-card: rgba(255, 255, 255, 0.94);
  --v-bg-panel: rgba(246, 250, 252, 0.92);
  --v-bg-elevated: #ffffff;
  --v-radius-md: 22rpx;
  --v-radius-lg: 32rpx;
  --v-radius-xl: 44rpx;
  --v-shadow-card: 0 18rpx 46rpx rgba(24, 56, 72, 0.08);
  --v-shadow-float: 0 26rpx 70rpx rgba(24, 56, 72, 0.14);
  min-height: 100vh;
  background:
    radial-gradient(circle at 18% -4%, rgba(95, 152, 164, 0.18), transparent 34%),
    linear-gradient(180deg, #f7fbfc 0%, var(--v-bg-page, #edf3f6) 48%, #e7f0f4 100%);
  color: var(--v-text-main, #142433);
  font-family:
    'HarmonyOS Sans SC',
    'MiSans',
    'PingFang SC',
    'Microsoft YaHei',
    sans-serif;
}

button {
  transition: transform 0.18s ease, opacity 0.18s ease, box-shadow 0.18s ease;
}

button:active {
  transform: scale(0.985);
}

input,
textarea {
  color: var(--v-text-main, #142433);
}

.v-page {
  min-height: 100vh;
  color: var(--v-text-main);
  background:
    radial-gradient(circle at 16% 0%, rgba(95, 152, 164, 0.18), transparent 34%),
    linear-gradient(180deg, #f7fbfc 0%, var(--v-bg-page) 42%, #e8f0f4 100%);
}

.v-card {
  border: 1rpx solid rgba(255, 255, 255, 0.72);
  border-radius: var(--v-radius-lg);
  background: var(--v-bg-card);
  box-shadow: var(--v-shadow-card);
  backdrop-filter: blur(18rpx);
}

.v-panel {
  border-radius: var(--v-radius-md);
  background: var(--v-bg-panel);
}

.v-pressable {
  transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
}

.v-pressable:active {
  transform: scale(0.985);
  box-shadow: 0 10rpx 26rpx rgba(24, 56, 72, 0.12);
}

.v-fade-in {
  animation: vFadeIn 0.42s ease both;
}

@keyframes vFadeIn {
  from {
    opacity: 0;
    transform: translateY(12rpx);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
