import { getConfig } from './config.js'
import { createOpenClawClient } from './openclawClient.js'

const config = getConfig()
const client = createOpenClawClient(config)

async function main() {
  console.log('[pc-openclaw-worker] probe start')
  console.log('[pc-openclaw-worker] gateway=%s model=%s', config.openclawBaseUrl, config.openclawModel)

  const models = await client.getModels()
  console.log('[pc-openclaw-worker] probe models ok:', JSON.stringify(models))

  const result = await client.chat({
    messages: [
      {
        role: 'user',
        content: '你是 CleanScout 智能调度助手，回复：链路已就绪。',
      },
    ],
  })

  console.log('[pc-openclaw-worker] probe chat ok:', JSON.stringify(result))
}

main().catch((error) => {
  console.error('[pc-openclaw-worker] probe fatal:', error)
  process.exit(1)
})
