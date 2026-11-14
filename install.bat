@echo off
rem Starts the UI+ installer, install.ps1, in PowerShell. Both are plain text: open them in Notepad to see what they do.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
echo.
pause
