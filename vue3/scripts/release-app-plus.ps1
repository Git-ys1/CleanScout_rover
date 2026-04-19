$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$currentPath = (Get-Location).Path

if ($currentPath -ne $repoRoot.Path) {
  Write-Error "Run this script from the repo root. Current directory: $currentPath"
  exit 1
}

Write-Error 'build:app-plus is not enabled in this repo. This script is a placeholder only. CLI app resources or wgt will be added later, and APK/IPA cloud packaging remains on HBuilderX for Windows.'
exit 1
