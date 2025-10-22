@echo off
REM Excel Data Visualizer Launcher - Windows Batch Script

echo Starting Excel Data Visualizer...
powershell -ExecutionPolicy Bypass -File "%~dp0run.ps1" start
pause
