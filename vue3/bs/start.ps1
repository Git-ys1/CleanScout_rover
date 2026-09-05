param([switch]$Chat)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$entryScript = if ($Chat) { 'agent.py' } else { 'server.py' }
$runtime = Join-Path $PSScriptRoot '.python\python.exe'
if (-not (Test-Path -LiteralPath $runtime)) {
    throw 'Missing bs/.python/python.exe. See README.md.'
}
& $runtime -B $entryScript
exit $LASTEXITCODE
