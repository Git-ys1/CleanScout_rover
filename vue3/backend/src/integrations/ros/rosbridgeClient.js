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

  function publish(topic, msg) {
    sendJson({
      op: 'publish',
      topic,
      msg,
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
      return
    }

    if (payload.topic === config.fanEnableTopic) {
      cache.updateFanEnable(payload.msg?.data)
      return
    }

    if (payload.topic === config.fanAPwmTopic) {
      cache.updateFanPwm({ fanA: payload.msg?.data })
      return
    }

    if (payload.topic === config.fanBPwmTopic) {
      cache.updateFanPwm({ fanB: payload.msg?.data })
      return
    }

    if (payload.topic === config.fanARpmTopic) {
      cache.updateFanRpm('fanA', payload.msg?.data)
      return
    }

    if (payload.topic === config.fanBRpmTopic) {
      cache.updateFanRpm('fanB', payload.msg?.data)
      return
    }

    if (payload.topic === config.fanLidStateTopic) {
      cache.updateFanLidState(payload.msg?.data)
      return
    }

    if (payload.topic === config.fanSummaryTopic) {
      cache.updateFanSummary(payload.msg?.data)
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
          subscribe(config.fanEnableTopic, 'std_msgs/Bool')
          subscribe(config.fanAPwmTopic, 'std_msgs/Float32')
          subscribe(config.fanBPwmTopic, 'std_msgs/Float32')
          subscribe(config.fanARpmTopic, 'std_msgs/Float32')
          subscribe(config.fanBRpmTopic, 'std_msgs/Float32')
          subscribe(config.fanLidStateTopic, 'std_msgs/Bool')
          subscribe(config.fanSummaryTopic, 'std_msgs/String')
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
    publish(config.cmdVelTopic, {
      linear: command.linear,
      angular: command.angular,
    })
    cache.applyCommand(command)
  }

  async function publishFanEnable(enabled) {
    await ensureConnected()
    publish(config.fanEnableTopic, {
      data: Boolean(enabled),
    })
    cache.updateFanEnable(enabled)
  }

  async function publishFanPwm({ fanA, fanB }) {
    await ensureConnected()
    publish(config.fanAPwmTopic, {
      data: Number(fanA || 0),
    })
    publish(config.fanBPwmTopic, {
      data: Number(fanB || 0),
    })
    cache.updateFanPwm({ fanA, fanB })
  }

  return {
    ensureConnected,
    publishCmdVel,
    publishFanEnable,
    publishFanPwm,
  }
}
