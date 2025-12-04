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
    echo "  Frontend:     http://localhost:3000"
    echo "  Backend API:  http://localhost:8000"
    echo "  API Docs:     http://localhost:8000/docs"
    echo "  MinIO:        http://localhost:9001 (minioadmin/minioadmin)"
    echo ""
    echo "Press Ctrl+C to stop all services"
    echo ""
    
    # Follow logs (keeps the script running and allows Ctrl+C to work)
    docker compose logs -f
}

main "$@"
