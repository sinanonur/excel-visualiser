@echo off
REM Frontend launcher with error visibility
echo =========================================
echo Excel Data Visualizer - Frontend Server
echo =========================================
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

echo Checking for frontend...
if exist "frontend\index.html" (
    echo [OK] Found: frontend\index.html
    dir /b frontend\*.* | find /c /v "" > temp_count.txt
    set /p FILE_COUNT=<temp_count.txt
    del temp_count.txt
    echo [INFO] Files in frontend: %FILE_COUNT%
) else (
    echo [ERROR] NOT FOUND: frontend\index.html
    echo.
    echo Checking if bundle exists...
    if exist "bundle\frontend-build\index.html" (
        echo [OK] Found: bundle\frontend-build\index.html
        echo.
        echo [FIX] Copying frontend files from bundle...
        xcopy /E /I /Y bundle\frontend-build frontend
        echo.
    ) else (
        echo [ERROR] Bundle not found either!
        echo.
        pause
        exit /b 1
    )
)
echo.

echo Starting frontend server...
echo Command: python\python.exe -m http.server 3000
echo Working directory: %CD%\frontend
echo.
echo ----------------------------------------
cd frontend
..\python\python.exe -m http.server 3000

echo.
echo ----------------------------------------
echo Frontend server stopped (exit code: %ERRORLEVEL%)
echo.
pause
