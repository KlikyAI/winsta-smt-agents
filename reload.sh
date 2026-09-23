#!/bin/bash

# ==============================================================================
# 🔄 WINSTA SMT - Quick Reload Script
# ==============================================================================
# This script is for quick reloads of the docker-compose stack.
#
# Usage:
#   ./reload.sh           # interactive: confirm restart
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

NETWORK_NAME="winsta_smt_network"

# Function to prompt with timeout
prompt_with_timeout() {
    local prompt_message=$1
    local default_choice=$2
    local timeout=$3
    local user_input

    read -t "$timeout" -p "$prompt_message" user_input || user_input="$default_choice"
    echo "$user_input"
}

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  🔄 WINSTA SMT - Quick Reload${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if network exists, create if not
if ! docker network inspect "$NETWORK_NAME" &> /dev/null; then
    echo -e "${YELLOW}Creating Docker network: $NETWORK_NAME${NC}"
    docker network create --driver bridge "$NETWORK_NAME"
fi

# Ask for no-cache build
choice=$(prompt_with_timeout "Build with --no-cache? (y/N) [auto-skip in 5s]: " "n" 5)
echo ""

if [[ "$choice" =~ ^[Yy]([Ee][Ss])?$ ]]; then
    echo -e "${BLUE}🔧 Building stack with --no-cache...${NC}"
    docker compose build --no-cache
else
    echo -e "${YELLOW}⏭ Skipping no-cache build...${NC}"
fi

echo ""
restart_choice=$(prompt_with_timeout "Restart stack now? (Y/n) [auto-yes in 10s, then tail api logs]: " "y" 10)
restart_choice="${restart_choice:-y}"
echo ""

if [[ "$restart_choice" =~ ^[Nn]([Oo])?$ ]]; then
    echo -e "${YELLOW}⏭ Restart skipped. No containers were stopped or started.${NC}"
    echo -e "${BLUE}When ready:${NC}"
    echo -e "  docker compose up -d"
    echo ""
    exit 0
fi

# Bring down existing containers
echo -e "${BLUE}📦 Stopping containers...${NC}"
docker compose down --remove-orphans

# Start containers
echo -e "${BLUE}🚀 Starting containers...${NC}"
docker compose up -d

# Quick health check
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  📊 Container Status${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

docker compose ps

echo ""
echo -e "${GREEN}✅ Reload complete!${NC}"
echo ""
echo -e "${YELLOW}Quick commands:${NC}"
echo -e "  docker compose logs -f api      - Main API logs only"
echo -e "  docker compose logs -f          - All services"
echo ""

# Auto-tail main API logs after restart (compose service name: api)
echo -e "${BLUE}📜 API logs (service: api, last 150 lines, then follow — Ctrl+C to exit)${NC}"
echo ""
sleep 2
docker compose logs -f --tail=150 api || {
    echo -e "${YELLOW}⚠️  Could not stream api logs. Try: docker compose logs api${NC}"
}
