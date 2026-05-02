import { fetchOpenMvSnapshotBuffer, getOpenMvRuntimeConfig, probeOpenMv } from './client.js'

function buildBaseStatus(config) {
  return {
    enabled: config.enabled,
    status: 'disabled',
    mode: config.mode,
    baseUrl: config.baseUrl,
    streamPath: config.streamPath,
    snapshotPath: config.snapshotPath,
    previewRefreshMs: config.refreshMs,
    lastProbeAt: new Date().toISOString(),
    message: 'OpenMV preview is disabled.',
  }
}

export async function getOpenMvStatus() {
  const config = getOpenMvRuntimeConfig()

  if (!config.enabled) {
    return {
      ...buildBaseStatus(config),
      message: 'OPENMV_ENABLED=false，当前未启用 OpenMV 图像预览。',
    }
  }

  try {
    const probe = await probeOpenMv(config)

    return {
      ...buildBaseStatus(config),
      status: 'healthy',
      message: `OpenMV ${config.mode.toUpperCase()} 图传可访问。`,
      contentType: probe.contentType,
      targetUrl: probe.targetUrl,
      previewPath: '/api/integrations/openmv/snapshot',
    }
  } catch (error) {
    return {
      ...buildBaseStatus(config),
      status: 'error',
      message: error.message || 'OpenMV 探测失败。',
    }
  }
}

export async function getOpenMvSnapshot() {
  const config = getOpenMvRuntimeConfig()

  if (!config.enabled) {
    const error = new Error('OpenMV preview is disabled.')
    error.status = 404
    error.code = 'OPENMV_DISABLED'
    throw error
  }

  return fetchOpenMvSnapshotBuffer(config)
}
