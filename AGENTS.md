# Excel Data Science Visualizer - AGENTS.md

This file provides AI coding agents with specific guidance for working on the Excel Data Science Visualizer project.

## Project Context

Full-stack web application for exploring and visualizing Excel datasets with automatic data type detection, smart list/set column expansion, advanced filtering, and interactive plotting capabilities.

**Stack**: React frontend (port 3000) + Flask backend (port 5001) + Pandas + Plotly

## Dev Environment Setup

### Backend Setup
```bash
# Create and activate virtual environment (requires Python 3.10+)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate.bat # Windows

# Install dependencies
pip install -r requirements.txt

# Start backend server
python start_backend.py
```

### Frontend Setup
```bash
# Install dependencies
npm install

# Start development server
npm start
```

### Unified Development
```bash
# Platform-specific scripts to start both servers
./start_frontend.sh     # Linux/macOS
./run-windows.bat       # Windows
```

## Code Style and Conventions

- **Backend**: Follow Flask patterns, use DataProcessor class for stateful data management
- **Frontend**: React functional components with hooks, Material-UI for styling
- **API**: RESTful endpoints with clear JSON responses
- **Data Processing**: Pandas-based pipeline with type-aware operations
- **No comments**: DO NOT add comments to code unless explicitly requested

## Testing Instructions

```bash
# Backend tests (run manually - no automated test runner)
python test_upload.py
python test_filtering.py

# Frontend tests
npm test

# Use provided test data
# test_data.xlsx: Sample Excel file for functionality testing
```

## Key Architecture Patterns

- **Stateful Backend**: DataProcessor maintains dataset state, filters, and metadata in memory
- **Type-Aware Processing**: Auto-detect and handle numeric, categorical, text, datetime, boolean, list/set columns
- **Filter-Aware Visualizations**: All plots respect currently active filters
- **List/Set Expansion**: Parse `[item1, item2]` or `{item1, item2}` formats into separate boolean columns

## Critical API Endpoints

- `POST /upload`: Process Excel files, detect column types
- `POST /apply-filters`: Apply filtering criteria to dataset
- `POST /plot`: Generate interactive Plotly visualizations
- `GET /data-preview`: Paginated data with filter support

## Pull Request Guidelines

- **Title Format**: `[component]: brief description` (e.g., `backend: add date range filtering`)
- **Pre-commit Checks**: Ensure both frontend and backend start successfully
- **Testing**: Verify with test_data.xlsx before submitting
- **No Auto-commits**: Only commit when explicitly requested by user

## Security and Performance Notes

- Never commit sensitive data or credentials
- Backend maintains dataset in memory - consider memory usage for large files
- All user inputs should be validated before processing
- Use type-aware filtering to prevent data type errors

## Build and Deployment

### Production Builds

```bash
# Frontend production build
npm run build

# Standalone build (cross-platform, includes Python)
./build-standalone.sh      # Linux/macOS
.\build-standalone.ps1     # Windows

# Production build (minimal, requires runtime)
./build-production.sh
```

### MSI Package (Windows only)

```powershell
# Online MSI (downloads dependencies during install)
.\build-msi.ps1

# Offline MSI (self-contained, no internet required) ⭐
.\prepare-offline-msi.ps1  # Download dependencies
.\build-msi.ps1 -Offline   # Build MSI with bundled dependencies

# Requirements: WiX Toolset 3.11+
```

**Offline MSI Features:**
- Bundles Python 3.11 embedded runtime (~40 MB)
- Includes all Python packages (~100 MB)
- Pre-built React frontend (~25 MB)
- No internet or dependencies required at install time
- Perfect for enterprise/air-gapped environments

### Platform-Specific Installers

```bash
# Quick install (auto-detects Docker)
./quick-install.sh   # Linux/macOS
quick-install.bat    # Windows

# Full platform installers
./install-linux.sh
./install-macos.sh
.\install-windows.ps1
```

## Working with Claude Code Agents

### When to Use Agents

✅ **DO use agents for:**
- Complex multi-step refactoring across files
- Feature implementation spanning frontend + backend
- Codebase exploration ("how does X work?")
- Cross-platform script updates
- Documentation updates across multiple files

❌ **DON'T use agents for:**
- Single file edits (use Edit tool)
- Reading specific files (use Read tool)
- Finding known classes/functions (use Grep/Glob)
- Simple one-line changes

### Recommended Agent Types

**Explore Agent** (use frequently!) ⭐
- Finding implementation patterns
- Understanding code architecture
- Locating specific functionality
- Answering "where is X?" questions

```
Example: "Use Explore agent with medium thoroughness to find
all places where port 5001 is configured"
```

**General-Purpose Agent**
- Multi-file feature implementation
- Complex refactoring
- Debugging across components
- Build system modifications

```
Example: "Use general-purpose agent to add error boundary
components to all main React routes"
```

### Project-Specific Agent Workflows

**Workflow 1: Adding New Filter Type**
```
Agent: general-purpose
Task: Implement date range filtering
Steps:
1. Backend: Add to DataProcessor.apply_filters()
2. Frontend: Create DateRangeFilter.js component
3. Frontend: Update FilterManager.js to include new filter
4. Update API documentation
```

**Workflow 2: MSI Installer Modifications**
```
Agent: general-purpose
Task: Add custom action to MSI
Steps:
1. Modify installer/Product.wxs
2. Update build-msi.ps1 if needed
3. Test build process
4. Update installer/README.md
```

**Workflow 3: Cross-Platform Script Updates**
```
Agent: general-purpose
Task: Update dependency versions across all installers
Files: install-*.{sh,ps1,bat}, quick-install.*
Ensure: Consistent behavior across platforms
```

### Best Practices for This Project

1. **Explore before modifying**: Use Explore agent to understand architecture first
2. **Test installations**: After MSI changes, test on clean Windows system
3. **Maintain consistency**: Keep all platform scripts in sync
4. **Update documentation**: CLAUDE.md, AGENTS.md, README.md, installer docs
5. **Verify paths**: Ensure Windows paths handle spaces (use `$PSScriptRoot`)

## Installation Script Patterns

### Portable Path Handling (Windows)

```powershell
# ✅ CORRECT: Use $PSScriptRoot for script-relative paths
$ScriptDir = $PSScriptRoot
$PythonPath = Join-Path $ScriptDir "python\python.exe"

# ❌ WRONG: Using $PWD depends on current directory
$PythonPath = "python\python.exe"
```

### Permission-Safe File Storage

```powershell
# ✅ CORRECT: Use temp directory for writable files
$PidDir = Join-Path $env:TEMP "ExcelVisualizer"
New-Item -ItemType Directory -Path $PidDir -Force | Out-Null

# ❌ WRONG: Writing to Program Files requires admin
$pidFile = "backend.pid"  # Fails in C:\Program Files\
```

### Cross-Platform Path Construction

```bash
# Linux/macOS
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_PATH="$SCRIPT_DIR/python/bin/python3"

# Windows (PowerShell)
$ScriptDir = $PSScriptRoot
$PythonPath = Join-Path $ScriptDir "python\python.exe"

# Windows (Batch)
set SCRIPT_DIR=%~dp0
set PYTHON_PATH=%SCRIPT_DIR%python\python.exe
```

## Troubleshooting Common Issues

### MSI Installation Errors

**Problem**: Files not found after installation
- **Check**: Directory structure in installer/Product.wxs
- **Fix**: Ensure ComponentGroups use correct Directory IDs

**Problem**: Permission denied errors
- **Check**: Are PID files being written to Program Files?
- **Fix**: Use user temp directory for runtime files

**Problem**: Custom actions fail silently
- **Check**: MSI Event Log in Windows
- **Fix**: Add error handling and logging to custom actions

### Launch Script Issues

**Problem**: Console windows close immediately
- **Solution**: Use batch launchers (launch-backend.bat, launch-frontend.bat)
- **Debug**: Run diagnose-offline.ps1 for diagnostics

**Problem**: Paths with spaces not working
- **Solution**: Use proper quoting and Join-Path for all paths
- **Example**: `Start-Process -FilePath $exe -ArgumentList "`"$path`""`

### Build Process Issues

**Problem**: Offline MSI missing dependencies
- **Solution**: Run prepare-offline-msi.ps1 first
- **Verify**: Check installer/bundle/ contains python-embed, python-wheels, frontend-build

**Problem**: WiX compilation errors
- **Solution**: Check for proper XML syntax in Product.wxs
- **Tool**: Use WiX validator or compile with -v for verbose output

## Reference Documentation

- **Project Instructions**: [CLAUDE.md](CLAUDE.md) - Comprehensive project guide
- **Installation Guide**: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - End-user instructions
- **MSI Documentation**: [installer/README.md](installer/README.md) - MSI-specific details
- **Main README**: [README.md](README.md) - Project overview

## Agent Task Templates

### Template 1: Add New Visualization

```
Use general-purpose agent to add [chart type] visualization:

Requirements:
- Backend: Add plot function to backend/app.py
- Frontend: Add to PlotGenerator.js chart type selector
- Frontend: Add configuration UI for chart options
- Test with test_data.xlsx
- Update documentation

Success criteria:
- Chart renders correctly with sample data
- Respects active filters
- Configuration options work as expected
```

### Template 2: Refactor Component

```
Use general-purpose agent to extract [functionality] into reusable hook:

Files affected:
- src/components/[Component].js (extract from here)
- src/hooks/use[HookName].js (create new hook)
- Update imports in components using this logic

Requirements:
- Maintain existing behavior
- Add PropTypes/TypeScript types
- Test with existing components
```

### Template 3: Update Build System

```
Use general-purpose agent to [build system change]:

Scope:
- build-msi.ps1
- prepare-offline-msi.ps1
- installer/Product.wxs
- Documentation updates

Testing:
- Clean build from scratch
- Install on fresh Windows system
- Verify all features work
- Test uninstall process
```

## Summary

This project emphasizes:
- **Cross-platform compatibility**: Scripts work on Windows, Linux, macOS
- **Offline capability**: MSI installer requires no internet
- **Professional installation**: Proper Windows installer with MSI
- **Portable execution**: Scripts use relative paths, work from any location
- **Error visibility**: Console windows stay open, diagnostic scripts available

When working with agents, prioritize understanding the architecture first (use Explore agent), then implement changes systematically (use general-purpose agent with clear requirements).

For detailed project structure and installation options, see [CLAUDE.md](CLAUDE.md).