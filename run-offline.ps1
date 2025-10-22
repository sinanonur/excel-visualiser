# Excel Data Visualizer Offline Launcher
# This script runs the application using bundled Python (no system Python/Node.js required)

param(
    [string]$Action = "start"
)

# Get the directory where THIS script is located (works regardless of current directory)
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) {
    # Fallback for older PowerShell versions
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

# Use temp directory for PID files (C:\Program Files is read-only for normal users)
$PidDir = Join-Path $env:TEMP "ExcelVisualizer"
if (-not (Test-Path $PidDir)) {
    New-Item -ItemType Directory -Path $PidDir -Force | Out-Null
}

$Colors = @{
    Info = 'Blue'
    Success = 'Green'
    Error = 'Red'
}

function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor $Colors.Info }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Success }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Error }

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

function Kill-ProcessOnPort {
    param($Port, $Name)

    if (Test-Port $Port) {
        Write-Info "Port $Port is in use. Attempting to free it..."

        # Find and kill process using the port
        $netstat = netstat -ano | Select-String ":$Port\s" | Select-Object -First 1
        if ($netstat) {
            $processId = $netstat -replace '.*\s(\d+)\s*$', '$1'
            try {
                Stop-Process -Id $processId -Force -ErrorAction Stop
                Start-Sleep -Seconds 1
                Write-Success "Freed port $Port (killed PID $processId)"
                return $true
            } catch {
                Write-Error "Could not kill process on port $Port. Please close it manually."
                return $false
            }
        }
    }
    return $true
}

function Get-PythonPath {
    # Detect Python location (installation vs source)
    $pythonInBundle = Join-Path $ScriptDir "python\python.exe"
    $pythonInStandalone = Join-Path $ScriptDir "standalone\python\python.exe"

    if (Test-Path $pythonInBundle) {
        return $pythonInBundle  # Installation (bundled Python)
    } elseif (Test-Path $pythonInStandalone) {
        return $pythonInStandalone  # Source with standalone build
    } elseif (Get-Command "python" -ErrorAction SilentlyContinue) {
        return "python"  # System Python
    } else {
        return $null
    }
}

function Start-Backend {
    Write-Info "Starting backend server..."

    # Find Python
    $pythonExe = Get-PythonPath
    if (-not $pythonExe) {
        Write-Error "Python not found. Please install Python or use the offline installer."
        Write-Error "Script directory: $ScriptDir"
        return $false
    }
    Write-Info "Using Python: $pythonExe"

    # Find backend (relative to script directory)
    $backendPath = Join-Path $ScriptDir "backend\app.py"
    if (-not (Test-Path $backendPath)) {
        Write-Error "Backend app.py not found at: $backendPath"
        Write-Error "Script directory: $ScriptDir"
        return $false
    }

    # Free port if in use
    if (-not (Kill-ProcessOnPort 5001 "Backend")) {
        return $false
    }

    try {
        Write-Info "Starting backend from: $backendPath"

        # Start backend with VISIBLE console window
        $backendProcess = Start-Process -FilePath $pythonExe `
                                       -ArgumentList "`"$backendPath`"" `
                                       -PassThru `
                                       -WindowStyle Normal `
                                       -WorkingDirectory $ScriptDir

        Start-Sleep -Seconds 3

        if (-not $backendProcess.HasExited) {
            Write-Success "Backend server started on http://localhost:5001"
            $pidFile = Join-Path $PidDir "backend.pid"
            $backendProcess.Id | Out-File -FilePath $pidFile -Encoding ascii
            return $true
        } else {
            Write-Error "Backend process exited immediately. Check the console window for errors."
            return $false
        }
    } catch {
        Write-Error "Error starting backend: $_"
        return $false
    }
}

function Get-FrontendPath {
    # Detect frontend location (installation vs source)
    $frontendInInstall = Join-Path $ScriptDir "frontend"
    $frontendInBuild = Join-Path $ScriptDir "build"
    $frontendInStandalone = Join-Path $ScriptDir "standalone\app\frontend"

    if (Test-Path (Join-Path $frontendInInstall "index.html")) {
        return $frontendInInstall  # Installation (copied from bundle)
    } elseif (Test-Path (Join-Path $frontendInBuild "index.html")) {
        return $frontendInBuild  # Source (npm build output)
    } elseif (Test-Path (Join-Path $frontendInStandalone "index.html")) {
        return $frontendInStandalone  # Standalone build
    } else {
        return $null
    }
}

function Start-Frontend {
    Write-Info "Starting frontend server..."

    # Find Python
    $pythonExe = Get-PythonPath
    if (-not $pythonExe) {
        Write-Error "Python not found. Please install Python or use the offline installer."
        return $false
    }

    # Find frontend (returns absolute path)
    $frontendDir = Get-FrontendPath
    if (-not $frontendDir) {
        Write-Error "Frontend build not found."
        Write-Error "Tried: frontend\, build\, standalone\app\frontend\"
        Write-Error "Script directory: $ScriptDir"
        Write-Error "Please run 'npm run build' to build the frontend first."
        return $false
    }
    Write-Info "Using frontend: $frontendDir"

    # Free port if in use
    if (-not (Kill-ProcessOnPort 3000 "Frontend")) {
        return $false
    }

    try {
        Write-Info "Starting Python HTTP server on port 3000"
        Write-Info "Serving from: $frontendDir"

        # Use Python's built-in HTTP server to serve the frontend with VISIBLE console
        $frontendProcess = Start-Process -FilePath $pythonExe `
                                        -ArgumentList "-m", "http.server", "3000" `
                                        -WorkingDirectory $frontendDir `
                                        -PassThru `
                                        -WindowStyle Normal

        Start-Sleep -Seconds 2
        Write-Success "Frontend server started on http://localhost:3000"
        $pidFile = Join-Path $PidDir "frontend.pid"
        $frontendProcess.Id | Out-File -FilePath $pidFile -Encoding ascii

        # Auto-open browser
        Start-Sleep -Seconds 2
        Start-Process "http://localhost:3000"

        return $true
    } catch {
        Write-Error "Error starting frontend: $_"
        return $false
    }
}

function Stop-Servers {
    Write-Info "Stopping servers..."

    $backendPidFile = Join-Path $PidDir "backend.pid"
    if (Test-Path $backendPidFile) {
        $backendPid = Get-Content $backendPidFile
        try {
            Stop-Process -Id $backendPid -Force -ErrorAction SilentlyContinue
            Write-Success "Backend server stopped"
        } catch {}
        Remove-Item $backendPidFile -Force -ErrorAction SilentlyContinue
    }

    $frontendPidFile = Join-Path $PidDir "frontend.pid"
    if (Test-Path $frontendPidFile) {
        $frontendPid = Get-Content $frontendPidFile
        try {
            Stop-Process -Id $frontendPid -Force -ErrorAction SilentlyContinue
            Write-Success "Frontend server stopped"
        } catch {}
        Remove-Item $frontendPidFile -Force -ErrorAction SilentlyContinue
    }
}

function Show-Status {
    Write-Info "Server Status:"

    $backendPidFile = Join-Path $PidDir "backend.pid"
    if (Test-Path $backendPidFile) {
        $backendPid = Get-Content $backendPidFile
        if (Get-Process -Id $backendPid -ErrorAction SilentlyContinue) {
            Write-Host "  Backend:  Running (PID: $backendPid) - http://localhost:5001"
        } else {
            Write-Host "  Backend:  Not running"
            Remove-Item $backendPidFile -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "  Backend:  Not running"
    }

    $frontendPidFile = Join-Path $PidDir "frontend.pid"
    if (Test-Path $frontendPidFile) {
        $frontendPid = Get-Content $frontendPidFile
        if (Get-Process -Id $frontendPid -ErrorAction SilentlyContinue) {
            Write-Host "  Frontend: Running (PID: $frontendPid) - http://localhost:3000"
        } else {
            Write-Host "  Frontend: Not running"
            Remove-Item $frontendPidFile -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "  Frontend: Not running"
    }
}

# Main logic
switch ($Action.ToLower()) {
    "start" {
        if (Start-Backend) {
            if (Start-Frontend) {
                Write-Host ""
                Write-Success "Excel Data Visualizer is running!"
                Write-Host ""
                Write-Info "Frontend: http://localhost:3000 (opens automatically)"
                Write-Info "Backend:  http://localhost:5001"
                Write-Host ""
                Write-Info "Server console windows are open and visible."
                Write-Info "You can see logs and errors in those windows."
                Write-Info "Do NOT close them or the application will stop."
                Write-Host ""

                # Show environment info
                $pythonExe = Get-PythonPath
                $frontendDir = Get-FrontendPath
                $bundledPython = Join-Path $ScriptDir "python\python.exe"

                if ($pythonExe -eq $bundledPython) {
                    Write-Info "Environment: Offline Installation (bundled Python, no internet needed)"
                } elseif ($pythonExe -like "*standalone*") {
                    Write-Info "Environment: Standalone Build"
                } else {
                    Write-Info "Environment: Source/Development (using system Python)"
                }

                Write-Host ""
                Write-Info "To stop: .\run-offline.ps1 stop"
                Write-Host ""
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
        Write-Host "Excel Data Visualizer - Offline Mode"
        Write-Host ""
        Write-Host "Usage: .\run-offline.ps1 {start|stop|restart|status}"
        Write-Host ""
        Write-Host "This version requires NO Python or Node.js installation!"
    }
}
