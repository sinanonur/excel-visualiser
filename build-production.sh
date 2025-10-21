#!/bin/bash
# Production Build Script for Excel Data Visualizer
# Creates an optimized, compact production build

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

echo "=============================================="
echo "  Excel Data Visualizer - Production Build  "
echo "=============================================="
echo

# Clean previous builds
print_info "Cleaning previous builds..."
rm -rf build dist production 2>/dev/null || true

# Build frontend
print_info "Building optimized frontend..."
npm run build

# Create production directory
print_info "Creating production package..."
mkdir -p production/frontend
mkdir -p production/backend

# Copy necessary files
cp -r build production/frontend/
cp -r backend production/
cp start_backend.py production/
cp requirements.txt production/
cp README.md production/

# Create optimized requirements.txt (production only)
cat > production/requirements.txt << EOF
flask==3.1.2
flask-cors==6.0.1
pandas==2.3.2
openpyxl==3.1.5
plotly==6.3.0
numpy==2.3.2
EOF

# Create production run script
cat > production/run-production.sh << 'EOFSCRIPT'
#!/bin/bash
# Production runner script

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start backend
python start_backend.py &
BACKEND_PID=$!

# Serve frontend (using Python's built-in server)
cd frontend/build
python -m http.server 3000 &
FRONTEND_PID=$!

echo
echo "Excel Data Visualizer is running!"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:5001"
echo
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
EOFSCRIPT

chmod +x production/run-production.sh

# Create Windows batch file
cat > production/run-production.bat << 'EOFBAT'
@echo off
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

start "Backend" /min python start_backend.py
timeout /t 3 /nobreak >nul
cd frontend\build
start "Frontend" python -m http.server 3000
cd ..\..

echo.
echo Excel Data Visualizer is running!
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:5001
timeout /t 5 /nobreak
start http://localhost:3000
EOFBAT

# Calculate sizes
FRONTEND_SIZE=$(du -sh production/frontend/build | cut -f1)
TOTAL_SIZE=$(du -sh production | cut -f1)

print_success "Production build complete!"
echo
echo "Build Statistics:"
echo "  Frontend build: $FRONTEND_SIZE"
echo "  Total package:  $TOTAL_SIZE"
echo
print_info "Production files are in: ./production/"
echo
print_info "To deploy:"
echo "  1. Copy the 'production' folder to your server"
echo "  2. Run: ./run-production.sh (Linux/macOS) or run-production.bat (Windows)"
echo
print_info "Or create a distribution package:"
echo "  tar -czf excel-visualizer-production.tar.gz production/"
echo
