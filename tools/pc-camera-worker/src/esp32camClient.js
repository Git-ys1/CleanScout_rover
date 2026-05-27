import { parseJpegFrames } from './mjpegParser.js'

async function applyCameraControls(config) {
  if (config.cameraVFlip === null && config.cameraHMirror === null && config.cameraFrameSize === null) {
    return
  }

  const sourceUrl = new URL(config.cameraSourceUrl)
  const controlBaseUrl = new URL('/control', `${sourceUrl.protocol}//${sourceUrl.hostname}`)

  async function applyOne(varName, value) {
    if (value === null) {
      return
    }

    const controlUrl = new URL(controlBaseUrl)
    controlUrl.searchParams.set('var', varName)
    controlUrl.searchParams.set('val', String(value))

    const response = await fetch(controlUrl, {
      signal: AbortSignal.timeout(config.cameraConnectTimeoutMs),
    })

    if (!response.ok) {
      throw Object.assign(new Error(`ESP32-CAM control ${varName} returned HTTP ${response.status}`), {
        code: 'CAMERA_CONTROL_HTTP_ERROR',
      })
    }
  }

  await applyOne('hmirror', config.cameraHMirror)
  await applyOne('vflip', config.cameraVFlip)
  await applyOne('framesize', config.cameraFrameSize)
}

export async function* readEsp32CamFrames(config) {
  await applyCameraControls(config)

  const controller = new AbortController()
  const connectTimer = setTimeout(() => controller.abort(), config.cameraConnectTimeoutMs)

  let response

  try {
    response = await fetch(config.cameraSourceUrl, {
      signal: controller.signal,
    })
  } finally {
    clearTimeout(connectTimer)
  }

  if (!response.ok) {
    throw Object.assign(new Error(`ESP32-CAM stream returned HTTP ${response.status}`), {
      code: 'CAMERA_SOURCE_HTTP_ERROR',
    })
  }

  const contentType = String(response.headers.get('content-type') || '')

  if (!contentType.toLowerCase().includes('multipart') && !contentType.toLowerCase().includes('image')) {
    console.warn(`[pc-camera-worker] unexpected camera content-type=${contentType}`)
  }

  yield* parseJpegFrames(response.body, {
    maxFrameBytes: config.maxFrameBytes,
    readTimeoutMs: config.cameraReadTimeoutMs,
  })
}
