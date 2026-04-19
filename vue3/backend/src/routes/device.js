import { Router } from 'express'
import { summary } from '../controllers/deviceController.js'
import { appAvailabilityRequired } from '../middleware/appAvailabilityRequired.js'
import { authRequired } from '../middleware/authRequired.js'

const router = Router()

router.get('/summary', authRequired, appAvailabilityRequired, summary)

export default router
