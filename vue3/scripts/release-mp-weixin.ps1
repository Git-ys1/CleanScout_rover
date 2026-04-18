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

if ($packageJson -notmatch '"build:mp-weixin"\s*:') {
  Write-Error 'build:mp-weixin is not defined in package.json.'
  exit 1
}

Write-Host 'Running mini program build: npm run build:mp-weixin'
cmd /c npm.cmd run build:mp-weixin

if ($LASTEXITCODE -ne 0) {
  Write-Error 'Mini program build failed.'
  exit $LASTEXITCODE
}

$artifactDir = Join-Path $repoRoot 'dist\build\mp-weixin'
$resolvedArtifactDir = [System.IO.Path]::GetFullPath($artifactDir)

Write-Host ''
Write-Host 'Mini program build finished.'
Write-Host "Artifact directory: $resolvedArtifactDir"
Write-Host 'Next step: import that dist/build/mp-weixin directory into WeChat DevTools.'
