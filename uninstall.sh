#!/bin/bash

# PyBinClock Uninstallation Script
# Removes the application from /usr/local and systemd service

set -e

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run as root. The script will use sudo when needed."
    exit 1
fi

# Installation paths
INSTALL_PREFIX="/usr/local"
APP_DIR="$INSTALL_PREFIX/lib/pybinclock"
BIN_DIR="$INSTALL_PREFIX/bin"
SERVICE_FILE="/etc/systemd/system/pybinclock.service"

echo "Uninstalling PyBinClock..."

# Stop and disable service
if systemctl is-enabled pybinclock.service &>/dev/null; then
    echo "Disabling pybinclock service..."
    sudo systemctl stop pybinclock.service
    sudo systemctl disable pybinclock.service
fi

# Remove service file
if [ -f "$SERVICE_FILE" ]; then
    echo "Removing systemd service file..."
    sudo rm "$SERVICE_FILE"
    sudo systemctl daemon-reload
fi

# Remove executables
echo "Removing executable scripts..."
sudo rm -f "$BIN_DIR/pybinclock"
sudo rm -f "$BIN_DIR/pybinclock-test"

# Remove application directory
if [ -d "$APP_DIR" ]; then
    echo "Removing application directory..."
    sudo rm -rf "$APP_DIR"
fi

echo ""
echo "PyBinClock uninstalled successfully!"
echo ""
echo "Note: This script does not remove uv or Python dependencies"
echo "that may be used by other applications."