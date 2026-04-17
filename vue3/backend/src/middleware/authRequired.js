import { prisma } from '../utils/prisma.js'
import { verifyToken } from '../utils/jwt.js'
import { createHttpError } from '../utils/response.js'

export async function authRequired(req, _res, next) {
  try {
    const header = req.headers.authorization || ''

    if (!header.startsWith('Bearer ')) {
      throw createHttpError(401, '未提供有效的 Bearer token', 'AUTH_TOKEN_MISSING')
    }

    const token = header.slice(7)
    const payload = verifyToken(token)

    const user = await prisma.user.findUnique({
      where: { id: payload.sub },
      select: { id: true, username: true, role: true },
    })

    if (!user) {
      throw createHttpError(401, '用户不存在或 token 已失效', 'AUTH_USER_NOT_FOUND')
    }

    req.user = user
    req.token = token
    next()
  } catch (error) {
    next(error.status ? error : createHttpError(401, '无效或过期的 token', 'AUTH_TOKEN_INVALID'))
  }
}
