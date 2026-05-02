const STATUS_META_MAP = {
  mock: { text: '模拟链路', tone: 'warn' },
  openclaw: { text: 'OpenClaw 链路', tone: 'brand' },
  rosbridge: { text: 'ROS 桥接', tone: 'brand' },
  'edge-relay': { text: '边缘中继', tone: 'brand' },
  mjpeg: { text: 'MJPEG 图传', tone: 'brand' },
  snapshot: { text: '单帧快照', tone: 'neutral' },
  healthy: { text: '正常', tone: 'success' },
  degraded: { text: '降级', tone: 'warn' },
  disabled: { text: '未启用', tone: 'neutral' },
  enabled: { text: '已启用', tone: 'success' },
  error: { text: '异常', tone: 'danger' },
  connected: { text: '已连接', tone: 'success' },
  disconnected: { text: '未连接', tone: 'danger' },
  online: { text: '在线', tone: 'success' },
  offline: { text: '离线', tone: 'danger' },
  available: { text: '正常', tone: 'success' },
  missing: { text: '缺失', tone: 'danger' },
  ready: { text: '就绪', tone: 'success' },
  loss: { text: '丢失', tone: 'danger' },
  chat: { text: '对话补全', tone: 'neutral' },
  responses: { text: '统一响应', tone: 'neutral' },
  admin: { text: '管理员', tone: 'brand' },
  user: { text: '普通用户', tone: 'neutral' },
  locked: { text: '仅管理员可操作', tone: 'danger' },
  idle: { text: '待命', tone: 'neutral' },
  recording: { text: '录音中', tone: 'brand' },
  transcribing: { text: '识别中', tone: 'warn' },
  open: { text: '已打开', tone: 'success' },
  closed: { text: '已关闭', tone: 'neutral' },
}

function normalizeKey(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
}

export function getStatusMeta(value, fallbackText = '--') {
  const key = normalizeKey(value)

  if (!key) {
    return {
      text: fallbackText,
      tone: 'neutral',
    }
  }

  const meta = STATUS_META_MAP[key]

  if (meta) {
    return meta
  }

  return {
    text: String(value),
    tone: 'neutral',
  }
}

export function getBooleanStatusMeta(value, truthyKey = 'online', falsyKey = 'offline') {
  return getStatusMeta(value ? truthyKey : falsyKey)
}

export function formatStatusText(value, fallbackText = '--') {
  return getStatusMeta(value, fallbackText).text
}
