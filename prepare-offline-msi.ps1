# Prepare Offline MSI Package
# This script downloads all dependencies locally for bundling in the MSI
# Run this before building the MSI to create a fully offline installer

param(
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"

# Colors
$Colors = @{
    Info = 'Blue'
    Success = 'Green'
    Warning = 'Yellow'
    Error = 'Red'
}

function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor $Colors.Info }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Success }
function Write-Warning { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Warning }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Error }

Write-Host "============================================================"
Write-Host "  MSI Offline Package Preparation"
Write-Host "============================================================"
Write-Host ""

# Create directories for bundled dependencies
$bundleDir = "installer\bundle"
$pythonWheelsDir = "$bundleDir\python-wheels"
$nodeModulesDir = "$bundleDir\node_modules"
$pythonEmbedDir = "$bundleDir\python-embed"

if ($Clean) {
    Write-Info "Cleaning previous bundle..."
    if (Test-Path $bundleDir) {
        Remove-Item $bundleDir -Recurse -Force
    }
}

Write-Info "Creating bundle directories..."
New-Item -ItemType Directory -Path $pythonWheelsDir -Force | Out-Null
New-Item -ItemType Directory -Path $pythonEmbedDir -Force | Out-Null

# Step 1: Download Python embedded distribution
Write-Info "Downloading Python 3.11 embedded distribution..."
$pythonVersion = "3.11.5"
$pythonUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-embed-amd64.zip"
$pythonZip = "$bundleDir\python-embed.zip"

if (-not (Test-Path $pythonZip)) {
    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonZip
        Write-Success "Downloaded Python embedded"
    } catch {
        Write-Error "Failed to download Python: $_"
        exit 1
    }
}

Write-Info "Extracting Python embedded..."
Expand-Archive -Path $pythonZip -DestinationPath $pythonEmbedDir -Force

# Enable site-packages in embedded Python
$pthFile = Get-ChildItem $pythonEmbedDir -Filter "*._pth" | Select-Object -First 1
if ($pthFile) {
    $content = Get-Content $pthFile.FullName
    $content = $content -replace "#import site", "import site"
    $content | Set-Content $pthFile.FullName
    Add-Content $pthFile.FullName "Lib`nLib/site-packages"
    Write-Success "Configured Python embedded for site-packages"
}

# Step 2: Download get-pip.py
Write-Info "Downloading get-pip.py..."
$getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$getPipFile = "$pythonEmbedDir\get-pip.py"
Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipFile

# Step 3: Install pip in embedded Python
Write-Info "Installing pip in embedded Python..."
& "$pythonEmbedDir\python.exe" $getPipFile --no-warn-script-location

# Step 4: Download Python wheels
Write-Info "Downloading Python package wheels..."
Write-Info "This may take several minutes..."

$packages = Get-Content requirements.txt

foreach ($package in $packages) {
    if ($package.Trim() -and -not $package.StartsWith("#")) {
        Write-Info "  Downloading: $package"
        & "$pythonEmbedDir\python.exe" -m pip download --dest $pythonWheelsDir --no-deps $package
    }
}

# Also download dependencies
Write-Info "Downloading all dependencies..."
& "$pythonEmbedDir\python.exe" -m pip download --dest $pythonWheelsDir -r requirements.txt

Write-Success "Downloaded all Python packages"

# Step 5: Build frontend for production (no Node.js needed at runtime)
Write-Info "Building frontend for production..."

if (-not (Test-Path "node_modules")) {
    Write-Info "Installing Node.js dependencies for build..."
    npm install
}

Write-Info "Building React frontend..."
npm run build

Write-Info "Copying built frontend to bundle..."
$frontendBuildDir = "$bundleDir\frontend-build"
if (Test-Path $frontendBuildDir) {
    Remove-Item $frontendBuildDir -Recurse -Force
}
Copy-Item -Path "build" -Destination $frontendBuildDir -Recurse

Write-Success "Frontend built and bundled (Node.js not needed at runtime)"

# Step 6: Calculate sizes
Write-Host ""
Write-Info "Calculating bundle sizes..."

$pythonEmbedSize = (Get-ChildItem -Path $pythonEmbedDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
$pythonWheelsSize = (Get-ChildItem -Path $pythonWheelsDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
$frontendBuildSize = (Get-ChildItem -Path $frontendBuildDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
$totalSize = $pythonEmbedSize + $pythonWheelsSize + $frontendBuildSize

Write-Host ""
Write-Host "============================================================"
Write-Host "Bundle Statistics:"
Write-Host "============================================================"
Write-Host "  Python embedded:     $([math]::Round($pythonEmbedSize, 1)) MB"
Write-Host "  Python wheels:       $([math]::Round($pythonWheelsSize, 1)) MB"
Write-Host "  Frontend build:      $([math]::Round($frontendBuildSize, 1)) MB"
Write-Host "  ----------------------------------------------------------"
Write-Host "  TOTAL BUNDLE SIZE:   $([math]::Round($totalSize, 1)) MB"
Write-Host "============================================================"
Write-Host ""

Write-Success "Offline package preparation complete!"
Write-Host ""
Write-Info "Bundle includes:"
Write-Host "  - Python 3.11 embedded runtime (no system Python needed)"
Write-Host "  - All Python packages pre-downloaded"
Write-Host "  - Pre-built React frontend (no Node.js needed)"
Write-Host ""
Write-Info "Next steps:"
Write-Host "  1. Run: .\build-msi.ps1 -Offline"
Write-Host "  2. The MSI will be fully self-contained"
Write-Host "  3. NO Python or Node.js required on target system!"
Write-Host ""
Write-Warning "Note: The MSI file will be approximately $([math]::Round($totalSize + 10, 0)) MB"
Write-Host ""
