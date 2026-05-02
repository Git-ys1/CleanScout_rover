function parseBoolean(value) {
  return /^(1|true|yes|on)$/i.test(String(value || '').trim())
}

function normalizeBaseUrl(value) {
  const normalized = String(value || 'http://192.168.4.1:8080').trim()

  return normalized.replace(/\/+$/, '')
}

function normalizeMode(value) {
  return String(value || 'mjpeg').trim().toLowerCase() === 'snapshot' ? 'snapshot' : 'mjpeg'
}

function normalizePath(value, fallback) {
  const normalized = String(value || fallback).trim() || fallback

  return normalized.startsWith('/') ? normalized : `/${normalized}`
}

function parseTimeout(value) {
  const timeout = Number(value || 5000)

  if (!Number.isFinite(timeout) || timeout <= 0) {
    return 5000
  }

  return timeout
}

function parseRefreshMs(value) {
  const refreshMs = Number(value || 1200)

  if (!Number.isFinite(refreshMs) || refreshMs < 300) {
    return 1200
  }

  return refreshMs
}

function buildAbsoluteUrl(baseUrl, path) {
  return new URL(path, `${baseUrl}/`).toString()
}

function findMarker(buffer, marker, fromIndex = 0) {
  for (let index = fromIndex; index <= buffer.length - marker.length; index += 1) {
    let matched = true

    for (let markerIndex = 0; markerIndex < marker.length; markerIndex += 1) {
      if (buffer[index + markerIndex] !== marker[markerIndex]) {
        matched = false
        break
      }
    }

    if (matched) {
      return index
    }
  }

  return -1
}

function createOpenMvError(message, code = 'OPENMV_REQUEST_FAILED', status = 502) {
  const error = new Error(message)
  error.code = code
  error.status = status
  return error
}

async function fetchOpenMv(url, timeoutMs) {
  const response = await fetch(url, {
    signal: AbortSignal.timeout(timeoutMs),
  })

  if (!response.ok) {
    throw createOpenMvError(`OpenMV request failed with status ${response.status}`, 'OPENMV_HTTP_ERROR', 502)
  }

  return response
}

async function readResponseAsBuffer(response) {
  const arrayBuffer = await response.arrayBuffer()
  return Buffer.from(arrayBuffer)
}

async function readFirstJpegFrame(response) {
  const reader = response.body?.getReader?.()

  if (!reader) {
    return readResponseAsBuffer(response)
  }

  const jpegStart = Buffer.from([0xff, 0xd8])
  const jpegEnd = Buffer.from([0xff, 0xd9])
  let buffer = Buffer.alloc(0)
  let startIndex = -1

  while (true) {
    const { done, value } = await reader.read()

    if (done) {
      break
    }

    const chunk = Buffer.from(value)
    buffer = Buffer.concat([buffer, chunk])

    if (startIndex < 0) {
      startIndex = findMarker(buffer, jpegStart)
    }

    if (startIndex >= 0) {
      const endIndex = findMarker(buffer, jpegEnd, startIndex + 2)

      if (endIndex >= 0) {
        await reader.cancel()
        return buffer.subarray(startIndex, endIndex + jpegEnd.length)
      }
    }

    if (buffer.length > 2 * 1024 * 1024) {
      throw createOpenMvError('OpenMV MJPEG stream did not yield a JPEG frame within 2MB.', 'OPENMV_FRAME_NOT_FOUND', 504)
    }
  }

  throw createOpenMvError('OpenMV MJPEG stream ended before a JPEG frame was received.', 'OPENMV_FRAME_NOT_FOUND', 504)
}

export function getOpenMvRuntimeConfig() {
  const enabled = parseBoolean(process.env.OPENMV_ENABLED)
  const baseUrl = normalizeBaseUrl(process.env.OPENMV_BASE_URL)
  const mode = normalizeMode(process.env.OPENMV_MODE)
  const streamPath = normalizePath(process.env.OPENMV_STREAM_PATH, '/')
  const snapshotPath = normalizePath(process.env.OPENMV_SNAPSHOT_PATH, '/snapshot')
  const timeoutMs = parseTimeout(process.env.OPENMV_REQUEST_TIMEOUT_MS)
  const refreshMs = parseRefreshMs(process.env.OPENMV_PREVIEW_REFRESH_MS)

  return {
    enabled,
    baseUrl,
    mode,
    streamPath,
    snapshotPath,
    timeoutMs,
    refreshMs,
    streamUrl: buildAbsoluteUrl(baseUrl, streamPath),
    snapshotUrl: buildAbsoluteUrl(baseUrl, snapshotPath),
  }
}

export async function probeOpenMv(config) {
  const targetUrl = config.mode === 'snapshot' ? config.snapshotUrl : config.streamUrl
  const response = await fetchOpenMv(targetUrl, config.timeoutMs)
  const contentType = String(response.headers.get('content-type') || '').trim()

  if (response.body?.cancel) {
    await response.body.cancel()
  }

  return {
    contentType,
    targetUrl,
  }
}

export async function fetchOpenMvSnapshotBuffer(config) {
  if (config.mode === 'snapshot') {
    const response = await fetchOpenMv(config.snapshotUrl, config.timeoutMs)
    const contentType = String(response.headers.get('content-type') || 'image/jpeg').trim() || 'image/jpeg'
    const payload = await readResponseAsBuffer(response)

    return {
      contentType,
      payload,
      sourceUrl: config.snapshotUrl,
    }
  }

  const response = await fetchOpenMv(config.streamUrl, config.timeoutMs)
  const payload = await readFirstJpegFrame(response)

  return {
    contentType: 'image/jpeg',
    payload,
    sourceUrl: config.streamUrl,
  }
}
