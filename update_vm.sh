#!/bin/bash

# Configuration
APP_DIR="/opt/lasercraft"

echo "Updating application from Git..."

# 1. Pull latest changes
cd $APP_DIR
sudo git pull

# 2. Update dependencies (in case requirements.txt changed)
source venv/bin/activate
pip install -r requirements.txt

# 3. Restart Service
echo "Restarting service..."
sudo systemctl restart lasercraft

echo "Update Complete!"
sudo systemctl status lasercraft --no-pager
