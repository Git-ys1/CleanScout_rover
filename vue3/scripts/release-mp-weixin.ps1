$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$currentPath = (Get-Location).Path

if ($currentPath -ne $repoRoot.Path) {
  Write-Error "Run this script from the repo root. Current directory: $currentPath"
  exit 1
}

$packageJsonPath = Join-Path $repoRoot 'package.json'

if (-not (Test-Path $packageJsonPath)) {
  Write-Error 'package.json was not found. Current directory is not a valid vue3 repo root.'
  exit 1
}

$packageJson = Get-Content -Encoding utf8 $packageJsonPath -Raw

if ($packageJson -notmatch '"build:mp-weixin:production"\s*:') {
  Write-Error 'build:mp-weixin:production is not defined in package.json.'
  exit 1
}

Write-Host 'Running mini program build: npm run build:mp-weixin:production'
cmd /c npm.cmd run build:mp-weixin:production

if ($LASTEXITCODE -ne 0) {
  Write-Error 'Mini program build failed.'
  exit $LASTEXITCODE
}

$artifactDir = Join-Path $repoRoot 'dist\build\mp-weixin'
$resolvedArtifactDir = [System.IO.Path]::GetFullPath($artifactDir)
$projectConfigPath = Join-Path $artifactDir 'project.config.json'

if (-not (Test-Path $projectConfigPath)) {
  Write-Error 'project.config.json was not generated.'
  exit 1
}

$projectConfig = Get-Content -Encoding utf8 $projectConfigPath -Raw | ConvertFrom-Json

if ($projectConfig.appid -ne 'wxce1a2e91132f4c41') {
  Write-Error "Unexpected mp-weixin appid: $($projectConfig.appid). Expected wxce1a2e91132f4c41."
  exit 1
}

Write-Host ''
Write-Host 'Mini program build finished.'
Write-Host "Artifact directory: $resolvedArtifactDir"
Write-Host "AppID: $($projectConfig.appid)"
Write-Host 'Next step: import that dist/build/mp-weixin directory into WeChat DevTools.'
