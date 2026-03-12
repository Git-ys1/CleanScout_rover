param(
    [string]$ArduinoHome = "F:\AcademicHub\Arduino",
    [string]$RepoRoot = "",
    [string]$SketchPath = "",
    [string]$BuildPath = ""
)

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

if ([string]::IsNullOrWhiteSpace($SketchPath)) {
    $SketchPath = Join-Path $RepoRoot "Tyler_1_Library\examples\Tyler_1\Tyler_1.ino"
}

if ([string]::IsNullOrWhiteSpace($BuildPath)) {
    $BuildPath = Join-Path $RepoRoot ".build\tyler1_uno"
}

$builder = Join-Path $ArduinoHome "arduino-builder.exe"
$hardware = Join-Path $ArduinoHome "hardware"
$toolsBuilder = Join-Path $ArduinoHome "tools-builder"
$toolsAvr = Join-Path $ArduinoHome "hardware\tools\avr"
$builtinLibs = Join-Path $ArduinoHome "libraries"

if (-not (Test-Path $builder)) {
    throw "arduino-builder not found: $builder"
}

if (-not (Test-Path $SketchPath)) {
    throw "Sketch not found: $SketchPath"
}

New-Item -ItemType Directory -Force $BuildPath | Out-Null

& $builder `
    -compile `
    -logger=human `
    -hardware $hardware `
    -tools $toolsBuilder `
    -tools $toolsAvr `
    -built-in-libraries $builtinLibs `
    -libraries $RepoRoot `
    -fqbn arduino:avr:uno `
    -build-path $BuildPath `
    -warnings all `
    $SketchPath

if ($LASTEXITCODE -ne 0) {
    throw "Compile failed with exit code $LASTEXITCODE"
}

Write-Host "Compile succeeded."
