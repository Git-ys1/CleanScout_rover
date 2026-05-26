import os from 'node:os'

export function printDiagnostics(config) {
  const interfaces = os.networkInterfaces()
  const addresses = []

  for (const [name, entries] of Object.entries(interfaces)) {
    for (const entry of entries || []) {
      if (entry.family === 'IPv4' && !entry.internal) {
        addresses.push(`${name}=${entry.address}`)
      }
    }
  }

  console.log(`[diag] local ip list ${addresses.join(', ') || 'none'}`)
  console.log(`[diag] camera url ${config.mock ? 'mock' : config.cameraSourceUrl}`)
  console.log(`[diag] cloud ws url ${config.cloudWsUrl}`)
  console.log(`[diag] device=${config.deviceId} camera=${config.cameraId} targetFps=${config.targetFps}`)
}
