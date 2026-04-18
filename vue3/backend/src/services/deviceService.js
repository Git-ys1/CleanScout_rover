import { prisma } from '../utils/prisma.js'

function buildFallbackSummary() {
  return {
    deviceId: 'mock-rover-001',
    online: true,
    battery: 87,
    taskStatus: 'idle',
    lastUpdate: new Date().toISOString(),
  }
}

export async function getDeviceSummary() {
  const cache = await prisma.deviceCache.findFirst({
    orderBy: { updatedAt: 'desc' },
  })

  if (!cache) {
    return buildFallbackSummary()
  }

  return JSON.parse(cache.summaryJson)
}
