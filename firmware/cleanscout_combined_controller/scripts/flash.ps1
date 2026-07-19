param(
    [string]$ProgrammerCliPath = 'F:\CodeForge\STM32CubeIDE_2.1.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.win32_2.2.400.202601091506\tools\bin\STM32_Programmer_CLI.exe',
    [switch]$BuildFirst
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$hexPath = Join-Path $projectRoot 'Build\Objects\CleanScout_Combined.hex'

if ($BuildFirst) { & (Join-Path $PSScriptRoot 'build.ps1') -StrictWarnings }
if (-not (Test-Path -LiteralPath $ProgrammerCliPath)) { throw "STM32CubeProgrammer CLI not found: $ProgrammerCliPath" }
if (-not (Test-Path -LiteralPath $hexPath)) { throw "HEX not found: $hexPath" }

$probeList = & $ProgrammerCliPath -l 2>&1
$probeList
if ($probeList -match 'No ST-Link detected') { throw 'ST-Link not detected.' }

& $ProgrammerCliPath -c port=SWD -w $hexPath -v -rst
if ($LASTEXITCODE -ne 0) { throw "Flash failed; exit code=$LASTEXITCODE" }

# Some ST-Link/CubeProgrammer combinations leave the core halted after reset.
& $ProgrammerCliPath -c port=SWD -g 0x08000000
if ($LASTEXITCODE -ne 0) { throw "Flash verified but explicit start failed; exit code=$LASTEXITCODE" }
Write-Host 'Flash, verify, reset, and explicit start completed.'
