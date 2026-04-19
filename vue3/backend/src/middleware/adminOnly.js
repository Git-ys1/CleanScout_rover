import { createHttpError } from '../utils/response.js'

export function adminOnly(req, _res, next) {
  if (!req.user || req.user.role !== 'admin') {
    return next(createHttpError(403, '当前用户无管理员权限', 'AUTH_ADMIN_REQUIRED'))
  }

  next()
}
