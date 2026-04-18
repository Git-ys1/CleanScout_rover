import 'dotenv/config'
import cors from 'cors'
import express from 'express'
import authRoutes from './routes/auth.js'
import deviceRoutes from './routes/device.js'
import chatRoutes from './routes/chat.js'
import adminRoutes from './routes/admin.js'
import integrationsRoutes from './routes/integrations.js'
import rosRoutes from './routes/ros.js'
import systemRoutes from './routes/system.js'
import { errorHandler } from './middleware/errorHandler.js'

const app = express()

function isAllowedOrigin(origin) {
  if (!origin) {
    return true
  }

  return /^https?:\/\/(127\.0\.0\.1|localhost):\d+$/.test(origin)
}

app.use(
  cors({
    origin(origin, callback) {
      if (isAllowedOrigin(origin)) {
        callback(null, true)
        return
      }

      callback(new Error(`Origin ${origin} is not allowed by CORS`))
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
        version: '1.3.3',
        status: 'running',
      },
    })
})

app.use('/api/auth', authRoutes)
app.use('/api/device', deviceRoutes)
app.use('/api/chat', chatRoutes)
app.use('/api/admin', adminRoutes)
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

const port = Number(process.env.PORT || 3000)

app.listen(port, () => {
  console.log(`V-1.3.3 backend service listening on http://127.0.0.1:${port}`)
})

export default app
