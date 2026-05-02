import './bootstrap/loadRuntimeEnv.js'
import cors from 'cors'
import express from 'express'
import authRoutes from './routes/auth.js'
import deviceRoutes from './routes/device.js'
import chatRoutes from './routes/chat.js'
import adminRoutes from './routes/admin.js'
import asrRoutes from './routes/asr.js'
import integrationsRoutes from './routes/integrations.js'
import rosRoutes from './routes/ros.js'
import systemRoutes from './routes/system.js'
import { errorHandler } from './middleware/errorHandler.js'

const app = express()

function parseAllowedOrigins(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

const allowedOrigins = new Set(parseAllowedOrigins(process.env.CORS_ALLOWED_ORIGINS))

function isLocalDevOrigin(origin) {
  return /^https?:\/\/(127\.0\.0\.1|localhost):\d+$/.test(origin)
}

function isAllowedOrigin(origin) {
  if (!origin) {
    return true
  }

  if (allowedOrigins.size > 0) {
    return allowedOrigins.has(origin)
  }

  return isLocalDevOrigin(origin)
}

app.use(
  cors({
    origin(origin, callback) {
      if (isAllowedOrigin(origin)) {
        callback(null, true)
        return
      }

      const error = new Error(`Origin ${origin} is not allowed by CORS`)
      error.status = 403
      error.code = 'CORS_ORIGIN_FORBIDDEN'
      callback(error)
    },
    credentials: false,
  })
)

app.use(express.json())

app.get('/', (_req, res) => {
  res.json({
    success: true,
    data: {
      service: 'vue3-backend',
      version: '1.6.0',
      status: 'running',
      profile: process.env.APP_PROFILE || 'local-lan',
    },
  })
})

app.use('/api/auth', authRoutes)
app.use('/api/device', deviceRoutes)
app.use('/api/chat', chatRoutes)
app.use('/api/admin', adminRoutes)
app.use('/api/asr', asrRoutes)
app.use('/api/integrations', integrationsRoutes)
app.use('/api/ros', rosRoutes)
app.use('/api/system', systemRoutes)

app.use((req, _res, next) => {
  const error = new Error(`Route ${req.method} ${req.originalUrl} not found`)
  error.status = 404
  error.code = 'ROUTE_NOT_FOUND'
  next(error)
})

app.use(errorHandler)

export default app
