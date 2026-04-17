import { Router } from 'express'
import { login, logout, me, register } from '../controllers/authController.js'
import { authRequired } from '../middleware/authRequired.js'

const router = Router()

router.post('/register', register)
router.post('/login', login)
router.get('/me', authRequired, me)
router.post('/logout', authRequired, logout)

export default router
