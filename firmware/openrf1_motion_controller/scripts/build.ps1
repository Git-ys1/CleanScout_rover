param(
    [string]$Uv4Path = 'D:\Work\Keil5\UV4\UV4.exe',
    [switch]$StrictWarnings
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPath = Join-Path $projectRoot 'OpenRF1_Motion.uvprojx'
$buildDirectory = Join-Path $projectRoot 'Build'
$logPath = Join-Path $buildDirectory 'build.log'

if (-not (Test-Path -LiteralPath $Uv4Path)) {
    throw "未找到 Keil UV4：$Uv4Path"
}

if (-not (Test-Path -LiteralPath $projectPath)) {
    throw "未找到 Keil 工程：$projectPath"
}

New-Item -ItemType Directory -Force -Path $buildDirectory | Out-Null

Remove-Item -LiteralPath $logPath -Force -ErrorAction SilentlyContinue
& $Uv4Path -b $projectPath -j0 -o $logPath

# UV4 在已有 GUI 实例时可能先返回，再异步完成编译。等待最终结果写入日志。
$log = ''
for ($attempt = 0; $attempt -lt 300; $attempt++) {
    if (Test-Path -LiteralPath $logPath) {
        $log = Get-Content -LiteralPath $logPath -Raw
        if ($log -match 'Error\(s\), \d+ Warning\(s\)') {
            break
        }
    }
    Start-Sleep -Milliseconds 100
}

if ($log -notmatch 'Error\(s\), \d+ Warning\(s\)') {
    throw "Keil 未在 30 秒内完成构建：$logPath"
}

$log

if ($log -notmatch '0 Error\(s\), (\d+) Warning\(s\)') {
    throw 'Keil 编译存在错误，请检查上方日志。'
}

$warningCount = [int]$Matches[1]
if ($StrictWarnings -and $warningCount -ne 0) {
    throw "Keil 编译有 $warningCount 个告警；StrictWarnings 模式要求 0 Warning。"
}

if ($warningCount -ne 0) {
    Write-Warning "构建包含 $warningCount 个已显示告警；固件源代码未为清告警而改变控制行为。"
}

$hexPath = Join-Path $projectRoot 'Build\Objects\OpenRF1_Motion.hex'
if (-not (Test-Path -LiteralPath $hexPath)) {
    throw "编译成功但未找到 HEX：$hexPath"
}

Write-Host "构建通过：$hexPath"
