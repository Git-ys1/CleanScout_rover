import { createServer } from 'node:http'
import app from './app.js'
import { printRuntimeProfile } from './bootstrap/loadRuntimeEnv.js'
import { attachRosEdgeRelayServer } from './integrations/ros/index.js'

const port = Number(process.env.PORT || 3000)
const server = createServer(app)

attachRosEdgeRelayServer(server)

server.listen(port, () => {
  console.log(`V-1.7.0 backend service listening on http://127.0.0.1:${port}`)
  printRuntimeProfile()
})

export default server
