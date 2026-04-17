import { Router } from 'express'
import { history, send } from '../controllers/chatController.js'
import { appAvailabilityRequired } from '../middleware/appAvailabilityRequired.js'
import { authRequired } from '../middleware/authRequired.js'

const router = Router()

router.get('/history', authRequired, appAvailabilityRequired, history)
router.post('/send', authRequired, appAvailabilityRequired, send)

export default router
