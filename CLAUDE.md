# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Excel Data Science Visualizer is a full-stack web application for exploring and visualizing Excel datasets. It features automatic data type detection, smart list/set column expansion, advanced filtering, and interactive plotting capabilities.

## Architecture

### Full-Stack Structure
- **Frontend**: React application (port 3000) with Material-UI components
- **Backend**: Flask API server (port 5001) for data processing and visualization
- **Data Processing**: Pandas-based pipeline with Plotly for interactive charts

### Key Components
- `backend/app.py`: Flask server with DataProcessor class handling Excel parsing, filtering, and plotting
- `src/components/`: React components for file upload, data preview, filtering, and visualization
- `src/App.js`: Main application with tab-based navigation (Data Preview, Column Management, Filters, Visualizations)

### Data Flow
1. Excel files uploaded via React dropzone component
2. Backend processes with pandas, detects column types (numeric, categorical, text, datetime, boolean, lists/sets)
3. Frontend displays data preview with pagination and type-aware filtering options
4. Plotly generates interactive visualizations that respect active filters

## Installation & Deployment

### Quick Install (Recommended)

**Fastest way to get started on any platform:**

```bash
# Linux/macOS
./quick-install.sh

# Windows
quick-install.bat
```

This automatically detects Docker and uses containerized installation if available, otherwise installs dependencies locally.

### Docker Installation (Easiest - All Platforms)

**Recommended for production and minimal disk usage:**

```bash
# Build and start (one command)
docker-compose up --build

# Or run in background
docker-compose up -d

# Stop
docker-compose down
```

**Benefits:**
- No local Python/Node.js installation required
- Consistent environment across all platforms
- Minimal disk space (500-700MB total)
- Production-ready configuration

**Files:**
- `Dockerfile`: Multi-stage build for compact image
- `docker-compose.yml`: Service orchestration
- `.dockerignore`: Excludes unnecessary files from build

### Platform-Specific Installation

**Windows:**
```powershell
.\install-windows.ps1  # PowerShell (recommended)
.\run.ps1 start

# Or
install-windows.bat    # Batch file
run.bat
```

**macOS:**
```bash
./install-macos.sh
./run.sh start
# Or double-click: "Excel Visualizer.app"
```

**Linux:**
```bash
./install-linux.sh
./run.sh start
```

All platform installers:
- Detect and install required dependencies
- Create virtual environments
- Generate platform-specific launcher scripts
- Support all major distributions/versions

### Production Build

Create optimized production package (requires Python/Node.js on target system):

```bash
./build-production.sh

# Output: production/ folder with:
# - Compiled frontend (optimized)
# - Backend application
# - Minimal dependencies
# - Run scripts for all platforms
```

### Standalone Build (RECOMMENDED FOR DISTRIBUTION)

**Build fully self-contained packages with Python embedded - NO installation required!**

```bash
# Linux/macOS
./build-standalone.sh

# Windows
.\build-standalone.ps1
```

**What's included in standalone builds:**
- Python 3.11 embedded runtime (~30-50 MB)
- All Python libraries (pandas, flask, plotly, numpy, etc.) (~250-300 MB)
- Compiled backend executable (~150-200 MB)
- Optimized frontend build (~50 MB)
- Platform-specific launcher scripts

**Benefits:**
- Users need ZERO dependencies installed
- No Python, Node.js, or pip required
- Fully portable (works from USB drives)
- One-click launch experience
- Perfect for distribution to non-technical users

**Size comparison (with dependencies included):**
- Repository (source code only): ~2 MB
- Production build (requires Python/Node): 50-100 MB
- **Standalone build (Python + all libs bundled): 450-550 MB** ⭐
- Docker image: 500-700 MB
- Full dev install (local dependencies): 400-600 MB

**Standalone package breakdown:**
- Python runtime: ~30-50 MB
- Python libraries (pandas, numpy, plotly, etc.): ~250-300 MB
- Backend executable (PyInstaller): ~150-200 MB
- Frontend (React build): ~50 MB
- Application code: ~2 MB
- **Compressed archive: ~200-300 MB**

### Development Commands

**Backend Setup:**
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate.bat # Windows

# Install dependencies
pip install -r requirements.txt

# Start backend server (port 5001)
python start_backend.py
# OR manually:
cd backend && python app.py
```

**Frontend Setup:**
```bash
# Install dependencies
npm install

# Start development server (port 3000)
npm start

# Build for production
npm run build

# Run tests
npm test
```

**Unified Development:**
```bash
# Start both servers (use platform-specific script)
./start_frontend.sh  # Linux/macOS - starts both backend and frontend
run.bat             # Windows
```

## Key APIs

### Backend Endpoints (Flask)
- `POST /upload`: Process Excel files and detect column types
- `GET /column-info`: Retrieve current column metadata
- `POST /update-column-type`: Manually override column data types
- `POST /expand-column`: Expand list/set columns into separate columns
- `POST /apply-filters`: Apply filtering criteria to dataset
- `POST /plot`: Generate interactive Plotly visualizations
- `GET /data-preview`: Paginated data preview with filter support

### Data Processing Features
- **Smart Type Detection**: Automatically identifies numeric, categorical, text, datetime, boolean, and list/set columns
- **List/Set Expansion**: Parses `[item1, item2]` or `{item1, item2}` formatted columns into separate boolean columns
- **Advanced Filtering**: Type-aware filters (categorical selection, numeric ranges, text patterns, boolean values)
- **Filter-Aware Plotting**: All visualizations respect currently active filters

## Testing

Test files are provided:
- `test_data.xlsx`: Sample Excel file for testing functionality
- `test_upload.py`: Backend upload functionality tests
- `test_filtering.py`: Data filtering tests

Run Python tests manually as there's no automated test runner configured.

## Architecture Notes

The application uses a stateful backend approach where the DataProcessor class maintains the current dataset state, applied filters, and column metadata in memory. This allows for real-time filtering and visualization updates without re-uploading files.

The frontend uses React state management for UI interactions and communicates with the backend via Axios HTTP requests. Material-UI provides the component library for consistent styling.

All visualizations are generated server-side using Plotly and returned as JSON for rendering in the React frontend using react-plotly.js.

## Windows MSI Package

### Overview

The MSI installer provides a professional Windows installation experience with two modes:

1. **Online MSI** (requires internet during installation)
2. **Offline MSI** ⭐ (fully self-contained, NO internet required)

### Building MSI Installer

**Prerequisites:**
- **WiX Toolset 3.11+** - Install from [wixtoolset.org](https://wixtoolset.org/releases/) or via Chocolatey: `choco install wixtoolset`

**Online MSI (Traditional):**
```powershell
# Build MSI package (downloads dependencies during installation)
.\build-msi.ps1

# Custom version
.\build-msi.ps1 -Version "1.0.1"

# Clean build with verbose output
.\build-msi.ps1 -Clean -Verbose -OutputPath "releases"
```

**Offline MSI (RECOMMENDED):** ⭐
```powershell
# Step 1: Prepare offline bundle (downloads all dependencies locally)
.\prepare-offline-msi.ps1

# This downloads and bundles:
# - Python 3.11 embedded runtime (~40 MB)
# - All Python packages as wheels (~100 MB)
# - Pre-built React frontend (~25 MB)
# Total bundle: ~165 MB

# Step 2: Build offline MSI (includes all dependencies)
.\build-msi.ps1 -Offline

# Output: dist/ExcelDataScienceVisualizer-1.0.0-Offline.msi (~176 MB)
```

### Offline MSI Benefits

**Why use Offline MSI:**
- ✅ **NO internet required** during installation
- ✅ **NO Python or Node.js** required on target system
- ✅ **Instant installation** - no downloading during install
- ✅ **Works in air-gapped environments** (offline/secure networks)
- ✅ **Consistent installations** - same dependencies every time
- ✅ **Perfect for distribution** to non-technical users

**What's bundled:**
- Python 3.11 embedded runtime (no system Python needed)
- All Python libraries pre-downloaded (pandas, flask, plotly, etc.)
- Pre-built React frontend (no Node.js needed)
- Launcher scripts with visible console windows

### MSI Structure

**Files:**
- `installer/Product.wxs`: WiX configuration with online/offline conditional compilation
- `installer/License.rtf`: License agreement for installer
- `installer/README.md`: Detailed MSI documentation
- `build-msi.ps1`: PowerShell script to build MSI (supports `-Offline` flag)
- `prepare-offline-msi.ps1`: Downloads and prepares offline bundle
- `diagnose-offline.ps1`: Diagnostic script for troubleshooting installations

**Outputs:**
- **Online**: `dist/ExcelDataScienceVisualizer-{version}.msi` (~385 KB)
- **Offline**: `dist/ExcelDataScienceVisualizer-{version}-Offline.msi` (~176 MB)
- `dist/INSTALLATION_GUIDE.md`: User installation instructions

### Installation Features

**Deployment:**
- Installs to `C:\Program Files\Excel Data Science Visualizer\`
- Creates proper directory structure (backend/, src/, public/, frontend/)
- Handles spaces in paths correctly
- Creates Start Menu and Desktop shortcuts
- Supports silent installation: `msiexec /i package.msi /quiet`
- Proper uninstallation via Windows Add/Remove Programs

**Post-Installation (Online MSI):**
- Creates Python virtual environment
- Downloads and installs Python dependencies
- Downloads and installs Node.js dependencies
- Requires internet connection

**Post-Installation (Offline MSI):**
- Copies bundled Python runtime to `python/`
- Installs pre-downloaded Python packages from `bundle/python-wheels/`
- Copies pre-built frontend from `bundle/frontend-build/` to `frontend/`
- NO internet connection required

**Launcher Script (`run-offline.ps1`):**
- Auto-detects Python location (bundled vs system)
- Auto-detects frontend location (installation vs source)
- Stores PID files in user temp directory (no admin privileges needed)
- Shows visible console windows for debugging
- Auto-kills old processes on ports 5001/3000
- Works from any directory (uses `$PSScriptRoot`)
- Opens browser automatically to http://localhost:3000

### Testing & Troubleshooting

**Test the installation:**
```powershell
# Run diagnostic script
cd "C:\Program Files\Excel Data Science Visualizer"
.\diagnose-offline.ps1

# Or use batch launchers (keep console open for errors)
.\launch-backend.bat
.\launch-frontend.bat

# Or use PowerShell launcher
.\run-offline.ps1 start
.\run-offline.ps1 stop
.\run-offline.ps1 status
```

**Common Issues:**
1. **Permission errors**: PID files now stored in `%TEMP%\ExcelVisualizer\`
2. **Path with spaces**: All paths use proper quoting
3. **Missing files**: Diagnostic script shows what's missing
4. **Frontend directory empty**: Batch launcher auto-copies from bundle

### Distribution

**For end users:**
1. Build offline MSI: `.\build-msi.ps1 -Offline`
2. Distribute: `dist/ExcelDataScienceVisualizer-1.0.0-Offline.msi`
3. Include: `dist/INSTALLATION_GUIDE.md`
4. Users double-click MSI to install
5. Launch from Start Menu or Desktop shortcut
6. NO technical knowledge required

## Size Optimization

The repository is designed to be compact and efficient:

### Repository Size
- **Git repository**: ~2 MB (excluding dependencies)
- **Excluded from Git** (via `.gitignore`):
  - `node_modules/` - installed via npm
  - `venv/` - created during setup
  - Build artifacts and caches
  - Platform-specific files

### Deployment Options by Size

1. **Offline MSI (BEST FOR WINDOWS USERS)** ⭐
   - Size: ~176 MB
   - Includes: Python runtime + all libraries + pre-built frontend
   - Requirements: NONE - fully self-contained!
   - Best for: Windows end-users, enterprise deployment, air-gapped environments
   - Scripts: `prepare-offline-msi.ps1` + `build-msi.ps1 -Offline`
   - Platform: Windows only (MSI installer)
   - Features: One-click install, no technical knowledge needed

2. **Standalone Build (BEST FOR CROSS-PLATFORM)** ⭐
   - Uncompressed: 450-550 MB
   - Compressed: 200-300 MB
   - Includes: Python runtime + all libraries + compiled executable
   - Requirements: NONE - fully self-contained!
   - Best for: End-user distribution, non-technical users, portable apps
   - Scripts: `build-standalone.sh` / `build-standalone.ps1`
   - Platform: Linux, macOS, Windows

3. **Docker (Recommended for servers)**
   - Size: 500-700 MB
   - Includes: Everything needed to run
   - Requirements: Docker only
   - Best for: Production servers, cloud deployment
   - Scripts: `docker-compose up`

4. **Production Build**
   - Size: 50-100 MB
   - Includes: Compiled code + minimal dependencies
   - Requirements: Python 3.7+ and Node.js 14+ on target system
   - Best for: Dedicated servers with runtime already installed
   - Scripts: `build-production.sh`

5. **Source + Dependencies**
   - Size: 400-600 MB
   - Includes: Full development environment
   - Requirements: Python 3.7+, Node.js 14+
   - Best for: Development, customization
   - Scripts: `install-*.sh` / `install-*.ps1`

### Optimization Tips

**Reduce local disk usage:**
```bash
# Clear caches after installation
npm cache clean --force
pip cache purge

# Use Docker instead of local install
docker-compose up  # No local dependencies!
```

**Reduce Docker image size:**
- Multi-stage build already implemented
- Uses Alpine/slim base images
- Only production dependencies included
- Build cache excluded via `.dockerignore`

**For distribution:**
```bash
# Create minimal production package
./build-production.sh

# Package for distribution
tar -czf excel-visualizer-v1.0.tar.gz production/
```

## Deployment Scenarios

### Local Development
```bash
./quick-install.sh  # or quick-install.bat
./run.sh start
```

### Docker Deployment
```bash
docker-compose up -d
# Application runs at http://localhost:3000
```

### Production Server
```bash
# Build production package locally
./build-production.sh

# Transfer to server
scp -r production/ user@server:/opt/excel-visualizer/

# On server
cd /opt/excel-visualizer
./run-production.sh
```

### Standalone Distribution (End Users)
```bash
# Build standalone package (includes Python!)
./build-standalone.sh      # Linux/macOS
.\build-standalone.ps1     # Windows

# Distribute the compressed archive
# Users extract and run with ONE click:
./launch.sh               # Linux/macOS
launch.bat                # Windows

# NO installation needed - Python and all dependencies are bundled!
```

### Cloud Deployment
The Docker image can be deployed to:
- AWS ECS/EKS
- Google Cloud Run
- Azure Container Instances
- Digital Ocean App Platform
- Heroku (with Dockerfile)

## File Structure

```
excel-visualiser/
├── backend/                  # Flask application
│   └── app.py               # Main backend server
├── src/                     # React frontend source
│   ├── components/          # UI components
│   │   └── filters/        # Filter components
│   └── App.js              # Main application
├── public/                  # Static assets
│   └── index.html          # HTML template
│
├── installer/               # MSI installer configuration ⭐
│   ├── Product.wxs         # WiX installer definition
│   ├── License.rtf         # License agreement
│   └── README.md           # MSI documentation
│
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # Container orchestration
├── .dockerignore            # Docker build exclusions
│
├── backend.spec             # PyInstaller configuration
├── build-standalone.sh      # Standalone build (Linux/macOS)
├── build-standalone.ps1     # Standalone build (Windows)
├── build-production.sh      # Production build script
│
├── build-msi.ps1            # MSI builder (online/offline) ⭐
├── prepare-offline-msi.ps1  # Offline bundle preparation ⭐
├── diagnose-offline.ps1     # Installation diagnostics ⭐
├── launch-backend.bat       # Backend launcher (visible console) ⭐
├── launch-frontend.bat      # Frontend launcher (visible console) ⭐
├── run-offline.ps1          # Offline runtime launcher ⭐
│
├── quick-install.sh         # Fast installer (Linux/macOS)
├── quick-install.bat        # Fast installer (Windows)
├── install-linux.sh         # Full Linux installer
├── install-macos.sh         # Full macOS installer
├── install-windows.ps1      # Full Windows installer
│
├── requirements.txt         # Python dependencies
├── package.json             # Node.js dependencies
├── INSTALLATION_GUIDE.md    # Detailed installation docs
├── CLAUDE.md               # This file (project instructions)
└── AGENTS.md               # Agent usage guide
```

**Build Outputs (not in Git):**
```
standalone/                  # Standalone build (450-550 MB)
├── python/                 # Embedded Python 3.11 runtime
├── runtime/                # Compiled backend executable
├── app/                    # Frontend and source
├── launch.sh / launch.bat  # One-click launcher
└── README.txt             # User instructions

production/                  # Production build (50-100 MB)
├── backend/                # Backend application
├── frontend/build/         # Compiled React app
└── run-production.sh       # Launcher (requires Python/Node)
```

See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed installation instructions and troubleshooting.