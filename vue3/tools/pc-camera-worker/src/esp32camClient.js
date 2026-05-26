import { parseJpegFrames } from './mjpegParser.js'

export async function* readEsp32CamFrames(config) {
  const response = await fetch(config.cameraSourceUrl, {
    signal: AbortSignal.timeout(config.cameraConnectTimeoutMs),
  })

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
  })
}
