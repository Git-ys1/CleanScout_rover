import { Router } from 'express'
import { chat, status } from '../controllers/openclawController.js'
import { appAvailabilityRequired } from '../middleware/appAvailabilityRequired.js'
import { authRequired } from '../middleware/authRequired.js'

const router = Router()

router.get('/status', authRequired, appAvailabilityRequired, status)
router.post('/chat', authRequired, appAvailabilityRequired, chat)

export default router
