# PyBinClock - Enhanced Binary Clock for Raspberry Pi

Binary clock for Raspberry Pi with Unicorn Mini HAT, now with improved error handling, configuration support, and comprehensive testing.

## Features

- 🕐 Binary time display (year, month, day, hour, minute, second)
- 🎨 Customizable color schemes via configuration
- 🔧 Robust error handling and graceful shutdown
- ⚙️ Configuration file support
- 🧪 Comprehensive unit tests
- 📝 Type hints and documentation
- 🔍 Linting and code formatting tools
- 🚀 Optimized LED update performance
- 🎮 Button controls (pause, mode toggle, exit)
- 📜 Scrolling text mode

## What's New

### Improvements Made

1. **Configuration System**: Full configuration support with JSON files
2. **Enhanced Error Handling**: Graceful handling of hardware failures
3. **Type Safety**: Complete type annotations throughout
4. **Testing**: Comprehensive unit test suite
5. **Code Quality**: Black formatting, flake8 linting, mypy type checking
6. **Performance**: Optimized LED updates (only changed pixels)
7. **Documentation**: Detailed docstrings and improved README
8. **Installation**: Fixed hardcoded paths in setup script

## Installation

### Prerequisites

- Raspberry Pi with [Unicorn Mini HAT](https://shop.pimoroni.com/products/unicorn-hat-mini)
- Python 3.9 or higher
- uv package manager

### Quick Install

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/rmrfslashbin/pybinclock.git
cd pybinclock
./setup.sh
```

### Development Setup

```bash
# Install with development dependencies
make install-dev

# Or manually
uv sync --dev
pre-commit install
```

## Configuration

PyBinClock now supports configuration files for customization.

### Create a Sample Config

```bash
python -c "from pybinclock.config import Config; Config().create_sample_config('~/.config/pybinclock/config.json')"
```

### Configuration Options

```json
{
  "display": {
    "rotation": 180,
    "brightness": 0.1,
    "refresh_rate": 1.0
  },
  "colors": {
    "on_color": [255, 0, 0],
    "off_color": [0, 0, 0],
    "status_okay": [0, 255, 0],
    "status_error": [255, 0, 0]
  },
  "buttons": {
    "button_a_pin": 5,
    "button_b_pin": 6,
    "button_x_pin": 16,
    "debounce_time": 0.3
  },
  "log_level": "INFO",
  "enable_buttons": true
}
```

## Usage

### Running the Clock

```bash
# Start the service
sudo systemctl start pybinclock

# Run manually with default config
pybinclock

# Run with custom config
pybinclock --config ~/.config/pybinclock/config.json

# Test mode (console output)
pybinclock-test
```

### Button Controls

- **Button A**: Pause/Resume the clock
- **Button B**: Toggle between binary and scrolling text mode
- **Button X**: Graceful exit
- **Button Y**: (Reserved for future use)

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
uv run pytest --cov=pybinclock --cov-report=html

# Run specific test
uv run pytest tests/test_config.py
```

### Code Quality

```bash
# Format code
make format

# Run linter
make lint

# Type checking
make type-check

# Run all checks
make all
```

### Project Structure

```
pybinclock/
├── pybinclock/
│   ├── __init__.py
│   ├── PyBinClock.py          # Core time conversion logic
│   ├── BinClockLEDs.py        # Original LED display
│   ├── BinClockLEDs_improved.py # Enhanced LED display
│   ├── BinClockLEDs_nobuttons.py # Service mode display
│   └── config.py              # Configuration management
├── tests/
│   ├── test_current_time.py   # Time conversion tests
│   ├── test_config.py         # Configuration tests
│   └── test_pybinclock.py     # Basic tests
├── setup.sh                   # Installation script
├── uninstall.sh              # Uninstallation script
├── Makefile                  # Development tasks
├── pyproject.toml            # Project configuration
├── .flake8                   # Linting configuration
└── .pre-commit-config.yaml   # Pre-commit hooks
```

## API Documentation

### CurrentTime Class

```python
from pybinclock.PyBinClock import CurrentTime

# Create instance
ct = CurrentTime()

# Update time
ct.update()

# Access binary representations
print(ct.binary['hour'])    # [0, 1, 1, 0, 0] for 12:00
print(ct.binary['minute'])  # [0, 1, 1, 1, 1, 0] for 30 minutes
```

### Configuration

```python
from pybinclock.config import Config

# Load default config
config = Config.load()

# Load custom config
config = Config.load("/path/to/config.json")

# Modify settings
config.display.brightness = 0.5
config.colors.on_color = [0, 255, 0]  # Green

# Save config
config.save("/path/to/config.json")
```

## Troubleshooting

### Hardware Not Found

If you see "Hardware libraries not available", ensure:
1. You're running on a Raspberry Pi
2. The Unicorn HAT Mini is properly connected
3. Required libraries are installed: `uv sync`

### Permission Errors

The service needs GPIO access:
```bash
# Add user to gpio group
sudo usermod -a -G gpio,spi,i2c $USER

# Logout and login again
```

### Service Issues

```bash
# Check service status
sudo systemctl status pybinclock

# View logs
sudo journalctl -u pybinclock -f

# Restart service
sudo systemctl restart pybinclock
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests and quality checks: `make all`
4. Commit your changes
5. Push to your fork
6. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Original author: Robert Sigler
- Unicorn HAT Mini by Pimoroni
- Built with love for the Raspberry Pi community