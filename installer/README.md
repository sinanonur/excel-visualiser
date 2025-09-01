# MSI Installer for Excel Data Science Visualizer

This directory contains the Windows Installer (MSI) package configuration for the Excel Data Science Visualizer application.

## Overview

The MSI installer provides a professional installation experience for Windows users, automatically handling:
- Application file deployment
- Python virtual environment setup
- Node.js dependency installation
- Desktop and Start Menu shortcuts
- Proper uninstallation support

## Prerequisites

To build the MSI package, you need:

### Required Software
- **Windows 10 or later** (development machine)
- **WiX Toolset 3.11 or later** - Download from [wixtoolset.org](https://wixtoolset.org/releases/)
- **PowerShell 5.1 or later**

### Install WiX Toolset

**Option 1: Direct Download**
1. Download WiX Toolset from https://wixtoolset.org/releases/
2. Run the installer
3. Add WiX bin directory to your PATH

**Option 2: Chocolatey (Recommended)**
```powershell
# Install via Chocolatey (run as Administrator)
choco install wixtoolset
```

**Option 3: Visual Studio Extension**
- Install "WiX Toolset Visual Studio Extension" if using Visual Studio

## Building the MSI

### Quick Build

```powershell
# Navigate to the project root directory
cd excel-visualiser

# Build the MSI package
.\build-msi.ps1
```

### Advanced Build Options

```powershell
# Build with custom version
.\build-msi.ps1 -Version "1.0.1"

# Build with verbose output
.\build-msi.ps1 -Verbose

# Clean build (remove previous artifacts)
.\build-msi.ps1 -Clean

# Custom output directory
.\build-msi.ps1 -OutputPath "releases"

# Combine options
.\build-msi.ps1 -Version "1.0.2" -OutputPath "releases" -Clean -Verbose
```

### Build Output

The build process creates:
- `dist/ExcelDataScienceVisualizer-{version}.msi` - Installation package
- `dist/INSTALLATION_GUIDE.md` - End-user installation instructions

## File Structure

```
installer/
├── Product.wxs           # Main WiX configuration file
├── License.rtf          # License agreement (RTF format)
└── README.md           # This file

# Generated during build:
dist/
├── ExcelDataScienceVisualizer-1.0.0.msi
└── INSTALLATION_GUIDE.md
```

## WiX Configuration Details

### Product.wxs Features

- **Product Definition**: Name, version, manufacturer, upgrade codes
- **Directory Structure**: Installation paths and folder organization
- **Component Groups**: Organized file deployment (frontend, backend, docs)
- **Custom Actions**: Post-install setup (Python venv, dependencies)
- **Shortcuts**: Desktop and Start Menu integration
- **Prerequisites**: Python/Node.js detection and validation
- **UI Configuration**: Standard Windows installer interface

### Installation Behavior

1. **File Deployment**: Copies all application files to Program Files
2. **Python Environment**: Creates virtual environment and installs requirements
3. **Node Dependencies**: Runs `npm install` for frontend dependencies
4. **Shortcut Creation**: Desktop and Start Menu shortcuts
5. **Registry Entries**: Installation tracking and uninstall support

## Customization

### Changing Product Information

Edit `Product.wxs`:
```xml
<Product Id="*" 
         Name="Your Product Name" 
         Manufacturer="Your Company"
         Version="1.0.0">
```

### Adding/Removing Files

Add components to the appropriate ComponentGroup:
```xml
<Component Id="NewComponent" Guid="NEW-GUID-HERE">
  <File Id="NewFile" Source="path\to\file.ext" />
</Component>
```

### Custom Actions

Modify the custom actions section to change post-install behavior:
```xml
<CustomAction Id="YourCustomAction" 
              Directory="INSTALLFOLDER" 
              ExeCommand="your-command-here" />
```

## Testing

### Local Testing

1. **Build the MSI** using the build script
2. **Install on a test machine** or VM with clean Windows
3. **Verify functionality**:
   - Application launches correctly
   - Dependencies are installed
   - Shortcuts work
   - Uninstall works properly

### Test Environments

- **Windows 10** (minimum supported version)
- **Windows 11** (latest)
- **Different user privilege levels** (admin vs. standard user)
- **Clean systems** without Python/Node.js pre-installed

## Troubleshooting

### Common Build Issues

**WiX not found**
```
Solution: Install WiX Toolset and add to PATH
Check: candle.exe and light.exe are accessible
```

**File not found errors**
```
Solution: Ensure all source files exist
Check: Run from project root directory
```

**GUID conflicts**
```
Solution: Generate new GUIDs for components
Tool: Use Visual Studio "Create GUID" tool
```

### Installation Issues

**Prerequisites missing**
- The installer checks for Python/Node.js but doesn't install them
- Users must install prerequisites manually first

**Permission errors**
- MSI requires elevated privileges for Program Files installation
- Users should "Run as Administrator"

**Antivirus interference**
- Some antivirus software blocks MSI installations
- Temporary disable during installation

## Distribution

### Signing (Recommended)

For production distribution, sign the MSI:
```powershell
# Sign with certificate
signtool sign /f "certificate.pfx" /p "password" /t "timestamp-server" dist/ExcelDataScienceVisualizer-1.0.0.msi
```

### Release Checklist

- [ ] Test installation on clean Windows systems
- [ ] Verify all features work after installation
- [ ] Test uninstallation process
- [ ] Check file associations and shortcuts
- [ ] Validate license agreement
- [ ] Sign the MSI (if distributing publicly)
- [ ] Create release notes
- [ ] Upload to distribution platform

## Advanced Topics

### Silent Installation

```cmd
# Silent install
msiexec /i ExcelDataScienceVisualizer-1.0.0.msi /quiet

# Silent install with custom directory
msiexec /i ExcelDataScienceVisualizer-1.0.0.msi /quiet INSTALLFOLDER="C:\MyApps\ExcelVisualizer"

# Silent uninstall
msiexec /x ExcelDataScienceVisualizer-1.0.0.msi /quiet
```

### Group Policy Deployment

For enterprise environments, the MSI can be deployed via:
- Group Policy Software Installation
- System Center Configuration Manager (SCCM)
- Microsoft Deployment Toolkit (MDT)

### Transform Files (.mst)

Create transform files for enterprise customization:
```powershell
# Use Orca or similar tools to create .mst files
# Deploy with: msiexec /i package.msi TRANSFORMS=custom.mst
```

## Support

For build issues or MSI-specific problems:
1. Check the build script output for error details
2. Review Windows Event Log (Windows Logs > Application)
3. Validate WiX source files with WiX validators
4. Test on different Windows versions and configurations

## License

The installer configuration follows the same license as the main application (MIT License).