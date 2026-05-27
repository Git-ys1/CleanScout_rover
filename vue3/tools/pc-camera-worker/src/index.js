import { CloudCameraClient } from './cloudCameraClient.js'
import { loadConfig } from './config.js'
import { printDiagnostics } from './diagnostics.js'
import { openEsp32CamStream, readEsp32CamFrames } from './esp32camClient.js'

const MOCK_JPEG = Buffer.from(
  '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAX/xAAVEAEBAAAAAAAAAAAAAAAAAAAAAf/aAAwDAQACEAMQAAAB9A//xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/ASP/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/ASP/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAY/Al//xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//2gAMAwEAAgADAAAAEP/EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQMBAT8QE//EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQIBAT8QE//EABQQAQAAAAAAAAAAAAAAAAAAABD/2gAIAQEAAT8QE//Z',
  'base64'
)

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function calculateFps(frameTimes) {
  if (frameTimes.length < 2) {
    return 0
  }

  const durationMs = frameTimes[frameTimes.length - 1] - frameTimes[0]

  if (durationMs <= 0) {
    return 0
  }

  return Math.round(((frameTimes.length - 1) * 10000) / durationMs) / 10
}

async function* createMockFrames(config) {
  const intervalMs = Math.max(1, Math.floor(1000 / config.targetFps))

  while (true) {
    yield MOCK_JPEG
    await delay(intervalMs)
  }
}

async function runOnce(config) {
  const cloud = new CloudCameraClient(config)
  await cloud.connect()

  if (!config.mock && config.uplinkMode === 'raw-mjpeg') {
    await runRawMjpegTunnel(config, cloud)
    return
  }

  const frameSource = config.mock ? createMockFrames(config) : readEsp32CamFrames(config)
  const minFrameIntervalMs = Math.floor(1000 / config.targetFps)
  const frameTimes = []
  let lastSentAt = 0
  let seq = 0
  let lastLogAt = Date.now()

  try {
    for await (const frame of frameSource) {
      const now = Date.now()

      if (now - lastSentAt < minFrameIntervalMs) {
        continue
      }

      if (!cloud.sendFrame(frame)) {
        throw new Error('cloud websocket is not open')
      }

      lastSentAt = now
      seq += 1
      frameTimes.push(now)

      while (frameTimes.length > 30) {
        frameTimes.shift()
      }

      if (now - lastLogAt >= 5000) {
        const fps = calculateFps(frameTimes)
        cloud.heartbeat({
          fps,
          cameraReachable: true,
        })
        console.log(`[camera] seq=${seq} fps=${fps} bytes=${frame.length} cloud=ok source=${config.mock ? 'mock' : 'esp32-cam'}`)
        lastLogAt = now
      }
    }
  } finally {
    cloud.close()
  }
}

async function runRawMjpegTunnel(config, cloud) {
  const stream = await openEsp32CamStream(config)
  const contentType = stream.contentType || 'multipart/x-mixed-replace'
  const chunkTimes = []
  let seq = 0
  let lastBytes = 0
  let lastLogAt = Date.now()
  let lastChunkAt = Date.now()

  cloud.startRawStream({
    contentType,
  })

  try {
    for await (const chunkLike of stream.body) {
      const chunk = Buffer.isBuffer(chunkLike) ? chunkLike : Buffer.from(chunkLike)
      const now = Date.now()

      if (!cloud.sendFrame(chunk)) {
        throw new Error(cloud.lastError || 'cloud websocket is not open')
      }

      seq += 1
      lastBytes = chunk.length
      lastChunkAt = now
      chunkTimes.push(now)

      while (chunkTimes.length > 120) {
        chunkTimes.shift()
      }

      if (now - lastLogAt >= 5000) {
        const chunkRate = calculateFps(chunkTimes)
        cloud.heartbeat({
          fps: chunkRate,
          cameraReachable: true,
        })
        console.log(`[camera-raw] chunks=${seq} chunkRate=${chunkRate}/s bytes=${lastBytes} cloud=ok contentType="${contentType}"`)
        lastLogAt = now
      }
    }
  } finally {
    cloud.heartbeat({
      fps: calculateFps(chunkTimes),
      lastChunkAgeMs: Date.now() - lastChunkAt,
      cameraReachable: false,
    })
    cloud.close()
  }
}

async function main() {
  const config = loadConfig()

  if (!config.enabled) {
    console.log('[pc-camera-worker] CAMERA_WORKER_ENABLED=false, exit')
    return
  }

  printDiagnostics(config)

  while (true) {
    try {
      await runOnce(config)
    } catch (error) {
      console.warn(`[pc-camera-worker] loop failed: ${error.code || 'CAMERA_WORKER_ERROR'} ${error.message || error}`)
    }

    await delay(config.reconnectDelayMs)
    console.log('[pc-camera-worker] reconnecting camera/cloud loop')
  }
}

main().catch((error) => {
  console.error(`[pc-camera-worker] fatal: ${error.message || error}`)
  process.exit(1)
})
