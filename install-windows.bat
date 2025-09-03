@echo off
REM Excel Data Visualizer - Windows Installation Script (Batch)
REM This is a simplified installer for users who prefer batch files

setlocal enabledelayedexpansion

title Excel Data Visualizer - Windows Setup

echo =============================================
echo    Excel Data Visualizer - Windows Setup    
echo =============================================
echo.

echo [INFO] Checking system requirements...

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python not found. Please install Python 3.7+ (tested up to 3.12) from https://python.org
    echo [INFO] Make sure to check "Add Python to PATH" during installation
    echo.
    echo Press any key to continue after installing Python...
    pause >nul
)

REM Check for Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Node.js not found. Please install Node.js from https://nodejs.org
    echo.
    echo Press any key to continue after installing Node.js...
    pause >nul
)

echo [SUCCESS] System requirements check completed

echo.
echo [INFO] Setting up Excel Data Visualizer...

REM Create Python virtual environment
echo [INFO] Creating Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    goto :error
)

REM Activate virtual environment and install dependencies
echo [INFO] Installing Python dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies
    goto :error
)

REM Install Node.js dependencies
echo [INFO] Installing Node.js dependencies...
npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies
    goto :error
)

REM Create run scripts
echo [INFO] Creating launcher scripts...

REM Create PowerShell runner
echo # Excel Data Visualizer Launcher > run.ps1
echo param([string]$Action = "start") >> run.ps1
echo if ($Action -eq "start") { >> run.ps1
echo     Write-Host "Starting Excel Data Visualizer..." >> run.ps1
echo     Start-Process -FilePath "cmd" -ArgumentList "/c", "cd /d `"$PWD`" && venv\Scripts\activate.bat && cd backend && python app.py" -WindowStyle Hidden >> run.ps1
echo     Start-Sleep -Seconds 3 >> run.ps1
echo     Start-Process -FilePath "cmd" -ArgumentList "/c", "cd /d `"$PWD`" && npm start" -WindowStyle Hidden >> run.ps1
echo     Start-Sleep -Seconds 5 >> run.ps1
echo     Start-Process "http://localhost:3000" >> run.ps1
echo     Write-Host "Excel Data Visualizer is running!" >> run.ps1
echo     Write-Host "Frontend: http://localhost:3000" >> run.ps1
echo     Write-Host "Backend:  http://localhost:5001" >> run.ps1
echo } >> run.ps1

REM Create simple batch runner
echo @echo off > run.bat
echo title Excel Data Visualizer >> run.bat
echo echo Starting Excel Data Visualizer... >> run.bat
echo start /min cmd /c "cd /d %%~dp0 && venv\Scripts\activate.bat && cd backend && python app.py" >> run.bat
echo timeout /t 3 /nobreak ^>nul >> run.bat
echo start /min cmd /c "cd /d %%~dp0 && npm start" >> run.bat
echo timeout /t 5 /nobreak ^>nul >> run.bat
echo start http://localhost:3000 >> run.bat
echo echo. >> run.bat
echo echo Excel Data Visualizer is running! >> run.bat
echo echo Frontend: http://localhost:3000 >> run.bat
echo echo Backend:  http://localhost:5001 >> run.bat
echo echo. >> run.bat
echo echo Close this window to stop the servers >> run.bat
echo pause >> run.bat

REM Create desktop shortcut
echo [INFO] Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Excel Data Visualizer.lnk'); $Shortcut.TargetPath = '%CD%\run.bat'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.Description = 'Excel Data Visualizer'; $Shortcut.Save()" >nul 2>&1

REM Test installation
echo [INFO] Testing installation...
call venv\Scripts\activate.bat
python -c "import pandas, flask, plotly, openpyxl; print('Python dependencies OK')" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python dependencies test failed
    goto :error
)

if not exist "node_modules" (
    echo [ERROR] Node.js dependencies missing
    goto :error
)

echo [SUCCESS] Installation test passed!

echo.
echo =============================================
echo [SUCCESS] Installation completed successfully!
echo =============================================
echo.
echo To start the application:
echo   Double-click "run.bat"
echo   OR use the desktop shortcut "Excel Data Visualizer"
echo.
echo The application will be available at:
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:5001
echo.
echo The browser should open automatically when starting.
echo.
echo Press any key to exit...
pause >nul
goto :end

:error
echo.
echo [ERROR] Installation failed!
echo Please check the error messages above and try again.
echo.
echo Common solutions:
echo - Make sure Python 3.7+ (tested up to 3.12) is installed and in PATH
echo - Make sure Node.js 14+ is installed and in PATH
echo - Run as Administrator if permission errors occur
echo - Check your internet connection for downloading dependencies
echo.
pause
exit /b 1

:end
exit /b 0