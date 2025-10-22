# Excel Data Science Visualizer - MSI Build Script
# This script builds the MSI installer package using WiX Toolset

param(
    [string]$Version = "1.0.0",
    [string]$OutputPath = "dist",
    [switch]$Clean = $false,
    [switch]$Verbose = $false,
    [switch]$Offline = $false
)

# Colors for output
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

function Test-WixToolset {
    try {
        $candle = Get-Command "candle.exe" -ErrorAction Stop
        $light = Get-Command "light.exe" -ErrorAction Stop
        Write-Success "WiX Toolset found: $($candle.Source)"
        return $true
    } catch {
        Write-Error "WiX Toolset not found. Please install WiX Toolset 3.11 or later."
        Write-Info "Download from: https://wixtoolset.org/releases/"
        Write-Info "Or install via Chocolatey: choco install wixtoolset"
        return $false
    }
}

function Test-Prerequisites {
    param([switch]$Offline)

    Write-Info "Checking prerequisites..."

    # Check for WiX Toolset
    if (-not (Test-WixToolset)) {
        return $false
    }

    # Check for source files
    $requiredFiles = @(
        "package.json",
        "requirements.txt",
        "backend\app.py",
        "src\App.js",
        "installer\Product.wxs",
        "installer\License.rtf"
    )

    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            Write-Error "Required file not found: $file"
            return $false
        }
    }

    # Check for offline bundle if offline mode is requested
    if ($Offline) {
        $bundleDir = "installer\bundle"
        if (-not (Test-Path "$bundleDir\python-embed")) {
            Write-Error "Offline bundle not found. Please run: .\prepare-offline-msi.ps1"
            return $false
        }
        if (-not (Test-Path "$bundleDir\python-wheels")) {
            Write-Error "Python wheels bundle not found. Please run: .\prepare-offline-msi.ps1"
            return $false
        }
        if (-not (Test-Path "$bundleDir\frontend-build")) {
            Write-Error "Frontend build not found. Please run: .\prepare-offline-msi.ps1"
            return $false
        }
        Write-Success "Offline bundle found"
    }

    Write-Success "All prerequisites met"
    return $true
}

function Clean-BuildArtifacts {
    Write-Info "Cleaning build artifacts..."
    
    $cleanPaths = @(
        "installer\*.wixobj",
        "installer\*.wixpdb",
        "installer\*.msi",
        $OutputPath
    )
    
    foreach ($path in $cleanPaths) {
        if (Test-Path $path) {
            Remove-Item $path -Recurse -Force
            Write-Info "Removed: $path"
        }
    }
}

function Build-MSI {
    param(
        $Version,
        [switch]$Offline
    )

    if ($Offline) {
        Write-Info "Building OFFLINE MSI package version $Version (includes all dependencies)..."
    } else {
        Write-Info "Building ONLINE MSI package version $Version (requires internet during install)..."
    }

    # Create output directory
    if (-not (Test-Path $OutputPath)) {
        New-Item -ItemType Directory -Path $OutputPath | Out-Null
    }

    # Build variables
    $productName = "ExcelDataScienceVisualizer"
    if ($Offline) {
        $msiFileName = "$productName-$Version-Offline.msi"
    } else {
        $msiFileName = "$productName-$Version.msi"
    }
    $wixObjFile = "installer\Product.wixobj"

    try {
        # Step 1: Compile WiX source to object file
        Write-Info "Compiling WiX source..."
        $candleArgs = @(
            "installer\Product.wxs",
            "-dVersion=$Version",
            "-dProductVersion=$Version",
            "-arch", "x64",
            "-out", $wixObjFile
        )

        # Pass offline mode as preprocessor variable
        if ($Offline) {
            $candleArgs += "-dOfflineMode=1"
        }

        if ($Verbose) {
            $candleArgs += "-v"
        }
        
        & candle.exe @candleArgs
        
        if ($LASTEXITCODE -ne 0) {
            throw "Candle compilation failed with exit code $LASTEXITCODE"
        }
        
        Write-Success "WiX source compiled successfully"
        
        # Step 2: Link object file to MSI
        Write-Info "Linking MSI package..."
        $lightArgs = @(
            $wixObjFile,
            "-ext", "WixUIExtension",
            "-cultures:en-us",
            "-out", "$OutputPath\$msiFileName"
        )

        # Include bundle folder for offline builds
        if ($Offline) {
            $lightArgs += "-b"
            $lightArgs += "installer\bundle"
            Write-Info "Including offline bundle in MSI..."
        }

        # Suppress ICE validation warnings
        $lightArgs += "-sice:ICE64"
        $lightArgs += "-sice:ICE03"

        if ($Verbose) {
            $lightArgs += "-v"
        }

        & light.exe @lightArgs
        
        if ($LASTEXITCODE -ne 0) {
            throw "Light linking failed with exit code $LASTEXITCODE"
        }
        
        Write-Success "MSI package created: $OutputPath\$msiFileName"
        
        # Get file size
        $msiFile = Get-Item "$OutputPath\$msiFileName"
        $fileSizeMB = [math]::Round($msiFile.Length / 1MB, 2)
        Write-Info "Package size: $fileSizeMB MB"
        
        return $true
        
    } catch {
        Write-Error "Build failed: $_"
        return $false
    } finally {
        # Clean up intermediate files
        if (Test-Path $wixObjFile) {
            Remove-Item $wixObjFile -Force
        }
        if (Test-Path "installer\Product.wixpdb") {
            Remove-Item "installer\Product.wixpdb" -Force
        }
    }
}

function Create-InstallationGuide {
    $guideContent = @"
# MSI Installation Package

## Generated Files

- **$OutputPath/ExcelDataScienceVisualizer-$Version.msi**: Main installation package

## Installation Instructions

### For End Users

1. **Download the MSI file** to your computer
2. **Double-click** the MSI file to start installation
3. **Follow the installer wizard**:
   - Accept the license agreement
   - Choose installation directory (default: C:\Program Files\Excel Data Science Visualizer\)
   - Select features to install
   - Click Install
4. **Wait for installation** to complete (may take several minutes)
5. **Launch the application** from:
   - Start Menu: Excel Data Science Visualizer
   - Desktop shortcut: Excel Data Science Visualizer

### System Requirements

- Windows 10 or later (64-bit)
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Internet connection (for initial setup)

### What Gets Installed

- Application files and source code
- Python virtual environment with dependencies
- Node.js dependencies
- Desktop and Start Menu shortcuts
- Uninstaller

### Post-Installation

The installer will automatically:
1. Create a Python virtual environment
2. Install Python dependencies (Flask, Pandas, Plotly, etc.)
3. Install Node.js dependencies (React, Material-UI, etc.)
4. Create launcher scripts
5. Set up shortcuts

### Uninstallation

- Use "Add or Remove Programs" in Windows Settings
- Or use the Start Menu shortcut "Uninstall Excel Data Science Visualizer"

### Troubleshooting

If installation fails:
1. **Run as Administrator** - Right-click MSI file and select "Run as administrator"
2. **Check Windows Event Log** for detailed error messages
3. **Ensure Python 3.7+** is installed and in PATH
4. **Ensure Node.js 14+** is installed and in PATH
5. **Free up disk space** - Ensure at least 2GB available
6. **Disable antivirus temporarily** during installation

### Advanced Options

- **Silent Installation**: ``msiexec /i ExcelDataScienceVisualizer-$Version.msi /quiet``
- **Custom Directory**: Use the installer GUI to specify a different installation path
- **Unattended Install**: ``msiexec /i ExcelDataScienceVisualizer-$Version.msi /qn INSTALLFOLDER="C:\MyPath"``

## Development Notes

This MSI was built using:
- WiX Toolset 3.11+
- Windows Installer 4.5
- .NET Framework support

For issues or source code, see the project repository.
"@

    $guideContent | Out-File -FilePath "$OutputPath\INSTALLATION_GUIDE.md" -Encoding UTF8
    Write-Success "Created installation guide: $OutputPath\INSTALLATION_GUIDE.md"
}

function Main {
    Write-Host "============================================="
    Write-Host "   Excel Data Science Visualizer MSI Builder"
    Write-Host "============================================="
    Write-Host ""

    if ($Offline) {
        Write-Host "Mode: OFFLINE (no internet required for installation)"
        Write-Host ""
    } else {
        Write-Host "Mode: ONLINE (requires internet during installation)"
        Write-Host ""
    }

    # Clean if requested
    if ($Clean) {
        Clean-BuildArtifacts
    }

    # Check prerequisites
    if (-not (Test-Prerequisites -Offline:$Offline)) {
        Write-Error "Prerequisites not met. Aborting build."
        exit 1
    }

    # Build MSI
    if (Build-MSI -Version $Version -Offline:$Offline) {
        # Create installation guide
        Create-InstallationGuide
        
        Write-Host ""
        Write-Host "============================================="
        Write-Success "MSI build completed successfully!"
        Write-Host "============================================="
        Write-Host ""
        Write-Info "Generated files:"
        Write-Host "  $OutputPath\ExcelDataScienceVisualizer-$Version.msi"
        Write-Host "  $OutputPath\INSTALLATION_GUIDE.md"
        Write-Host ""
        Write-Info "To test the installer:"
        Write-Host "  1. Copy the MSI file to a test machine"
        Write-Host "  2. Double-click to install"
        Write-Host "  3. Launch from Start Menu or Desktop"
        Write-Host ""
        Write-Info "For distribution:"
        Write-Host "  - Upload the MSI file to your download site"
        Write-Host "  - Include the installation guide"
        Write-Host "  - Test on clean Windows 10/11 systems"
        Write-Host ""
    } else {
        Write-Error "MSI build failed. Check the error messages above."
        exit 1
    }
}

# Validate Windows platform
if (-not $IsWindows) {
    if ($PSVersionTable.PSVersion.Major -ge 6) {
        Write-Error "This script requires Windows. Current platform: $($PSVersionTable.Platform)"
        exit 1
    }
}

# Run main function
Main