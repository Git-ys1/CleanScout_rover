import { Router } from 'express'
import {
  command,
  createUser,
  deleteUser,
  getSystemConfigValue,
  listUsers,
  patchSystemConfig,
  updateUser,
} from '../controllers/adminController.js'
import { adminOnly } from '../middleware/adminOnly.js'
import { authRequired } from '../middleware/authRequired.js'

const router = Router()

router.use(authRequired, adminOnly)
router.get('/users', listUsers)
router.post('/users', createUser)
router.patch('/users/:id', updateUser)
router.delete('/users/:id', deleteUser)
router.get('/system-config', getSystemConfigValue)
router.patch('/system-config', patchSystemConfig)
router.post('/command', command)

export default router
