#!/bin/bash

# Configuration
APP_DIR="/opt/lasercraft"
REPO_URL="YOUR_REPO_URL_HERE" # Optional: If using git

echo "Starting deployment..."

# 1. Update system and install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git

# 2. Setup Application Directory
if [ ! -d "$APP_DIR" ]; then
    echo "Creating directory $APP_DIR..."
    sudo mkdir -p $APP_DIR
fi

# 3. Copy files (Assumes you upload files to current dir or use git)
# For this script, we assume you are running it from the uploaded folder
echo "Copying files to $APP_DIR..."
sudo cp -r ./* $APP_DIR/

# 4. Setup Virtual Environment
cd $APP_DIR
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 5. Install Python Dependencies
echo "Installing requirements..."
source venv/bin/activate
pip install -r requirements.txt

# 6. Setup Systemd Service
echo "Configuring Systemd Service..."
sudo cp lasercraft.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lasercraft
sudo systemctl restart lasercraft

echo "Deployment Complete! Service status:"
sudo systemctl status lasercraft --no-pager
