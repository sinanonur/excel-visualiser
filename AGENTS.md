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

```bash
# Frontend production build
npm run build

# MSI Package (Windows only)
.\build-msi.ps1
# Requires WiX Toolset 3.11+
```