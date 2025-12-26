#!/bin/bash
#
# Seed Demo Data for SoSoft Neighborhood Issue Tracker
#
# Usage:
#   ./scripts/seed.sh              # Basic seeding (300 tickets)
#   ./scripts/seed.sh --clear      # Clear existing data and re-seed
#   ./scripts/seed.sh --tickets 500  # Custom ticket count
#   ./scripts/seed.sh --clear --tickets 200  # Both options
#
# This script runs the seed_all.py script inside the Docker container.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CONTAINER_NAME="sosoft-staging-backend"
CLEAR_FLAG=""
TICKETS_FLAG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clear)
            CLEAR_FLAG="--clear"
            shift
            ;;
        --tickets)
            TICKETS_FLAG="--tickets $2"
            shift 2
            ;;
        --container)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --clear           Clear existing demo data before seeding"
            echo "  --tickets N       Number of tickets to create (default: 300)"
            echo "  --container NAME  Docker container name (default: sosoft-staging-backend)"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                      # Basic seeding with 300 tickets"
            echo "  $0 --clear              # Clear and re-seed"
            echo "  $0 --tickets 500        # Create 500 tickets"
            echo "  $0 --clear --tickets 200"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  SoSoft Demo Data Seeding${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if container exists and is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}Container '${CONTAINER_NAME}' is not running.${NC}"
    echo ""
    echo "Available containers:"
    docker ps --format '  - {{.Names}}'
    echo ""
    echo -e "Try one of these:"
    echo "  1. Start the containers: docker compose up -d"
    echo "  2. Specify a different container: $0 --container <name>"
    exit 1
fi

echo -e "${GREEN}Found container: ${CONTAINER_NAME}${NC}"
echo ""

# Build the command
CMD="python -m app.scripts.seed_all"
if [ -n "$CLEAR_FLAG" ]; then
    CMD="$CMD $CLEAR_FLAG"
    echo -e "${YELLOW}Mode: Clear existing data and re-seed${NC}"
else
    echo -e "${GREEN}Mode: Append new data${NC}"
fi

if [ -n "$TICKETS_FLAG" ]; then
    CMD="$CMD $TICKETS_FLAG"
    echo -e "${GREEN}Tickets: ${TICKETS_FLAG#--tickets }${NC}"
else
    echo -e "${GREEN}Tickets: 300 (default)${NC}"
fi

echo ""
echo -e "${BLUE}Running seed script...${NC}"
echo ""

# Run the seed script
docker exec -it "$CONTAINER_NAME" $CMD

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Seeding Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Default login credentials:"
echo -e "  ${BLUE}Manager:${NC}  manager@sosoft.com / manager123!"
echo -e "  ${BLUE}Support:${NC}  support@sosoft.com / support123!"
echo -e "  ${BLUE}Citizen:${NC}  citizen@sosoft.com / citizen123!"
echo ""
