import dotenv from 'dotenv'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const validProfiles = new Set(['local-lan', 'public-cloud', 'public-edge'])
const currentFile = fileURLToPath(import.meta.url)
const backendRoot = path.resolve(path.dirname(currentFile), '../..')
const repoRoot = path.resolve(backendRoot, '..')

function normalizeProfile(value) {
  const profile = String(value || 'local-lan').trim()
  return validProfiles.has(profile) ? profile : 'local-lan'
}

function loadEnvFile(filePath, { override = false, required = false } = {}) {
  if (!filePath) {
    return null
  }

  const resolvedPath = path.resolve(filePath)

  if (!fs.existsSync(resolvedPath)) {
    if (required) {
      throw new Error(`Runtime env file was not found: ${resolvedPath}`)
    }

    return null
  }

  const result = dotenv.config({ path: resolvedPath, override })

  if (result.error) {
    throw result.error
  }

  return resolvedPath
}

const explicitEnvFile = String(process.env.ENV_FILE || '').trim()
const localEnvPath = path.join(backendRoot, '.env')

const loadedExplicitEnv = explicitEnvFile
  ? loadEnvFile(explicitEnvFile, { override: true, required: true })
  : null

const appProfile = normalizeProfile(process.env.APP_PROFILE)
process.env.APP_PROFILE = appProfile

const profileTemplatePath = path.join(repoRoot, 'deploy', 'env', `vline-backend.${appProfile}.env.example`)
const loadedProfileTemplate = loadEnvFile(profileTemplatePath, { override: false })

const loadedRuntimeEnv = loadedExplicitEnv || loadEnvFile(localEnvPath, { override: true })

export const runtimeEnv = {
  appProfile,
  profileTemplatePath: loadedProfileTemplate,
  envFile: loadedRuntimeEnv,
}

export function printRuntimeProfile() {
  console.log(`[runtime] APP_PROFILE=${runtimeEnv.appProfile}`)
  console.log(`[runtime] profile_template=${runtimeEnv.profileTemplatePath || 'not-loaded'}`)
  console.log(`[runtime] ENV_FILE=${runtimeEnv.envFile || 'not-loaded'}`)
  console.log(`[runtime] ROS_TRANSPORT=${process.env.ROS_TRANSPORT || ''}`)
  console.log(`[runtime] ROSBRIDGE_URL=${process.env.ROSBRIDGE_URL || ''}`)
  console.log(`[runtime] EDGE_RELAY_ENABLED=${process.env.EDGE_RELAY_ENABLED || ''}`)
  console.log(`[runtime] EDGE_RELAY_PATH=${process.env.EDGE_RELAY_PATH || ''}`)
  console.log(`[runtime] OPENCLAW_ENABLED=${process.env.OPENCLAW_ENABLED || ''}`)
}
