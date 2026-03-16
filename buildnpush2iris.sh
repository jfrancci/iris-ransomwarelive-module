#!/bin/bash
#
# buildnpush2iris.sh - IRIS Ransomware.live Module Installer
# Version: 3.3.2
# Author: DFIR Team
#

set -e

MODULE_NAME="iris_ransomwarelive"
MODULE_VERSION="3.3.2"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Usage
usage() {
    cat << EOF
═══════════════════════════════════════════════════════
    buildnpush2iris.sh - Ransomware.live Module v${MODULE_VERSION}
═══════════════════════════════════════════════════════

Usage: $0 [-i IRIS_DIR] [-a] [-r] [-h]

Options:
  -i DIR    Specify IRIS installation directory
  -a        Install in app container too (besides worker)
  -r        Restart services after installation
  -h        Show this help message

Examples:
  $0                    # Install in worker only
  $0 -ar                # Install in both containers and restart
  $0 -i /custom/path    # Use custom IRIS directory

EOF
    exit 0
}

# Parse arguments
IRIS_DIR=""
INSTALL_APP=false
RESTART_SERVICES=false

while getopts "i:arh" opt; do
    case $opt in
        i) IRIS_DIR="$OPTARG" ;;
        a) INSTALL_APP=true ;;
        r) RESTART_SERVICES=true ;;
        h) usage ;;
        \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
    esac
done

# Detect docker compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    log_error "Docker Compose not found"
    exit 1
fi

log_info "Using: $DOCKER_COMPOSE"

# Auto-detect IRIS directory
if [ -z "$IRIS_DIR" ]; then
    log_info "Auto-detecting IRIS installation directory..."
    if [ -d "/opt/dfir-mesi/iris-web" ]; then
        IRIS_DIR="/opt/dfir-mesi/iris-web"
        log_info "Detected IRIS directory: $IRIS_DIR"
    elif [ -d "/opt/iris-web" ]; then
        IRIS_DIR="/opt/iris-web"
        log_info "Detected IRIS directory: $IRIS_DIR"
    elif [ -d "/opt/dfir-iris" ]; then
        IRIS_DIR="/opt/dfir-iris"
        log_info "Detected IRIS directory: $IRIS_DIR"
    else
        log_error "Could not auto-detect IRIS directory"
        log_info "Please specify with -i option"
        exit 1
    fi
fi

log_info "Using IRIS directory: $IRIS_DIR"

# Check IRIS directory exists
if [ ! -d "$IRIS_DIR" ]; then
    log_error "IRIS directory not found: $IRIS_DIR"
    exit 1
fi

# Count source lines (used later for verification)
SOURCE_LINES=$(wc -l < iris_ransomwarelive/RansomwareLiveModule.py)
log_info "Source file: ${SOURCE_LINES} lines"

# Detect Python version in container
log_info "Detecting Python version in container..."
PY_VERSION=$(docker exec iriswebapp_worker /opt/venv/bin/python --version 2>/dev/null | cut -d' ' -f2 || echo "unknown")
PY_MAJOR_MINOR_CONTAINER=$(echo "$PY_VERSION" | cut -d. -f1,2)
log_info "Container Python version: $PY_VERSION"

# Check build tools
log_info "Pre-flight: checking Python build tooling (host)..."
HOST_PY_VERSION=$(python3 --version | cut -d' ' -f2)
log_info "Host Python version: $HOST_PY_VERSION"

# Install build dependencies
log_info "Installing build dependencies via apt..."
PY_MAJOR_MINOR=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
    python3-pip \
    python3-venv \
    python3-build \
    python3-setuptools \
    python3-wheel \
    "python${PY_MAJOR_MINOR}-venv" 2>/dev/null || true

# Verify build module
if python3 -c "import build" 2>/dev/null; then
    log_success "✓ Build module available (Python package)"
elif dpkg -l | grep -q python3-build; then
    log_success "✓ Build module available (system package)"
else
    log_warn "Build module not found, installing..."
    python3 -m pip install --break-system-packages --upgrade build || true
fi

# Verify module structure
log_info "Verifying module structure..."
if [ ! -d "iris_ransomwarelive" ]; then
    log_error "iris_ransomwarelive directory not found"
    exit 1
fi

if [ ! -f "iris_ransomwarelive/__init__.py" ]; then
    log_error "iris_ransomwarelive/__init__.py not found"
    exit 1
fi

# Create pyproject.toml if missing
if [ ! -f "pyproject.toml" ]; then
    log_info "Creating pyproject.toml (build-system declaration)..."
    cat > pyproject.toml << 'EOFTOML'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
EOFTOML
fi

# Clean previous builds
log_info "Cleaning previous build artifacts..."
rm -rf build/ dist/ *.egg-info
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Create setup.py if missing
if [ ! -f "setup.py" ]; then
    log_info "Creating setup.py..."
    cat > setup.py << 'EOFSETUP'
from setuptools import setup, find_packages
import os

setup(
    name='iris_ransomwarelive',
    version='3.3.2',
    author='DFIR Team',
    author_email='neto@francci.net',
    description='DFIR-IRIS Ransomware.live Integration Module',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    packages=find_packages(),
    python_requires='>=3.8,<3.14',
    install_requires=[
        'requests>=2.28.0,<3.0.0',
        'iris-module-interface>=1.2.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Information Technology',
        'Topic :: Security',
        'Programming Language :: Python :: 3',
    ],
)
EOFSETUP
fi

# Build wheel
log_info "Building wheel package..."
python3 -m build --wheel --outdir dist 2>&1 | grep -v "WARNING" || true

if [ ! -f dist/*.whl ]; then
    log_error "Build failed - wheel not created"
    exit 1
fi

log_success "✓ Build successful"
WHEEL_FILE=$(ls dist/*.whl)
log_info "Built: $(basename $WHEEL_FILE)"

# Verify wheel contents before installing
WHEEL_LINES=$(unzip -p dist/*.whl "*/RansomwareLiveModule.py" | wc -l)
log_info "Wheel contains ${WHEEL_LINES} lines"

if [ "$WHEEL_LINES" -ne "$SOURCE_LINES" ]; then
    log_error "WHEEL MISMATCH: source=${SOURCE_LINES} lines, wheel=${WHEEL_LINES} lines"
    log_error "Build produced incomplete wheel - aborting"
    exit 1
fi

log_success "✓ Wheel verified: ${WHEEL_LINES} lines match source"

# Function to install in container
install_in_container() {
    local CONTAINER=$1
    local CONTAINER_NAME=$2
    
    log_info "Installing in $CONTAINER_NAME container..."
    
    # Get container ID
    CONTAINER_ID=$(docker ps -qf "name=$CONTAINER")
    if [ -z "$CONTAINER_ID" ]; then
        log_error "$CONTAINER_NAME container not running"
        return 1
    fi
    
    log_info "Container ID: $CONTAINER_ID"
    
    # Clean previous /tmp/module in container
    docker exec $CONTAINER_ID rm -rf /tmp/module/ 2>/dev/null || true
    
    # Copy wheel to container
    docker cp dist/ $CONTAINER_ID:/tmp/module/
    
    # Create installation script
    cat > /tmp/${MODULE_NAME}_install.sh << 'INSTALL_SCRIPT'
#!/bin/sh
set -e

MODULE_NAME="iris_ransomwarelive"

# Pick proper pip/python
PIP_BIN="/opt/venv/bin/pip"
PY_BIN="/opt/venv/bin/python"

echo "[1/8] Checking Python version..."
$PY_BIN --version

echo "[2/8] Removing previous installations..."
$PIP_BIN uninstall -y ${MODULE_NAME} >/dev/null 2>&1 || true
# Also remove site-packages directory to ensure clean slate
PY_VER=$($PY_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
rm -rf /opt/venv/lib/python${PY_VER}/site-packages/${MODULE_NAME}/ 2>/dev/null || true
rm -rf /opt/venv/lib/python${PY_VER}/site-packages/${MODULE_NAME}-*.dist-info/ 2>/dev/null || true
rm -rf /opt/venv/lib/python${PY_VER}/site-packages/${MODULE_NAME}-*.egg-info/ 2>/dev/null || true

echo "[3/8] Ensuring base tooling (setuptools/wheel)..."
$PY_BIN -m pip install --no-cache-dir --upgrade pip >/dev/null 2>&1 || true
$PY_BIN -m pip install --no-cache-dir 'setuptools>=65.0,<75.0' wheel >/dev/null 2>&1 || true

echo "[4/8] Installing requests library..."
$PY_BIN -m pip install --no-cache-dir 'requests>=2.28.0,<3.0.0'

echo "[5/8] Installing iris-module-interface..."
$PIP_BIN uninstall -y iris-module-interface >/dev/null 2>&1 || true
$PY_BIN -m pip install --no-cache-dir \
    "git+https://github.com/dfir-iris/iris-module-interface@v1.2.0"

echo "[6/8] Verifying iris-module-interface installation..."
$PY_BIN -c "import iris_interface; print('✓ iris-module-interface OK')"

echo "[7/8] Installing module wheel..."
$PY_BIN -m pip install --no-cache-dir --no-deps --force-reinstall /tmp/module/*.whl

echo "[8/8] Verifying installation..."
$PY_BIN -c "from iris_ransomwarelive.RansomwareLiveModule import RansomwareLiveModule; print('✓ Module OK')"

echo "Installation complete for container!"
INSTALL_SCRIPT
    
    # Copy install script to container
    docker cp /tmp/${MODULE_NAME}_install.sh $CONTAINER_ID:/tmp/install.sh
    
    # Execute installation
    if ! docker exec $CONTAINER_ID sh /tmp/install.sh; then
        log_error "pip installation failed in $CONTAINER_NAME"
        return 1
    fi
    
    # =========================================================
    # POST-INSTALL VERIFICATION: check line count matches source
    # =========================================================
    local PY_VER_CONTAINER
    PY_VER_CONTAINER=$(docker exec $CONTAINER_ID /opt/venv/bin/python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local INSTALLED_PATH="/opt/venv/lib/python${PY_VER_CONTAINER}/site-packages/iris_ransomwarelive/RansomwareLiveModule.py"
    
    local CONTAINER_LINES
    CONTAINER_LINES=$(docker exec $CONTAINER_ID wc -l < "$INSTALLED_PATH" 2>/dev/null || echo "0")
    
    log_info "Verification: source=${SOURCE_LINES} lines, container=${CONTAINER_LINES} lines"
    
    if [ "$CONTAINER_LINES" -ne "$SOURCE_LINES" ]; then
        log_warn "LINE MISMATCH detected! pip installed truncated file (${CONTAINER_LINES} vs ${SOURCE_LINES})"
        log_info "Applying docker cp fallback..."
        
        # Direct copy bypassing pip
        docker cp iris_ransomwarelive/RansomwareLiveModule.py $CONTAINER_ID:"$INSTALLED_PATH"
        docker exec $CONTAINER_ID rm -rf "$(dirname $INSTALLED_PATH)/__pycache__" 2>/dev/null || true
        
        # Re-verify
        CONTAINER_LINES=$(docker exec $CONTAINER_ID wc -l < "$INSTALLED_PATH" 2>/dev/null || echo "0")
        
        if [ "$CONTAINER_LINES" -ne "$SOURCE_LINES" ]; then
            log_error "docker cp fallback also failed! (${CONTAINER_LINES} vs ${SOURCE_LINES})"
            return 1
        fi
        
        log_success "✓ docker cp fallback successful (${CONTAINER_LINES} lines)"
    else
        log_success "✓ $CONTAINER_NAME installation verified (${CONTAINER_LINES} lines)"
    fi
    
    # Clean __pycache__
    docker exec $CONTAINER_ID find /opt/venv/lib/ -path "*/iris_ransomwarelive/__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    return 0
}

# Install in worker (always)
if ! install_in_container "iriswebapp_worker" "worker"; then
    log_error "Worker installation failed - this is required"
    exit 1
fi

# Install in app (if -a flag)
if [ "$INSTALL_APP" = true ]; then
    if ! install_in_container "iriswebapp_app" "app"; then
        log_warn "App installation failed - module may not appear in UI"
    fi
fi

# Restart services if requested
if [ "$RESTART_SERVICES" = true ]; then
    log_info "Restarting IRIS services..."
    cd "$IRIS_DIR"
    $DOCKER_COMPOSE restart worker
    if [ "$INSTALL_APP" = true ]; then
        $DOCKER_COMPOSE restart app
    fi
    log_success "✓ Services restarted"
else
    log_warn "Services not restarted. Use -r flag or restart manually:"
    echo "  cd $IRIS_DIR && $DOCKER_COMPOSE restart worker"
fi

# Quick verification
log_info "Performing quick verification..."
if docker exec iriswebapp_worker /opt/venv/bin/pip show iris_ransomwarelive >/dev/null 2>&1; then
    VERSION=$(docker exec iriswebapp_worker /opt/venv/bin/pip show iris_ransomwarelive | grep Version | cut -d' ' -f2)
    log_success "✓ Module installed: v$VERSION"
else
    log_error "Module verification failed"
    exit 1
fi

# Success message
cat << 'EOFSUCCESS'

═══════════════════════════════════════════════════════
              Installation Completed!                   
═══════════════════════════════════════════════════════

Next steps:

1. Open IRIS web interface
   https://your-iris-server

2. Navigate to modules
   Advanced → Modules → Add Module → and type: iris_ransomwarelive

3. Configure the module (optional)
   • API URL: https://api-pro.ransomware.live
   • Timeout: 30 seconds

To test the module:

1. Create a new case with ransomware_group custom field (Summary → Manage → Ransomware Group)

2. And add an IOC of type 'ransomware-group' with value:
   lockbit

3. Click: Processors → iris_ransomwarelive::on_manual_trigger_case

Troubleshooting:

• Check module logs:
  docker logs iriswebapp_worker --tail 50 | grep '[RL]'

• Verify module status:
  docker exec iriswebapp_worker /opt/venv/bin/pip show iris_ransomwarelive

• If module doesn't appear, restart worker:
  cd /opt/dfir-mesi/iris-web && docker compose restart worker

EOFSUCCESS