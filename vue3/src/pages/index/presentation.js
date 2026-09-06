// Page-only presentation; do not infer task execution from connectivity.
export function onlineLabel(status, summary, loading = false) {
  if (status?.enabled === true && typeof status.connected === 'boolean') return status.connected ? '在线' : '离线'
  if (status?.enabled === false) return '状态未知'
  if (loading) return '连接中'
  if (typeof summary?.online === 'boolean') return summary.online ? '在线' : '离线'
  return '状态未知'
}
export function taskLabel(value) {
  return ({ idle: '待机中', cleaning: '清扫中', paused: '已暂停', completed: '已完成', stopped: '已停止', error: '任务异常' })[value] || '状态未知'
}
export function numberText(value, unit = '') {
  if (value === null || value === undefined || value === '' || typeof value === 'boolean' || !Number.isFinite(Number(value))) return '暂未收到数据'
  return `${Number(Number(value).toFixed(2))}${unit}`
}
export function isStale(value, now = Date.now()) {
  return Boolean(value) && Number.isFinite(new Date(value).getTime()) && now - new Date(value).getTime() > 30000
}
export function ageText(value, now = Date.now()) {
  const at = value ? new Date(value).getTime() : NaN
  if (!Number.isFinite(at) || at > now + 5000) return '更新时间未知'
  const seconds = Math.max(0, Math.floor((now - at) / 1000))
  if (seconds < 60) return `${seconds} 秒前更新`
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前更新`
  return `${Math.floor(seconds / 3600)} 小时前更新`
}
