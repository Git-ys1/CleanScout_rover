import { Router } from 'express'
import { health } from '../controllers/systemController.js'

const router = Router()

router.get('/health', health)

export default router
