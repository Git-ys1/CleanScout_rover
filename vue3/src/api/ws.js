import { WS_BASE_URL } from './config.js'

export function createSocketTaskTransportPlaceholder() {
  return {
    type: 'socket-task-placeholder',
    endpoint: WS_BASE_URL,
    connected: false,
    todo: 'V-1.1.0 仅预留 SocketTask transport 接口，不建立真实连接。',
  }
}
