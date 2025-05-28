#!/bin/bash

# PyBinClock Installation Script
# Installs the application to /usr/local and sets up systemd service

set -e

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run as root. The script will use sudo when needed."
    exit 1
fi

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Installation paths
INSTALL_PREFIX="/usr/local"
APP_DIR="$INSTALL_PREFIX/lib/pybinclock"
BIN_DIR="$INSTALL_PREFIX/bin"
SERVICE_FILE="/etc/systemd/system/pybinclock.service"

echo "Installing PyBinClock to $INSTALL_PREFIX..."

# Create application directory
sudo mkdir -p "$APP_DIR"

# Copy Python package
sudo cp -r "$SCRIPT_DIR/pybinclock" "$APP_DIR/"
sudo cp "$SCRIPT_DIR/pyproject.toml" "$APP_DIR/"
sudo cp "$SCRIPT_DIR/uv.lock" "$APP_DIR/"
sudo cp "$SCRIPT_DIR/5x7.ttf" "$APP_DIR/"

# Install Python dependencies using uv
echo "Installing Python dependencies..."
cd "$APP_DIR"
# Try to find uv in common locations
UV_PATH=""
if command -v uv &> /dev/null; then
    UV_PATH=$(command -v uv)
elif [ -f "$HOME/.local/bin/uv" ]; then
    UV_PATH="$HOME/.local/bin/uv"
elif [ -f "/usr/local/bin/uv" ]; then
    UV_PATH="/usr/local/bin/uv"
else
    echo "Error: uv not found. Please install uv first: https://github.com/astral-sh/uv"
    exit 1
fi
echo "Using uv at: $UV_PATH"
sudo "$UV_PATH" sync --frozen

# Create wrapper scripts in /usr/local/bin
echo "Creating executable scripts..."
sudo tee "$BIN_DIR/pybinclock" > /dev/null << EOF
#!/bin/bash
cd /usr/local/lib/pybinclock
# Check for config file in standard locations
CONFIG_PATH=""
if [ -f "\$HOME/.config/pybinclock/config.json" ]; then
    CONFIG_PATH="\$HOME/.config/pybinclock/config.json"
elif [ -f "/etc/pybinclock/config.json" ]; then
    CONFIG_PATH="/etc/pybinclock/config.json"
fi

if [ -n "\$CONFIG_PATH" ]; then
    exec "$UV_PATH" run python -c "from pybinclock.BinClockLEDs_nobuttons import BinClockLEDs; BinClockLEDs('\$CONFIG_PATH')"
else
    exec "$UV_PATH" run python -c 'from pybinclock.BinClockLEDs_nobuttons import BinClockLEDs; BinClockLEDs()'
fi
EOF

sudo tee "$BIN_DIR/pybinclock-test" > /dev/null << EOF
#!/bin/bash
cd /usr/local/lib/pybinclock
exec "$UV_PATH" run python -c 'from pybinclock.PyBinClock import PyBinClock; PyBinClock()'
EOF

# Make scripts executable
sudo chmod +x "$BIN_DIR/pybinclock"
sudo chmod +x "$BIN_DIR/pybinclock-test"

# Create systemd service file
echo "Creating systemd service..."
sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=PyBinClock Binary Clock Display
After=network.target
Wants=network.target

[Service]
Type=simple
User=$(whoami)
Group=$(whoami)
SupplementaryGroups=gpio spi i2c
WorkingDirectory=$APP_DIR
Environment=PATH=/usr/bin:/bin:/usr/local/bin
Environment=GPIOZERO_PIN_FACTORY=lgpio
ExecStart=$BIN_DIR/pybinclock
Restart=always
RestartSec=5
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
EOF

# Set proper ownership
sudo chown -R root:root "$APP_DIR"
sudo chmod -R 755 "$APP_DIR"
# But keep the virtual environment owned by the user
sudo chown -R $(whoami):$(whoami) "$APP_DIR/.venv"

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable pybinclock.service

echo ""
echo "PyBinClock installed successfully!"
echo ""
echo "Installation paths:"
echo "  Application: $APP_DIR"
echo "  Executables: $BIN_DIR/pybinclock, $BIN_DIR/pybinclock-test"
echo "  Service: $SERVICE_FILE"
echo ""
echo "Usage:"
echo "  Start service: sudo systemctl start pybinclock"
echo "  Stop service:  sudo systemctl stop pybinclock"
echo "  Status:        sudo systemctl status pybinclock"
echo "  Logs:          sudo journalctl -u pybinclock -f"
echo "  Test manually: pybinclock-test"
echo ""
echo "The service will start automatically on boot."