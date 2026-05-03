import 'dotenv/config'
import bcrypt from 'bcrypt'
import prismaPackage from '@prisma/client'

const { PrismaClient, Role } = prismaPackage

const prisma = new PrismaClient()
const ADMIN_USERNAME = 'admin'
const ADMIN_PASSWORD = '123456'
const DEFAULT_DEVICE_ID = 'mock-rover-001'
const SYSTEM_CONFIG_ID = 'system'
const EDGE_DEVICE_BOOTSTRAP_ID = String(process.env.EDGE_DEVICE_BOOTSTRAP_ID || '').trim()
const EDGE_DEVICE_BOOTSTRAP_TOKEN = String(process.env.EDGE_DEVICE_BOOTSTRAP_TOKEN || '').trim()
const SALT_ROUNDS = 10

async function ensureAdminSeed() {
  const existingAdmin = await prisma.user.findUnique({
    where: { username: ADMIN_USERNAME },
  })

  if (existingAdmin) {
    console.log(
      `[seed] admin detected: username=${existingAdmin.username}, role=${existingAdmin.role}, isEnabled=${existingAdmin.isEnabled}`
    )
    return existingAdmin
  }

  const passwordHash = await bcrypt.hash(ADMIN_PASSWORD, SALT_ROUNDS)

  const admin = await prisma.user.create({
    data: {
      username: ADMIN_USERNAME,
      passwordHash,
      role: Role.admin,
      isEnabled: true,
    },
  })

  console.log(`[seed] admin created: username=${admin.username}, role=${admin.role}, isEnabled=${admin.isEnabled}`)
  return admin
}

async function ensureDeviceSeed() {
  const existingDevice = await prisma.deviceCache.findUnique({
    where: { deviceId: DEFAULT_DEVICE_ID },
  })

  if (existingDevice) {
    console.log(`[seed] device cache detected: deviceId=${existingDevice.deviceId}`)
    return existingDevice
  }

  const device = await prisma.deviceCache.create({
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

  console.log(`[seed] device cache created: deviceId=${device.deviceId}`)
  return device
}

async function ensureSystemConfigSeed() {
  const existingSystemConfig = await prisma.systemConfig.findUnique({
    where: { id: SYSTEM_CONFIG_ID },
  })

  if (existingSystemConfig) {
    console.log(
      `[seed] system config detected: id=${existingSystemConfig.id}, registrationEnabled=${existingSystemConfig.registrationEnabled}, appEnabled=${existingSystemConfig.appEnabled}`
    )
    return existingSystemConfig
  }

  const systemConfig = await prisma.systemConfig.create({
    data: {
      id: SYSTEM_CONFIG_ID,
      registrationEnabled: true,
      appEnabled: true,
      maintenanceMessage: '',
      openclawEnabled: false,
    },
  })

  console.log(
    `[seed] system config created: id=${systemConfig.id}, registrationEnabled=${systemConfig.registrationEnabled}, appEnabled=${systemConfig.appEnabled}`
  )
  return systemConfig
}

async function ensureEdgeDeviceSeed() {
  if (!EDGE_DEVICE_BOOTSTRAP_ID || !EDGE_DEVICE_BOOTSTRAP_TOKEN) {
    console.log(
      '[seed] edge device skipped: EDGE_DEVICE_BOOTSTRAP_ID or EDGE_DEVICE_BOOTSTRAP_TOKEN is empty; first public-edge deployment will not create csrpi-001'
    )
    return null
  }

  if (EDGE_DEVICE_BOOTSTRAP_TOKEN.length < 32) {
    console.log(
      '[seed] edge device skipped: EDGE_DEVICE_BOOTSTRAP_TOKEN must be at least 32 characters; first public-edge deployment will not create csrpi-001'
    )
    return null
  }

  const existingEdgeDevice = await prisma.edgeDevice.findUnique({
    where: { deviceId: EDGE_DEVICE_BOOTSTRAP_ID },
  })

  if (existingEdgeDevice) {
    console.log(
      `[seed] edge device detected: deviceId=${existingEdgeDevice.deviceId}, isEnabled=${existingEdgeDevice.isEnabled}, transport=${existingEdgeDevice.transport}`
    )
    return existingEdgeDevice
  }

  const tokenHash = await bcrypt.hash(EDGE_DEVICE_BOOTSTRAP_TOKEN, SALT_ROUNDS)

  const edgeDevice = await prisma.edgeDevice.create({
    data: {
      deviceId: EDGE_DEVICE_BOOTSTRAP_ID,
      tokenHash,
      isEnabled: true,
      transport: 'edge-relay',
      topicsJson: JSON.stringify({
        cmd_vel: '/cmd_vel',
        odom: '/odom',
        imu: '/imu/data',
        scan: '/scan',
      }),
      capabilitiesJson: JSON.stringify(['manual_control', 'odom', 'imu', 'scan_summary']),
    },
  })

  console.log(
    `[seed] edge device created: deviceId=${edgeDevice.deviceId}, isEnabled=${edgeDevice.isEnabled}, transport=${edgeDevice.transport}`
  )
  return edgeDevice
}

async function main() {
  const admin = await ensureAdminSeed()
  const device = await ensureDeviceSeed()
  const systemConfig = await ensureSystemConfigSeed()
  const edgeDevice = await ensureEdgeDeviceSeed()

  console.log('[seed] verification summary')
  console.log(`[seed] admin=${admin.username}`)
  console.log(`[seed] deviceCache=${device.deviceId}`)
  console.log(`[seed] systemConfig=${systemConfig.id}`)
  console.log(`[seed] edgeDevice=${edgeDevice?.deviceId || 'skipped'}`)
  console.log('[seed] complete')
}

main()
  .catch((error) => {
    console.error('Prisma seed failed:', error)
    process.exitCode = 1
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
