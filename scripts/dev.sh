#!/usr/bin/env bash
#
# Development environment startup script for Neighborhood Issue Tracker
# Starts all services via Docker Compose
#
# Usage: ./scripts/dev.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Cleanup handler - calls stop.sh
cleanup() {
    echo ""
    log_info "Caught interrupt signal, stopping services..."
    "$PROJECT_ROOT/scripts/stop.sh"
    exit 0
}

# Wait for a service to be ready
wait_for_service() {
    local service_name=$1
    local max_attempts=30
    local attempt=0
    
    log_info "Waiting for $service_name to be ready..."
    # Temporarily disable exit on error for this function
    set +e
    while [ $attempt -lt $max_attempts ]; do
        if docker compose ps "$service_name" 2>/dev/null | grep -q "running\|Up"; then
            # Check if service is healthy (for services with healthchecks)
            local health=$(docker compose ps "$service_name" --format json 2>/dev/null | grep -o '"Health":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "")
            if [ -z "$health" ] || [ "$health" = "healthy" ]; then
                set -e
                log_success "$service_name is ready!"
                return 0
            fi
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    set -e
    log_error "$service_name failed to start within expected time"
    return 1
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    # Temporarily disable exit on error for this function
    set +e
    if docker exec sosoft-backend python -m alembic upgrade head 2>/dev/null; then
        log_success "Database migrations completed!"
    else
        # Check if it's just because migrations are already applied
        if docker exec sosoft-backend python -m alembic current 2>/dev/null | grep -q "head\|alembic_version"; then
            log_info "Database migrations already up to date"
        else
            log_error "Migration failed - check logs if this is your first setup"
        fi
    fi
    set -e
}

# Seed database with initial data
seed_database() {
    log_info "Seeding database with default categories and users..."
    # Temporarily disable exit on error for this function
    set +e
    if docker exec sosoft-backend python -m app.scripts.seed 2>/dev/null; then
        log_success "Database seeding completed!"
    else
        # Seed script handles duplicates gracefully, so any error is likely OK
        log_info "Database may already be seeded or seed script encountered an issue"
    fi
    set -e
}

# Setup first-time tasks
setup_first_time() {
    log_info "Setting up first-time tasks..."
    
    # Wait for backend to be ready
    if ! wait_for_service backend; then
        log_error "Backend service is not ready, skipping first-time setup"
        return 1
    fi
    
    # Wait a bit more for database connection to be established
    sleep 3
    
    # Run migrations
    run_migrations
    
    # Seed database
    seed_database
    
    echo ""
}

# Main
main() {
    check_docker
    
    # Set trap for Ctrl+C to trigger stop.sh
    trap cleanup SIGINT SIGTERM
    
    echo ""
    echo "=========================================="
    echo "  Neighborhood Issue Tracker - Dev Mode"
    echo "=========================================="
    echo ""
    
    log_info "Starting all services (development mode - no build)..."
    docker compose up -d
    
    log_success "All services started!"
    echo ""
    
    # Run first-time setup (migrations and seeding)
    setup_first_time
    
    echo ""
    echo "  Frontend:     http://localhost:3000"
    echo "  Backend API:  http://localhost:8000"
    echo "  API Docs:     http://localhost:8000/docs"
    echo "  MinIO:        http://localhost:9001 (minioadmin/minioadmin)"
    echo ""
    log_info "Staff login credentials:"
    echo "    Manager:  manager@sosoft.com / manager123!"
    echo "    Support:  support@sosoft.com / support123!"
    echo ""
    echo "Press Ctrl+C to stop all services"
    echo ""
    
    # Follow logs (keeps the script running and allows Ctrl+C to work)
    docker compose logs -f
}

main "$@"
