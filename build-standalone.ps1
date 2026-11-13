# Standalone build (Windows): one folder with a single executable that
# contains Python, every library, the API and the web page.
# Users need nothing installed. The build machine needs Node.js; Python is
# downloaded (embedded distribution) and used only to build.

param(
    [string]$PythonVersion = "3.11.5"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }

# Native commands do not stop the script on failure; check their exit codes.
function Invoke-Checked {
    param([string]$Description, [scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Description failed with exit code $LASTEXITCODE" }
}

Write-Host "============================================================"
Write-Host "  Excel Data Visualizer - Standalone Build (Windows)        "
Write-Host "============================================================"
Write-Host ""

$PythonEmbedUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"
# Build-only Python, kept outside the package and reused between builds.
$BuildPythonDir = "standalone-build\python"
$BuildPython = "$BuildPythonDir\python.exe"

Write-Info "Cleaning previous builds..."
Remove-Item -Path "standalone", "build", "dist", "pyinstaller-work" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path "standalone" -Force | Out-Null

if (-not (Test-Path $BuildPython)) {
    Write-Info "Downloading Python $PythonVersion (embedded) for the build..."
    New-Item -ItemType Directory -Path $BuildPythonDir -Force | Out-Null
    $pythonZip = "standalone-build\python-embed.zip"
    Invoke-WebRequest -Uri $PythonEmbedUrl -OutFile $pythonZip
    Expand-Archive -Path $pythonZip -DestinationPath $BuildPythonDir -Force
    Remove-Item $pythonZip

    # Enable site-packages in the embedded Python
    $pthFile = Get-ChildItem $BuildPythonDir -Filter "*._pth" | Select-Object -First 1
    if ($pthFile) {
        $content = Get-Content $pthFile.FullName
        $content = $content -replace "#import site", "import site"
        $content | Set-Content $pthFile.FullName
        Add-Content $pthFile.FullName "Lib`nLib/site-packages"
    }

    Write-Info "Installing pip..."
    Invoke-WebRequest -Uri $GetPipUrl -OutFile "$BuildPythonDir\get-pip.py"
    Invoke-Checked "Installing pip" { & $BuildPython "$BuildPythonDir\get-pip.py" --no-warn-script-location }
}

Write-Info "Installing Python dependencies and PyInstaller (this may take several minutes)..."
Invoke-Checked "pip install" { & $BuildPython -m pip install --no-warn-script-location -r requirements.txt pyinstaller }

Write-Info "Building optimized frontend..."
if (-not (Test-Path "node_modules")) {
    Invoke-Checked "npm ci" { npm ci }
}
Invoke-Checked "npm run build" { npm run build }

Write-Info "Building the executable (this may take a few minutes)..."
Invoke-Checked "PyInstaller" {
    & $BuildPython -m PyInstaller backend.spec --clean --noconfirm --workpath pyinstaller-work --distpath "standalone\runtime"
}

Write-Info "Creating launchers..."
@'
@echo off
cd /d "%~dp0"
REM Excel Data Visualizer launcher. Run "launch.bat --shared" to let other
REM computers on this network use the app (there is no login).

echo ==========================================
echo   Excel Data Visualizer is starting...
echo ==========================================
start "Excel Data Visualizer" runtime\excel-visualizer-backend\excel-visualizer-backend.exe %*

REM Give the server a moment, then open the browser
timeout /t 4 /nobreak >nul
start http://localhost:5001

echo.
echo   The app is running at http://localhost:5001
echo   To stop it, close the "Excel Data Visualizer" window.
echo.
pause
'@ | Out-File -FilePath "standalone\launch.bat" -Encoding ASCII

@'
# Excel Data Visualizer launcher. Run ".\launch.ps1 -Shared" to let other
# computers on this network use the app (there is no login).
param([switch]$Shared)

Set-Location $PSScriptRoot
$arguments = @()
if ($Shared) { $arguments += "--shared" }
$exe = "runtime\excel-visualizer-backend\excel-visualizer-backend.exe"
$app = if ($arguments.Count) {
    Start-Process -FilePath $exe -ArgumentList $arguments -PassThru -WindowStyle Minimized
} else {
    Start-Process -FilePath $exe -PassThru -WindowStyle Minimized
}

# Wait up to 30 seconds for the server to answer
$ready = $false
for ($i = 0; $i -lt 60 -and -not $app.HasExited; $i++) {
    try {
        Invoke-WebRequest -Uri "http://localhost:5001/health" -UseBasicParsing -TimeoutSec 2 | Out-Null
        $ready = $true
        break
    } catch {
        Start-Sleep -Milliseconds 500
    }
}
if (-not $ready) {
    Write-Host "The app did not start. Run launch.bat to see its messages."
    Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

Start-Process "http://localhost:5001"
Write-Host "Excel Data Visualizer is running at http://localhost:5001"
Write-Host "Press Ctrl+C to stop it."
try {
    while (-not $app.HasExited) { Start-Sleep -Seconds 1 }
} finally {
    Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue
}
'@ | Out-File -FilePath "standalone\launch.ps1" -Encoding UTF8

@"
Excel Data Visualizer - Standalone Edition (Windows)
====================================================

Everything the app needs is in this folder. Nothing has to be installed,
and no administrator rights are needed.

START
-----
Double-click launch.bat. Your browser opens http://localhost:5001.
To stop the app, close the "Excel Data Visualizer" window.

SHARE WITH OTHER COMPUTERS (optional)
-------------------------------------
Run "launch.bat --shared" (or ".\launch.ps1 -Shared").
Other computers on the same network can then open
http://<this computer's name>:5001. Windows asks once for firewall
permission; allow it for private networks only.
There is no login: anyone on the network can see the loaded file.

PORTABLE USE
------------
Copy the whole folder anywhere (USB drive, network share) and run launch.bat.

TROUBLESHOOTING
---------------
Port 5001 already in use: close the program using it.
The browser shows "cannot reach": wait a few seconds and reload; the first
start after unpacking can be slow while Windows scans the files.

Build date: $(Get-Date -Format "yyyy-MM-dd")
"@ | Out-File -FilePath "standalone\README.txt" -Encoding UTF8

$AppSize = (Get-ChildItem -Path "standalone\runtime" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
$TotalSize = (Get-ChildItem -Path "standalone" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB

Write-Success "Standalone build complete!"
Write-Host ""
Write-Host "  Application (Python, libraries, web page): $([math]::Round($AppSize, 1)) MB"
Write-Host "  TOTAL PACKAGE SIZE:                        $([math]::Round($TotalSize, 1)) MB"
Write-Host ""

Write-Info "Creating distribution package..."
Compress-Archive -Path "standalone" -DestinationPath "excel-visualizer-standalone-windows.zip" -Force
$ArchiveSize = (Get-Item "excel-visualizer-standalone-windows.zip").Length / 1MB
Write-Success "Distribution package: excel-visualizer-standalone-windows.zip ($([math]::Round($ArchiveSize, 1)) MB)"
Write-Host "  Users extract it and double-click launch.bat"
