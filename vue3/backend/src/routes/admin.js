import { Router } from 'express'
import { command } from '../controllers/adminController.js'
import { adminOnly } from '../middleware/adminOnly.js'
import { authRequired } from '../middleware/authRequired.js'

const router = Router()

router.post('/command', authRequired, adminOnly, command)

export default router
