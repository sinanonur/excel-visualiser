#!/bin/bash

# Excel Data Visualizer - Linux Installation Script
# This script installs all dependencies and sets up the application on Linux

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

# Function to detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        DISTRO=$ID
    elif [ -f /etc/redhat-release ]; then
        OS="Red Hat"
        DISTRO="rhel"
    elif [ -f /etc/debian_version ]; then
        OS="Debian"
        DISTRO="debian"
    else
        OS=$(uname -s)
        DISTRO="unknown"
    fi
}

# Function to install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    case "$DISTRO" in
        "ubuntu"|"debian"|"pop"|"mint")
            sudo apt update
            sudo apt install -y curl wget gnupg2 software-properties-common build-essential
            ;;
        "fedora"|"centos"|"rhel")
            if command_exists dnf; then
                sudo dnf install -y curl wget gnupg2 gcc gcc-c++ make
            else
                sudo yum install -y curl wget gnupg2 gcc gcc-c++ make
            fi
            ;;
        "arch"|"manjaro")
            sudo pacman -Sy curl wget gnupg base-devel --noconfirm
            ;;
        "opensuse"|"sles")
            sudo zypper install -y curl wget gnupg2 gcc gcc-c++ make
            ;;
        *)
            print_warning "Unknown distribution. You may need to install curl, wget, and build tools manually."
            ;;
    esac
}

# Function to install Python
install_python() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_status "Python3 found: $PYTHON_VERSION"
        
        # Check if version is 3.7+
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
            print_success "Python version is compatible (3.7+, tested up to 3.12)"
        else
            print_error "Python 3.7+ is required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_status "Installing Python 3..."
        case "$DISTRO" in
            "ubuntu"|"debian"|"pop"|"mint")
                sudo apt install -y python3 python3-pip python3-venv
                ;;
            "fedora"|"centos"|"rhel")
                if command_exists dnf; then
                    sudo dnf install -y python3 python3-pip python3-virtualenv
                else
                    sudo yum install -y python3 python3-pip
                fi
                ;;
            "arch"|"manjaro")
                sudo pacman -S python python-pip python-virtualenv --noconfirm
                ;;
            "opensuse"|"sles")
                sudo zypper install -y python3 python3-pip python3-virtualenv
                ;;
            *)
                print_error "Please install Python 3.7+ manually for your distribution"
                exit 1
                ;;
        esac
    fi
    
    # Install/upgrade pip
    if ! command_exists pip3; then
        print_status "Installing pip3..."
        curl -sS https://bootstrap.pypa.io/get-pip.py | python3
    fi
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
        fi
    else
        print_status "Installing Node.js and npm..."
        
        # Install NodeSource repository and Node.js
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        
        case "$DISTRO" in
            "ubuntu"|"debian"|"pop"|"mint")
                sudo apt install -y nodejs
                ;;
            "fedora"|"centos"|"rhel")
                curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
                if command_exists dnf; then
                    sudo dnf install -y nodejs npm
                else
                    sudo yum install -y nodejs npm
                fi
                ;;
            "arch"|"manjaro")
                sudo pacman -S nodejs npm --noconfirm
                ;;
            "opensuse"|"sles")
                sudo zypper install -y nodejs14 npm14
                ;;
            *)
                print_warning "Installing Node.js via NodeSource..."
                curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
                sudo apt install -y nodejs || {
                    print_error "Failed to install Node.js. Please install manually."
                    exit 1
                }
                ;;
        esac
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
    
    # Create run.sh script
    cat > run.sh << 'EOF'
#!/bin/bash

# Excel Data Visualizer Launcher Script

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

# Function to start backend
start_backend() {
    print_info "Starting backend server..."
    cd "$(dirname "$0")"
    
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Please run install-linux.sh first."
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
        print_error "Node modules not found. Please run install-linux.sh first."
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
        print_info "Frontend: http://localhost:3000"
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
        echo "Excel Data Visualizer Control Script"
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
    echo "    Excel Data Visualizer - Linux Setup    "
    echo "============================================="
    echo
    
    # Detect system
    detect_distro
    print_status "Detected OS: $OS ($DISTRO)"
    echo
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        print_error "Please do not run this script as root"
        exit 1
    fi
    
    # Install system dependencies
    install_system_deps
    
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
    echo
    print_info "To stop the application:"
    echo "  ./run.sh stop"
    echo
    print_info "The application will be available at:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:5001"
    echo
}

# Run main installation
main "$@"