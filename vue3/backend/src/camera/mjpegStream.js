function writeJsonError(res, status, code, message) {
  res.status(status).json({
    success: false,
    error: {
      code,
      message,
    },
  })
}

function writeFrame(res, boundary, frame) {
  res.write(`--${boundary}\r\n`)
  res.write('Content-Type: image/jpeg\r\n')
  res.write(`Content-Length: ${frame.buffer.length}\r\n`)
  res.write(`X-Frame-Seq: ${frame.seq}\r\n`)
  res.write(`X-Frame-Time: ${new Date(frame.at).toISOString()}\r\n`)
  res.write('\r\n')
  res.write(frame.buffer)
  res.write('\r\n')
}

export function streamLatestMjpeg(req, res, hub, config) {
  const initialFrame = hub.getLatestFrame()

  if (!initialFrame || !hub.isFrameFresh(config.staleMs)) {
    writeJsonError(res, 503, 'CAMERA_FRAME_UNAVAILABLE', '当前没有可用的 OpenMV / ESP32-CAM 图像帧。')
    return
  }

  if (config.maxViewers > 0 && hub.getViewerCount() >= config.maxViewers) {
    writeJsonError(res, 429, 'CAMERA_VIEWER_LIMIT', '当前图传观看人数已达到限制。')
    return
  }

  hub.addViewer()

  let closed = false
  let lastSeq = 0
  let lastKeepAliveAt = Date.now()

  function cleanup() {
    if (closed) {
      return
    }

    closed = true
    hub.removeViewer()
    clearInterval(timer)
  }

  res.statusCode = 200
  res.setHeader('Content-Type', `multipart/x-mixed-replace; boundary=${config.streamBoundary}`)
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate')
  res.setHeader('Pragma', 'no-cache')
  res.setHeader('Expires', '0')
  res.setHeader('Connection', 'keep-alive')
  res.setHeader('X-Accel-Buffering', 'no')

  if (typeof res.flushHeaders === 'function') {
    res.flushHeaders()
  }

  const timer = setInterval(() => {
    if (closed || res.destroyed || req.destroyed) {
      cleanup()
      return
    }

    const frame = hub.getLatestFrame()

    if (!frame || frame.seq === lastSeq || !hub.isFrameFresh(config.staleMs)) {
      const now = Date.now()

      if (now - lastKeepAliveAt >= config.streamHeartbeatMs) {
        lastKeepAliveAt = now
        res.write('\r\n')
      }
      return
    }

    lastSeq = frame.seq
    lastKeepAliveAt = Date.now()
    writeFrame(res, config.streamBoundary, frame)
  }, config.streamIntervalMs)

  lastSeq = initialFrame.seq
  writeFrame(res, config.streamBoundary, initialFrame)

  req.on('close', cleanup)
  res.on('close', cleanup)
  res.on('error', cleanup)
}
