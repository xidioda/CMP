#!/bin/bash

# CMP Production Deployment Script
# This script sets up and deploys the CMP application in production

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error ".env file not found. Please copy .env.example to .env and configure it."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Validate environment configuration
validate_environment() {
    log_info "Validating environment configuration..."
    
    # Check required environment variables
    local required_vars=(
        "SECRET_KEY"
        "JWT_SECRET_KEY"
        "DATABASE_URL"
        "DB_PASSWORD"
        "POSTGRES_PASSWORD"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE" || grep -q "^${var}=your_" "$ENV_FILE"; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing or unconfigured environment variables:"
        printf '%s\n' "${missing_vars[@]}" | sed 's/^/  - /'
        log_error "Please configure these variables in $ENV_FILE"
        exit 1
    fi
    
    log_success "Environment configuration validated"
}

# Setup SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    local ssl_dir="$PROJECT_ROOT/ssl"
    mkdir -p "$ssl_dir"
    
    # Check if SSL certificates exist
    if [[ ! -f "$ssl_dir/cert.pem" ]] || [[ ! -f "$ssl_dir/key.pem" ]]; then
        log_warning "SSL certificates not found. Generating self-signed certificates for development..."
        
        openssl req -x509 -newkey rsa:4096 -keyout "$ssl_dir/key.pem" -out "$ssl_dir/cert.pem" -days 365 -nodes \
            -subj "/C=AE/ST=Dubai/L=Dubai/O=CMP/OU=IT/CN=localhost"
        
        log_warning "Self-signed certificates generated. Replace with proper certificates for production."
    else
        log_success "SSL certificates found"
    fi
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    local dirs=(
        "$PROJECT_ROOT/local_storage/bank_statements"
        "$PROJECT_ROOT/local_storage/invoices"
        "$PROJECT_ROOT/local_storage/ml_models"
        "$PROJECT_ROOT/logs"
        "$PROJECT_ROOT/backups"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        log_info "Created directory: $dir"
    done
    
    # Set proper permissions
    chmod 755 "$PROJECT_ROOT/local_storage"
    chmod 750 "$PROJECT_ROOT/logs"
    chmod 700 "$PROJECT_ROOT/backups"
    
    log_success "Directories created with proper permissions"
}

# Build and start services
deploy_services() {
    log_info "Building and starting services..."
    
    cd "$PROJECT_ROOT"
    
    # Pull latest images
    docker-compose pull
    
    # Build the application image
    docker-compose build --no-cache
    
    # Start services
    docker-compose up -d
    
    log_success "Services started"
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if docker-compose ps | grep -q "healthy"; then
            log_success "Services are healthy"
            return 0
        fi
        
        ((attempt++))
        log_info "Attempt $attempt/$max_attempts - waiting for services..."
        sleep 10
    done
    
    log_error "Services failed to become healthy within timeout"
    docker-compose logs
    exit 1
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    docker-compose exec -T app python -c "
from cmp.db import init_db
init_db()
print('Database initialized successfully')
"
    
    log_success "Database migrations completed"
}

# Perform health checks
health_check() {
    log_info "Performing health checks..."
    
    # Check if application is responding
    local app_url="http://localhost:8000/health"
    local max_attempts=10
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f -s "$app_url" > /dev/null; then
            log_success "Application health check passed"
            break
        fi
        
        ((attempt++))
        log_info "Health check attempt $attempt/$max_attempts"
        sleep 5
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        log_error "Application health check failed"
        exit 1
    fi
    
    # Check database connectivity
    docker-compose exec -T db pg_isready -U cmp_user -d cmp_prod
    log_success "Database connectivity check passed"
    
    # Check Redis connectivity
    docker-compose exec -T redis redis-cli ping
    log_success "Redis connectivity check passed"
}

# Setup monitoring (if enabled)
setup_monitoring() {
    if grep -q "PROMETHEUS_ENABLED=true" "$ENV_FILE"; then
        log_info "Setting up monitoring..."
        
        # Start monitoring services
        docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
        
        log_success "Monitoring services started"
    fi
}

# Create backup
create_backup() {
    log_info "Creating initial backup..."
    
    local backup_dir="$PROJECT_ROOT/backups"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$backup_dir/backup_$timestamp.sql"
    
    docker-compose exec -T db pg_dump -U cmp_user cmp_prod > "$backup_file"
    
    log_success "Backup created: $backup_file"
}

# Main deployment function
main() {
    log_info "Starting CMP production deployment..."
    
    check_root
    check_prerequisites
    validate_environment
    setup_ssl
    create_directories
    deploy_services
    wait_for_services
    run_migrations
    health_check
    setup_monitoring
    create_backup
    
    log_success "🎉 CMP deployment completed successfully!"
    log_info "Application is running at: http://localhost:8000"
    log_info "To view logs: docker-compose logs -f"
    log_info "To stop services: docker-compose down"
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"