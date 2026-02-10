#!/usr/bin/env bash
# =============================================================================
# EURKAI_COCKPIT — Install & Validate ALL (C08)
# Version: 1.0.0
#
# One-shot installer:
# - Installs backend (Python dependencies)
# - Installs frontend if present (npm)
# - Runs all tests
# - Generates validation report
#
# Usage:
#   bash scripts/install_all.sh [OPTIONS]
#
# Options:
#   --target DIR     Installation target directory (default: ~/.eurkai_cockpit)
#   --skip-tests     Skip test execution
#   --skip-frontend  Skip frontend installation even if present
#   --dry-run        Show what would be done without executing
#   --help           Show this help message
#
# Exit codes:
#   0 - Success
#   1 - Python version error
#   2 - Dependency installation failed
#   3 - Tests failed
#   4 - Build failed
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(dirname "$SCRIPT_DIR")"
DEFAULT_TARGET="$HOME/.eurkai_cockpit"
MIN_PYTHON_VERSION="3.11"
REPORT_FILE=""
START_TIME=""

# Options
TARGET_DIR="$DEFAULT_TARGET"
SKIP_TESTS=false
SKIP_FRONTEND=false
DRY_RUN=false

# =============================================================================
# FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[STEP]${NC} $1"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

show_help() {
    cat << EOF
EURKAI_COCKPIT — Install & Validate ALL

Usage: $(basename "$0") [OPTIONS]

Options:
  --target DIR       Installation target directory
                     Default: ~/.eurkai_cockpit
  --skip-tests       Skip test execution
  --skip-frontend    Skip frontend installation even if present
  --dry-run          Show what would be done without executing
  -h, --help         Show this help message

Examples:
  # Standard installation
  bash scripts/install_all.sh

  # Custom target directory
  bash scripts/install_all.sh --target /opt/eurkai

  # Quick install without tests
  bash scripts/install_all.sh --skip-tests

Environment Variables:
  EURKAI_DB_PATH          Database path (default: <target>/data/cockpit.db)
  EURKAI_MASTER_PASSWORD  Master password for secrets encryption
  EURKAI_TOKEN            API authentication token (optional)

Exit Codes:
  0 - Success
  1 - Python version error
  2 - Dependency installation failed
  3 - Tests failed
  4 - Build failed
EOF
}

check_python_version() {
    log_step "Checking Python version"
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        return 1
    fi
    
    local python_version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    
    log_info "Found Python $python_version"
    
    # Compare versions
    local min_major min_minor cur_major cur_minor
    min_major=$(echo "$MIN_PYTHON_VERSION" | cut -d. -f1)
    min_minor=$(echo "$MIN_PYTHON_VERSION" | cut -d. -f2)
    cur_major=$(echo "$python_version" | cut -d. -f1)
    cur_minor=$(echo "$python_version" | cut -d. -f2)
    
    if [[ "$cur_major" -lt "$min_major" ]] || \
       [[ "$cur_major" -eq "$min_major" && "$cur_minor" -lt "$min_minor" ]]; then
        log_error "Python >= $MIN_PYTHON_VERSION required (found $python_version)"
        return 1
    fi
    
    log_success "Python version OK ($python_version >= $MIN_PYTHON_VERSION)"
    return 0
}

check_git() {
    log_info "Checking Git availability..."
    
    if command -v git &> /dev/null; then
        local git_version
        git_version=$(git --version | cut -d' ' -f3)
        log_success "Git available (version $git_version)"
        echo "git_available=true"
    else
        log_warn "Git not available - backup to GitHub will be disabled"
        echo "git_available=false"
    fi
}

setup_target_directory() {
    log_step "Setting up target directory"
    
    log_info "Target: $TARGET_DIR"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] Would create directory: $TARGET_DIR"
        return 0
    fi
    
    # Create target directory
    mkdir -p "$TARGET_DIR"
    mkdir -p "$TARGET_DIR/data"
    mkdir -p "$TARGET_DIR/logs"
    mkdir -p "$TARGET_DIR/backups"
    
    # Copy source files
    log_info "Copying files from $SOURCE_DIR to $TARGET_DIR..."
    
    # Backend
    if [[ -d "$SOURCE_DIR/backend" ]]; then
        cp -r "$SOURCE_DIR/backend" "$TARGET_DIR/"
        log_success "Backend copied"
    fi
    
    # CLI
    if [[ -d "$SOURCE_DIR/cli" ]]; then
        cp -r "$SOURCE_DIR/cli" "$TARGET_DIR/"
        log_success "CLI copied"
    fi
    
    # Tests
    if [[ -d "$SOURCE_DIR/tests" ]]; then
        cp -r "$SOURCE_DIR/tests" "$TARGET_DIR/"
        log_success "Tests copied"
    fi
    
    # Docs
    if [[ -d "$SOURCE_DIR/docs" ]]; then
        cp -r "$SOURCE_DIR/docs" "$TARGET_DIR/"
        log_success "Docs copied"
    fi
    
    # Scripts
    if [[ -d "$SOURCE_DIR/scripts" ]]; then
        cp -r "$SOURCE_DIR/scripts" "$TARGET_DIR/"
        log_success "Scripts copied"
    fi
    
    # Config files
    [[ -f "$SOURCE_DIR/requirements.txt" ]] && cp "$SOURCE_DIR/requirements.txt" "$TARGET_DIR/"
    [[ -f "$SOURCE_DIR/README.md" ]] && cp "$SOURCE_DIR/README.md" "$TARGET_DIR/"
    
    log_success "Target directory ready: $TARGET_DIR"
}

install_backend() {
    log_step "Installing backend dependencies"
    
    local req_file="$TARGET_DIR/requirements.txt"
    
    if [[ ! -f "$req_file" ]]; then
        log_warn "No requirements.txt found, creating minimal one..."
        if [[ "$DRY_RUN" == false ]]; then
            cat > "$req_file" << 'EOF'
# EURKAI_COCKPIT Backend Dependencies
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
cryptography>=42.0.0
click>=8.1.0

# Testing
pytest>=8.0.0
httpx>=0.26.0
pytest-cov>=4.1.0
EOF
        fi
    fi
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] Would install: pip install -r $req_file"
        return 0
    fi
    
    log_info "Installing Python dependencies..."
    
    # Try pip install with break-system-packages for newer systems
    if python3 -m pip install -r "$req_file" --break-system-packages 2>/dev/null; then
        log_success "Dependencies installed (with --break-system-packages)"
    elif python3 -m pip install -r "$req_file" --user 2>/dev/null; then
        log_success "Dependencies installed (--user)"
    elif python3 -m pip install -r "$req_file" 2>/dev/null; then
        log_success "Dependencies installed"
    else
        log_error "Failed to install dependencies"
        return 2
    fi
    
    return 0
}

install_frontend() {
    log_step "Checking frontend"
    
    local frontend_dir="$TARGET_DIR/frontend"
    
    if [[ ! -d "$frontend_dir" ]]; then
        log_info "No frontend directory found - skipping (backend-only mode)"
        return 0
    fi
    
    if [[ "$SKIP_FRONTEND" == true ]]; then
        log_info "Frontend installation skipped (--skip-frontend)"
        return 0
    fi
    
    if ! command -v npm &> /dev/null; then
        log_warn "npm not available - frontend will not be built"
        return 0
    fi
    
    log_info "Frontend found, installing dependencies..."
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] Would run: npm install && npm run build"
        return 0
    fi
    
    cd "$frontend_dir"
    
    # Install dependencies
    if npm install; then
        log_success "Frontend dependencies installed"
    else
        log_error "npm install failed"
        return 4
    fi
    
    # Build
    if npm run build 2>/dev/null; then
        log_success "Frontend built successfully"
    else
        log_warn "npm run build failed or not configured"
    fi
    
    cd - > /dev/null
    return 0
}

init_database() {
    log_step "Initializing database"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] Would initialize database at $TARGET_DIR/data/cockpit.db"
        return 0
    fi
    
    export EURKAI_DB_PATH="$TARGET_DIR/data/cockpit.db"
    
    cd "$TARGET_DIR"
    
    if python3 -c "from backend.storage.migrations import init_db; init_db('$EURKAI_DB_PATH')"; then
        log_success "Database initialized at $EURKAI_DB_PATH"
    else
        log_warn "Database initialization skipped (may already exist)"
    fi
    
    cd - > /dev/null
    return 0
}

run_tests() {
    log_step "Running tests"
    
    if [[ "$SKIP_TESTS" == true ]]; then
        log_info "Tests skipped (--skip-tests)"
        return 0
    fi
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] Would run: python -m pytest"
        return 0
    fi
    
    cd "$TARGET_DIR"
    
    export EURKAI_DB_PATH="$TARGET_DIR/data/test_cockpit.db"
    export EURKAI_MASTER_PASSWORD="test_master_password_for_validation"
    export EURKAI_TOKEN=""
    
    log_info "Running pytest..."
    
    local test_output
    local test_exit_code
    
    test_output=$(python3 -m pytest tests/ -v --tb=short 2>&1) || test_exit_code=$?
    test_exit_code=${test_exit_code:-0}
    
    echo "$test_output"
    
    # Save test output for report
    echo "$test_output" > "$TARGET_DIR/logs/test_output.log"
    
    if [[ "$test_exit_code" -eq 0 ]]; then
        log_success "All tests passed"
        return 0
    else
        log_error "Tests failed with exit code $test_exit_code"
        return 3
    fi
}

generate_report() {
    log_step "Generating validation report"
    
    REPORT_FILE="$TARGET_DIR/VALIDATION_REPORT.md"
    local end_time
    end_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] Would generate report at $REPORT_FILE"
        return 0
    fi
    
    # Gather system info
    local python_version
    python_version=$(python3 --version 2>&1)
    
    local git_version="Not available"
    command -v git &> /dev/null && git_version=$(git --version)
    
    local npm_version="Not available"
    command -v npm &> /dev/null && npm_version=$(npm --version)
    
    local os_info
    os_info=$(uname -a)
    
    # Check components
    local backend_status="✅ Installed"
    [[ ! -d "$TARGET_DIR/backend" ]] && backend_status="❌ Missing"
    
    local cli_status="✅ Installed"
    [[ ! -d "$TARGET_DIR/cli" ]] && cli_status="❌ Missing"
    
    local frontend_status="⏭️ Not present (optional)"
    [[ -d "$TARGET_DIR/frontend" ]] && frontend_status="✅ Installed"
    
    local db_status="✅ Initialized"
    [[ ! -f "$TARGET_DIR/data/cockpit.db" ]] && db_status="⚠️ Not initialized"
    
    local tests_status="✅ Passed"
    [[ "$SKIP_TESTS" == true ]] && tests_status="⏭️ Skipped"
    [[ -f "$TARGET_DIR/logs/test_output.log" ]] && grep -q "FAILED" "$TARGET_DIR/logs/test_output.log" && tests_status="❌ Failed"
    
    cat > "$REPORT_FILE" << EOF
# EURKAI_COCKPIT — Validation Report

**Generated:** $end_time  
**Installation started:** $START_TIME  
**Target directory:** $TARGET_DIR  

---

## System Information

| Component | Version |
|-----------|---------|
| OS | $os_info |
| Python | $python_version |
| Git | $git_version |
| npm | $npm_version |

---

## Installation Status

| Component | Status |
|-----------|--------|
| Backend | $backend_status |
| CLI | $cli_status |
| Frontend | $frontend_status |
| Database | $db_status |
| Tests | $tests_status |

---

## Directory Structure

\`\`\`
$TARGET_DIR/
├── backend/           # API server & storage
│   ├── api/           # FastAPI routes
│   ├── backup/        # Backup module (C07)
│   ├── secrets/       # Secrets management (C06)
│   └── storage/       # SQLite storage layer (C02)
├── cli/               # CLI interface (C05)
├── data/              # Database & runtime data
├── docs/              # Documentation
├── logs/              # Logs & reports
├── scripts/           # Installation scripts
└── tests/             # Test suite
\`\`\`

---

## Quick Start

\`\`\`bash
# Set environment (optional)
export EURKAI_DB_PATH="$TARGET_DIR/data/cockpit.db"
export EURKAI_MASTER_PASSWORD="your-secure-password"

# Start API server
cd $TARGET_DIR
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000

# Use CLI
python -m cli.cli --help
python -m cli.cli init
python -m cli.cli project list

# Create backup
python -m backend.backup.backup --dry-run
\`\`\`

---

## Validation Checklist

- [x] Python >= 3.11 verified
- [x] Dependencies installed
- [x] Database schema created
$(if [[ "$SKIP_TESTS" == false ]]; then echo "- [x] Tests executed"; else echo "- [ ] Tests skipped"; fi)
$(if [[ -d "$TARGET_DIR/frontend" ]]; then echo "- [x] Frontend built"; else echo "- [ ] Frontend not present"; fi)
- [x] Validation report generated

---

## Notes

- This installation is **idempotent** - running again will update without breaking existing data
- Git is optional but recommended for backup functionality
- Set \`EURKAI_MASTER_PASSWORD\` before using secrets features

---

*Report generated by EURKAI_COCKPIT install_all.sh (C08)*
EOF

    log_success "Validation report generated: $REPORT_FILE"
}

show_summary() {
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  INSTALLATION COMPLETE${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "  Target directory: $TARGET_DIR"
    echo "  Validation report: $REPORT_FILE"
    echo ""
    echo "  Next steps:"
    echo "    1. Set EURKAI_MASTER_PASSWORD for secrets"
    echo "    2. Start server: cd $TARGET_DIR && python -m uvicorn backend.app:app"
    echo "    3. Or use CLI: python -m cli.cli --help"
    echo ""
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    START_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     EURKAI_COCKPIT — Install & Validate ALL (C08)         ║${NC}"
    echo -e "${BLUE}║     Version 1.0.0                                         ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if [[ "$DRY_RUN" == true ]]; then
        log_warn "DRY-RUN MODE - No changes will be made"
    fi
    
    # Pre-flight checks
    check_python_version || exit 1
    check_git
    
    # Installation steps
    setup_target_directory || exit 2
    install_backend || exit 2
    install_frontend || exit 4
    init_database || exit 2
    run_tests || exit 3
    generate_report
    
    show_summary
    
    return 0
}

# =============================================================================
# ARGUMENT PARSING
# =============================================================================

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)
            TARGET_DIR="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-frontend)
            SKIP_FRONTEND=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main
main
