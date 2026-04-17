import bcrypt from 'bcrypt'
import prismaPackage from '@prisma/client'
import { prisma } from '../utils/prisma.js'
import { createHttpError } from '../utils/response.js'

const { Role } = prismaPackage

const SALT_ROUNDS = 10

function normalizeUsername(username) {
  return String(username || '').trim()
}

function normalizePassword(password) {
  return String(password || '')
}

function normalizeRole(role) {
  const normalizedRole = String(role || '').trim()

  if (normalizedRole !== Role.user && normalizedRole !== Role.admin) {
    throw createHttpError(400, '用户角色非法', 'ADMIN_USER_ROLE_INVALID')
  }

  return normalizedRole
}

function sanitizeManagedUser(user) {
  return {
    id: user.id,
    username: user.username,
    role: user.role,
    isEnabled: user.isEnabled,
    createdAt: user.createdAt,
    updatedAt: user.updatedAt,
  }
}

async function countEnabledAdmins(excludeUserId) {
  return prisma.user.count({
    where: {
      role: Role.admin,
      isEnabled: true,
      ...(excludeUserId ? { id: { not: excludeUserId } } : {}),
    },
  })
}

async function getManagedUserById(userId) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
  })

  if (!user) {
    throw createHttpError(404, '目标用户不存在', 'ADMIN_USER_NOT_FOUND')
  }

  return user
}

export async function listManagedUsers() {
  const users = await prisma.user.findMany({
    orderBy: [{ role: 'desc' }, { createdAt: 'desc' }],
    select: {
      id: true,
      username: true,
      role: true,
      isEnabled: true,
      createdAt: true,
      updatedAt: true,
    },
  })

  return users.map(sanitizeManagedUser)
}

export async function createManagedUser({ username, password, role, isEnabled = true }) {
  const normalizedUsername = normalizeUsername(username)
  const normalizedPassword = normalizePassword(password)
  const normalizedRole = normalizeRole(role)

  if (!normalizedUsername) {
    throw createHttpError(400, '用户名不能为空', 'ADMIN_USER_USERNAME_REQUIRED')
  }

  if (normalizedPassword.length < 6) {
    throw createHttpError(400, '密码长度不能少于 6 位', 'ADMIN_USER_PASSWORD_TOO_SHORT')
  }

  const existingUser = await prisma.user.findUnique({
    where: { username: normalizedUsername },
  })

  if (existingUser) {
    throw createHttpError(409, '用户名已存在', 'ADMIN_USER_USERNAME_EXISTS')
  }

  const passwordHash = await bcrypt.hash(normalizedPassword, SALT_ROUNDS)

  const user = await prisma.user.create({
    data: {
      username: normalizedUsername,
      passwordHash,
      role: normalizedRole,
      isEnabled: Boolean(isEnabled),
    },
    select: {
      id: true,
      username: true,
      role: true,
      isEnabled: true,
      createdAt: true,
      updatedAt: true,
    },
  })

  return sanitizeManagedUser(user)
}

export async function updateManagedUser(userId, payload, actor) {
  const user = await getManagedUserById(userId)
  const data = {}

  if (payload.password !== undefined) {
    const normalizedPassword = normalizePassword(payload.password)

    if (normalizedPassword.length < 6) {
      throw createHttpError(400, '密码长度不能少于 6 位', 'ADMIN_USER_PASSWORD_TOO_SHORT')
    }

    data.passwordHash = await bcrypt.hash(normalizedPassword, SALT_ROUNDS)
  }

  if (payload.role !== undefined) {
    data.role = normalizeRole(payload.role)
  }

  if (payload.isEnabled !== undefined) {
    data.isEnabled = Boolean(payload.isEnabled)
  }

  if (!Object.keys(data).length) {
    throw createHttpError(400, '未提供可更新字段', 'ADMIN_USER_PATCH_EMPTY')
  }

  const nextRole = data.role ?? user.role
  const nextIsEnabled = data.isEnabled ?? user.isEnabled

  if (user.role === Role.admin && (!nextIsEnabled || nextRole !== Role.admin)) {
    const remainingEnabledAdmins = await countEnabledAdmins(user.id)

    if (remainingEnabledAdmins === 0) {
      throw createHttpError(409, '必须至少保留一个启用中的管理员', 'ADMIN_LAST_ADMIN_REQUIRED')
    }
  }

  const updatedUser = await prisma.user.update({
    where: { id: userId },
    data,
    select: {
      id: true,
      username: true,
      role: true,
      isEnabled: true,
      createdAt: true,
      updatedAt: true,
    },
  })

  return sanitizeManagedUser(updatedUser)
}

export async function deleteManagedUser(userId, actor) {
  if (userId === actor.id) {
    throw createHttpError(409, '管理员不能删除自己', 'ADMIN_SELF_DELETE_FORBIDDEN')
  }

  const user = await getManagedUserById(userId)

  if (user.role === Role.admin) {
    const remainingEnabledAdmins = await countEnabledAdmins(user.id)

    if (remainingEnabledAdmins === 0) {
      throw createHttpError(409, '必须至少保留一个启用中的管理员', 'ADMIN_LAST_ADMIN_REQUIRED')
    }
  }

  await prisma.user.delete({
    where: { id: userId },
  })

  return { deletedUserId: userId }
}

export async function executeAdminCommand(command, user) {
  const normalizedCommand = String(command || '').trim()

  if (!normalizedCommand) {
    throw createHttpError(400, '管理员命令不能为空', 'ADMIN_COMMAND_REQUIRED')
  }

  return {
    command: normalizedCommand,
    accepted: true,
    result: `Mock command "${normalizedCommand}" accepted by ${user.username}.`,
    executedAt: new Date().toISOString(),
  }
}
