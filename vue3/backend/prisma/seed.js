import 'dotenv/config'
import bcrypt from 'bcrypt'
import prismaPackage from '@prisma/client'

const { PrismaClient, Role } = prismaPackage

const prisma = new PrismaClient()
const ADMIN_USERNAME = 'admin'
const ADMIN_PASSWORD = '123456'
const DEFAULT_DEVICE_ID = 'mock-rover-001'
const SYSTEM_CONFIG_ID = 'system'
const SALT_ROUNDS = 10

async function ensureAdminSeed() {
  const existingAdmin = await prisma.user.findUnique({
    where: { username: ADMIN_USERNAME },
  })

  if (existingAdmin) {
    console.log(`Admin seed already exists: ${ADMIN_USERNAME}`)
    return existingAdmin
  }

  const passwordHash = await bcrypt.hash(ADMIN_PASSWORD, SALT_ROUNDS)

  return prisma.user.create({
    data: {
      username: ADMIN_USERNAME,
      passwordHash,
      role: Role.admin,
      isEnabled: true,
    },
  })
}

async function ensureDeviceSeed() {
  const existingDevice = await prisma.deviceCache.findUnique({
    where: { deviceId: DEFAULT_DEVICE_ID },
  })

  if (existingDevice) {
    console.log(`Device seed already exists: ${DEFAULT_DEVICE_ID}`)
    return existingDevice
  }

  return prisma.deviceCache.create({
    data: {
      deviceId: DEFAULT_DEVICE_ID,
      summaryJson: JSON.stringify({
        deviceId: DEFAULT_DEVICE_ID,
        online: true,
        battery: 87,
        taskStatus: 'idle',
        lastUpdate: new Date().toISOString(),
      }),
    },
  })
}

async function ensureSystemConfigSeed() {
  const existingSystemConfig = await prisma.systemConfig.findUnique({
    where: { id: SYSTEM_CONFIG_ID },
  })

  if (existingSystemConfig) {
    console.log(`System config already exists: ${SYSTEM_CONFIG_ID}`)
    return existingSystemConfig
  }

  return prisma.systemConfig.create({
    data: {
      id: SYSTEM_CONFIG_ID,
      registrationEnabled: true,
      appEnabled: true,
      maintenanceMessage: '',
      openclawEnabled: false,
    },
  })
}

async function main() {
  const admin = await ensureAdminSeed()
  const device = await ensureDeviceSeed()
  const systemConfig = await ensureSystemConfigSeed()

  console.log(
    `Seed complete for user ${admin.username}, device ${device.deviceId}, and system config ${systemConfig.id}`
  )
}

main()
  .catch((error) => {
    console.error('Prisma seed failed:', error)
    process.exitCode = 1
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
