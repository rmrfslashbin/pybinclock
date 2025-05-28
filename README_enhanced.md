# PyBinClock - Binary Clock Display for Unicorn HAT Mini

A Python-based binary clock display for the Pimoroni Unicorn HAT Mini. Features configurable colors, multiple display modes, and systemd integration for automatic startup.

## Table of Contents

- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Color Themes](#color-themes)
- [Development](#development)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

## Features

- **Binary Time Display**: Shows current time in binary format across 6 rows:
  - Year (11 bits)
  - Month (4 bits)
  - Day (5 bits)
  - Hour (5 bits, 24-hour format)
  - Minute (6 bits)
  - Second (6 bits)
- **Configurable Colors**: Customize LED colors via JSON configuration
- **Multiple Display Modes**: Binary clock or scrolling text
- **Button Support**: Control pause, mode switching, and exit (optional)
- **Systemd Integration**: Runs as a service on boot
- **Error Handling**: Graceful degradation and recovery
- **Mock Hardware**: Development/testing without physical hardware

## Hardware Requirements

- Raspberry Pi (any model with GPIO)
- Pimoroni Unicorn HAT Mini (17x7 LED matrix)
- Python 3.8+
- GPIO access (user must be in `gpio`, `spi`, and `i2c` groups)

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/pybinclock.git
cd pybinclock

# Run the setup script (do not use sudo)
./setup.sh
```

The setup script will:
- Install the application to `/usr/local/lib/pybinclock`
- Create executable scripts in `/usr/local/bin`
- Set up a systemd service for automatic startup
- Configure proper permissions

### Manual Service Control

```bash
# Start the service
sudo systemctl start pybinclock

# Stop the service
sudo systemctl stop pybinclock

# Check service status
sudo systemctl status pybinclock

# View logs
sudo journalctl -u pybinclock -f

# Disable automatic startup
sudo systemctl disable pybinclock
```

## Configuration

PyBinClock uses JSON configuration files to customize display settings and colors.

### Configuration File Locations

The application searches for configuration in this order:
1. `~/.config/pybinclock/config.json` (user config)
2. `/etc/pybinclock/config.json` (system config)
3. Built-in defaults

### Creating a Configuration

```bash
# Create user config directory
mkdir -p ~/.config/pybinclock

# Generate a sample configuration
cd /path/to/pybinclock
uv run python -c "from pybinclock.config import Config; Config().create_sample_config('~/.config/pybinclock/config.json')"
```

### Configuration Options

```json
{
  "display": {
    "rotation": 180,          // Display rotation: 0, 90, 180, 270
    "brightness": 0.1,        // LED brightness: 0.0-1.0
    "refresh_rate": 1.0       // Update frequency in seconds
  },
  "colors": {
    "on_color": [255, 0, 0],  // RGB for "on" bits (red)
    "off_color": [0, 0, 0],   // RGB for "off" bits (black)
    "status_okay": [0, 255, 0],
    "status_error": [255, 0, 0],
    "status_warn": [255, 255, 0],
    "status_info": [0, 0, 255]
  },
  "buttons": {
    "button_a_pin": 5,        // GPIO pin numbers
    "button_b_pin": 6,
    "button_x_pin": 16,
    "button_y_pin": 24,
    "debounce_time": 0.3
  },
  "font_path": "/usr/local/lib/pybinclock/5x7.ttf",
  "log_level": "INFO",        // DEBUG, INFO, WARNING, ERROR
  "enable_buttons": true      // Enable/disable button support
}
```

## Usage

### Reading the Binary Clock

The display shows 6 rows of binary data:

```
Row 0: Year   [11 bits] 2024 = 11111101000
Row 1: Month  [4 bits]  May = 0101  
Row 2: Day    [5 bits]  28 = 11100
Row 3: Hour   [5 bits]  13 = 01101
Row 4: Minute [6 bits]  45 = 101101
Row 5: Second [6 bits]  30 = 011110
```

LEDs are displayed in little-endian format (least significant bit on the right).

### Button Controls (if enabled)

- **Button A**: Pause/Resume clock updates
- **Button B**: Toggle between binary clock and scrolling text mode
- **Button X**: Exit the application
- **Button Y**: (Reserved for future use)

### Console Testing

```bash
# Test the binary clock in console mode
pybinclock-test

# Run with specific configuration
cd /path/to/pybinclock
uv run python -c "from pybinclock.BinClockLEDs import BinClockLEDs; BinClockLEDs('/path/to/config.json')"
```

## Color Themes

Several pre-made color themes are included in the `themes/` directory:

### Blue Theme
```json
{
  "colors": {
    "on_color": [0, 100, 255],
    "off_color": [0, 0, 20]
  }
}
```

### Green/Matrix Theme
```json
{
  "colors": {
    "on_color": [0, 255, 0],
    "off_color": [0, 20, 0]
  }
}
```

### Amber/Retro Theme
```json
{
  "colors": {
    "on_color": [255, 140, 0],
    "off_color": [20, 10, 0]
  }
}
```

### Purple/Cyberpunk Theme
```json
{
  "colors": {
    "on_color": [147, 0, 211],
    "off_color": [20, 0, 30]
  }
}
```

To use a theme:
```bash
cp themes/blue_theme.json ~/.config/pybinclock/config.json
sudo systemctl restart pybinclock
```

## Development

### Setting Up Development Environment

```bash
# Install development dependencies
make install-dev

# Run tests
make test

# Run linting
make lint

# Format code
make format

# Run type checking
make type-check
```

### Project Structure

```
pybinclock/
├── pybinclock/                  # Main package
│   ├── PyBinClock.py           # Core time/binary conversion
│   ├── BinClockLEDs.py         # LED controller with buttons
│   ├── BinClockLEDs_nobuttons.py # Simplified LED controller
│   ├── BinClockLEDs_improved.py  # Enhanced controller with config
│   └── config.py               # Configuration management
├── tests/                      # Unit tests
├── themes/                     # Color theme examples
├── setup.sh                    # Installation script
├── uninstall.sh               # Uninstallation script
└── Makefile                   # Development tasks
```

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test file
uv run pytest tests/test_led_controllers.py -v

# Run with coverage report
uv run pytest --cov=pybinclock --cov-report=html
```

## API Reference

### CurrentTime Class

Manages current time and binary representations.

```python
from pybinclock.PyBinClock import CurrentTime

ct = CurrentTime()
ct.update()  # Update to current time

# Access binary representations
ct.binary['year']    # List of 11 bits
ct.binary['month']   # List of 4 bits
ct.binary['day']     # List of 5 bits
ct.binary['hour']    # List of 5 bits
ct.binary['minute']  # List of 6 bits
ct.binary['second']  # List of 6 bits
```

### Config Class

Manages application configuration with defaults and file loading.

```python
from pybinclock.config import Config

# Load configuration
config = Config.load("/path/to/config.json")

# Access settings
config.display.brightness
config.colors.on_color
config.enable_buttons

# Create sample config
config.create_sample_config("sample.json")
```

### LEDController Classes

Three implementations available:

1. **LEDController** - Full featured with button support
2. **LEDControllerNoButtons** - Simplified for service mode
3. **LEDController (improved)** - Enhanced with configuration support

```python
# No buttons version (for service)
from pybinclock.BinClockLEDs_nobuttons import LEDControllerNoButtons

with LEDControllerNoButtons(rotation=180, brightness=0.1) as leds:
    leds.field[row][col] = [r, g, b]  # Set pixel
    leds.draw()  # Update display
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Add user to required groups
   sudo usermod -a -G gpio,spi,i2c $USER
   # Log out and back in for changes to take effect
   ```

2. **Service Won't Start**
   ```bash
   # Check logs for errors
   sudo journalctl -u pybinclock -n 50
   
   # Verify installation
   ls -la /usr/local/lib/pybinclock
   ls -la /usr/local/bin/pybinclock
   ```

3. **LEDs Not Lighting Up**
   - Check HAT is properly connected
   - Verify SPI is enabled: `sudo raspi-config` > Interface Options > SPI
   - Test with Pimoroni examples first

4. **Wrong Colors/Brightness**
   - Check configuration file syntax
   - Ensure RGB values are 0-255
   - Brightness should be 0.0-1.0

### Debug Mode

Enable debug logging in your config:
```json
{
  "log_level": "DEBUG"
}
```

Then check logs:
```bash
sudo journalctl -u pybinclock -f
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Pimoroni for the Unicorn HAT Mini hardware and libraries
- Contributors and testers from the Raspberry Pi community