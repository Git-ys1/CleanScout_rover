import bcrypt from 'bcrypt'
import { Role } from '@prisma/client'
import { prisma } from '../utils/prisma.js'
import { createHttpError } from '../utils/response.js'
import { signToken } from '../utils/jwt.js'

const SALT_ROUNDS = 10

function normalizeUsername(username) {
  return String(username || '').trim()
}

export async function registerUser({ username, password }) {
  const normalizedUsername = normalizeUsername(username)
  const normalizedPassword = String(password || '')

  if (!normalizedUsername) {
    throw createHttpError(400, '用户名不能为空', 'AUTH_USERNAME_REQUIRED')
  }

  if (normalizedPassword.length < 6) {
    throw createHttpError(400, '密码长度不能少于 6 位', 'AUTH_PASSWORD_TOO_SHORT')
  }

  const existingUser = await prisma.user.findUnique({
    where: { username: normalizedUsername },
  })

  if (existingUser) {
    throw createHttpError(409, '用户名已存在', 'AUTH_USERNAME_EXISTS')
  }

  const passwordHash = await bcrypt.hash(normalizedPassword, SALT_ROUNDS)

  const user = await prisma.user.create({
    data: {
      username: normalizedUsername,
      passwordHash,
      role: Role.user,
    },
    select: {
      id: true,
      username: true,
      role: true,
      createdAt: true,
    },
  })

  return user
}

export async function loginUser({ username, password }) {
  const normalizedUsername = normalizeUsername(username)
  const normalizedPassword = String(password || '')

  if (!normalizedUsername || !normalizedPassword) {
    throw createHttpError(400, '用户名和密码不能为空', 'AUTH_CREDENTIALS_REQUIRED')
  }

  const user = await prisma.user.findUnique({
    where: { username: normalizedUsername },
  })

  if (!user) {
    throw createHttpError(401, '用户名或密码错误', 'AUTH_INVALID_CREDENTIALS')
  }

  const isPasswordValid = await bcrypt.compare(normalizedPassword, user.passwordHash)

  if (!isPasswordValid) {
    throw createHttpError(401, '用户名或密码错误', 'AUTH_INVALID_CREDENTIALS')
  }

  const safeUser = {
    id: user.id,
    username: user.username,
    role: user.role,
  }

  return {
    token: signToken(safeUser),
    user: safeUser,
  }
}

export async function getCurrentUser(userId) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: {
      id: true,
      username: true,
      role: true,
      createdAt: true,
      updatedAt: true,
    },
  })

  if (!user) {
    throw createHttpError(404, '用户不存在', 'AUTH_USER_NOT_FOUND')
  }

  return user
}
