function readRequiredEnv(name) {
  const value = String(import.meta.env?.[name] || '').trim()

  if (!value) {
    throw new Error(`${name} is required for frontend runtime configuration`)
  }

  return value
}

function readOptionalEnv(name) {
  return String(import.meta.env?.[name] || '').trim()
}

export const API_BASE_URL = readRequiredEnv('VITE_API_BASE_URL')
export const WS_BASE_URL = readOptionalEnv('VITE_WS_BASE_URL')
export const REQUEST_TIMEOUT = 10000
