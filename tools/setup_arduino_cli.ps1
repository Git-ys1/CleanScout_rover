param(
    [string]$ArduinoCliPath = ""
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

$cli = Resolve-ArduinoCli -ManualPath $ArduinoCliPath

& $cli version
if ($LASTEXITCODE -ne 0) {
    throw "Failed to execute arduino-cli version."
}

& $cli core update-index
if ($LASTEXITCODE -ne 0) {
    throw "Failed to update core index."
}

$coreList = & $cli core list | Out-String
if ($LASTEXITCODE -ne 0) {
    throw "Failed to list installed cores."
}

if ($coreList -match "arduino:avr") {
    Write-Host "Core arduino:avr already installed."
} else {
    & $cli core install arduino:avr
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install core arduino:avr."
    }
}

& $cli lib update-index
if ($LASTEXITCODE -ne 0) {
    throw "Failed to update library index."
}

$libList = & $cli lib list | Out-String
if ($LASTEXITCODE -ne 0) {
    throw "Failed to list installed libraries."
}

if ($libList -match "(?i)\bServo\b") {
    Write-Host "Library Servo already installed."
} else {
    & $cli lib install Servo
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install library Servo."
    }
}

Write-Host "arduino-cli setup finished."
