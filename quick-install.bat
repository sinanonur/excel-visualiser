@echo off
REM Quick Install Script for Excel Data Visualizer - Windows
REM This script provides the fastest way to get started

echo ==============================================
echo   Excel Data Visualizer - Quick Install
echo ==============================================
echo.

REM Check for Docker
where docker >nul 2>nul
if %errorlevel% equ 0 (
    where docker-compose >nul 2>nul
    if %errorlevel% equ 0 (
        echo [INFO] Docker detected! Using containerized installation
        echo.
        echo [INFO] Building Docker image...
        docker-compose build

        echo.
        echo [SUCCESS] Installation complete!
        echo.
        echo [INFO] To start the application, run:
        echo   docker-compose up
        echo.
        echo [INFO] The application will be available at:
        echo   http://localhost:3000
        echo.
        echo [INFO] To stop the application:
        echo   docker-compose down
        echo.
        pause
        exit /b 0
    )
)

echo [WARNING] Docker not found. Installing dependencies locally...
echo.

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 is required but not installed.
    echo [INFO] Please install Python 3.7+ from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Check Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is required but not installed.
    echo [INFO] Please install Node.js 14+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Python and Node.js found
echo.

REM Install Python dependencies
echo [INFO] Creating Python virtual environment...
python -m venv venv

echo [INFO] Installing Python dependencies...
call venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

REM Install Node.js dependencies
echo [INFO] Installing Node.js dependencies...
call npm install --silent

echo.
echo [SUCCESS] Installation complete!
echo.

REM Create simple run script
echo @echo off > run-quick.bat
echo cd /d "%%~dp0" >> run-quick.bat
echo call venv\Scripts\activate.bat >> run-quick.bat
echo start "Backend Server" /min python start_backend.py >> run-quick.bat
echo timeout /t 3 /nobreak ^>nul >> run-quick.bat
echo start "Frontend Server" npm start >> run-quick.bat
echo echo. >> run-quick.bat
echo echo Excel Data Visualizer is starting... >> run-quick.bat
echo echo Frontend: http://localhost:3000 >> run-quick.bat
echo echo Backend:  http://localhost:5001 >> run-quick.bat
echo timeout /t 5 /nobreak >> run-quick.bat
echo start http://localhost:3000 >> run-quick.bat

echo [INFO] To start the application, run:
echo   run-quick.bat
echo.
echo [INFO] Or use the PowerShell script:
echo   .\run.ps1 start
echo.
pause
