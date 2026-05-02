import { Router } from 'express'
import { transcribe } from '../controllers/asrController.js'
import { authRequired } from '../middleware/authRequired.js'
import { appAvailabilityRequired } from '../middleware/appAvailabilityRequired.js'
import { asrUploadSingle } from '../middleware/asrUpload.js'

const router = Router()

router.post('/transcribe', authRequired, appAvailabilityRequired, asrUploadSingle, transcribe)

export default router
