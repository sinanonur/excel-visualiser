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

Create optimized production package:

```bash
./build-production.sh

# Output: production/ folder with:
# - Compiled frontend (optimized)
# - Backend application
# - Minimal dependencies
# - Run scripts for all platforms
```

**Size comparison:**
- Repository: ~2 MB
- Production build: 50-100 MB
- Docker image: 500-700 MB
- Full dev install: 400-600 MB

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

### Building MSI Installer
```powershell
# Prerequisites: Install WiX Toolset 3.11+ from wixtoolset.org
# Or via Chocolatey: choco install wixtoolset

# Build MSI package
.\build-msi.ps1

# Build with custom version
.\build-msi.ps1 -Version "1.0.1"

# Clean build with verbose output
.\build-msi.ps1 -Clean -Verbose -OutputPath "releases"
```

### MSI Structure
- `installer/Product.wxs`: WiX configuration defining installation behavior
- `installer/License.rtf`: License agreement for installer
- `build-msi.ps1`: PowerShell script to build MSI package
- Output: `dist/ExcelDataScienceVisualizer-{version}.msi`

### Installation Features
- Deploys all application files to Program Files
- Creates Python virtual environment and installs dependencies
- Installs Node.js dependencies via npm
- Creates desktop and Start Menu shortcuts
- Supports silent installation: `msiexec /i package.msi /quiet`
- Proper uninstallation via Windows Add/Remove Programs

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

1. **Docker (Recommended for ease)**
   - Size: 500-700 MB
   - Includes: Everything needed to run
   - Best for: Production, cross-platform deployment

2. **Production Build**
   - Size: 50-100 MB
   - Includes: Compiled code + minimal dependencies
   - Best for: Dedicated servers, VMs

3. **Source + Dependencies**
   - Size: 400-600 MB
   - Includes: Full development environment
   - Best for: Development, customization

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
├── backend/              # Flask application
│   └── app.py           # Main backend server
├── src/                 # React frontend source
│   ├── components/      # UI components
│   └── App.js          # Main application
├── public/              # Static assets
├── Dockerfile           # Multi-stage Docker build
├── docker-compose.yml   # Container orchestration
├── .dockerignore        # Docker build exclusions
├── quick-install.sh     # Fast installer (Linux/macOS)
├── quick-install.bat    # Fast installer (Windows)
├── build-production.sh  # Production build script
├── install-*.sh         # Platform-specific installers
├── requirements.txt     # Python dependencies
├── package.json         # Node.js dependencies
└── INSTALLATION_GUIDE.md # Detailed installation docs
```

See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed installation instructions and troubleshooting.