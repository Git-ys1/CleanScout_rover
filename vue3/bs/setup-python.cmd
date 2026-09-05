@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; if (Test-Path -LiteralPath '.python') { throw '.python already exists; keeping it unchanged.' }; $archive='python-3.13.15-embed-amd64.zip'; Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.13.15/python-3.13.15-embed-amd64.zip' -OutFile $archive; if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne 'd1f04d990aee1253d8569e8e5104e30fa9f5fa830899f14843448872d936a2cf') { throw 'SHA256 mismatch' }; Expand-Archive -LiteralPath $archive -DestinationPath '.python'; Add-Content -LiteralPath '.python/python313._pth' -Value '..' -Encoding ASCII; Write-Output 'Python is ready. Configure .env, then run chat.cmd or web.cmd.'"
exit /b %errorlevel%
