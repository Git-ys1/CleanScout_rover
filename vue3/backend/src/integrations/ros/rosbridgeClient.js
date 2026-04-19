import WebSocket from 'ws'

function getWsOpenConstant() {
  return WebSocket.OPEN
}

function safeParseJson(payload) {
  try {
    return JSON.parse(String(payload || ''))
  } catch (_error) {
    return null
  }
}

export function createRosbridgeClient(config, cache) {
  let socket = null
  let connectPromise = null
  let reconnectTimer = null

  function clearReconnectTimer() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  function isOpen() {
    return socket && socket.readyState === getWsOpenConstant()
  }

  function sendJson(payload) {
    if (!isOpen()) {
      throw new Error('ROS bridge is not connected')
    }

    socket.send(JSON.stringify(payload))
  }

  function subscribe(topic, type) {
    sendJson({
      op: 'subscribe',
      topic,
      type,
      queue_length: 1,
    })
  }

  function handleMessage(data) {
    const payload = safeParseJson(data)

    if (!payload || typeof payload !== 'object') {
      return
    }

    cache.markHeartbeat()

    if (payload.op !== 'publish') {
      return
    }

    if (payload.topic === config.odomTopic) {
      cache.updateOdom(payload.msg)
      return
    }

    if (payload.topic === config.imuTopic) {
      cache.updateImu(payload.msg)
      return
    }

    if (payload.topic === config.scanTopic) {
      cache.updateScan(payload.msg)
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer || !config.enabled) {
      return
    }

    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      ensureConnected().catch(() => {})
    }, config.reconnectDelayMs)
  }

  async function ensureConnected() {
    if (!config.enabled) {
      return false
    }

    if (isOpen()) {
      return true
    }

    if (connectPromise) {
      return connectPromise
    }

    clearReconnectTimer()

    connectPromise = new Promise((resolve, reject) => {
      const ws = new WebSocket(config.rosbridgeUrl)
      let settled = false

      ws.once('open', () => {
        socket = ws
        cache.setConnected(true)

        try {
          subscribe(config.odomTopic, 'nav_msgs/Odometry')
          subscribe(config.imuTopic, 'sensor_msgs/Imu')
          subscribe(config.scanTopic, 'sensor_msgs/LaserScan')
        } catch (error) {
          cache.setLastError(error.message || 'ROS 订阅初始化失败')
        }

        settled = true
        resolve(true)
      })

      ws.on('message', handleMessage)

      ws.on('error', (error) => {
        cache.setConnected(false)
        cache.setLastError(error.message || 'ROS bridge 连接错误')

        if (!settled) {
          settled = true
          reject(error)
        }
      })

      ws.on('close', () => {
        cache.setConnected(false)

        if (!settled) {
          settled = true
          reject(new Error('ROS bridge 已关闭'))
        }

        if (socket === ws) {
          socket = null
        }

        scheduleReconnect()
      })
    })

    try {
      return await connectPromise
    } finally {
      connectPromise = null
    }
  }

  async function publishCmdVel(command) {
    await ensureConnected()
    sendJson({
      op: 'publish',
      topic: config.cmdVelTopic,
      msg: {
        linear: command.linear,
        angular: command.angular,
      },
    })
    cache.applyCommand(command)
  }

  return {
    ensureConnected,
    publishCmdVel,
  }
}
