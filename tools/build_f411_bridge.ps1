param(
    [string]$CubeIdeRoot = "F:\CodeForge\STM32CubeIDE_2.1.0\STM32CubeIDE",
    [string]$RepoRoot = "",
    [string]$BuildPath = "",
    [string]$ArtifactDir = ""
)

function Resolve-ToolPath {
    param(
        [string]$Root,
        [string]$ToolName
    )

    $tool = Get-ChildItem -Path $Root -Recurse -Filter $ToolName -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $tool) {
        throw "$ToolName not found under $Root"
    }
    return $tool.FullName
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

if ([string]::IsNullOrWhiteSpace($BuildPath)) {
    $BuildPath = Join-Path $RepoRoot ".build\cj_bridge_f411"
}

if ([string]::IsNullOrWhiteSpace($ArtifactDir)) {
    $ArtifactDir = Join-Path $RepoRoot "artifacts\C-1.2.2\f411"
}

$projectRoot = Join-Path $RepoRoot "firmware\cj_bridge_f411_cubeide"
$gcc = Resolve-ToolPath -Root $CubeIdeRoot -ToolName "arm-none-eabi-gcc.exe"
$objcopy = Resolve-ToolPath -Root $CubeIdeRoot -ToolName "arm-none-eabi-objcopy.exe"

$includeDirs = @(
    Join-Path $projectRoot "Core\Inc"
)

$cSources = @(
    [System.IO.Path]::Combine($projectRoot, 'Core\Src\cj_ring_buffer.c'),
    [System.IO.Path]::Combine($projectRoot, 'Core\Src\cj_bridge_protocol.c'),
    [System.IO.Path]::Combine($projectRoot, 'Core\Src\cj_bridge.c'),
    [System.IO.Path]::Combine($projectRoot, 'Core\Src\main.c')
)

$startupFile = Join-Path $projectRoot "startup_stm32f411xe.s"
$linkerScript = Join-Path $projectRoot "stm32f411_flash.ld"
$elfPath = Join-Path $ArtifactDir "cj_bridge_f411.elf"
$hexPath = Join-Path $ArtifactDir "cj_bridge_f411.hex"
$mapPath = Join-Path $ArtifactDir "cj_bridge_f411.map"

New-Item -ItemType Directory -Force $BuildPath | Out-Null
New-Item -ItemType Directory -Force $ArtifactDir | Out-Null

$commonFlags = @(
    '-mcpu=cortex-m4',
    '-mthumb',
    '-ffunction-sections',
    '-fdata-sections',
    '-fno-common',
    '-Wall',
    '-Wextra',
    '-Werror',
    '-Os',
    '-std=c11'
)

$includeFlags = foreach ($dir in $includeDirs) { "-I$dir" }
$objectFiles = @()

foreach ($source in $cSources) {
    $object = Join-Path $BuildPath (([System.IO.Path]::GetFileNameWithoutExtension($source)) + '.o')
    $compileArgs = @()
    $compileArgs += $commonFlags
    $compileArgs += $includeFlags
    $compileArgs += '-c', $source, '-o', $object
    & $gcc $compileArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Compile failed: $source"
    }
    $objectFiles += $object
}

$startupObject = Join-Path $BuildPath 'startup_stm32f411xe.o'
$startupArgs = @('-mcpu=cortex-m4', '-mthumb', '-c', $startupFile, '-o', $startupObject)
& $gcc $startupArgs
if ($LASTEXITCODE -ne 0) {
    throw "Assemble failed: $startupFile"
}
$objectFiles += $startupObject

$linkFlags = @(
    '-mcpu=cortex-m4',
    '-mthumb',
    '-T', $linkerScript,
    '-Wl,--gc-sections',
    "-Wl,-Map=$mapPath",
    '-specs=nano.specs',
    '-specs=nosys.specs'
)

$linkArgs = @()
$linkArgs += $linkFlags
$linkArgs += $objectFiles
$linkArgs += '-o', $elfPath
& $gcc $linkArgs
if ($LASTEXITCODE -ne 0) {
    throw 'Link failed.'
}

$objcopyArgs = @('-O', 'ihex', $elfPath, $hexPath)
& $objcopy $objcopyArgs
if ($LASTEXITCODE -ne 0) {
    throw 'HEX generation failed.'
}

Write-Host "Built: $elfPath"
Write-Host "Built: $hexPath"
