@echo off
REM Backend launcher with error visibility
echo ========================================
echo Excel Data Visualizer - Backend Server
echo ========================================
echo.

cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo Checking for Python...
if exist "python\python.exe" (
    echo [OK] Found: python\python.exe
) else (
    echo [ERROR] NOT FOUND: python\python.exe
    echo.
    pause
    exit /b 1
)
echo.

echo Checking for backend...
if exist "backend\app.py" (
    echo [OK] Found: backend\app.py
) else (
    echo [ERROR] NOT FOUND: backend\app.py
    echo.
    pause
    exit /b 1
)
echo.

echo Starting backend server...
echo Command: python\python.exe backend\app.py
echo.
echo ----------------------------------------
python\python.exe backend\app.py

echo.
echo ----------------------------------------
echo Backend server stopped (exit code: %ERRORLEVEL%)
echo.
pause
