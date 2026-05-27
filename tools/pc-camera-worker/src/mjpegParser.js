const JPEG_START = Buffer.from([0xff, 0xd8])
const JPEG_END = Buffer.from([0xff, 0xd9])

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

export async function* parseJpegFrames(readable, options = {}) {
  const maxFrameBytes = options.maxFrameBytes || 200000
  const readTimeoutMs = options.readTimeoutMs || 8000
  const reader = readable?.getReader?.()

  if (!reader) {
    throw new Error('camera response body is not readable')
  }

  async function readChunk() {
    if (!readTimeoutMs || readTimeoutMs <= 0) {
      return await reader.read()
    }

    let timer = null

    try {
      return await Promise.race([
        reader.read(),
        new Promise((_, reject) => {
          timer = setTimeout(() => {
            reject(Object.assign(new Error(`camera stream read timed out after ${readTimeoutMs}ms`), {
              code: 'CAMERA_STREAM_READ_TIMEOUT',
            }))
          }, readTimeoutMs)
        }),
      ])
    } finally {
      if (timer) {
        clearTimeout(timer)
      }
    }
  }

  let buffer = Buffer.alloc(0)

  while (true) {
    const { done, value } = await readChunk()

    if (done) {
      break
    }

    buffer = Buffer.concat([buffer, Buffer.from(value)])

    while (buffer.length > 0) {
      const startIndex = findMarker(buffer, JPEG_START)

      if (startIndex < 0) {
        buffer = buffer.length > maxFrameBytes ? buffer.subarray(buffer.length - 2) : buffer
        break
      }

      const endIndex = findMarker(buffer, JPEG_END, startIndex + JPEG_START.length)

      if (endIndex < 0) {
        if (startIndex > 0) {
          buffer = buffer.subarray(startIndex)
        }

        if (buffer.length > maxFrameBytes) {
          throw Object.assign(new Error(`JPEG frame exceeds limit: ${buffer.length} > ${maxFrameBytes}`), {
            code: 'CAMERA_FRAME_TOO_LARGE',
          })
        }
        break
      }

      const frame = buffer.subarray(startIndex, endIndex + JPEG_END.length)
      buffer = buffer.subarray(endIndex + JPEG_END.length)

      if (frame.length > maxFrameBytes) {
        throw Object.assign(new Error(`JPEG frame exceeds limit: ${frame.length} > ${maxFrameBytes}`), {
          code: 'CAMERA_FRAME_TOO_LARGE',
        })
      }

      yield frame
    }
  }
}
