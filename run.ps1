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
