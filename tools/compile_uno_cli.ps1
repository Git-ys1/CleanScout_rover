param(
    [string]$ArduinoCliPath = "",
    [string]$RepoRoot = "",
    [string]$SketchDir = "",
    [string]$BuildPath = "",
    [string]$Fqbn = "arduino:avr:uno"
)

function Resolve-ArduinoCli {
    param([string]$ManualPath)

    if (-not [string]::IsNullOrWhiteSpace($ManualPath)) {
        if (-not (Test-Path $ManualPath)) {
            throw "arduino-cli not found at manual path: $ManualPath"
        }
        return (Resolve-Path $ManualPath).Path
    }

    $cmd = Get-Command arduino-cli -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        return $cmd.Path
    }

    $extRoot = Join-Path $env:USERPROFILE ".vscode\extensions"
    if (Test-Path $extRoot) {
        $candidate = Get-ChildItem -Path $extRoot -Directory -Filter "vscode-arduino.vscode-arduino-community-*" `
            | Sort-Object LastWriteTime -Descending `
            | Select-Object -First 1

        if ($null -ne $candidate) {
            $embedded = Join-Path $candidate.FullName "assets\platform\win32-x64\arduino-cli\arduino-cli.exe"
            if (Test-Path $embedded) {
                return (Resolve-Path $embedded).Path
            }
        }
    }

    throw "arduino-cli not found. Install it or pass -ArduinoCliPath."
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

if ([string]::IsNullOrWhiteSpace($SketchDir)) {
    $SketchDir = Join-Path $RepoRoot "sketches\c002_uno_baseline"
}

if ([string]::IsNullOrWhiteSpace($BuildPath)) {
    $BuildPath = Join-Path $RepoRoot ".build\c002_uno_cli"
}

$tylerLibPath = Join-Path $RepoRoot "libraries\Tyler_1"
$afmotorLibPath = Join-Path $RepoRoot "Adafruit-Motor-Shield-library-master"
$cli = Resolve-ArduinoCli -ManualPath $ArduinoCliPath

if (-not (Test-Path $SketchDir)) {
    throw "Sketch directory not found: $SketchDir"
}

if (-not (Test-Path $tylerLibPath)) {
    throw "Tyler controlled library path not found: $tylerLibPath"
}

if (-not (Test-Path $afmotorLibPath)) {
    throw "AFMotor library path not found: $afmotorLibPath"
}

$coreList = & $cli core list | Out-String
if ($LASTEXITCODE -ne 0) {
    throw "Failed to list installed cores by arduino-cli."
}

if ($coreList -notmatch "arduino:avr") {
    throw "Core arduino:avr is not installed. Run tools/setup_arduino_cli.ps1 first."
}

$libList = & $cli lib list | Out-String
if ($LASTEXITCODE -ne 0) {
    throw "Failed to list installed libraries by arduino-cli."
}

if ($libList -notmatch "(?i)\bServo\b") {
    throw "Library Servo is not installed. Run tools/setup_arduino_cli.ps1 first."
}

New-Item -ItemType Directory -Force $BuildPath | Out-Null

& $cli compile `
    --fqbn $Fqbn `
    --warnings all `
    --build-path $BuildPath `
    --library $tylerLibPath `
    --library $afmotorLibPath `
    $SketchDir

if ($LASTEXITCODE -ne 0) {
    throw "Compile failed with exit code $LASTEXITCODE"
}

Write-Host "Compile succeeded via arduino-cli."
