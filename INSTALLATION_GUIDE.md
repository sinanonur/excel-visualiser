# Excel Data Visualizer - Installation Guide

This guide provides multiple installation options to suit your needs and environment.

## Table of Contents

- [Quick Start (Recommended)](#quick-start-recommended)
- [Docker Installation (Easiest)](#docker-installation-easiest)
- [Platform-Specific Installation](#platform-specific-installation)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

---

## Quick Start (Recommended)

The fastest way to get started on any platform:

### Windows
```cmd
quick-install.bat
run-quick.bat
```

### Linux / macOS
```bash
chmod +x quick-install.sh
./quick-install.sh
./run.sh
```

This will automatically:
- Detect if Docker is available (uses containerized installation)
- Otherwise, install dependencies locally
- Create run scripts for easy launching

---

## Docker Installation (Easiest)

**Recommended for all platforms** - No need to install Python, Node.js, or dependencies!

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/macOS)
- Docker Engine (Linux)
- Docker Compose (usually included with Docker Desktop)

### Installation Steps

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd excel-visualiser
   ```

2. **Build and start with one command**
   ```bash
   docker-compose up --build
   ```

   Or run in detached mode:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5001

4. **Stop the application**
   ```bash
   docker-compose down
   ```

### Docker Benefits
- **Minimal disk space** - No local dependencies
- **Consistent environment** - Works the same everywhere
- **Easy updates** - Just rebuild the image
- **Isolation** - Doesn't affect your system

### Docker Image Size
- Final image: ~500-700MB (includes all dependencies)
- Repository size: ~2MB (excluding node_modules and venv)

---

## Platform-Specific Installation

For users who prefer native installation:

### Windows

#### Option 1: PowerShell Script (Recommended)
```powershell
.\install-windows.ps1
.\run.ps1 start
```

#### Option 2: Batch File
```cmd
install-windows.bat
run.bat
```

**Requirements:**
- Python 3.7+
- Node.js 14+
- Windows 10 or later

### macOS

```bash
chmod +x install-macos.sh
./install-macos.sh
./run.sh start
```

**Or use the app bundle:**
```bash
open "Excel Visualizer.app"
```

**Requirements:**
- macOS 10.14+
- Xcode Command Line Tools
- Homebrew (will be installed automatically)

### Linux

```bash
chmod +x install-linux.sh
./install-linux.sh
./run.sh start
```

**Supported distributions:**
- Ubuntu / Debian
- Fedora / CentOS / RHEL
- Arch / Manjaro
- openSUSE

**Requirements:**
- Python 3.7+
- Node.js 14+
- Build tools (gcc, make)

---

## Production Deployment

For deploying to a server or creating a distributable package:

### Build Production Package

```bash
chmod +x build-production.sh
./build-production.sh
```

This creates an optimized `production/` folder with:
- Compiled frontend (optimized React build)
- Backend Python application
- Minimal dependencies (production only)
- Platform-specific run scripts

### Deploy Production Build

1. **Copy to server**
   ```bash
   tar -czf excel-visualizer.tar.gz production/
   scp excel-visualizer.tar.gz user@server:/opt/
   ```

2. **Extract and run on server**
   ```bash
   ssh user@server
   cd /opt
   tar -xzf excel-visualizer.tar.gz
   cd production
   ./run-production.sh  # Linux/macOS
   # or
   run-production.bat   # Windows
   ```

### Production Size Comparison

| Installation Type | Size (approx) |
|------------------|---------------|
| Repository only | 2 MB |
| Production build | 50-100 MB |
| Docker image | 500-700 MB |
| Full dev install | 400-600 MB |

---

## Installation Size Optimization Tips

### Reduce Dependencies
The application uses minimal dependencies by default, but you can further reduce size:

1. **Use Docker** - No local dependencies needed
2. **Production build** - Removes dev dependencies
3. **Clear caches** after installation:
   ```bash
   # Node.js cache
   npm cache clean --force

   # Python cache
   pip cache purge

   # System package caches
   # Ubuntu/Debian
   sudo apt clean

   # macOS
   brew cleanup
   ```

### Exclude from Git
The following are automatically excluded (check `.gitignore`):
- `node_modules/` (200-300 MB)
- `venv/` (100-200 MB)
- `build/` (production builds)
- Cache files

---

## Troubleshooting

### Port Already in Use

**Error:** Port 3000 or 5001 is already in use

**Solution:**
```bash
# Linux/macOS - Find and kill process
lsof -ti:3000 | xargs kill -9
lsof -ti:5001 | xargs kill -9

# Windows - Find and kill process
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Docker Issues

**Error:** Docker build fails

**Solution:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

### Python/Node Not Found

**Error:** Command not found

**Solution:**
```bash
# Check if installed
python3 --version
node --version

# Add to PATH if installed but not found
# Windows: Add to System Environment Variables
# Linux/macOS: Add to ~/.bashrc or ~/.zshrc
export PATH="$PATH:/path/to/python:/path/to/node"
```

### Permission Denied (Linux/macOS)

**Error:** Permission denied when running scripts

**Solution:**
```bash
chmod +x *.sh
```

### Installation Fails

**Error:** Package installation fails

**Solution:**
```bash
# Update package managers
# Ubuntu/Debian
sudo apt update && sudo apt upgrade

# macOS
brew update && brew upgrade

# Python
pip install --upgrade pip setuptools wheel

# Node.js
npm install -g npm@latest
```

---

## Uninstallation

### Docker Installation
```bash
docker-compose down -v
docker rmi excel-visualiser_excel-visualizer
```

### Local Installation

**Windows:**
```cmd
rmdir /s venv
rmdir /s node_modules
```

**Linux/macOS:**
```bash
rm -rf venv node_modules build
```

---

## Support

If you encounter issues not covered here:

1. Check the [main README](README.md)
2. Review the [CLAUDE.md](CLAUDE.md) file for architecture details
3. Open an issue on GitHub with:
   - Your operating system and version
   - Installation method attempted
   - Complete error message
   - Steps to reproduce

---

## Next Steps

After installation:
1. Read the [Quick Start Guide](QUICK_START.md)
2. Review the [README](README.md) for features
3. Check [CLAUDE.md](CLAUDE.md) for development details
