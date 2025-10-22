@echo off
REM Excel Data Visualizer - Virtual Environment Setup Script for Windows
REM Requires Python 3.11+ and Node.js

setlocal enabledelayedexpansion

echo [INFO] Excel Data Visualizer - Virtual Environment Setup
echo [INFO] ==================================================

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Check Python version
echo [INFO] Checking for Python 3.11+...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+ from https://python.org/downloads/
    echo [ERROR] Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Found Python %PYTHON_VERSION%

REM Check if Python version is 3.11+
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% LSS 3 (
    echo [ERROR] Python %PYTHON_VERSION% is too old. Please install Python 3.11+ from https://python.org/downloads/
    pause
    exit /b 1
)

if %MAJOR% EQU 3 if %MINOR% LSS 11 (
    echo [ERROR] Python %PYTHON_VERSION% is too old. Please install Python 3.11+ from https://python.org/downloads/
    pause
    exit /b 1
)

echo [SUCCESS] Python version %PYTHON_VERSION% is compatible

REM Check Node.js
echo [INFO] Checking for Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

for /f %%i in ('node --version') do set NODE_VERSION=%%i
echo [SUCCESS] Found Node.js %NODE_VERSION%

REM Remove existing virtual environment if it exists
if exist "venv" (
    echo [WARNING] Existing virtual environment found. Removing...
    rmdir /s /q venv
)

REM Create virtual environment
echo [INFO] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment and install dependencies
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

echo [INFO] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)

echo [INFO] Installing Node.js dependencies...
npm install
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js dependencies
    pause
    exit /b 1
)

REM Create run script
echo [INFO] Creating run script...
(
echo @echo off
echo REM Excel Data Visualizer - Run Script for Windows
echo.
echo setlocal enabledelayedexpansion
echo.
echo set SCRIPT_DIR=%%~dp0
echo cd /d "%%SCRIPT_DIR%%"
echo.
echo if "%%1"=="stop" goto :stop
echo if "%%1"=="status" goto :status
echo if "%%1"=="restart" goto :restart
echo.
echo :start
echo echo [INFO] Starting Excel Data Visualizer...
echo.
echo REM Check if virtual environment exists
echo if not exist "venv" ^(
echo     echo [ERROR] Virtual environment not found. Please run setup-venv.bat first.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Check for port conflicts
echo netstat -an ^| find ":3000 " ^>nul 2^>^&1
echo if not errorlevel 1 ^(
echo     echo [ERROR] Port 3000 is already in use. Please stop the conflicting service.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo netstat -an ^| find ":5001 " ^>nul 2^>^&1
echo if not errorlevel 1 ^(
echo     echo [ERROR] Port 5001 is already in use. Please stop the conflicting service.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Start backend
echo echo [INFO] Starting backend server on port 5001...
echo start /min "Backend" cmd /c "venv\Scripts\activate.bat && cd backend && python app.py"
echo.
echo REM Wait for backend to start
echo timeout /t 3 /nobreak ^>nul
echo.
echo REM Start frontend
echo echo [INFO] Starting frontend server on port 3000...
echo start /min "Frontend" cmd /c "npm start"
echo.
echo REM Wait for frontend to start
echo timeout /t 5 /nobreak ^>nul
echo.
echo echo [SUCCESS] Application started successfully!
echo echo [INFO] Frontend: http://localhost:3000
echo echo [INFO] Backend:  http://localhost:5001
echo echo [INFO] 
echo echo [INFO] To stop the application, run: run.bat stop
echo.
echo REM Open browser
echo start http://localhost:3000
echo.
echo goto :end
echo.
echo :stop
echo echo [INFO] Stopping Excel Data Visualizer...
echo taskkill /f /im python.exe /fi "WINDOWTITLE eq Backend*" ^>nul 2^>^&1
echo taskkill /f /im node.exe /fi "WINDOWTITLE eq Frontend*" ^>nul 2^>^&1
echo echo [SUCCESS] Application stopped successfully!
echo goto :end
echo.
echo :status
echo echo [INFO] Checking application status...
echo netstat -an ^| find ":3000 " ^>nul 2^>^&1
echo if not errorlevel 1 ^(
echo     echo [SUCCESS] Frontend is running on port 3000
echo ^) else ^(
echo     echo [ERROR] Frontend is not running
echo ^)
echo.
echo netstat -an ^| find ":5001 " ^>nul 2^>^&1
echo if not errorlevel 1 ^(
echo     echo [SUCCESS] Backend is running on port 5001
echo ^) else ^(
echo     echo [ERROR] Backend is not running
echo ^)
echo goto :end
echo.
echo :restart
echo echo [INFO] Restarting Excel Data Visualizer...
echo call :stop
echo timeout /t 2 /nobreak ^>nul
echo call :start
echo goto :end
echo.
echo :end
echo if "%%1"=="" pause
) > run.bat

echo [SUCCESS] Setup completed successfully!
echo [INFO] 
echo [INFO] Next steps:
echo [INFO] 1. Start the application: run.bat
echo [INFO] 2. Open your browser to: http://localhost:3000
echo [INFO] 3. Upload test_data.xlsx to try the application
echo [INFO] 
echo [INFO] Other commands:
echo [INFO] - Stop:    run.bat stop
echo [INFO] - Restart: run.bat restart
echo [INFO] - Status:  run.bat status

pause
