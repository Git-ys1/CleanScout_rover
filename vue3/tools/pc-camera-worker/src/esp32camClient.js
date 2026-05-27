import { parseJpegFrames } from './mjpegParser.js'

export async function openEsp32CamStream(config) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), config.cameraConnectTimeoutMs)

  let response

  try {
    response = await fetch(config.cameraSourceUrl, {
      signal: controller.signal,
    })
  } finally {
    clearTimeout(timeout)
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

  if (!response.body) {
    throw Object.assign(new Error('ESP32-CAM stream response has no body'), {
      code: 'CAMERA_SOURCE_EMPTY_BODY',
    })
  }

  return {
    contentType,
    body: response.body,
  }
}

export async function* readEsp32CamRawChunks(config) {
  const stream = await openEsp32CamStream(config)

  for await (const chunk of stream.body) {
    yield Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)
  }
}

export async function* readEsp32CamFrames(config) {
  const stream = await openEsp32CamStream(config)

  yield* parseJpegFrames(stream.body, {
    maxFrameBytes: config.maxFrameBytes,
  })
}
