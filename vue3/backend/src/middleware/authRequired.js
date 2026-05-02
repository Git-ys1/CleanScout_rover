import { prisma } from '../utils/prisma.js'
import { verifyToken } from '../utils/jwt.js'
import { createHttpError } from '../utils/response.js'

function readBearerToken(header) {
  const normalized = String(header || '')

  if (!normalized.startsWith('Bearer ')) {
    return ''
  }

  return normalized.slice(7).trim()
}

export async function resolveAuthenticatedUserByToken(token) {
  if (!token) {
    throw createHttpError(401, '未提供有效的 Bearer token', 'AUTH_TOKEN_MISSING')
  }

  const payload = verifyToken(token)
  const user = await prisma.user.findUnique({
    where: { id: payload.sub },
    select: { id: true, username: true, role: true, isEnabled: true },
  })

  if (!user) {
    throw createHttpError(401, '用户不存在或 token 已失效', 'AUTH_USER_NOT_FOUND')
  }

  if (!user.isEnabled) {
    throw createHttpError(403, '当前用户已停用', 'AUTH_USER_DISABLED')
  }

  return user
}

export async function authRequired(req, _res, next) {
  try {
    const token = readBearerToken(req.headers.authorization)
    const user = await resolveAuthenticatedUserByToken(token)

    req.user = user
    req.token = token
    next()
  } catch (error) {
    next(error.status ? error : createHttpError(401, '无效或过期的 token', 'AUTH_TOKEN_INVALID'))
  }
}
