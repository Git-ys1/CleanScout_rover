Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $repoRoot "backend"
$envFile = Join-Path $env:TEMP "vline-backend-public-edge-local.env"

$ip = Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254*" -and $_.InterfaceAlias -eq "WLAN" } |
  Select-Object -First 1 -ExpandProperty IPAddress

if (-not $ip) {
  $ip = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254*" } |
    Select-Object -First 1 -ExpandProperty IPAddress
}

@"
APP_PROFILE=public-edge
PORT=3000
DATABASE_URL=file:./dev.db
JWT_SECRET=v-line-local-dev-secret
JWT_EXPIRES_IN=7d
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
OPENCLAW_ENABLED=false
ASR_ENABLED=false
OPENMV_ENABLED=true
OPENMV_INPUT_MODE=push-stream
CAMERA_INGEST_ENABLED=true
CAMERA_INGEST_PATH=/edge/camera
CAMERA_INGEST_TOKEN=local-camera-token-change-me
CAMERA_ALLOWED_DEVICE_IDS=pc-001
CAMERA_ALLOWED_CAMERA_IDS=openmv-arm-cam-001
CAMERA_FRAME_STALE_MS=3000
CAMERA_MAX_FRAME_BYTES=300000
CAMERA_STREAM_BOUNDARY=cleanscout-openmv
CAMERA_STREAM_HEARTBEAT_MS=1000
CAMERA_MAX_VIEWERS=3
ROS_ENABLED=true
ROS_TRANSPORT=edge-relay
ROS_CMD_REPEAT_HZ=10
ROS_CMD_DEFAULT_HOLD_MS=400
ROS_MANUAL_LINEAR_SPEED=0.5
ROS_MANUAL_STRAFE_SPEED=0.5
ROS_MANUAL_ANGULAR_SPEED=0.8
EDGE_RELAY_ENABLED=true
EDGE_RELAY_PATH=/edge/ros
EDGE_DEVICE_AUTH_REQUIRED=true
EDGE_HELLO_TIMEOUT_MS=5000
EDGE_HEARTBEAT_TIMEOUT_MS=15000
EDGE_SERVER_PING_INTERVAL_MS=25000
EDGE_ALLOWED_DEVICE_IDS=csrpi-001
"@ | Set-Content -Encoding UTF8 $envFile

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "`$env:ENV_FILE='$envFile'; Set-Location '$backendRoot'; cmd /c npm.cmd run start"
)

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$repoRoot'; cmd /c npm.cmd run dev:h5"
)

Write-Host "backend: http://127.0.0.1:3000"
Write-Host "H5:      http://localhost:5173"

  if ($ip) {
    Write-Host "LAN API: http://$ip`:3000/api"
    Write-Host "edge:    ws://$ip`:3000/edge/ros"
    Write-Host "camera:  ws://$ip`:3000/edge/camera?token=local-camera-token-change-me&deviceId=pc-001&cameraId=openmv-arm-cam-001"
  }
