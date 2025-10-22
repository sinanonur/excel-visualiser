# Diagnostic script for offline installation
# Run this to see what's wrong

Write-Host "=== Excel Visualizer Installation Diagnostics ===" -ForegroundColor Cyan
Write-Host ""

$installDir = Get-Location
Write-Host "[CHECK] Current directory: $installDir" -ForegroundColor Yellow
Write-Host ""

# Check Python
Write-Host "[CHECK] Looking for Python..." -ForegroundColor Yellow
if (Test-Path "python\python.exe") {
    Write-Host "  [OK] Found: python\python.exe" -ForegroundColor Green
    $pythonVersion = & python\python.exe --version 2>&1
    Write-Host "  [INFO] Version: $pythonVersion" -ForegroundColor Cyan
} else {
    Write-Host "  [ERROR] NOT FOUND: python\python.exe" -ForegroundColor Red
}
Write-Host ""

# Check Backend
Write-Host "[CHECK] Looking for backend..." -ForegroundColor Yellow
if (Test-Path "backend\app.py") {
    Write-Host "  [OK] Found: backend\app.py" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] NOT FOUND: backend\app.py" -ForegroundColor Red
}
Write-Host ""

# Check Frontend
Write-Host "[CHECK] Looking for frontend..." -ForegroundColor Yellow
if (Test-Path "frontend") {
    Write-Host "  [OK] Found: frontend directory" -ForegroundColor Green
    $frontendFiles = Get-ChildItem "frontend" -Recurse | Measure-Object
    Write-Host "  [INFO] Files in frontend: $($frontendFiles.Count)" -ForegroundColor Cyan

    if (Test-Path "frontend\index.html") {
        Write-Host "  [OK] Found: frontend\index.html" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] NOT FOUND: frontend\index.html" -ForegroundColor Red
    }
} else {
    Write-Host "  [ERROR] NOT FOUND: frontend directory" -ForegroundColor Red
    Write-Host "  [INFO] Checking if bundle exists..." -ForegroundColor Yellow

    if (Test-Path "bundle\frontend-build") {
        Write-Host "  [OK] Found: bundle\frontend-build" -ForegroundColor Green
        Write-Host "  [FIX] Run this command to copy frontend:" -ForegroundColor Yellow
        Write-Host "    xcopy /E /I /Y bundle\frontend-build frontend" -ForegroundColor White
    } else {
        Write-Host "  [ERROR] NOT FOUND: bundle\frontend-build" -ForegroundColor Red
    }
}
Write-Host ""

# Check bundle directory
Write-Host "[CHECK] Looking for bundle..." -ForegroundColor Yellow
if (Test-Path "bundle") {
    Write-Host "  [OK] Found: bundle directory" -ForegroundColor Green

    if (Test-Path "bundle\python-embed") {
        $pythonEmbedFiles = Get-ChildItem "bundle\python-embed" | Measure-Object
        Write-Host "  [OK] Found: bundle\python-embed ($($pythonEmbedFiles.Count) files)" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] NOT FOUND: bundle\python-embed" -ForegroundColor Red
    }

    if (Test-Path "bundle\python-wheels") {
        $wheelFiles = Get-ChildItem "bundle\python-wheels" | Measure-Object
        Write-Host "  [OK] Found: bundle\python-wheels ($($wheelFiles.Count) files)" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] NOT FOUND: bundle\python-wheels" -ForegroundColor Red
    }

    if (Test-Path "bundle\frontend-build") {
        $frontendBuildFiles = Get-ChildItem "bundle\frontend-build" -Recurse | Measure-Object
        Write-Host "  [OK] Found: bundle\frontend-build ($($frontendBuildFiles.Count) files)" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] NOT FOUND: bundle\frontend-build" -ForegroundColor Red
    }
} else {
    Write-Host "  [ERROR] NOT FOUND: bundle directory" -ForegroundColor Red
}
Write-Host ""

# Try to start backend (inline to see errors)
Write-Host "[TEST] Attempting to start backend..." -ForegroundColor Yellow
if ((Test-Path "python\python.exe") -and (Test-Path "backend\app.py")) {
    Write-Host "  [INFO] Running: python\python.exe backend\app.py" -ForegroundColor Cyan
    Write-Host "  [INFO] Press Ctrl+C to stop the backend server" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "--- Backend Output ---" -ForegroundColor Cyan

    & python\python.exe backend\app.py

    Write-Host ""
    Write-Host "--- Backend Exited ---" -ForegroundColor Cyan
} else {
    Write-Host "  [SKIP] Cannot test - missing python or backend files" -ForegroundColor Yellow
}
