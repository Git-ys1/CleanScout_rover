import { computed, onBeforeUnmount, ref } from 'vue'

const DEFAULT_RECORD_MAX_MS = 60000

function pickSupportedMimeType() {
  if (typeof MediaRecorder === 'undefined' || typeof MediaRecorder.isTypeSupported !== 'function') {
    return ''
  }

  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/ogg',
  ]

  return candidates.find((candidate) => MediaRecorder.isTypeSupported(candidate)) || ''
}

export function useSpeechRecorder() {
  const status = ref('idle')
  const durationMs = ref(0)
  const errorMessage = ref('')

  let startedAt = 0
  let timerId = null
  let h5Stream = null
  let h5Recorder = null
  let h5Chunks = []
  let h5StopResolver = null
  let h5StopRejecter = null
  let mpRecorder = null
  let mpStopResolver = null
  let mpStopRejecter = null
  let lastPlatform = ''

  const isH5Supported = computed(() => {
    return Boolean(
      typeof navigator !== 'undefined' &&
      navigator.mediaDevices?.getUserMedia &&
      typeof MediaRecorder !== 'undefined'
    )
  })

  const isMiniProgramSupported = computed(() => typeof uni?.getRecorderManager === 'function')
  const isSupported = computed(() => isH5Supported.value || isMiniProgramSupported.value)

  function startTimer() {
    startedAt = Date.now()
    durationMs.value = 0
    clearTimer()
    timerId = setInterval(() => {
      durationMs.value = Date.now() - startedAt
    }, 200)
  }

  function clearTimer() {
    if (timerId) {
      clearInterval(timerId)
      timerId = null
    }
  }

  function cleanupH5Stream() {
    if (h5Stream?.getTracks) {
      h5Stream.getTracks().forEach((track) => track.stop())
    }

    h5Stream = null
    h5Recorder = null
    h5Chunks = []
  }

  function resetState(nextStatus = 'idle') {
    clearTimer()
    status.value = nextStatus
  }

  function ensureMiniProgramRecorder() {
    if (mpRecorder || typeof uni?.getRecorderManager !== 'function') {
      return mpRecorder
    }

    mpRecorder = uni.getRecorderManager()

    mpRecorder.onStop((result) => {
      const elapsedMs = durationMs.value
      resetState('idle')

      const resolve = mpStopResolver
      mpStopResolver = null
      mpStopRejecter = null

      if (resolve) {
        resolve({
          platform: 'mp-weixin',
          tempFilePath: result.tempFilePath,
          fileName: `recording-${Date.now()}.${result.fileType || 'mp3'}`,
          mimeType: result.fileType === 'aac' ? 'audio/aac' : 'audio/mpeg',
          durationMs: elapsedMs,
        })
      }
    })

    mpRecorder.onError((error) => {
      const reject = mpStopRejecter
      const message = error?.errMsg || '小程序录音失败'

      errorMessage.value = message
      resetState('error')
      mpStopResolver = null
      mpStopRejecter = null

      if (reject) {
        reject(new Error(message))
      }
    })

    return mpRecorder
  }

  async function startH5Recording() {
    const mimeType = pickSupportedMimeType()
    h5Stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    h5Chunks = []
    h5Recorder = mimeType ? new MediaRecorder(h5Stream, { mimeType }) : new MediaRecorder(h5Stream)

    h5Recorder.ondataavailable = (event) => {
      if (event.data?.size) {
        h5Chunks.push(event.data)
      }
    }

    h5Recorder.onstop = () => {
      const elapsedMs = durationMs.value
      const blob = new Blob(h5Chunks, {
        type: h5Recorder?.mimeType || mimeType || 'audio/webm',
      })
      const extension = blob.type.includes('ogg') ? 'ogg' : 'webm'
      const file = new File([blob], `recording-${Date.now()}.${extension}`, {
        type: blob.type || 'audio/webm',
      })

      cleanupH5Stream()
      resetState('idle')

      const resolve = h5StopResolver
      h5StopResolver = null
      h5StopRejecter = null

      if (resolve) {
        resolve({
          platform: 'h5',
          file,
          fileName: file.name,
          mimeType: file.type,
          durationMs: elapsedMs,
        })
      }
    }

    h5Recorder.onerror = (event) => {
      const reject = h5StopRejecter
      const message = event?.error?.message || '浏览器录音失败'

      errorMessage.value = message
      cleanupH5Stream()
      resetState('error')
      h5StopResolver = null
      h5StopRejecter = null

      if (reject) {
        reject(new Error(message))
      }
    }

    h5Recorder.start()
  }

  async function startMiniProgramRecording() {
    const recorder = ensureMiniProgramRecorder()

    if (!recorder) {
      throw new Error('当前平台不支持录音')
    }

    recorder.start({
      duration: DEFAULT_RECORD_MAX_MS,
      sampleRate: 16000,
      numberOfChannels: 1,
      encodeBitRate: 96000,
      format: 'mp3',
    })
  }

  async function startRecording() {
    if (status.value === 'recording') {
      return
    }

    if (!isSupported.value) {
      throw new Error('当前平台不支持语音录入')
    }

    errorMessage.value = ''
    status.value = 'recording'
    startTimer()

    try {
      if (isH5Supported.value) {
        lastPlatform = 'h5'
        await startH5Recording()
        return
      }

      lastPlatform = 'mp-weixin'
      await startMiniProgramRecording()
    } catch (error) {
      errorMessage.value = error.message || '录音启动失败'
      resetState('error')
      throw error
    }
  }

  function stopRecording() {
    if (status.value !== 'recording') {
      return Promise.reject(new Error('当前不在录音中'))
    }

    if (lastPlatform === 'h5' && h5Recorder) {
      return new Promise((resolve, reject) => {
        h5StopResolver = resolve
        h5StopRejecter = reject
        h5Recorder.stop()
      })
    }

    if (lastPlatform === 'mp-weixin') {
      const recorder = ensureMiniProgramRecorder()

      return new Promise((resolve, reject) => {
        mpStopResolver = resolve
        mpStopRejecter = reject
        recorder.stop()
      })
    }

    resetState('error')
    return Promise.reject(new Error('当前录音平台不可用'))
  }

  function cancelRecording() {
    if (status.value !== 'recording') {
      resetState('idle')
      return
    }

    if (lastPlatform === 'h5' && h5Recorder) {
      h5Recorder.stop()
      return
    }

    if (lastPlatform === 'mp-weixin') {
      const recorder = ensureMiniProgramRecorder()
      recorder.stop()
      return
    }

    resetState('idle')
  }

  onBeforeUnmount(() => {
    clearTimer()
    cleanupH5Stream()
  })

  return {
    status,
    durationMs,
    errorMessage,
    isSupported,
    startRecording,
    stopRecording,
    cancelRecording,
  }
}
