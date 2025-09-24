#!/bin/bash

# CMP Local Production Testing Script
# This script validates the production configuration without requiring Docker

set -eo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    log_info "Testing: $test_name"
    
    if eval "$test_command" 2>/dev/null; then
        log_success "✓ $test_name"
        ((TESTS_PASSED++)) || true
    else
        log_error "✗ $test_name"
        ((TESTS_FAILED++)) || true
    fi
}

# Validate environment file exists
test_env_file() {
    run_test "Environment file exists" "[[ -f '$ENV_FILE' ]]"
}

# Validate required environment variables
test_env_variables() {
    local required_vars=(
        "SECRET_KEY"
        "JWT_SECRET_KEY"
        "DATABASE_URL"
        "DB_PASSWORD"
        "POSTGRES_PASSWORD"
        "ZOHO_CLIENT_ID"
        "ZOHO_ORGANIZATION_ID"
    )
    
    for var in "${required_vars[@]}"; do
        run_test "Environment variable $var is set" "grep -q '^${var}=' '$ENV_FILE' && ! grep -q '^${var}=your_' '$ENV_FILE'"
    done
}

# Test file structure
test_file_structure() {
    local required_files=(
        "Dockerfile"
        "docker-compose.yml"
        "requirements.txt"
        "cmp/main.py"
        "cmp/auth.py"
        "cmp/db.py"
        "cmp/routers/settings.py"
        "cmp/templates/settings.html"
    )
    
    for file in "${required_files[@]}"; do
        run_test "Required file exists: $file" "[[ -f '$PROJECT_ROOT/$file' ]]"
    done
}

# Test directory structure
test_directory_structure() {
    local required_dirs=(
        "cmp"
        "cmp/agents"
        "cmp/routers"
        "cmp/templates"
        "cmp/utils"
        "local_storage"
        "logs"
        "scripts/deployment"
        ".github/workflows"
    )
    
    for dir in "${required_dirs[@]}"; do
        run_test "Required directory exists: $dir" "[[ -d '$PROJECT_ROOT/$dir' ]]"
    done
}

# Test SSL certificates
test_ssl_certificates() {
    run_test "SSL certificate exists" "[[ -f '$PROJECT_ROOT/ssl/cert.pem' ]]"
    run_test "SSL private key exists" "[[ -f '$PROJECT_ROOT/ssl/key.pem' ]]"
    
    if [[ -f "$PROJECT_ROOT/ssl/cert.pem" ]]; then
        run_test "SSL certificate is valid" "openssl x509 -in '$PROJECT_ROOT/ssl/cert.pem' -noout -text"
    fi
}

# Test Python syntax
test_python_syntax() {
    log_info "Testing Python syntax..."
    
    local python_files
    python_files=$(find "$PROJECT_ROOT/cmp" -name "*.py" 2>/dev/null || true)
    
    if [[ -n "$python_files" ]]; then
        while IFS= read -r file; do
            run_test "Python syntax: $(basename "$file")" "python -m py_compile '$file'"
        done <<< "$python_files"
    else
        log_warning "No Python files found for syntax checking"
    fi
}

# Test configuration consistency
test_configuration() {
    # Check if DEBUG is set to false for production
    run_test "DEBUG is disabled" "grep -q '^DEBUG=false' '$ENV_FILE'"
    
    # Check if ENVIRONMENT is set to production
    run_test "Environment is production" "grep -q '^ENVIRONMENT=production' '$ENV_FILE'"
    
    # Check if secure cookies are configured
    run_test "Secure session cookies configured" "grep -q '^SESSION_COOKIE_HTTPONLY=true' '$ENV_FILE'"
}

# Test deployment scripts
test_deployment_scripts() {
    local scripts=(
        "scripts/deployment/deploy.sh"
    )
    
    for script in "${scripts[@]}"; do
        run_test "Deployment script exists: $script" "[[ -f '$PROJECT_ROOT/$script' ]]"
        if [[ -f "$PROJECT_ROOT/$script" ]]; then
            run_test "Deployment script is executable: $script" "[[ -x '$PROJECT_ROOT/$script' ]]"
        fi
    done
}

# Test CI/CD configuration
test_cicd_config() {
    local cicd_files=(
        ".github/workflows/ci-cd.yml"
        ".github/workflows/dependencies.yml"
    )
    
    for file in "${cicd_files[@]}"; do
        run_test "CI/CD file exists: $file" "[[ -f '$PROJECT_ROOT/$file' ]]"
    done
}

# Test documentation
test_documentation() {
    local doc_files=(
        "README.md"
        "docs/production-deployment.md"
        ".env.example"
    )
    
    for file in "${doc_files[@]}"; do
        run_test "Documentation exists: $file" "[[ -f '$PROJECT_ROOT/$file' ]]"
    done
}

# Test Docker configuration
test_docker_config() {
    # Test Dockerfile
    if [[ -f "$PROJECT_ROOT/Dockerfile" ]]; then
        run_test "Dockerfile uses multi-stage build" "grep -qi 'FROM.*as' '$PROJECT_ROOT/Dockerfile'"
        run_test "Dockerfile uses non-root user" "grep -q 'USER cmp' '$PROJECT_ROOT/Dockerfile'"
        run_test "Dockerfile has health check" "grep -q 'HEALTHCHECK' '$PROJECT_ROOT/Dockerfile'"
    fi
    
    # Test docker-compose.yml
    if [[ -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        run_test "Docker Compose includes app service" "grep -q 'app:' '$PROJECT_ROOT/docker-compose.yml'"
        run_test "Docker Compose includes database service" "grep -qE '(db|postgres):' '$PROJECT_ROOT/docker-compose.yml'"
        run_test "Docker Compose includes Redis service" "grep -q 'redis:' '$PROJECT_ROOT/docker-compose.yml'"
    fi
}

# Generate test report
generate_report() {
    echo
    echo "=============================================="
    echo "         CMP Production Test Report"
    echo "=============================================="
    echo
    echo "Tests Passed: $TESTS_PASSED"
    echo "Tests Failed: $TESTS_FAILED"
    echo "Total Tests:  $((TESTS_PASSED + TESTS_FAILED))"
    echo
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "🎉 All tests passed! Production configuration is ready."
        echo
        echo "Next steps:"
        echo "1. Install Docker and Docker Compose"
        echo "2. Run: ./scripts/deployment/deploy.sh"
        echo "3. Or manually: docker-compose up -d"
        echo
        return 0
    else
        log_error "❌ Some tests failed. Please fix the issues before deploying."
        echo
        echo "Common fixes:"
        echo "1. Configure all required environment variables in .env"
        echo "2. Ensure all required files are present"
        echo "3. Fix any Python syntax errors"
        echo
        return 1
    fi
}

# Main function
main() {
    log_info "Starting CMP Production Configuration Tests..."
    echo
    
    cd "$PROJECT_ROOT"
    
    test_env_file
    test_env_variables
    test_file_structure
    test_directory_structure
    test_ssl_certificates
    test_python_syntax
    test_configuration
    test_deployment_scripts
    test_cicd_config
    test_documentation
    test_docker_config
    
    generate_report
}

# Run tests
main "$@"