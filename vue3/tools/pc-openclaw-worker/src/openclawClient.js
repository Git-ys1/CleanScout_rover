const SYSTEM_PROMPT = [
  '你是 CleanScout 实验室清扫巡检车的智能调度助手。',
  '你可以解释机器人状态、规划巡检任务、生成操作建议。',
  '你不能直接生成底层 PWM、电机速度或绕过后端权限控制。',
  '涉及导航、风机、机械臂、OpenMV 图像采集、急停等动作时，你只能输出计划和结构化意图，必须等待后端权限校验和管理员确认。',
  '如果用户要求危险动作、连续运动或绕过安全限制，你必须拒绝并建议安全替代方案。',
].join('\n')

function createTimeoutSignal(timeoutMs) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  return {
    signal: controller.signal,
    clear() {
      clearTimeout(timer)
    },
  }
}

function buildHeaders(token) {
  const headers = {
    'Content-Type': 'application/json',
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  return headers
}

function normalizeMessages(messages = []) {
  return [
    {
      role: 'system',
      content: SYSTEM_PROMPT,
    },
    ...messages
      .filter((message) => message && message.content)
      .map((message) => ({
        role: message.role === 'assistant' ? 'assistant' : message.role === 'system' ? 'system' : 'user',
        content: String(message.content || ''),
      })),
  ]
}

function extractReply(payload) {
  const choice = payload?.choices?.[0]
  const content = choice?.message?.content || choice?.text || ''

  if (Array.isArray(content)) {
    return content.map((item) => item?.text || item?.content || '').join('').trim()
  }

  return String(content || '').trim()
}

export function createOpenClawClient(config) {
  async function request(path, options = {}) {
    const timeout = createTimeoutSignal(config.requestTimeoutMs)

    try {
      const response = await fetch(`${config.openclawBaseUrl}${path}`, {
        ...options,
        signal: timeout.signal,
        headers: {
          ...buildHeaders(config.openclawGatewayToken),
          ...(options.headers || {}),
        },
      })

      if (!response.ok) {
        const text = await response.text()
        const error = new Error(text || `OpenClaw request failed with ${response.status}`)
        error.code = 'OPENCLAW_REQUEST_FAILED'
        error.status = response.status
        throw error
      }

      return response.json()
    } catch (error) {
      if (error.name === 'AbortError') {
        const timeoutError = new Error('OpenClaw request timeout')
        timeoutError.code = 'OPENCLAW_TIMEOUT'
        throw timeoutError
      }

      if (!error.code) {
        error.code = 'OPENCLAW_UNREACHABLE'
      }

      throw error
    } finally {
      timeout.clear()
    }
  }

  async function getModels() {
    return request('/v1/models')
  }

  async function probe() {
    try {
      const models = await getModels()
      const modelList = Array.isArray(models?.data) ? models.data : []
      return {
        reachable: true,
        models: modelList,
        model: config.openclawModel,
      }
    } catch (error) {
      return {
        reachable: false,
        errorCode: error.code || 'OPENCLAW_UNREACHABLE',
        message: error.message || 'OpenClaw Gateway unreachable',
      }
    }
  }

  async function chat({ messages }) {
    const payload = await request('/v1/chat/completions', {
      method: 'POST',
      body: JSON.stringify({
        model: config.openclawModel,
        messages: normalizeMessages(messages),
      }),
    })
    const reply = extractReply(payload)

    if (!reply) {
      const error = new Error('OpenClaw returned empty reply')
      error.code = 'OPENCLAW_EMPTY_REPLY'
      throw error
    }

    return {
      reply,
      raw: {
        model: payload?.model || config.openclawModel,
      },
    }
  }

  return {
    getModels,
    probe,
    chat,
  }
}
