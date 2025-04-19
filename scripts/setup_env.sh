#!/bin/bash
# Setup script for local development environment

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up development environment for trading bot...${NC}"

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed! Please install Python 3 and try again.${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Python version $PYTHON_VERSION is not supported. Please use Python $REQUIRED_VERSION or higher.${NC}"
    exit 1
fi

echo -e "${GREEN}Python $PYTHON_VERSION detected.${NC}"

# Create virtual environment
echo -e "${GREEN}Creating virtual environment...${NC}"
python3 -m venv venv

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
echo -e "${GREEN}Creating logs directory...${NC}"
mkdir -p logs

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${GREEN}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${RED}Please edit the .env file with your API keys and configuration.${NC}"
else
    echo -e "${GREEN}.env file already exists.${NC}"
fi

echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}To activate the virtual environment in the future, run:${NC}"
echo -e "source venv/bin/activate"
echo -e "${GREEN}To run the trading bot, run:${NC}"
echo -e "python -m src.main --mode live"
echo -e "${GREEN}To run backtesting, run:${NC}"
echo -e "python -m src.main --mode backtest" 