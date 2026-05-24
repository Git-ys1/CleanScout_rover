import { get, post } from './http.js'

const DEFAULT_DEVICE_ID = 'cleanscout-001'

export function requestOpenClawAgentStatus(deviceId = DEFAULT_DEVICE_ID) {
  return get(`/openclaw/status?deviceId=${encodeURIComponent(deviceId)}`, { auth: true })
}

export function requestSendOpenClawMessage({
  deviceId = DEFAULT_DEVICE_ID,
  conversationId = 'conv-cleanscout-001',
  message,
  mode = 'chat',
}) {
  return post(
    '/openclaw/chat',
    {
      deviceId,
      conversationId,
      message,
      mode,
    },
    { auth: true }
  )
}
