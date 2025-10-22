# Excel Data Visualizer Offline Launcher
# This script runs the application using bundled Python (no system Python/Node.js required)

param(
    [string]$Action = "start"
)

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
    if (Test-Path "python\python.exe") {
        return "python\python.exe"  # Installation (bundled Python)
    } elseif (Test-Path "standalone\python\python.exe") {
        return "standalone\python\python.exe"  # Source with standalone build
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
        Write-Error "Current directory: $(Get-Location)"
        return $false
    }
    Write-Info "Using Python: $pythonExe"

    # Find backend
    if (-not (Test-Path "backend\app.py")) {
        Write-Error "Backend app.py not found at: backend\app.py"
        Write-Error "Current directory: $(Get-Location)"
        return $false
    }

    # Free port if in use
    if (-not (Kill-ProcessOnPort 5001 "Backend")) {
        return $false
    }

    try {
        Write-Info "Starting: $pythonExe backend\app.py"

        # Start backend with VISIBLE console window
        $backendProcess = Start-Process -FilePath $pythonExe `
                                       -ArgumentList "backend\app.py" `
                                       -PassThru `
                                       -WindowStyle Normal `
                                       -WorkingDirectory $PWD

        Start-Sleep -Seconds 3

        if (-not $backendProcess.HasExited) {
            Write-Success "Backend server started on http://localhost:5001"
            $backendProcess.Id | Out-File -FilePath "backend.pid" -Encoding ascii
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
    if (Test-Path "frontend\index.html") {
        return "frontend"  # Installation (copied from bundle)
    } elseif (Test-Path "build\index.html") {
        return "build"  # Source (npm build output)
    } elseif (Test-Path "standalone\app\frontend\index.html") {
        return "standalone\app\frontend"  # Standalone build
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

    # Find frontend
    $frontendDir = Get-FrontendPath
    if (-not $frontendDir) {
        Write-Error "Frontend build not found. Tried: frontend\, build\, standalone\app\frontend\"
        Write-Error "Current directory: $(Get-Location)"
        Write-Error "Please run 'npm run build' to build the frontend first."
        return $false
    }
    Write-Info "Using frontend: $frontendDir"

    # Free port if in use
    if (-not (Kill-ProcessOnPort 3000 "Frontend")) {
        return $false
    }

    try {
        Write-Info "Starting: $pythonExe -m http.server 3000 (from $frontendDir)"

        # Use Python's built-in HTTP server to serve the frontend with VISIBLE console
        $frontendProcess = Start-Process -FilePath $pythonExe `
                                        -ArgumentList "-m", "http.server", "3000" `
                                        -WorkingDirectory "$PWD\$frontendDir" `
                                        -PassThru `
                                        -WindowStyle Normal

        Start-Sleep -Seconds 2
        Write-Success "Frontend server started on http://localhost:3000"
        $frontendProcess.Id | Out-File -FilePath "frontend.pid" -Encoding ascii

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

    if (Test-Path "backend.pid") {
        $backendPid = Get-Content "backend.pid"
        try {
            Stop-Process -Id $backendPid -Force -ErrorAction SilentlyContinue
            Write-Success "Backend server stopped"
        } catch {}
        Remove-Item "backend.pid" -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path "frontend.pid") {
        $frontendPid = Get-Content "frontend.pid"
        try {
            Stop-Process -Id $frontendPid -Force -ErrorAction SilentlyContinue
            Write-Success "Frontend server stopped"
        } catch {}
        Remove-Item "frontend.pid" -Force -ErrorAction SilentlyContinue
    }
}

function Show-Status {
    Write-Info "Server Status:"

    if (Test-Path "backend.pid") {
        $backendPid = Get-Content "backend.pid"
        if (Get-Process -Id $backendPid -ErrorAction SilentlyContinue) {
            Write-Host "  Backend:  Running (PID: $backendPid) - http://localhost:5001"
        } else {
            Write-Host "  Backend:  Not running"
            Remove-Item "backend.pid" -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "  Backend:  Not running"
    }

    if (Test-Path "frontend.pid") {
        $frontendPid = Get-Content "frontend.pid"
        if (Get-Process -Id $frontendPid -ErrorAction SilentlyContinue) {
            Write-Host "  Frontend: Running (PID: $frontendPid) - http://localhost:3000"
        } else {
            Write-Host "  Frontend: Not running"
            Remove-Item "frontend.pid" -Force -ErrorAction SilentlyContinue
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
                if ($pythonExe -eq "python\python.exe") {
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
