#!/bin/bash

# Cloudflare GeoTracker Pro - Termux Startup Script
# This script automates the complete setup and deployment

echo ""
echo "========================================"
echo "  🚀 Cloudflare GeoTracker Pro"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python not found. Installing...${NC}"
    pkg install python -y
fi

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo -e "${RED}❌ pip not found. Installing...${NC}"
    pkg install python-pip -y
fi

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}⚠️ cloudflared not found. Installing...${NC}"
    echo -e "${BLUE}Downloading cloudflared for Android ARM64...${NC}"
    
    # Download cloudflared for Termux (ARM64)
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -O cloudflared
    
    if [ $? -eq 0 ]; then
        chmod +x cloudflared
        mv cloudflared $PREFIX/bin/
        echo -e "${GREEN}✅ cloudflared installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to download cloudflared${NC}"
        echo -e "${YELLOW}Please install manually from: https://github.com/cloudflare/cloudflared/releases${NC}"
        exit 1
    fi
fi

# Start Flask app in background
echo -e "${BLUE}🌐 Starting Flask server...${NC}"
python app.py > flask.log 2>&1 &
FLASK_PID=$!

# Wait for Flask to start
sleep 3

# Check if Flask is running
if ps -p $FLASK_PID > /dev/null; then
    echo -e "${GREEN}✅ Flask server started (PID: $FLASK_PID)${NC}"
else
    echo -e "${RED}❌ Failed to start Flask server${NC}"
    cat flask.log
    exit 1
fi

# Start cloudflared tunnel
echo -e "${BLUE}🌍 Starting Cloudflare Tunnel...${NC}"
echo ""
cloudflared tunnel --url http://localhost:5000

# Cleanup on exit
trap "kill $FLASK_PID; echo '\nShutting down...'; exit" INT TERM

wait