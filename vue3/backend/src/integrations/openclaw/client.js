function parseBoolean(value) {
  return String(value || '').trim().toLowerCase() === 'true'
}

function parseTimeout(value, fallback = 30000) {
  const timeout = Number(value)

  if (!Number.isFinite(timeout) || timeout <= 0) {
    return fallback
  }

  return timeout
}

function normalizeBaseUrl(baseUrl) {
  return String(baseUrl || 'http://127.0.0.1:18789').trim().replace(/\/+$/, '')
}

function normalizeApiMode(apiMode) {
  return String(apiMode || 'chat').trim().toLowerCase() === 'responses' ? 'responses' : 'chat'
}

function buildHeaders(config) {
  return {
    'Content-Type': 'application/json',
    ...(config.bearerToken ? { Authorization: `Bearer ${config.bearerToken}` } : {}),
  }
}

async function parseResponseBody(response) {
  const contentType = response.headers.get('content-type') || ''

  if (contentType.includes('application/json')) {
    return response.json()
  }

  return response.text()
}

function createOpenClawRequestError(response, payload) {
  const message =
    payload?.error?.message ||
    payload?.message ||
    `OpenClaw request failed with status ${response.status}`
  const error = new Error(message)

  error.status = response.status
  error.code = 'OPENCLAW_REQUEST_FAILED'
  error.payload = payload

  return error
}

export function getOpenClawRuntimeConfig(systemConfig) {
  const hardEnabled = parseBoolean(process.env.OPENCLAW_ENABLED)
  const softEnabled = Boolean(systemConfig?.openclawEnabled)

  return {
    hardEnabled,
    softEnabled,
    enabled: hardEnabled && softEnabled,
    baseUrl: normalizeBaseUrl(process.env.OPENCLAW_BASE_URL),
    apiMode: normalizeApiMode(process.env.OPENCLAW_API_MODE),
    model: String(process.env.OPENCLAW_MODEL || 'openclaw/default').trim() || 'openclaw/default',
    bearerToken: String(process.env.OPENCLAW_BEARER_TOKEN || '').trim(),
    timeoutMs: parseTimeout(process.env.OPENCLAW_REQUEST_TIMEOUT_MS),
  }
}

export async function openClawFetch(path, options = {}, config) {
  const response = await fetch(`${config.baseUrl}${path}`, {
    method: options.method || 'GET',
    headers: buildHeaders(config),
    body: options.body ? JSON.stringify(options.body) : undefined,
    signal: AbortSignal.timeout(config.timeoutMs),
  })
  const payload = await parseResponseBody(response)

  if (!response.ok) {
    throw createOpenClawRequestError(response, payload)
  }

  return payload
}

export function fetchOpenClawModels(config) {
  return openClawFetch('/v1/models', {}, config)
}

export function sendOpenClawChatCompletions(messages, config) {
  return openClawFetch(
    '/v1/chat/completions',
    {
      method: 'POST',
      body: {
        model: config.model,
        messages,
      },
    },
    config
  )
}

export function sendOpenClawResponses(input, config) {
  return openClawFetch(
    '/v1/responses',
    {
      method: 'POST',
      body: {
        model: config.model,
        input,
      },
    },
    config
  )
}
