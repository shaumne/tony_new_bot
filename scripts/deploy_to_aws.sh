#!/bin/bash
# AWS EC2 deployment script for the trading bot

# Exit on error
set -e

# Configuration
EC2_USER="ubuntu"
EC2_HOST="your-ec2-instance-public-dns"
EC2_KEY_PATH="~/.ssh/your-key.pem"
REPO_URL="https://github.com/yourusername/bitget-trading-bot.git"
REMOTE_DIR="/home/ubuntu/bitget-trading-bot"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deploying trading bot to AWS EC2...${NC}"

# Upload .env file if it exists
if [ -f .env ]; then
    echo -e "${GREEN}Uploading .env file...${NC}"
    scp -i "$EC2_KEY_PATH" .env "$EC2_USER@$EC2_HOST:/tmp/.env"
else
    echo -e "${RED}Warning: No .env file found!${NC}"
    echo -e "${RED}Please create one on the server or ensure it's in the current directory.${NC}"
fi

# Connect to EC2 instance and run setup
echo -e "${GREEN}Connecting to EC2 instance and setting up...${NC}"
ssh -i "$EC2_KEY_PATH" "$EC2_USER@$EC2_HOST" << EOF
    # Update system
    echo "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    
    # Install dependencies
    echo "Installing dependencies..."
    sudo apt install -y python3-pip git
    
    # Clone or update repository
    if [ -d "$REMOTE_DIR" ]; then
        echo "Updating existing repository..."
        cd "$REMOTE_DIR"
        git pull
    else
        echo "Cloning repository..."
        git clone "$REPO_URL" "$REMOTE_DIR"
        cd "$REMOTE_DIR"
    fi
    
    # Install Python dependencies
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
    
    # Move .env file if uploaded
    if [ -f /tmp/.env ]; then
        echo "Moving .env file to project directory..."
        mv /tmp/.env "$REMOTE_DIR/.env"
    fi
    
    # Create logs directory if it doesn't exist
    echo "Creating logs directory..."
    mkdir -p "$REMOTE_DIR/logs"
    
    # Create systemd service file
    echo "Creating systemd service file..."
    cat << EOT | sudo tee /etc/systemd/system/trading-bot.service
[Unit]
Description=Trading Bot Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$REMOTE_DIR
ExecStart=/usr/bin/python3 -m src.main --mode live
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOT
    
    # Reload systemd, enable and restart service
    echo "Configuring and starting service..."
    sudo systemctl daemon-reload
    sudo systemctl enable trading-bot
    sudo systemctl restart trading-bot
    
    # Check status
    echo "Service status:"
    sudo systemctl status trading-bot --no-pager
EOF

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}To check the logs, run:${NC}"
echo -e "ssh -i $EC2_KEY_PATH $EC2_USER@$EC2_HOST 'sudo journalctl -u trading-bot -f'" 