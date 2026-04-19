import { WS_BASE_URL } from './config.js'

export function createSocketTaskTransportPlaceholder() {
  const disabled = !WS_BASE_URL

  return {
    type: 'socket-task-placeholder',
    endpoint: WS_BASE_URL,
    connected: false,
    disabled,
    todo: disabled
      ? 'V-1.5.0 当前 backend 没有真实 /ws 服务，SocketTask transport 保持禁用占位。'
      : 'V-1.5.0 当前仅保留 SocketTask transport 占位，不建立真实连接。',
  }
}
