@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0patch-cfw.ps1" %*
exit /b %errorlevel%
