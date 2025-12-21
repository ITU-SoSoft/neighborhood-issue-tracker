#!/usr/bin/env bash
#
# Stop all development services for Neighborhood Issue Tracker
#
# Usage: ./scripts/stop.sh

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

main() {
    echo ""
    log_info "Stopping all development services..."
    
    # Stop and remove all containers, networks, images, and orphans
    docker compose down --remove-orphans --rmi local
    
    log_success "All services stopped"
    echo ""
}

main "$@"
