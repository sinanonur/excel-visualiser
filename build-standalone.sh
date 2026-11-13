#!/bin/bash
# Standalone build (Linux/macOS): one folder with a single executable that
# contains Python, every library, the API and the web page.
# Users need nothing installed. Build machine needs Python 3.11 and Node.js.

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

cd "$(dirname "$0")"

echo "============================================================"
echo "  Excel Data Visualizer - Standalone Build                 "
echo "============================================================"
echo

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
else
    print_warning "Unsupported platform for this script. Use build-standalone.ps1 for Windows"
    exit 1
fi
print_info "Building for platform: $PLATFORM"

PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
    for candidate in python3.11 python3; do
        if command -v "$candidate" &> /dev/null; then PYTHON="$candidate"; break; fi
    done
fi
if [ -z "$PYTHON" ]; then
    print_warning "Python 3 not found. Install Python 3.11 or set PYTHON=/path/to/python3.11"
    exit 1
fi
print_info "Using $($PYTHON --version)"

print_info "Cleaning previous builds..."
rm -rf standalone build dist pyinstaller-work 2>/dev/null || true
mkdir -p standalone

# Build environment: kept outside the package; reused between builds.
BUILD_ENV="standalone-build/venv"
if [ ! -x "$BUILD_ENV/bin/python" ]; then
    print_info "Creating build environment in $BUILD_ENV..."
    "$PYTHON" -m venv "$BUILD_ENV"
fi
print_info "Installing Python dependencies and PyInstaller into the build environment..."
"$BUILD_ENV/bin/python" -m pip install --quiet --upgrade pip
"$BUILD_ENV/bin/python" -m pip install --quiet -r requirements.txt pyinstaller

print_info "Building optimized frontend..."
if [ ! -d node_modules ]; then
    npm ci
fi
npm run build

print_info "Building the executable (this may take a few minutes)..."
"$BUILD_ENV/bin/python" -m PyInstaller backend.spec --clean --noconfirm \
    --workpath pyinstaller-work --distpath standalone/runtime

print_info "Creating launcher script..."
cat > standalone/launch.sh << 'EOFLAUNCH'
#!/bin/bash
# Excel Data Visualizer launcher. Pass --shared to let other computers on
# this network use the app (there is no login).
cd "$(dirname "$0")"

./runtime/excel-visualizer-backend/excel-visualizer-backend "$@" &
APP_PID=$!
trap "kill $APP_PID 2>/dev/null; exit" INT TERM

# Wait up to 30 seconds for the server to answer.
for _ in $(seq 1 60); do
    if (echo > /dev/tcp/127.0.0.1/5001) 2>/dev/null; then break; fi
    if ! kill -0 $APP_PID 2>/dev/null; then echo "The app stopped while starting."; exit 1; fi
    sleep 0.5
done

echo
echo "=========================================="
echo "  Excel Data Visualizer is running"
echo "  Open http://localhost:5001"
echo "  Press Ctrl+C to stop"
echo "=========================================="
echo

if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5001 2>/dev/null &
elif command -v open &> /dev/null; then
    open http://localhost:5001 2>/dev/null &
fi

wait $APP_PID
EOFLAUNCH
chmod +x standalone/launch.sh

cat > standalone/README.txt << 'EOFREADME'
Excel Data Visualizer - Standalone Edition
==========================================

Everything the app needs is in this folder. Nothing has to be installed.

START
-----
  ./launch.sh

Your browser opens http://localhost:5001. Stop the app with Ctrl+C.

SHARE WITH OTHER COMPUTERS (optional)
-------------------------------------
  ./launch.sh --shared

Other computers on the same network can then open http://<this computer's
name or address>:5001. There is no login: anyone on the network can see the
loaded file. Use this only on a network you trust.

TROUBLESHOOTING
---------------
Port 5001 already in use: stop the other program using it
  (find it with: lsof -i :5001).
Permission denied: chmod +x launch.sh runtime/excel-visualizer-backend/excel-visualizer-backend
EOFREADME

APP_SIZE=$(du -sh standalone/runtime | cut -f1)
TOTAL_SIZE=$(du -sh standalone | cut -f1)

print_success "Standalone build complete!"
echo
echo "  Application (Python, libraries, web page): $APP_SIZE"
echo "  TOTAL PACKAGE SIZE:                        $TOTAL_SIZE"
echo
print_info "Creating distribution package..."
tar -czf "excel-visualizer-standalone-$PLATFORM.tar.gz" standalone/
ARCHIVE_SIZE=$(du -sh "excel-visualizer-standalone-$PLATFORM.tar.gz" | cut -f1)
print_success "Distribution package: excel-visualizer-standalone-$PLATFORM.tar.gz ($ARCHIVE_SIZE)"
echo "  Users extract it and run ./launch.sh"
