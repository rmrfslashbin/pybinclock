#!/bin/bash

# Script to install PyBinClock as a systemd daemon

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run as root. Run as the user who will run the daemon."
    exit 1
fi

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "Installing PyBinClock daemon..."

# Copy service file to systemd directory
sudo cp "$PROJECT_DIR/pybinclock.service" /etc/systemd/system/

# Update the service file with correct paths
USER=$(whoami)
HOME_DIR=$(eval echo ~$USER)

sudo sed -i "s|User=pi|User=$USER|g" /etc/systemd/system/pybinclock.service
sudo sed -i "s|Group=pi|Group=$USER|g" /etc/systemd/system/pybinclock.service
sudo sed -i "s|/home/pi/pybinclock|$PROJECT_DIR|g" /etc/systemd/system/pybinclock.service

# Reload systemd
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable pybinclock.service

echo "PyBinClock daemon installed successfully!"
echo ""
echo "To start the daemon now: sudo systemctl start pybinclock"
echo "To check status: sudo systemctl status pybinclock"
echo "To view logs: sudo journalctl -u pybinclock -f"
echo "To stop the daemon: sudo systemctl stop pybinclock"
echo "To disable auto-start: sudo systemctl disable pybinclock"