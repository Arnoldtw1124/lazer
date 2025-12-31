#!/bin/bash
# Auto-deployment script for LaserCraft

echo "Starting deployment..."

# 1. Pull latest code
echo "Pulls latest code from Git..."
git pull

# 2. Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# 3. Initialize DB (optional, explicit)
# python3 -c "from app import db; db.create_all()"

# 4. Restart Service
echo "Restarting Service..."
sudo systemctl restart lasercraft

echo "Deployment Complete! 🚀"
