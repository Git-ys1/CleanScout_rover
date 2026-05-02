import { Router } from 'express'
import { fansEnable, fansPwm, fansState, summary } from '../controllers/deviceController.js'
import { adminOnly } from '../middleware/adminOnly.js'
import { appAvailabilityRequired } from '../middleware/appAvailabilityRequired.js'
import { authRequired } from '../middleware/authRequired.js'

const router = Router()

router.get('/summary', authRequired, appAvailabilityRequired, summary)
router.get('/fans/state', authRequired, appAvailabilityRequired, fansState)
router.post('/fans/enable', authRequired, appAvailabilityRequired, adminOnly, fansEnable)
router.post('/fans/pwm', authRequired, appAvailabilityRequired, adminOnly, fansPwm)

export default router
