param(
    [string]$ProgrammerCliPath =
        'F:\CodeForge\STM32CubeIDE_2.1.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.win32_2.2.400.202601091506\tools\bin\STM32_Programmer_CLI.exe',
    [switch]$BuildFirst
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$hexPath = Join-Path $projectRoot 'Build\Objects\OpenRF1_Motion.hex'

if ($BuildFirst) {
    & (Join-Path $PSScriptRoot 'build.ps1')
}

if (-not (Test-Path -LiteralPath $ProgrammerCliPath)) {
    throw "未找到 STM32CubeProgrammer CLI：$ProgrammerCliPath"
}

if (-not (Test-Path -LiteralPath $hexPath)) {
    throw "未找到待烧录 HEX，请先执行 build.ps1：$hexPath"
}

Write-Host '正在检测 STLink...'
$probeList = & $ProgrammerCliPath -l 2>&1
$probeList

if ($probeList -match 'No ST-Link detected') {
    throw '未检测到 STLink。请检查 USB 数据线、驱动和探针设备状态。'
}

Write-Host "正在烧录：$hexPath"
& $ProgrammerCliPath -c port=SWD -w $hexPath -v -rst

if ($LASTEXITCODE -ne 0) {
    throw "烧录失败，STM32CubeProgrammer 返回码：$LASTEXITCODE"
}

Write-Host '烧录、校验和复位完成。'

