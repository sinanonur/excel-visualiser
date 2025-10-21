# Standalone Build Script for Windows - Bundles Python and all dependencies
# Creates a fully portable application requiring NO external dependencies

param(
    [string]$PythonVersion = "3.11.5"
)

$ErrorActionPreference = "Stop"

# Colors
$Colors = @{
    Info = 'Blue'
    Success = 'Green'
    Warning = 'Yellow'
}

function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor $Colors.Info }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Success }
function Write-Warning { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Warning }

Write-Host "============================================================"
Write-Host "  Excel Data Visualizer - Standalone Build (with Python)  "
Write-Host "============================================================"
Write-Host ""

# URLs for embedded Python
$PythonEmbedUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"

# Clean previous builds
Write-Info "Cleaning previous builds..."
Remove-Item -Path "standalone", "build", "dist" -Recurse -Force -ErrorAction SilentlyContinue

# Create standalone directory structure
Write-Info "Creating standalone directory structure..."
New-Item -ItemType Directory -Path "standalone/app" -Force | Out-Null
New-Item -ItemType Directory -Path "standalone/python" -Force | Out-Null
New-Item -ItemType Directory -Path "standalone/runtime" -Force | Out-Null

# Download embedded Python
Write-Info "Downloading Python $PythonVersion embedded..."
$pythonZip = "standalone/python-embed.zip"
Invoke-WebRequest -Uri $PythonEmbedUrl -OutFile $pythonZip

Write-Info "Extracting Python..."
Expand-Archive -Path $pythonZip -DestinationPath "standalone/python" -Force
Remove-Item $pythonZip

# Enable site-packages in embedded Python
$pthFile = Get-ChildItem "standalone/python" -Filter "*._pth" | Select-Object -First 1
if ($pthFile) {
    $content = Get-Content $pthFile.FullName
    $content = $content -replace "#import site", "import site"
    $content | Set-Content $pthFile.FullName
    Add-Content $pthFile.FullName "Lib`nLib/site-packages"
}

# Download and install pip
Write-Info "Installing pip in embedded Python..."
Invoke-WebRequest -Uri $GetPipUrl -OutFile "standalone/python/get-pip.py"
& "standalone/python/python.exe" "standalone/python/get-pip.py" --no-warn-script-location

# Install dependencies
Write-Info "Installing Python dependencies (this may take several minutes)..."
& "standalone/python/python.exe" -m pip install --no-warn-script-location -r requirements.txt

# Install PyInstaller
Write-Info "Installing PyInstaller..."
& "standalone/python/python.exe" -m pip install --no-warn-script-location pyinstaller

# Build frontend
Write-Info "Building optimized frontend..."
npm run build
Copy-Item -Path "build" -Destination "standalone/app/frontend" -Recurse

# Copy backend
Write-Info "Copying backend application..."
Copy-Item -Path "backend" -Destination "standalone/app/backend" -Recurse
Copy-Item -Path "start_backend.py" -Destination "standalone/app/"
Copy-Item -Path "requirements.txt" -Destination "standalone/app/"

# Build standalone backend with PyInstaller
Write-Info "Building standalone backend executable (this may take a few minutes)..."
& "standalone/python/python.exe" -m PyInstaller backend.spec --clean --distpath "standalone/runtime"

# Calculate sizes
$PythonSize = (Get-ChildItem -Path "standalone/python" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
$BackendSize = (Get-ChildItem -Path "standalone/runtime" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
$FrontendSize = (Get-ChildItem -Path "standalone/app/frontend" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB

# Create launcher batch file
Write-Info "Creating launcher script..."
@'
@echo off
cd /d "%~dp0"

echo ==========================================
echo   Excel Data Visualizer is starting...
echo ==========================================
echo.

REM Start backend
start "Backend Server" /min runtime\excel-visualizer-backend\excel-visualizer-backend.exe

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend using Python's built-in server
cd app\frontend
start "Frontend Server" /min ..\..python\python.exe -m http.server 3000

REM Wait a moment
timeout /t 2 /nobreak >nul

echo.
echo ==========================================
echo   Excel Data Visualizer is running!
echo ==========================================
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:5001
echo.
echo Opening browser...
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo To stop the application, close this window
echo or press Ctrl+C and close the server windows.
echo.
pause
'@ | Out-File -FilePath "standalone/launch.bat" -Encoding ASCII

# Create PowerShell launcher (alternative)
@'
# Excel Data Visualizer Standalone Launcher
$Host.UI.RawUI.WindowTitle = "Excel Data Visualizer"

Write-Host "=========================================="
Write-Host "  Excel Data Visualizer is starting..."
Write-Host "=========================================="
Write-Host ""

# Start backend
$backendProcess = Start-Process -FilePath "runtime\excel-visualizer-backend\excel-visualizer-backend.exe" -PassThru -WindowStyle Hidden

# Wait for backend
Start-Sleep -Seconds 3

# Start frontend
Set-Location "app\frontend"
$frontendProcess = Start-Process -FilePath "..\..\python\python.exe" -ArgumentList "-m", "http.server", "3000" -PassThru -WindowStyle Hidden
Set-Location "..\..\"

Write-Host ""
Write-Host "=========================================="
Write-Host "  Excel Data Visualizer is running!"
Write-Host "=========================================="
Write-Host ""
Write-Host "  Frontend: http://localhost:3000"
Write-Host "  Backend:  http://localhost:5001"
Write-Host ""

# Open browser
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"

Write-Host "Press Ctrl+C to stop the servers"
Write-Host ""

# Wait and cleanup on exit
try {
    while ($true) {
        Start-Sleep -Seconds 1
        if ($backendProcess.HasExited -or $frontendProcess.HasExited) {
            break
        }
    }
} finally {
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
}
'@ | Out-File -FilePath "standalone/launch.ps1" -Encoding UTF8

# Create README
@"
Excel Data Visualizer - Standalone Edition (Windows)
====================================================

This is a fully self-contained version of Excel Data Visualizer.
NO installation required - all dependencies are bundled!

QUICK START
-----------

Simply double-click:
  launch.bat

Or run in PowerShell:
  .\launch.ps1

The application will start automatically and open in your browser at:
  http://localhost:3000

WHAT'S INCLUDED
---------------

- Python $PythonVersion embedded runtime
- All required Python libraries (pandas, flask, plotly, etc.)
- React frontend (pre-built, optimized)
- Flask backend (compiled executable)
- No external dependencies needed!

SIZE BREAKDOWN
--------------

Total Package: ~$([math]::Round($PythonSize + $BackendSize + $FrontendSize, 0)) MB
- Python runtime + libraries: ~$([math]::Round($PythonSize, 0)) MB
- Backend executable: ~$([math]::Round($BackendSize, 0)) MB
- Frontend build: ~$([math]::Round($FrontendSize, 0)) MB

SYSTEM REQUIREMENTS
-------------------

- Windows 10 or later (64-bit)
- RAM: 512 MB minimum, 1 GB recommended
- Disk: 600 MB free space
- No administrator rights required
- No Python/Node.js installation needed

PORTABLE USE
------------

This application is fully portable:
1. Copy the entire 'standalone' folder anywhere
2. Run launch.bat from the new location
3. Works from USB drives, network shares, etc.

TROUBLESHOOTING
---------------

Port already in use:
  If ports 3000 or 5001 are already in use:
  1. Close other applications using these ports
  2. Or modify the ports in launch.bat

Firewall warning:
  Windows may ask for firewall permission
  Click "Allow access" to enable the application

Can't start:
  Make sure you have:
  - Extracted all files
  - Not running from a restricted location
  - Sufficient disk space

SUPPORT
-------

For issues and updates:
  https://github.com/yourusername/excel-visualiser

Version: 1.0.0
Build date: $(Get-Date -Format "yyyy-MM-dd")
"@ | Out-File -FilePath "standalone/README.txt" -Encoding UTF8

# Calculate total size
$TotalSize = (Get-ChildItem -Path "standalone" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB

Write-Success "Standalone build complete!"
Write-Host ""
Write-Host "=========================================="
Write-Host "Build Statistics (including Python):"
Write-Host "=========================================="
Write-Host "  Python runtime:       $([math]::Round($PythonSize, 1)) MB"
Write-Host "  Backend executable:   $([math]::Round($BackendSize, 1)) MB"
Write-Host "  Frontend build:       $([math]::Round($FrontendSize, 1)) MB"
Write-Host "  TOTAL PACKAGE SIZE:   $([math]::Round($TotalSize, 1)) MB"
Write-Host ""
Write-Info "Standalone package location: .\standalone\"
Write-Host ""

Write-Info "To distribute:"
Write-Host "  1. Create ZIP: Compress-Archive -Path standalone -DestinationPath excel-visualizer-standalone-windows.zip"
Write-Host "  2. Users extract and run: launch.bat"
Write-Host "  3. No installation needed!"
Write-Host ""

Write-Info "Creating distribution package..."
Compress-Archive -Path "standalone" -DestinationPath "excel-visualizer-standalone-windows.zip" -Force

$ArchiveSize = (Get-Item "excel-visualizer-standalone-windows.zip").Length / 1MB
Write-Success "Distribution package created: excel-visualizer-standalone-windows.zip ($([math]::Round($ArchiveSize, 1)) MB compressed)"
Write-Host ""
