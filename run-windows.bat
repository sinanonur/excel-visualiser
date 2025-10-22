@echo off
echo Starting Excel Data Science Visualizer...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.11 from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set pyversion=%%i
set pyver_major_minor=%pyversion:~0,4%
if not "%pyver_major_minor%" == "3.11" (
    echo Warning: Python version is %pyversion%, recommended is Python 3.11
    echo Some features may not work correctly with other versions
    echo.
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM Start backend server in a new window
echo Starting backend server (port 5001)...
start "Backend Server" cmd /k "call venv\Scripts\activate.bat && python start_backend.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server
echo Starting frontend server (port 3000)...
echo Please wait for npm install and server startup...
call npm install
start "Frontend Server" cmd /k "npm start"

echo.
echo Both servers are starting...
echo Backend: http://localhost:5001
echo Frontend: http://localhost:3000
echo.
echo Press any key to keep this window open or close it to terminate both servers.
pause >nul