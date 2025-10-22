#!/bin/bash

# Excel Data Visualizer - Virtual Environment Setup Script
# Supports Linux and macOS with Python 3.11+ requirement

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

# Function to get Python version
get_python_version() {
    local python_cmd="$1"
    if command_exists "$python_cmd"; then
        $python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0"
    else
        echo "0.0"
    fi
}

# Function to compare version numbers
version_ge() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# Function to find suitable Python version
find_python() {
    local python_candidates=("python3.12" "python3.11" "python3" "python")
    local min_version="3.11"
    
    for python_cmd in "${python_candidates[@]}"; do
        if command_exists "$python_cmd"; then
            local version=$(get_python_version "$python_cmd")
            if version_ge "$version" "$min_version"; then
                echo "$python_cmd"
                return 0
            fi
        fi
    done
    
    return 1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Function to install Python on different systems
install_python() {
    local os=$(detect_os)
    
    print_status "Attempting to install Python 3.11..."
    
    case $os in
        "linux")
            if command_exists apt; then
                print_status "Installing Python 3.11 via apt..."
                sudo apt update
                sudo apt install -y python3.11 python3.11-pip python3.11-venv python3.11-dev
            elif command_exists dnf; then
                print_status "Installing Python 3.11 via dnf..."
                sudo dnf install -y python3.11 python3.11-pip python3.11-devel
            elif command_exists yum; then
                print_status "Installing Python 3.11 via yum..."
                sudo yum install -y python3.11 python3.11-pip python3.11-devel
            elif command_exists pacman; then
                print_status "Installing Python 3.11 via pacman..."
                sudo pacman -S python311 python-pip
            else
                print_error "No supported package manager found. Please install Python 3.11+ manually."
                return 1
            fi
            ;;
        "macos")
            if command_exists brew; then
                print_status "Installing Python 3.11 via Homebrew..."
                brew install python@3.11
            else
                print_error "Homebrew not found. Please install Homebrew first:"
                echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
                return 1
            fi
            ;;
        *)
            print_error "Unsupported operating system. Please install Python 3.11+ manually."
            return 1
            ;;
    esac
}

# Function to install Node.js
install_nodejs() {
    local os=$(detect_os)
    
    print_status "Attempting to install Node.js..."
    
    case $os in
        "linux")
            if command_exists apt; then
                print_status "Installing Node.js via apt..."
                sudo apt install -y nodejs npm
            elif command_exists dnf; then
                print_status "Installing Node.js via dnf..."
                sudo dnf install -y nodejs npm
            elif command_exists yum; then
                print_status "Installing Node.js via yum..."
                sudo yum install -y nodejs npm
            elif command_exists pacman; then
                print_status "Installing Node.js via pacman..."
                sudo pacman -S nodejs npm
            fi
            ;;
        "macos")
            if command_exists brew; then
                print_status "Installing Node.js via Homebrew..."
                brew install node
            fi
            ;;
    esac
}

# Main setup function
main() {
    print_status "Excel Data Visualizer - Virtual Environment Setup"
    print_status "=================================================="
    
    # Check if we're in the right directory
    if [[ ! -f "requirements.txt" ]]; then
        print_error "requirements.txt not found. Please run this script from the project root directory."
        exit 1
    fi
    
    # Find suitable Python version
    print_status "Checking for Python 3.11+..."
    PYTHON_CMD=$(find_python)
    
    if [[ $? -ne 0 ]]; then
        print_warning "Python 3.11+ not found. Attempting to install..."
        install_python
        
        # Try to find Python again
        PYTHON_CMD=$(find_python)
        if [[ $? -ne 0 ]]; then
            print_error "Failed to install or find Python 3.11+. Please install manually."
            exit 1
        fi
    fi
    
    local python_version=$(get_python_version "$PYTHON_CMD")
    print_success "Found Python $python_version at: $(which $PYTHON_CMD)"
    
    # Check Node.js
    print_status "Checking for Node.js..."
    if ! command_exists node; then
        print_warning "Node.js not found. Attempting to install..."
        install_nodejs
        
        if ! command_exists node; then
            print_error "Failed to install Node.js. Please install manually from https://nodejs.org/"
            exit 1
        fi
    fi
    
    local node_version=$(node --version)
    print_success "Found Node.js $node_version"
    
    # Remove existing virtual environment if it exists
    if [[ -d "venv" ]]; then
        print_warning "Existing virtual environment found. Removing..."
        rm -rf venv
    fi
    
    # Create virtual environment
    print_status "Creating virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv venv
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    python -m pip install --upgrade pip
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Install Node.js dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    # Create run script
    print_status "Creating run script..."
    cat > run.sh << 'EOF'
#!/bin/bash

# Excel Data Visualizer - Run Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to start the application
start_app() {
    print_status "Starting Excel Data Visualizer..."
    
    # Check if virtual environment exists
    if [[ ! -d "venv" ]]; then
        print_error "Virtual environment not found. Please run setup-venv.sh first."
        exit 1
    fi
    
    # Check for port conflicts
    if port_in_use 3000; then
        print_error "Port 3000 is already in use. Please stop the conflicting service."
        exit 1
    fi
    
    if port_in_use 5001; then
        print_error "Port 5001 is already in use. Please stop the conflicting service."
        exit 1
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start backend in background
    print_status "Starting backend server on port 5001..."
    cd backend
    python app.py &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    cd ..
    
    # Wait a moment for backend to start
    sleep 3
    
    # Start frontend
    print_status "Starting frontend server on port 3000..."
    npm start &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > frontend.pid
    
    # Wait a moment for frontend to start
    sleep 5
    
    print_success "Application started successfully!"
    print_status "Frontend: http://localhost:3000"
    print_status "Backend:  http://localhost:5001"
    print_status ""
    print_status "To stop the application, run: ./run.sh stop"
    
    # Open browser (optional)
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:3000 >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then
        open http://localhost:3000 >/dev/null 2>&1 &
    fi
}

# Function to stop the application
stop_app() {
    print_status "Stopping Excel Data Visualizer..."
    
    # Stop backend
    if [[ -f "backend.pid" ]]; then
        BACKEND_PID=$(cat backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            print_status "Backend stopped (PID: $BACKEND_PID)"
        fi
        rm -f backend.pid
    fi
    
    # Stop frontend
    if [[ -f "frontend.pid" ]]; then
        FRONTEND_PID=$(cat frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            print_status "Frontend stopped (PID: $FRONTEND_PID)"
        fi
        rm -f frontend.pid
    fi
    
    # Kill any remaining processes
    pkill -f "python.*app.py" 2>/dev/null || true
    pkill -f "npm.*start" 2>/dev/null || true
    
    print_success "Application stopped successfully!"
}

# Function to check status
status_app() {
    print_status "Checking application status..."
    
    local backend_running=false
    local frontend_running=false
    
    if [[ -f "backend.pid" ]]; then
        BACKEND_PID=$(cat backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            print_success "Backend is running (PID: $BACKEND_PID)"
            backend_running=true
        else
            print_error "Backend is not running (stale PID file)"
            rm -f backend.pid
        fi
    else
        print_error "Backend is not running"
    fi
    
    if [[ -f "frontend.pid" ]]; then
        FRONTEND_PID=$(cat frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            print_success "Frontend is running (PID: $FRONTEND_PID)"
            frontend_running=true
        else
            print_error "Frontend is not running (stale PID file)"
            rm -f frontend.pid
        fi
    else
        print_error "Frontend is not running"
    fi
    
    if $backend_running && $frontend_running; then
        print_success "Application is fully operational!"
        print_status "Frontend: http://localhost:3000"
        print_status "Backend:  http://localhost:5001"
    fi
}

# Function to restart the application
restart_app() {
    print_status "Restarting Excel Data Visualizer..."
    stop_app
    sleep 2
    start_app
}

# Main script logic
case "${1:-start}" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        status_app
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the application (default)"
        echo "  stop    - Stop the application"
        echo "  restart - Restart the application"
        echo "  status  - Check application status"
        exit 1
        ;;
esac
EOF
    
    chmod +x run.sh
    
    print_success "Setup completed successfully!"
    print_status ""
    print_status "Next steps:"
    print_status "1. Start the application: ./run.sh start"
    print_status "2. Open your browser to: http://localhost:3000"
    print_status "3. Upload test_data.xlsx to try the application"
    print_status ""
    print_status "Other commands:"
    print_status "- Stop:    ./run.sh stop"
    print_status "- Restart: ./run.sh restart"
    print_status "- Status:  ./run.sh status"
}

# Run main function
main "$@"
