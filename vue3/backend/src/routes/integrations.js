import { Router } from 'express'
import { openClawStatus, rosStatus } from '../controllers/integrationController.js'
import { authRequired } from '../middleware/authRequired.js'

const router = Router()

router.get('/openclaw/status', authRequired, openClawStatus)
router.get('/ros/status', authRequired, rosStatus)

export default router
