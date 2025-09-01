# Excel Data Visualizer - Installation Guide

This guide provides step-by-step installation instructions for Linux, macOS, and Windows systems.

## Quick Start

| Operating System | Command |
|------------------|---------|
| **Linux** | `./install-linux.sh` |
| **macOS** | `./install-macos.sh` |
| **Windows** | Double-click `install-windows.bat` or run `.\install-windows.ps1` in PowerShell |

---

## System Requirements

### Minimum Requirements
- **Operating System**: Linux (Ubuntu 18.04+, CentOS 7+, etc.), macOS 10.14+, or Windows 10+
- **Python**: 3.7 or higher
- **Node.js**: 14.0 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 1GB free space
- **Internet**: Required for initial setup

### Recommended Requirements
- **Python**: 3.9+
- **Node.js**: 18.0+ (LTS)
- **RAM**: 8GB or more
- **Storage**: 2GB free space

---

## Linux Installation

### Supported Distributions
- Ubuntu 18.04+, Debian 10+
- CentOS 7+, RHEL 7+, Fedora 30+
- Arch Linux, Manjaro
- openSUSE Leap 15+

### Automatic Installation

```bash
# Make the script executable
chmod +x install-linux.sh

# Run the installer
./install-linux.sh
```

### Manual Installation

If the automatic installer fails, follow these steps:

1. **Install System Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install -y python3 python3-pip python3-venv nodejs npm build-essential
   
   # CentOS/RHEL/Fedora
   sudo yum install -y python3 python3-pip nodejs npm gcc gcc-c++
   # OR for newer versions:
   sudo dnf install -y python3 python3-pip nodejs npm gcc gcc-c++
   
   # Arch Linux
   sudo pacman -S python python-pip nodejs npm base-devel
   ```

2. **Setup Application**
   ```bash
   # Create Python virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install Python dependencies
   pip install --upgrade pip
   pip install -r requirements.txt
   
   # Install Node.js dependencies
   npm install
   ```

3. **Create Run Script**
   ```bash
   # Copy the run.sh script created by the installer
   # Or use the manual commands:
   
   # Start backend
   source venv/bin/activate
   cd backend
   python app.py &
   cd ..
   
   # Start frontend
   npm start
   ```

### Post-Installation

```bash
# Start the application
./run.sh start

# Check status
./run.sh status

# Stop the application
./run.sh stop
```

---

## macOS Installation

### Prerequisites
- macOS 10.14 (Mojave) or later
- Administrator access (for Homebrew installation)

### Automatic Installation

```bash
# Make the script executable
chmod +x install-macos.sh

# Run the installer
./install-macos.sh
```

The installer will:
1. Install Xcode Command Line Tools (if needed)
2. Install Homebrew (if needed)
3. Install Python 3 via Homebrew
4. Install Node.js via Homebrew
5. Setup the application
6. Create an macOS app bundle

### Manual Installation

1. **Install Homebrew**
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Dependencies**
   ```bash
   # Install Python and Node.js
   brew install python node
   ```

3. **Setup Application**
   ```bash
   # Create Python virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install --upgrade pip
   pip install -r requirements.txt
   npm install
   ```

### Post-Installation

```bash
# Start the application
./run.sh start

# OR double-click the app bundle
open "Excel Visualizer.app"

# Stop the application
./run.sh stop
```

---

## Windows Installation

### Prerequisites
- Windows 10 or Windows 11
- Administrator access (recommended)
- PowerShell execution policy allowing scripts (for PowerShell installer)

### Option 1: Batch File Installer (Recommended)

1. **Download and Run**
   - Double-click `install-windows.bat`
   - Follow the on-screen instructions
   - Install Python and Node.js if prompted

2. **Start Application**
   - Double-click `run.bat`
   - OR use the desktop shortcut "Excel Data Visualizer"

### Option 2: PowerShell Installer (Advanced)

1. **Enable PowerShell Scripts** (Run as Administrator)
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Run Installer**
   ```powershell
   # As Administrator (recommended)
   .\install-windows.ps1
   
   # As regular user
   .\install-windows.ps1 -NoAdmin
   ```

3. **Start Application**
   ```powershell
   .\run.ps1 start
   ```

### Option 3: Manual Installation

1. **Install Python**
   - Download from [python.org](https://www.python.org/downloads/)
   - ⚠️ **Important**: Check "Add Python to PATH" during installation

2. **Install Node.js**
   - Download from [nodejs.org](https://nodejs.org/)
   - Install with default options

3. **Setup Application**
   ```cmd
   # Open Command Prompt in the project directory
   
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   venv\Scripts\activate.bat
   
   # Install Python dependencies
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   
   # Install Node.js dependencies
   npm install
   ```

4. **Create Run Script**
   ```cmd
   # Create a batch file to start the application
   echo @echo off > start.bat
   echo start /min cmd /c "venv\Scripts\activate.bat && cd backend && python app.py" >> start.bat
   echo timeout /t 3 /nobreak ^>nul >> start.bat
   echo start /min cmd /c "npm start" >> start.bat
   echo timeout /t 5 /nobreak ^>nul >> start.bat
   echo start http://localhost:3000 >> start.bat
   ```

### Windows Troubleshooting

**Common Issues:**

1. **Python not found**
   - Reinstall Python with "Add to PATH" option
   - Or manually add Python to PATH

2. **Node.js not found**
   - Reinstall Node.js
   - Restart Command Prompt/PowerShell

3. **Permission errors**
   - Run installer as Administrator
   - Check antivirus software blocking installations

4. **Port conflicts**
   - Close any applications using ports 3000 or 5001
   - Check Task Manager for running node.exe or python.exe processes

---

## Verification

After installation, verify everything works:

1. **Check Application Structure**
   ```
   excel-visualiser/
   ├── venv/                 # Python virtual environment
   ├── node_modules/         # Node.js dependencies
   ├── backend/
   │   └── app.py           # Backend server
   ├── src/                 # Frontend source
   ├── public/              # Frontend public files
   ├── run.sh/.ps1/.bat     # Launcher scripts
   └── requirements.txt     # Python dependencies
   ```

2. **Test Backend**
   ```bash
   # Activate Python environment
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate.bat # Windows
   
   # Test imports
   python -c "import pandas, flask, plotly, openpyxl; print('Backend dependencies OK')"
   ```

3. **Test Frontend**
   ```bash
   # Check Node.js dependencies
   npm list --depth=0
   ```

4. **Test Full Application**
   - Start the application using your platform's method
   - Open http://localhost:3000 in your browser
   - Upload the provided `test_data.xlsx` file
   - Verify data preview, filtering, and plotting features work

---

## Usage

### Starting the Application

| Platform | Method |
|----------|--------|
| **Linux** | `./run.sh start` |
| **macOS** | `./run.sh start` or double-click "Excel Visualizer.app" |
| **Windows** | Double-click `run.bat` or desktop shortcut |

### Stopping the Application

| Platform | Method |
|----------|--------|
| **Linux** | `./run.sh stop` |
| **macOS** | `./run.sh stop` |
| **Windows** | `.\run.ps1 stop` or close the command windows |

### Application URLs
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:5001

---

## Troubleshooting

### General Issues

1. **Port Already in Use**
   ```bash
   # Find processes using ports
   lsof -i :3000  # Linux/macOS
   netstat -ano | findstr :3000  # Windows
   
   # Kill the process and restart
   ```

2. **Python/Node.js Version Issues**
   ```bash
   # Check versions
   python --version
   node --version
   npm --version
   ```

3. **Dependencies Not Installing**
   - Check internet connection
   - Try clearing cache:
     ```bash
     pip cache purge
     npm cache clean --force
     ```

4. **Permission Issues**
   - Linux/macOS: Check file permissions with `ls -la`
   - Windows: Run as Administrator

### Platform-Specific Issues

**Linux:**
- Missing build tools: Install `build-essential` (Ubuntu) or `gcc` (other distros)
- Python headers missing: Install `python3-dev`

**macOS:**
- Xcode Command Line Tools: `xcode-select --install`
- Homebrew issues: Reinstall Homebrew
- Apple Silicon: Ensure Homebrew is installed in `/opt/homebrew`

**Windows:**
- PowerShell execution policy: `Set-ExecutionPolicy RemoteSigned`
- Long path support: Enable in Windows settings
- Antivirus blocking: Add project folder to exclusions

---

## Development Setup

For developers who want to modify the application:

1. **Install Development Dependencies**
   ```bash
   # Python dev dependencies
   pip install pytest black flake8
   
   # Node.js dev dependencies  
   npm install --save-dev eslint prettier
   ```

2. **Development Servers**
   ```bash
   # Backend with auto-reload
   cd backend
   python -m flask --app app.py --debug run --port 5001
   
   # Frontend with hot reload
   npm start
   ```

3. **Code Formatting**
   ```bash
   # Python
   black backend/
   flake8 backend/
   
   # JavaScript
   npm run lint
   npm run format
   ```

---

## Uninstallation

To completely remove the application:

### Linux/macOS
```bash
# Remove virtual environment
rm -rf venv/

# Remove Node.js dependencies
rm -rf node_modules/

# Remove generated files
rm -f *.pid run.sh

# Remove app bundle (macOS only)
rm -rf "Excel Visualizer.app"
```

### Windows
```cmd
# Remove virtual environment
rmdir /s venv

# Remove Node.js dependencies
rmdir /s node_modules

# Remove generated files
del *.pid run.ps1 run.bat

# Remove desktop shortcut
del "%USERPROFILE%\Desktop\Excel Data Visualizer.lnk"
```

---

## Getting Help

If you encounter issues during installation:

1. **Check the logs** - Installation scripts provide detailed output
2. **Verify system requirements** - Ensure your system meets minimum requirements
3. **Try manual installation** - If automatic installers fail
4. **Check common issues** - Review the troubleshooting section above
5. **Platform-specific help**:
   - Linux: Check your distribution's package manager documentation
   - macOS: Ensure Homebrew is working properly
   - Windows: Verify PowerShell execution policy and administrator access

---

## Updates

To update the application:

1. **Pull latest changes** (if using git)
   ```bash
   git pull origin main
   ```

2. **Update dependencies**
   ```bash
   # Update Python dependencies
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate.bat # Windows
   pip install -r requirements.txt --upgrade
   
   # Update Node.js dependencies
   npm update
   ```

3. **Restart the application**
   ```bash
   ./run.sh restart  # Linux/macOS
   .\run.ps1 restart # Windows
   ```