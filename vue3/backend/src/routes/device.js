import { Router } from 'express'
import { summary } from '../controllers/deviceController.js'
import { authRequired } from '../middleware/authRequired.js'

const router = Router()

router.get('/summary', authRequired, summary)

export default router
