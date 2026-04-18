import { Router } from 'express'
import { cmdVel, manualPreset, telemetrySummary } from '../controllers/rosController.js'
import { adminOnly } from '../middleware/adminOnly.js'
import { authRequired } from '../middleware/authRequired.js'

const router = Router()

router.get('/telemetry/summary', authRequired, telemetrySummary)
router.post('/cmd-vel', authRequired, adminOnly, cmdVel)
router.post('/manual-preset', authRequired, adminOnly, manualPreset)

export default router
