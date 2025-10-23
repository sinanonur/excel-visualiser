#!/bin/bash
# Quick Install Script for Excel Data Visualizer
# Supports Linux and macOS with minimal dependencies

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "=============================================="
echo "  Excel Data Visualizer - Quick Install     "
echo "=============================================="
echo

# Check for Docker (easiest option)
if command_exists docker && command_exists docker-compose; then
    print_info "Docker detected! Using containerized installation (fastest & smallest)"
    echo
    print_info "Building Docker image..."
    docker-compose build

    print_success "Installation complete!"
    echo
    print_info "To start the application, run:"
    echo "  docker-compose up"
    echo
    print_info "The application will be available at:"
    echo "  http://localhost:3000"
    echo
    print_info "To stop the application:"
    echo "  docker-compose down"
    echo
    exit 0
fi

print_warning "Docker not found. Installing dependencies locally..."
echo

# Check Python
if ! command_exists python3; then
    print_error "Python 3 is required but not installed."
    print_info "Please install Python 3.7+ from:"
    echo "  macOS: brew install python3"
    echo "  Linux: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Check Node.js
if ! command_exists node || ! command_exists npm; then
    print_error "Node.js and npm are required but not installed."
    print_info "Please install Node.js 14+ from:"
    echo "  macOS: brew install node"
    echo "  Linux: sudo apt install nodejs npm"
    exit 1
fi

print_success "Python and Node.js found"
echo

# Install dependencies
print_info "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

print_info "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

print_info "Installing Node.js dependencies..."
npm install --silent

print_success "Installation complete!"
echo

# Create simple run script
cat > run.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python start_backend.py &
BACKEND_PID=$!
sleep 3
npm start &
FRONTEND_PID=$!

echo
echo "Excel Data Visualizer is running!"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:5001"
echo
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
EOF

chmod +x run.sh

print_info "To start the application, run:"
echo "  ./run.sh"
echo
print_info "Or manually:"
echo "  source venv/bin/activate && python start_backend.py"
echo "  npm start  (in a new terminal)"
echo
