#!/bin/bash

# Excel Data Visualizer - macOS Installation Script
# This script installs all dependencies and sets up the application on macOS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check macOS version
check_macos_version() {
    local version=$(sw_vers -productVersion)
    local major=$(echo $version | cut -d. -f1)
    local minor=$(echo $version | cut -d. -f2)
    
    print_status "macOS version: $version"
    
    # Check if macOS 10.14+ (minimum for Node.js LTS)
    if [ "$major" -ge 11 ] || ([ "$major" -eq 10 ] && [ "$minor" -ge 14 ]); then
        print_success "macOS version is supported"
    else
        print_warning "macOS 10.14+ is recommended. Some features may not work on older versions."
    fi
}

# Function to install Homebrew
install_homebrew() {
    if command_exists brew; then
        print_status "Homebrew found: $(brew --version | head -n1)"
        print_status "Updating Homebrew..."
        brew update
    else
        print_status "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH
        if [[ $(uname -m) == "arm64" ]]; then
            # Apple Silicon Mac
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            # Intel Mac
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        
        print_success "Homebrew installed successfully"
    fi
}

# Function to install Xcode Command Line Tools
install_xcode_tools() {
    if xcode-select -p >/dev/null 2>&1; then
        print_status "Xcode Command Line Tools already installed"
    else
        print_status "Installing Xcode Command Line Tools..."
        xcode-select --install
        
        print_warning "Please wait for Xcode Command Line Tools installation to complete,"
        print_warning "then press Enter to continue..."
        read
    fi
}

# Function to install Python
install_python() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_status "Python3 found: $PYTHON_VERSION"
        
        # Check if version is 3.7+
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
            print_success "Python version is compatible (3.7+)"
        else
            print_warning "Python 3.7+ recommended. Current version: $PYTHON_VERSION"
            print_status "Installing latest Python via Homebrew..."
            brew install python
        fi
    else
        print_status "Installing Python 3..."
        brew install python
    fi
    
    # Install/upgrade pip
    print_status "Upgrading pip..."
    python3 -m pip install --upgrade pip
}

# Function to install Node.js and npm
install_nodejs() {
    if command_exists node && command_exists npm; then
        NODE_VERSION=$(node --version | cut -d'v' -f2)
        print_status "Node.js found: v$NODE_VERSION"
        
        # Check if version is 14+
        if node -e "process.exit(process.version.slice(1).split('.')[0] >= 14 ? 0 : 1)" 2>/dev/null; then
            print_success "Node.js version is compatible (14+)"
        else
            print_warning "Node.js 14+ recommended. Current version: v$NODE_VERSION"
            print_status "Installing latest Node.js via Homebrew..."
            brew install node
        fi
    else
        print_status "Installing Node.js and npm..."
        brew install node
    fi
}

# Function to setup the application
setup_application() {
    print_status "Setting up Excel Data Visualizer..."
    
    # Create virtual environment for Python
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip in virtual environment
    pip install --upgrade pip
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Install Node.js dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    print_success "Application setup completed!"
}

# Function to create startup scripts
create_startup_scripts() {
    print_status "Creating startup scripts..."
    
    # Create run.sh script for macOS
    cat > run.sh << 'EOF'
#!/bin/bash

# Excel Data Visualizer Launcher Script for macOS

print_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Function to open browser
open_browser() {
    sleep 3
    if command -v open >/dev/null 2>&1; then
        print_info "Opening browser..."
        open http://localhost:3000
    fi
}

# Function to start backend
start_backend() {
    print_info "Starting backend server..."
    cd "$(dirname "$0")"
    
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Please run install-macos.sh first."
        exit 1
    fi
    
    source venv/bin/activate
    
    if ! check_port 5001; then
        print_error "Port 5001 is already in use. Please stop the existing service or change the port."
        exit 1
    fi
    
    cd backend
    python app.py &
    BACKEND_PID=$!
    
    # Wait a moment for backend to start
    sleep 3
    
    if ps -p $BACKEND_PID > /dev/null; then
        print_success "Backend server started on http://localhost:5001 (PID: $BACKEND_PID)"
        echo $BACKEND_PID > ../backend.pid
    else
        print_error "Failed to start backend server"
        exit 1
    fi
}

# Function to start frontend
start_frontend() {
    print_info "Starting frontend server..."
    cd "$(dirname "$0")"
    
    if [ ! -d "node_modules" ]; then
        print_error "Node modules not found. Please run install-macos.sh first."
        exit 1
    fi
    
    if ! check_port 3000; then
        print_error "Port 3000 is already in use. Please stop the existing service."
        exit 1
    fi
    
    npm start &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > frontend.pid
    
    sleep 5
    print_success "Frontend server started on http://localhost:3000 (PID: $FRONTEND_PID)"
    
    # Auto-open browser on macOS
    open_browser &
}

# Function to stop servers
stop_servers() {
    print_info "Stopping servers..."
    
    if [ -f "backend.pid" ]; then
        BACKEND_PID=$(cat backend.pid)
        if ps -p $BACKEND_PID > /dev/null; then
            kill $BACKEND_PID
            print_success "Backend server stopped"
        fi
        rm -f backend.pid
    fi
    
    if [ -f "frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null; then
            kill $FRONTEND_PID
            print_success "Frontend server stopped"
        fi
        rm -f frontend.pid
    fi
}

# Function to show status
show_status() {
    print_info "Server Status:"
    
    if [ -f "backend.pid" ]; then
        BACKEND_PID=$(cat backend.pid)
        if ps -p $BACKEND_PID > /dev/null; then
            echo "  Backend:  Running (PID: $BACKEND_PID) - http://localhost:5001"
        else
            echo "  Backend:  Not running (stale PID file)"
            rm -f backend.pid
        fi
    else
        echo "  Backend:  Not running"
    fi
    
    if [ -f "frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null; then
            echo "  Frontend: Running (PID: $FRONTEND_PID) - http://localhost:3000"
        else
            echo "  Frontend: Not running (stale PID file)"
            rm -f frontend.pid
        fi
    else
        echo "  Frontend: Not running"
    fi
}

# Main script logic
case "$1" in
    "start")
        start_backend
        start_frontend
        echo
        print_success "Excel Data Visualizer is running!"
        print_info "Frontend: http://localhost:3000 (should open automatically)"
        print_info "Backend:  http://localhost:5001"
        print_info "Use './run.sh stop' to stop the servers"
        ;;
    "stop")
        stop_servers
        ;;
    "restart")
        stop_servers
        sleep 2
        start_backend
        start_frontend
        ;;
    "status")
        show_status
        ;;
    *)
        echo "Excel Data Visualizer Control Script for macOS"
        echo
        echo "Usage: $0 {start|stop|restart|status}"
        echo
        echo "Commands:"
        echo "  start   - Start both backend and frontend servers"
        echo "  stop    - Stop both servers"
        echo "  restart - Restart both servers"
        echo "  status  - Show server status"
        echo
        exit 1
        ;;
esac
EOF
    
    chmod +x run.sh
    print_success "Created run.sh launcher script"
    
    # Create app bundle structure (optional)
    create_app_bundle
}

# Function to create macOS app bundle
create_app_bundle() {
    print_status "Creating macOS application bundle..."
    
    mkdir -p "Excel Visualizer.app/Contents/MacOS"
    mkdir -p "Excel Visualizer.app/Contents/Resources"
    
    # Create Info.plist
    cat > "Excel Visualizer.app/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>excel-visualizer</string>
    <key>CFBundleIdentifier</key>
    <string>com.local.excel-visualizer</string>
    <key>CFBundleName</key>
    <string>Excel Data Visualizer</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
</dict>
</plist>
EOF
    
    # Create executable
    cat > "Excel Visualizer.app/Contents/MacOS/excel-visualizer" << EOF
#!/bin/bash
cd "\$(dirname "\$0")/../../.."
./run.sh start
EOF
    
    chmod +x "Excel Visualizer.app/Contents/MacOS/excel-visualizer"
    
    print_success "Created 'Excel Visualizer.app' bundle"
    print_info "You can double-click the app bundle to start the application"
}

# Function to test installation
test_installation() {
    print_status "Testing installation..."
    
    # Test Python dependencies
    source venv/bin/activate
    python3 -c "import pandas, flask, plotly, openpyxl; print('Python dependencies OK')" || {
        print_error "Python dependencies test failed"
        return 1
    }
    
    # Test Node.js dependencies
    if [ -d "node_modules" ]; then
        print_success "Node.js dependencies installed"
    else
        print_error "Node.js dependencies missing"
        return 1
    fi
    
    print_success "Installation test passed!"
}

# Main installation flow
main() {
    echo "============================================="
    echo "    Excel Data Visualizer - macOS Setup    "
    echo "============================================="
    echo
    
    # Check macOS version
    check_macos_version
    echo
    
    # Install Xcode Command Line Tools
    install_xcode_tools
    
    # Install Homebrew
    install_homebrew
    
    # Install Python
    install_python
    
    # Install Node.js
    install_nodejs
    
    # Setup application
    setup_application
    
    # Create startup scripts
    create_startup_scripts
    
    # Test installation
    test_installation
    
    echo
    echo "============================================="
    print_success "Installation completed successfully!"
    echo "============================================="
    echo
    print_info "To start the application:"
    echo "  ./run.sh start"
    echo "  OR double-click 'Excel Visualizer.app'"
    echo
    print_info "To stop the application:"
    echo "  ./run.sh stop"
    echo
    print_info "The application will be available at:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:5001"
    echo
    print_info "The browser should open automatically when starting."
    echo
}

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    print_error "This script is for macOS only. Use install-linux.sh for Linux systems."
    exit 1
fi

# Run main installation
main "$@"