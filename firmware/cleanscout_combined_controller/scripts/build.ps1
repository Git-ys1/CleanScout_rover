param(
    [string]$Uv4Path = 'D:\Work\Keil5\UV4\UV4.exe',
    [switch]$StrictWarnings
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPath = Join-Path $projectRoot 'CleanScout_Combined.uvprojx'
$buildDirectory = Join-Path $projectRoot 'Build'
$logPath = Join-Path $buildDirectory 'build.log'

if (-not (Test-Path -LiteralPath $Uv4Path)) { throw "Keil UV4 not found: $Uv4Path" }
if (-not (Test-Path -LiteralPath $projectPath)) { throw "Keil project not found: $projectPath" }

New-Item -ItemType Directory -Force -Path $buildDirectory | Out-Null
Remove-Item -LiteralPath $logPath -Force -ErrorAction SilentlyContinue
& $Uv4Path -r $projectPath -j0 -o $logPath

$log = ''
for ($attempt = 0; $attempt -lt 600; $attempt++) {
    if (Test-Path -LiteralPath $logPath) {
        $log = Get-Content -LiteralPath $logPath -Raw
        if ($log -match 'Error\(s\), \d+ Warning\(s\)') { break }
    }
    Start-Sleep -Milliseconds 100
}

if ($log -notmatch 'Error\(s\), \d+ Warning\(s\)') { throw "Keil build did not finish within 60 seconds: $logPath" }
$log
if ($log -notmatch '0 Error\(s\), (\d+) Warning\(s\)') { throw 'Keil build contains errors.' }
$warningCount = [int]$Matches[1]
if ($StrictWarnings -and $warningCount -ne 0) { throw "StrictWarnings requires 0 warnings; actual=$warningCount" }

$hexPath = Join-Path $projectRoot 'Build\Objects\CleanScout_Combined.hex'
$axfPath = Join-Path $projectRoot 'Build\Objects\CleanScout_Combined.axf'
$mapPath = Join-Path $projectRoot 'Build\Listings\CleanScout_Combined.map'
foreach ($path in @($hexPath, $axfPath, $mapPath)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing build artifact: $path" }
}

Write-Host "Build passed: $hexPath"
