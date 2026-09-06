import { Router } from 'express'
import { history, send, sendImage, status } from '../controllers/chatController.js'
import { appAvailabilityRequired } from '../middleware/appAvailabilityRequired.js'
import { authRequired } from '../middleware/authRequired.js'
import { chatImageUploadSingle } from '../middleware/chatImageUpload.js'

const router = Router()

router.get('/status', authRequired, appAvailabilityRequired, status)

router.get('/history', authRequired, appAvailabilityRequired, history)
router.post('/send', authRequired, appAvailabilityRequired, send)
router.post('/image', authRequired, appAvailabilityRequired, chatImageUploadSingle, sendImage)

export default router
