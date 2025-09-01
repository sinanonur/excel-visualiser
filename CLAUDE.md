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

## Development Commands

### Backend Setup
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

### Frontend Setup
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

### Unified Development
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