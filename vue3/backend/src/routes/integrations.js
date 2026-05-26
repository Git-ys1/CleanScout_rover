import { Router } from 'express'
import { asrStatus, openClawStatus, openMvSnapshot, openMvStatus, openMvStream, rosStatus } from '../controllers/integrationController.js'
import { authRequired } from '../middleware/authRequired.js'

const router = Router()

router.get('/openclaw/status', authRequired, openClawStatus)
router.get('/asr/status', authRequired, asrStatus)
router.get('/openmv/status', authRequired, openMvStatus)
router.get('/openmv/snapshot', openMvSnapshot)
router.get('/openmv/stream', openMvStream)
router.get('/ros/status', authRequired, rosStatus)

export default router
