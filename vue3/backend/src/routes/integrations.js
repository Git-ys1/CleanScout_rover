import { Router } from 'express'
import { openClawStatus } from '../controllers/integrationController.js'
import { authRequired } from '../middleware/authRequired.js'

const router = Router()

router.get('/openclaw/status', authRequired, openClawStatus)

export default router
