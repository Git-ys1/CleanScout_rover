import { computed, onUnmounted, ref } from 'vue'
import { buildOpenMvSnapshotUrl, requestOpenMvStatus } from '../api/integrations.js'

function getDefaultStatus() {
  return {
    enabled: false,
    status: 'disabled',
    mode: 'mjpeg',
    baseUrl: '',
    streamPath: '/',
    snapshotPath: '/snapshot',
    previewRefreshMs: 1200,
    message: 'OpenMV 预览尚未启用。',
  }
}

export function useOpenMvPreview(getToken) {
  const status = ref(getDefaultStatus())
  const previewTick = ref(Date.now())
  let previewTimer = null

  const snapshotUrl = computed(() => {
    const token = typeof getToken === 'function' ? getToken() : ''

    if (status.value.status !== 'healthy' || !token) {
      return ''
    }

    return buildOpenMvSnapshotUrl(token, previewTick.value)
  })

  async function loadStatus() {
    try {
      status.value = {
        ...status.value,
        ...(await requestOpenMvStatus()),
      }
      restartPreviewLoop()
      return status.value
    } catch (error) {
      status.value = {
        ...status.value,
        status: 'error',
        message: error.message || 'OpenMV 状态获取失败。',
      }
      stopPreviewLoop()
      return status.value
    }
  }

  function restartPreviewLoop() {
    stopPreviewLoop()

    if (status.value.status !== 'healthy') {
      return
    }

    previewTick.value = Date.now()
    previewTimer = setInterval(() => {
      previewTick.value = Date.now()
    }, status.value.previewRefreshMs || 1200)
  }

  function stopPreviewLoop() {
    if (previewTimer) {
      clearInterval(previewTimer)
      previewTimer = null
    }
  }

  function handlePreviewError() {
    stopPreviewLoop()
    status.value = {
      ...status.value,
      status: 'error',
      message: 'OpenMV 预览帧加载失败，请确认已连接 OpenMV WiFi 且 backend 可访问图传地址。',
    }
  }

  function reset() {
    stopPreviewLoop()
    status.value = getDefaultStatus()
    previewTick.value = Date.now()
  }

  onUnmounted(() => {
    stopPreviewLoop()
  })

  return {
    status,
    snapshotUrl,
    loadStatus,
    restartPreviewLoop,
    stopPreviewLoop,
    handlePreviewError,
    reset,
  }
}
