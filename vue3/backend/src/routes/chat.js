import { Router } from 'express'
import { history, send } from '../controllers/chatController.js'
import { authRequired } from '../middleware/authRequired.js'

const router = Router()

router.get('/history', authRequired, history)
router.post('/send', authRequired, send)

export default router
