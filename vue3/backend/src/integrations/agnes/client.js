import { createHttpError } from '../../utils/response.js'

export function getAgnesConfig() {
  const timeoutMs = Number(process.env.AGNES_TIMEOUT_MS || 60000)
  if (!Number.isInteger(timeoutMs) || timeoutMs < 100 || timeoutMs > 120000) {
    throw createHttpError(503, 'AGNES_TIMEOUT_MS 必须为 100–120000 毫秒', 'AGNES_CONFIG_INVALID')
  }
  return {
    key: String(process.env.AGNES_API_KEY || '').trim(),
    baseUrl: String(process.env.AGNES_BASE_URL || 'https://apihub.agnes-ai.com/v1').replace(/\/+$/, ''),
    model: String(process.env.AGNES_MODEL || 'agnes-2.5-flash'),
    prompt: process.env.AGNES_SYSTEM_PROMPT || '你是 CleanScout 巡检项目的中文助手。根据对话与图片回答用户问题，描述可见物体、场景和关系。无法确定时明确说明，不编造识别结果。仅提供文字建议，不声称已执行车辆或机械臂控制。',
    timeoutMs,
  }
}

export async function callAgnes(messages) {
  const config = getAgnesConfig()
  if (!config.key) throw createHttpError(503, '服务端未配置 AGNES_API_KEY，请联系管理员', 'AGNES_KEY_MISSING')
  let endpoint
  try {
    endpoint = new URL(`${config.baseUrl}/chat/completions`)
    if (!['https:', 'http:'].includes(endpoint.protocol) || endpoint.username || endpoint.password) throw new Error()
    if (endpoint.protocol !== 'https:' && !['127.0.0.1', 'localhost', '[::1]'].includes(endpoint.hostname)) throw new Error()
  } catch {
    throw createHttpError(503, 'AGNES_BASE_URL 配置无效', 'AGNES_CONFIG_INVALID')
  }
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), config.timeoutMs)
  try {
    const response = await fetch(endpoint, {
      method: 'POST', redirect: 'error', signal: controller.signal,
      headers: { Authorization: `Bearer ${config.key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: config.model, messages: [{ role: 'system', content: config.prompt }, ...messages], max_tokens: 2048, stream: false }),
    })
    if (!response.ok) {
      const hint = { 401: '密钥无效', 403: '无访问权限', 429: '限流或额度不足' }[response.status] || '模型服务拒绝请求'
      throw createHttpError(502, `Agnes 调用失败（HTTP ${response.status}：${hint}），可以重试`, 'AGNES_HTTP_ERROR')
    }
    const data = await response.json()
    const choice = data?.choices?.[0]
    const text = choice?.message?.content
    if (typeof text !== 'string' || !text.trim()) throw createHttpError(502, 'Agnes 未返回有效文字，可以重试', 'AGNES_EMPTY_REPLY')
    return text.trim() + (choice.finish_reason === 'length' ? '\n（回复达到长度限制，可继续追问。）' : '')
  } catch (error) {
    if (controller.signal.aborted) throw createHttpError(504, 'Agnes 响应超时，请重试', 'AGNES_TIMEOUT')
    if (error.status) throw error
    throw createHttpError(502, '无法获取 Agnes 回复，请检查服务端网络或稍后重试', 'AGNES_NETWORK_ERROR')
  } finally {
    clearTimeout(timer)
  }
}
