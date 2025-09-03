# Excel Data Visualizer - Windows Installation Script
# This script installs all dependencies and sets up the application on Windows
# Run this script in PowerShell as Administrator for best results

param(
    [switch]$NoAdmin = $false
)

# Colors for output
$script:Colors = @{
    Red = 'Red'
    Green = 'Green'
    Yellow = 'Yellow'
    Blue = 'Blue'
    White = 'White'
}

# Function to print colored output
function Write-Status {
    param($Message)
    Write-Host "[INFO] " -ForegroundColor $Colors.Blue -NoNewline
    Write-Host $Message -ForegroundColor $Colors.White
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] " -ForegroundColor $Colors.Green -NoNewline
    Write-Host $Message -ForegroundColor $Colors.White
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] " -ForegroundColor $Colors.Yellow -NoNewline
    Write-Host $Message -ForegroundColor $Colors.White
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] " -ForegroundColor $Colors.Red -NoNewline
    Write-Host $Message -ForegroundColor $Colors.White
}

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Function to check if command exists
function Test-CommandExists {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to install Chocolatey
function Install-Chocolatey {
    if (Test-CommandExists "choco") {
        Write-Status "Chocolatey found: $(choco --version)"
    } else {
        Write-Status "Installing Chocolatey package manager..."
        try {
            Set-ExecutionPolicy Bypass -Scope Process -Force
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
            Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
            
            # Refresh environment variables
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            Write-Success "Chocolatey installed successfully"
        } catch {
            Write-Error "Failed to install Chocolatey: $_"
            Write-Status "Please install Chocolatey manually from https://chocolatey.org/install"
            return $false
        }
    }
    return $true
}

# Function to install Python
function Install-Python {
    if (Test-CommandExists "python") {
        $pythonVersion = python --version 2>&1
        Write-Status "Python found: $pythonVersion"
        
        # Check if version is 3.7+
        try {
            $versionCheck = python -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Python version is compatible (3.7+, tested up to 3.12)"
            } else {
                Write-Warning "Python 3.7+ recommended. Current version may not be compatible."
            }
        } catch {
            Write-Warning "Could not verify Python version compatibility"
        }
    } else {
        Write-Status "Installing Python 3..."
        try {
            if (Test-Administrator -and -not $NoAdmin) {
                choco install python -y
            } else {
                Write-Status "Downloading Python installer..."
                $pythonUrl = "https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe"
                $pythonInstaller = "$env:TEMP\python-installer.exe"
                
                Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller
                Write-Status "Running Python installer..."
                Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0" -Wait
                Remove-Item $pythonInstaller -Force
            }
            
            # Refresh environment variables
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            Write-Success "Python installed successfully"
        } catch {
            Write-Error "Failed to install Python: $_"
            return $false
        }
    }
    
    # Install/upgrade pip
    Write-Status "Upgrading pip..."
    try {
        python -m pip install --upgrade pip
    } catch {
        Write-Warning "Could not upgrade pip: $_"
    }
    
    return $true
}

# Function to install Node.js
function Install-NodeJS {
    if ((Test-CommandExists "node") -and (Test-CommandExists "npm")) {
        $nodeVersion = node --version
        Write-Status "Node.js found: $nodeVersion"
        
        # Check if version is 14+
        try {
            $versionCheck = node -e "process.exit(process.version.slice(1).split('.')[0] >= 14 ? 0 : 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Node.js version is compatible (14+)"
            } else {
                Write-Warning "Node.js 14+ recommended. Current version: $nodeVersion"
            }
        } catch {
            Write-Warning "Could not verify Node.js version compatibility"
        }
    } else {
        Write-Status "Installing Node.js and npm..."
        try {
            if (Test-Administrator -and -not $NoAdmin) {
                choco install nodejs -y
            } else {
                Write-Status "Downloading Node.js installer..."
                $nodeUrl = "https://nodejs.org/dist/v18.17.1/node-v18.17.1-x64.msi"
                $nodeInstaller = "$env:TEMP\node-installer.msi"
                
                Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeInstaller
                Write-Status "Running Node.js installer..."
                Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", $nodeInstaller, "/quiet", "/norestart" -Wait
                Remove-Item $nodeInstaller -Force
            }
            
            # Refresh environment variables
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            Write-Success "Node.js installed successfully"
        } catch {
            Write-Error "Failed to install Node.js: $_"
            return $false
        }
    }
    return $true
}

# Function to setup the application
function Setup-Application {
    Write-Status "Setting up Excel Data Visualizer..."
    
    # Create virtual environment for Python
    Write-Status "Creating Python virtual environment..."
    try {
        python -m venv venv
        
        # Activate virtual environment
        & ".\venv\Scripts\Activate.ps1"
        
        # Upgrade pip in virtual environment
        python -m pip install --upgrade pip
        
        # Install Python dependencies
        Write-Status "Installing Python dependencies..."
        python -m pip install -r requirements.txt
        
        Write-Success "Python environment setup completed"
    } catch {
        Write-Error "Failed to setup Python environment: $_"
        return $false
    }
    
    # Install Node.js dependencies
    Write-Status "Installing Node.js dependencies..."
    try {
        npm install
        Write-Success "Node.js dependencies installed"
    } catch {
        Write-Error "Failed to install Node.js dependencies: $_"
        return $false
    }
    
    Write-Success "Application setup completed!"
    return $true
}

# Function to create startup scripts
function Create-StartupScripts {
    Write-Status "Creating startup scripts..."
    
    # Create PowerShell runner script
    $runnerScript = @'
# Excel Data Visualizer Launcher Script for Windows

param(
    [string]$Action = ""
)

$Colors = @{
    Red = 'Red'
    Green = 'Green'
    Yellow = 'Yellow'
    Blue = 'Blue'
    White = 'White'
}

function Write-Info {
    param($Message)
    Write-Host "[INFO] " -ForegroundColor $Colors.Blue -NoNewline
    Write-Host $Message -ForegroundColor $Colors.White
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] " -ForegroundColor $Colors.Green -NoNewline
    Write-Host $Message -ForegroundColor $Colors.White
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] " -ForegroundColor $Colors.Red -NoNewline
    Write-Host $Message -ForegroundColor $Colors.White
}

function Test-Port {
    param($Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

function Start-Backend {
    Write-Info "Starting backend server..."
    
    if (-not (Test-Path "venv")) {
        Write-Error "Virtual environment not found. Please run install-windows.ps1 first."
        return $false
    }
    
    if (Test-Port 5001) {
        Write-Error "Port 5001 is already in use. Please stop the existing service."
        return $false
    }
    
    try {
        # Activate virtual environment and start backend
        $backendProcess = Start-Process -FilePath "powershell" -ArgumentList "-Command", "& '.\venv\Scripts\Activate.ps1'; cd backend; python app.py" -PassThru -WindowStyle Hidden
        
        Start-Sleep -Seconds 3
        
        if (-not $backendProcess.HasExited) {
            Write-Success "Backend server started on http://localhost:5001 (PID: $($backendProcess.Id))"
            $backendProcess.Id | Out-File -FilePath "backend.pid" -Encoding ascii
            return $true
        } else {
            Write-Error "Failed to start backend server"
            return $false
        }
    } catch {
        Write-Error "Error starting backend: $_"
        return $false
    }
}

function Start-Frontend {
    Write-Info "Starting frontend server..."
    
    if (-not (Test-Path "node_modules")) {
        Write-Error "Node modules not found. Please run install-windows.ps1 first."
        return $false
    }
    
    if (Test-Port 3000) {
        Write-Error "Port 3000 is already in use. Please stop the existing service."
        return $false
    }
    
    try {
        $frontendProcess = Start-Process -FilePath "npm" -ArgumentList "start" -PassThru -WindowStyle Hidden
        
        Start-Sleep -Seconds 5
        Write-Success "Frontend server started on http://localhost:3000 (PID: $($frontendProcess.Id))"
        $frontendProcess.Id | Out-File -FilePath "frontend.pid" -Encoding ascii
        
        # Auto-open browser
        Start-Sleep -Seconds 3
        Start-Process "http://localhost:3000"
        
        return $true
    } catch {
        Write-Error "Error starting frontend: $_"
        return $false
    }
}

function Stop-Servers {
    Write-Info "Stopping servers..."
    
    if (Test-Path "backend.pid") {
        $backendPid = Get-Content "backend.pid"
        try {
            Stop-Process -Id $backendPid -Force -ErrorAction SilentlyContinue
            Write-Success "Backend server stopped"
        } catch {
            Write-Info "Backend process not found or already stopped"
        }
        Remove-Item "backend.pid" -Force -ErrorAction SilentlyContinue
    }
    
    if (Test-Path "frontend.pid") {
        $frontendPid = Get-Content "frontend.pid"
        try {
            Stop-Process -Id $frontendPid -Force -ErrorAction SilentlyContinue
            Write-Success "Frontend server stopped"
        } catch {
            Write-Info "Frontend process not found or already stopped"
        }
        Remove-Item "frontend.pid" -Force -ErrorAction SilentlyContinue
    }
    
    # Also kill any remaining node/python processes
    try {
        Get-Process -Name "node" | Where-Object {$_.MainWindowTitle -eq ""} | Stop-Process -Force -ErrorAction SilentlyContinue
        Get-Process -Name "python" | Where-Object {$_.CommandLine -like "*app.py*"} | Stop-Process -Force -ErrorAction SilentlyContinue
    } catch {
        # Ignore errors
    }
}

function Show-Status {
    Write-Info "Server Status:"
    
    $backendRunning = $false
    $frontendRunning = $false
    
    if (Test-Path "backend.pid") {
        $backendPid = Get-Content "backend.pid"
        if (Get-Process -Id $backendPid -ErrorAction SilentlyContinue) {
            Write-Host "  Backend:  Running (PID: $backendPid) - http://localhost:5001"
            $backendRunning = $true
        } else {
            Write-Host "  Backend:  Not running (stale PID file)"
            Remove-Item "backend.pid" -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "  Backend:  Not running"
    }
    
    if (Test-Path "frontend.pid") {
        $frontendPid = Get-Content "frontend.pid"
        if (Get-Process -Id $frontendPid -ErrorAction SilentlyContinue) {
            Write-Host "  Frontend: Running (PID: $frontendPid) - http://localhost:3000"
            $frontendRunning = $true
        } else {
            Write-Host "  Frontend: Not running (stale PID file)"
            Remove-Item "frontend.pid" -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "  Frontend: Not running"
    }
}

switch ($Action.ToLower()) {
    "start" {
        if (Start-Backend) {
            if (Start-Frontend) {
                Write-Host ""
                Write-Success "Excel Data Visualizer is running!"
                Write-Info "Frontend: http://localhost:3000 (should open automatically)"
                Write-Info "Backend:  http://localhost:5001"
                Write-Info "Use 'run.ps1 stop' to stop the servers"
            }
        }
    }
    "stop" {
        Stop-Servers
    }
    "restart" {
        Stop-Servers
        Start-Sleep -Seconds 2
        if (Start-Backend) {
            Start-Frontend
        }
    }
    "status" {
        Show-Status
    }
    default {
        Write-Host "Excel Data Visualizer Control Script for Windows"
        Write-Host ""
        Write-Host "Usage: .\run.ps1 {start|stop|restart|status}"
        Write-Host ""
        Write-Host "Commands:"
        Write-Host "  start   - Start both backend and frontend servers"
        Write-Host "  stop    - Stop both servers"
        Write-Host "  restart - Restart both servers"
        Write-Host "  status  - Show server status"
        Write-Host ""
        Write-Host "Alternative: Double-click 'run.bat' to start the application"
    }
}
'@
    
    $runnerScript | Out-File -FilePath "run.ps1" -Encoding UTF8
    Write-Success "Created run.ps1 launcher script"
    
    # Create batch file for easier access
    $batchScript = @'
@echo off
echo Starting Excel Data Visualizer...
powershell -ExecutionPolicy Bypass -File "%~dp0run.ps1" start
pause
'@
    
    $batchScript | Out-File -FilePath "run.bat" -Encoding ASCII
    Write-Success "Created run.bat launcher script"
    
    # Create desktop shortcut
    Create-DesktopShortcut
}

# Function to create desktop shortcut
function Create-DesktopShortcut {
    try {
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Excel Data Visualizer.lnk")
        $Shortcut.TargetPath = "powershell.exe"
        $Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$(Get-Location)\run.ps1`" start"
        $Shortcut.WorkingDirectory = Get-Location
        $Shortcut.Description = "Excel Data Visualizer"
        $Shortcut.Save()
        
        Write-Success "Created desktop shortcut"
    } catch {
        Write-Warning "Could not create desktop shortcut: $_"
    }
}

# Function to test installation
function Test-Installation {
    Write-Status "Testing installation..."
    
    # Test Python dependencies
    try {
        & ".\venv\Scripts\Activate.ps1"
        $testResult = python -c "import pandas, flask, plotly, openpyxl; print('Python dependencies OK')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python dependencies test passed"
        } else {
            Write-Error "Python dependencies test failed: $testResult"
            return $false
        }
    } catch {
        Write-Error "Python dependencies test failed: $_"
        return $false
    }
    
    # Test Node.js dependencies
    if (Test-Path "node_modules") {
        Write-Success "Node.js dependencies installed"
    } else {
        Write-Error "Node.js dependencies missing"
        return $false
    }
    
    Write-Success "Installation test passed!"
    return $true
}

# Main installation flow
function Main {
    Write-Host "============================================="
    Write-Host "   Excel Data Visualizer - Windows Setup   "
    Write-Host "============================================="
    Write-Host ""
    
    # Check Windows version
    $osVersion = [System.Environment]::OSVersion.Version
    Write-Status "Windows version: $($osVersion.Major).$($osVersion.Minor)"
    
    if ($osVersion.Major -lt 10) {
        Write-Warning "Windows 10 or later is recommended"
    }
    
    # Check administrator rights
    if (-not (Test-Administrator) -and -not $NoAdmin) {
        Write-Warning "Running without administrator rights. Some installations may require manual steps."
        Write-Status "Re-run with -NoAdmin parameter to suppress this warning."
    }
    
    # Install Chocolatey (if admin)
    if (Test-Administrator -and -not $NoAdmin) {
        if (-not (Install-Chocolatey)) {
            Write-Error "Failed to install Chocolatey"
            return
        }
    } else {
        Write-Status "Skipping Chocolatey installation (not running as admin)"
    }
    
    # Install Python
    if (-not (Install-Python)) {
        Write-Error "Failed to install Python"
        return
    }
    
    # Install Node.js
    if (-not (Install-NodeJS)) {
        Write-Error "Failed to install Node.js"
        return
    }
    
    # Setup application
    if (-not (Setup-Application)) {
        Write-Error "Failed to setup application"
        return
    }
    
    # Create startup scripts
    Create-StartupScripts
    
    # Test installation
    if (-not (Test-Installation)) {
        Write-Error "Installation test failed"
        return
    }
    
    Write-Host ""
    Write-Host "============================================="
    Write-Success "Installation completed successfully!"
    Write-Host "============================================="
    Write-Host ""
    Write-Info "To start the application:"
    Write-Host "  .\run.ps1 start"
    Write-Host "  OR double-click 'run.bat'"
    Write-Host "  OR use the desktop shortcut"
    Write-Host ""
    Write-Info "To stop the application:"
    Write-Host "  .\run.ps1 stop"
    Write-Host ""
    Write-Info "The application will be available at:"
    Write-Host "  Frontend: http://localhost:3000"
    Write-Host "  Backend:  http://localhost:5001"
    Write-Host ""
    Write-Info "The browser should open automatically when starting."
    Write-Host ""
}

# Check if running on Windows
if (-not $IsWindows -and $PSVersionTable.PSVersion.Major -lt 6) {
    # PowerShell 5.x on Windows
    $IsWindows = $true
}

if (-not $IsWindows) {
    Write-Error "This script is for Windows only."
    exit 1
}

# Run main installation
Main