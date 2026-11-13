# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Excel Data Science Visualizer is a full-stack web application for exploring and visualizing Excel and CSV datasets. It features automatic data type detection, a data profile with quality alerts, smart list/set column expansion, advanced filtering, export, and interactive plotting capabilities.

## Architecture

### Full-Stack Structure
- **Frontend**: React application (port 3000) with Material-UI components
- **Backend**: Flask API server (port 5001) for data processing and visualization
- **Data Processing**: Pandas-based pipeline with Plotly for interactive charts

### Key Components
- `backend/app.py`: Flask routes only (plus the AI-plot execution helper)
- `backend/processing.py`: `DataProcessor` - loading, type detection/conversion, list expansion, filtering, preview paging, profiling, export
- `backend/plots.py`: Plotly figure builders; raise `PlotError` with a user-facing reason
- `backend/llm/`: LLM back-ends for the AI plot (`GeminiLlm`, offline `TestLlm`)
- `src/components/`: React components for file upload, data preview, profile, filtering, and visualization
- `src/App.js`: Main application; owns the dataset state mirrored from the backend and the tab navigation (Data Preview, Profile, Column Management, Filters, Visualizations)

### Data Flow
1. Excel (.xlsx/.xls/.xlsm) or CSV/TSV files uploaded via React dropzone component
2. Backend processes with pandas, detects column types (numeric, categorical, text, datetime, boolean, lists/sets)
3. Frontend displays data preview (paging, sorting, search), a data profile, and type-aware filtering options
4. Plotly generates interactive visualizations that respect active filters
5. The filtered data can be exported as CSV or Excel

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

**Builds one folder that users unpack and run. Nothing has to be installed.**

```bash
# Linux/macOS (build machine needs Python 3.11 and Node.js)
./build-standalone.sh

# Windows (build machine needs Node.js; Python is downloaded for the build)
.\build-standalone.ps1
```

**How it works:**
- PyInstaller (`backend.spec`) bundles Python, the libraries, the backend and the built React app into `standalone/runtime/excel-visualizer-backend/`
- The executable serves the web page and the API on one port, `http://localhost:5001`
- `launch.sh` / `launch.bat` / `launch.ps1` start it and open the browser; add `--shared` (`-Shared` for `launch.ps1`) to let other computers on the network use it
- The build environment (`standalone-build/`) and PyInstaller work folder (`pyinstaller-work/`) stay outside the package
- `python scripts/smoke_standalone.py <path to executable>` checks a build; CI runs it on Linux and Windows

**Size, Linux build measured 13.11.2026:** 179 MB unpacked, 75 MB as `.tar.gz`. The Windows size is reported in the CI log (Package size step).

**Size comparison:**
- Repository (source code only): ~2 MB
- Production build (requires Python/Node): 50-100 MB
- **Standalone build: 179 MB unpacked, 75 MB compressed (Linux)** ⭐
- Docker image: 500-700 MB
- Full dev install (local dependencies): 400-600 MB

### Development Commands

**Backend Setup:**
```bash
# Create and activate virtual environment (requires Python 3.10+)
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

The frontend finds the backend on its own (`src/config.js`): when the backend serves the page (standalone package) it uses the page's address; otherwise `REACT_APP_API_URL` if set at build/start time; otherwise port 5001 on the host the page was loaded from (`localhost` locally, the serving computer in shared mode).

**Backend environment variables:**
- `FLASK_HOST` (default `127.0.0.1`; Docker sets `0.0.0.0`), `FLASK_PORT` (default `5001`)
- `EXCEL_VISUALIZER_SHARED=1` or `--shared` (on `backend/app.py`, `start_backend.py` and the standalone launchers): listen on the network so other computers can use the app. No login; anyone on the network can read the loaded file
- `EXCEL_VISUALIZER_FRONTEND_DIR`: a built frontend (`build/`) for the backend to serve on its own port. The standalone package sets this up automatically
- `FLASK_DEBUG=1` enables the reloader/debugger (off by default - without it, restart the backend after editing Python files)
- `CORS_ORIGINS`: comma-separated exact origins, or `*`. Default: pages from this computer, and pages served from the same host name the browser used to reach the API (needed by shared mode)
- `MAX_UPLOAD_MB` (default `200`), `GEMINI_API_KEY` (AI plots), `EXCEL_VISUALIZER_CACHE_DIR` (type-override cache)

**Unified Development:**
```bash
# Start both servers (use platform-specific script)
./start_frontend.sh     # Linux/macOS - starts both backend and frontend
./run-windows.bat       # Windows - starts both servers in parallel
```

## Key APIs

### Backend Endpoints (Flask)
- `GET /health`: Liveness check (used by the Docker health check)
- `GET /session`: Current dataset state, so a reloaded page resumes the loaded file
- `POST /upload`: Load .xlsx/.xls/.xlsm/.csv/.tsv and detect column types (optional form field `sheet`)
- `POST /select-sheet`: Switch to another sheet of the uploaded workbook
- `GET /column-info`: Retrieve current column metadata
- `POST /update-column-type`: Override a column type **and convert its values** (reports values that could not be converted)
- `POST /expand-column`: Expand list/set columns; `mode` is `positional` (`col_item_1..n`) or `onehot` (boolean `col [item]` columns)
- `GET /filter-options?column=`: Values/ranges needed to build a filter (`/filter-options/<column>` also works)
- `POST /apply-filters`, `POST /clear-filters`, `GET /filter-status`: Manage filters
- `GET /data-preview`: Paginated preview; supports `sort_by`, `sort_dir`, `search`
- `GET /profile`: Per-column statistics, histograms, correlations and data-quality alerts for the filtered data
- `GET /export?format=csv|xlsx&scope=filtered|all`: Download the data
- `POST /plot`: Generate interactive Plotly visualizations (errors explain what to change)
- `POST /generate-llm-plot`: Plot from a natural-language prompt

Most state-changing endpoints return the full dataset state (`columns`, `column_info`, `shape`, filter status), which the frontend merges into its own state.

### Data Processing Features
- **Smart Type Detection**: numeric, categorical, text, datetime (including text dates in CSVs, month-first or day-first), boolean, and list/set columns
- **Type Overrides Convert Data**: conversions always start from the raw values, so they are reversible; overrides are remembered per file for 2 days
- **List/Set Expansion**: Parses `[item1, item2]` or `{item1, item2}` cells (quoted or bare words) into positional columns or one boolean column per item
- **Advanced Filtering**: categorical selection, numeric ranges, text contains/regex (optionally negated), boolean values, date ranges
- **Data Profile**: missing values, duplicates, distribution statistics, top values, correlations, and alerts (mixed types, constant columns, outliers, skew, high cardinality, high correlation). Thresholds are constants at the top of `backend/processing.py`
- **Plot Types**: histogram, box, violin, bar (counts, split, or aggregated numeric), pie, scatter (colour-by, trendline), line (date grouping), correlation heatmap, AI custom
- **Filter-Aware**: previews, profile, plots and exports all use the filtered data

### Dataset State Model
`DataProcessor` keeps three frames: `raw_data` (as loaded, plus expanded columns), `original_data` (typed, unfiltered) and `data` (typed, filtered). Filters never rebuild from the raw file, so expanded columns and type conversions survive filtering.

## Testing

**Backend unit tests (no server needed):**
```bash
pip install -r requirements-dev.txt
python -m pytest            # runs tests/unit against the Flask test client
```

`tests/unit/conftest.py` builds an in-memory workbook covering every column type; add cases there rather than new fixture files.

**Legacy smoke tests (need a running backend on port 5001):** `tests/test_upload.py`, `tests/test_filtering.py`, using `test_data.xlsx`.

There are no frontend unit tests. Before committing frontend changes run `CI=true npm run build`, which fails on any ESLint warning.

**CI** (`.github/workflows/ci.yml`, GitHub Actions) runs on pull requests and pushes to `main`:
- backend tests on Linux and Windows;
- the frontend build with lint warnings as errors;
- the standalone package built on Linux and Windows, then smoke-tested with `scripts/smoke_standalone.py` (starts the executable, loads `test_data.xlsx`, draws plots, exports);
- the Docker image built and started, then checked over HTTP.

## Architecture Notes

The application uses a stateful backend approach where the DataProcessor class maintains the current dataset state, applied filters, and column metadata in memory. This allows for real-time filtering and visualization updates without re-uploading files.

The frontend uses React state management for UI interactions and communicates with the backend via Axios HTTP requests. Material-UI provides the component library for consistent styling.

All visualizations are generated server-side using Plotly and returned as JSON for rendering in the React frontend using react-plotly.js.

**Security posture:** the app is a single-user local tool. The backend binds to localhost and only lets pages from this computer (or, in shared mode, from the same host) read its responses. It has no authentication, so shared mode is for trusted networks only. AI plots execute model-generated Python with a restricted import list; that limits accidents but is not a sandbox, so do not expose the backend to untrusted networks.

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
- `installer/Product.wxs`: WiX configuration with online/offline conditional compilation. It lists every source file explicitly: **when you add a backend module or a React component, add a `<File>` entry here** or the MSI will ship without it
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
- Creates Python 3.11 virtual environment (online) or copies embedded Python (offline)
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
   - Unpacked: 179 MB, compressed: 75 MB (Linux, measured 13.11.2026)
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
│   ├── app.py               # Routes
│   ├── processing.py        # DataProcessor (load, types, filters, profile, export)
│   ├── plots.py             # Plotly figure builders
│   └── llm/                 # AI plot back-ends
├── tests/unit/              # pytest suite (in-process)
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
├── backend.spec             # PyInstaller configuration (bundles backend + built web page)
├── scripts/smoke_standalone.py  # Smoke test for a built standalone package
├── .github/workflows/ci.yml # CI: tests, frontend build, standalone (Linux+Windows), Docker
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
├── requirements-dev.txt     # + pytest
├── pytest.ini               # Test configuration
├── package.json             # Node.js dependencies
├── INSTALLATION_GUIDE.md    # Detailed installation docs
├── CLAUDE.md               # This file (project instructions)
└── AGENTS.md               # Agent usage guide
```

**Build Outputs (not in Git):**
```
standalone/                  # Standalone build (179 MB on Linux)
├── runtime/                # Executable: Python, libraries, backend and web page
├── launch.sh / launch.bat / launch.ps1  # Start it and open the browser
└── README.txt             # User instructions

production/                  # Production build (50-100 MB)
├── backend/                # Backend application
├── frontend/build/         # Compiled React app
└── run-production.sh       # Launcher (requires Python/Node)
```

See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed installation instructions and troubleshooting.