import { computed, onUnmounted, ref } from 'vue'
import { buildOpenMvSnapshotUrl, buildOpenMvStreamUrl, requestOpenMvStatus } from '../api/integrations.js'

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
  const streamTick = ref(Date.now())
  const streamFailed = ref(false)
  const previewActive = ref(true)
  let previewTimer = null

  const useStream = computed(() => {
    return previewActive.value && status.value.status === 'healthy' && status.value.mode === 'mjpeg-stream-relay' && !streamFailed.value
  })

  const streamUrl = computed(() => {
    const token = typeof getToken === 'function' ? getToken() : ''

    if (!useStream.value || !token) {
      return ''
    }

    return buildOpenMvStreamUrl(token, streamTick.value)
  })

  const snapshotUrl = computed(() => {
    const token = typeof getToken === 'function' ? getToken() : ''

    if (!previewActive.value || status.value.status !== 'healthy' || !token) {
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
      streamFailed.value = false
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
    previewActive.value = true

    if (status.value.status !== 'healthy') {
      return
    }

    if (status.value.mode === 'mjpeg-stream-relay' && !streamFailed.value) {
      streamTick.value = Date.now()
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
    previewActive.value = false
  }

  function handlePreviewError() {
    if (status.value.mode === 'mjpeg-stream-relay' && !streamFailed.value) {
      streamFailed.value = true
      status.value = {
        ...status.value,
        message: 'MJPEG stream 加载失败，已切换到 snapshot 兜底预览。',
      }
      restartPreviewLoop()
      return
    }

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
    streamTick.value = Date.now()
    streamFailed.value = false
    previewActive.value = true
  }

  onUnmounted(() => {
    stopPreviewLoop()
  })

  return {
    status,
    snapshotUrl,
    streamUrl,
    useStream,
    loadStatus,
    restartPreviewLoop,
    stopPreviewLoop,
    handlePreviewError,
    reset,
  }
}
