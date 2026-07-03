# PyBinClock — Binary Clock for Unicorn HAT Mini

A Python binary clock for the Pimoroni [Unicorn HAT Mini](https://shop.pimoroni.com/products/unicorn-hat-mini)
on a Raspberry Pi. It displays the local date and time (24-hour) as a binary
LED matrix, with configurable colors, optional button controls, a
scrolling-text mode, and systemd integration for automatic startup.

## Why?

Everyone needs a hobby, and coding random things is mine — a nice distraction
from daily stress. And binary clocks are just cool.

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

- **Binary time display** across 6 rows (top to bottom):
  - Year (11 bits)
  - Month (4 bits)
  - Day (5 bits)
  - Hour (5 bits, 24-hour format)
  - Minute (6 bits)
  - Second (6 bits)
- **Configurable colors** via JSON configuration
- **Two display modes**: binary clock or scrolling ISO-8601 text
- **Optional button controls**: pause, mode switch, exit (`enable_buttons`)
- **Systemd integration** for automatic startup
- **Graceful error handling** and signal-based shutdown
- **Mock hardware fallback** so the package imports and tests on any machine

## Hardware Requirements

- Raspberry Pi (any model with GPIO)
- Pimoroni Unicorn HAT Mini (17×7 LED matrix)
- Python 3.10+
- GPIO access — the service user must be in the `gpio`, `spi`, and `i2c` groups

Set up the Pi and the HAT (read the manual, run the Pimoroni examples) before
installing this project.

## Installation

### System Install (recommended)

```bash
git clone https://github.com/rmrfslashbin/pybinclock.git
cd pybinclock

# Run the setup script (do NOT use sudo; it calls sudo where needed)
./setup.sh
```

The setup script will:

- Install the application to `/usr/local/lib/pybinclock`
- Create executable wrappers in `/usr/local/bin` (`pybinclock`, `pybinclock-test`)
- Install a systemd service (`pybinclock.service`) for automatic startup
- Configure permissions and the `lgpio` pin factory

### Development Setup

```bash
git clone https://github.com/rmrfslashbin/pybinclock.git
cd pybinclock
uv sync --extra dev
```

### Service Control

```bash
sudo systemctl start pybinclock     # Start
sudo systemctl stop pybinclock      # Stop
sudo systemctl restart pybinclock   # Restart (e.g. after a config change)
sudo systemctl status pybinclock    # Status
sudo journalctl -u pybinclock -f    # Follow logs
sudo systemctl disable pybinclock   # Disable autostart
```

To uninstall completely, run `./uninstall.sh`.

## Configuration

PyBinClock is driven entirely by an optional JSON config file.

### Search Order

1. `~/.config/pybinclock/config.json` (user config)
2. `/etc/pybinclock/config.json` (system config)
3. `/usr/local/etc/pybinclock/config.json`
4. `./config.json` (current working directory)
5. Built-in defaults

### Create a Configuration

```bash
mkdir -p ~/.config/pybinclock
uv run python -c \
  "from pybinclock.config import Config; \
   Config().create_sample_config('$HOME/.config/pybinclock/config.json')"
```

### Options

```jsonc
{
  "display": {
    "rotation": 180,          // 0, 90, 180, or 270
    "brightness": 0.1,        // 0.0 - 1.0
    "refresh_rate": 1.0       // seconds between updates
  },
  "colors": {
    "on_color": [255, 0, 0],  // RGB for "on" bits
    "off_color": [0, 0, 0],   // RGB for "off" bits
    "status_okay": [0, 255, 0],
    "status_error": [255, 0, 0],
    "status_warn": [255, 255, 0],
    "status_info": [0, 0, 255]
  },
  "buttons": {
    "button_a_pin": 5,
    "button_b_pin": 6,
    "button_x_pin": 16,
    "button_y_pin": 24,
    "debounce_time": 0.3
  },
  "font_path": "/usr/local/lib/pybinclock/5x7.ttf",
  "log_level": "INFO",        // DEBUG, INFO, WARNING, ERROR
  "enable_buttons": true      // set false for headless/service use
}
```

> **Headless service note:** the systemd service runs with
> `"enable_buttons": false` so no GPIO buttons are claimed. Set it to `true`
> only if you have the buttons wired and want interactive controls.
>
> The panel dimensions (17×7) are read directly from the hardware, so there
> are no `width`/`height` settings. Unknown keys in a config file are ignored,
> so older config files keep loading.

## Usage

### Reading the Clock

Six rows of binary data, most-significant field on top, least-significant bit
on the right (little-endian):

```
Row 0: Year   [11 bits]  2024 = 11111101000
Row 1: Month  [ 4 bits]  May  = 0101
Row 2: Day    [ 5 bits]  28   = 11100
Row 3: Hour   [ 5 bits]  13   = 01101
Row 4: Minute [ 6 bits]  45   = 101101
Row 5: Second [ 6 bits]  30   = 011110
```

The bottom row (row 6) shows small status indicator pixels.

### Button Controls (when `enable_buttons` is true)

- **Button A** — pause / resume. Freeze the display, count the dots, and work
  out the time it was when you pushed it. Push again to resume.
- **Button B** — toggle between the binary clock and a scrolling ISO-8601
  date/time.
- **Button X** — exit the application.
- **Button Y** — reserved for future use.

### Console Test

```bash
# Print the binary clock to the console (no hardware needed)
pybinclock-test

# Run the LED display against a specific config
uv run python -c \
  "from pybinclock.BinClockLEDs import BinClockLEDs; BinClockLEDs('/path/to/config.json')"
```

## Color Themes

Ready-made themes live in `themes/`. To apply one:

```bash
cp themes/blue_theme.json ~/.config/pybinclock/config.json
sudo systemctl restart pybinclock
```

Available: `blue_theme.json`, `green_theme.json`, `amber_theme.json`,
`purple_theme.json`.

## Development

```bash
make install-dev   # Install dev dependencies + pre-commit hooks
make test          # Run tests with coverage
make lint          # flake8
make format        # black
make type-check    # mypy
make all           # format, lint, type-check, test
```

Dependencies are managed with [uv](https://github.com/astral-sh/uv); the pinned
set lives in `uv.lock`.

### Project Structure

```
pybinclock/
├── pybinclock/
│   ├── PyBinClock.py       # Time → binary conversion + console clock
│   ├── BinClockLEDs.py     # Unicorn HAT Mini controller (config-driven)
│   └── config.py           # Configuration dataclasses + JSON loading
├── tests/                  # Unit tests (mock hardware, no Pi required)
├── themes/                 # Color theme examples
├── setup.sh / uninstall.sh # Install / uninstall (systemd)
├── Makefile                # Development tasks
└── pyproject.toml          # Project + tooling configuration
```

## API Reference

### CurrentTime

```python
from pybinclock.PyBinClock import CurrentTime

ct = CurrentTime()
ct.update()
ct.binary["hour"]   # e.g. [0, 1, 1, 0, 1]
```

### Config

```python
from pybinclock.config import Config

config = Config.load("/path/to/config.json")   # or Config.load() to search
config.display.brightness
config.colors.on_color
config.enable_buttons
config.create_sample_config("sample.json")
```

### LEDController

A single config-driven controller. Falls back to mock hardware when the
`gpiozero` / `unicornhatmini` libraries are unavailable.

```python
from pybinclock.config import Config
from pybinclock.BinClockLEDs import LEDController

with LEDController(Config.load()) as leds:
    leds.field[row][col] = [r, g, b]
    leds.draw()
```

## Troubleshooting

**Permission denied / GPIO errors**

```bash
sudo usermod -a -G gpio,spi,i2c $USER   # then log out and back in
```

**Service won't start**

```bash
sudo journalctl -u pybinclock -n 50
ls -la /usr/local/lib/pybinclock /usr/local/bin/pybinclock
```

**LEDs not lighting up** — check the HAT is seated, enable SPI via
`sudo raspi-config` → Interface Options → SPI, and confirm the Pimoroni
examples work.

**Wrong colors/brightness** — verify JSON syntax, RGB values in 0–255, and
brightness in 0.0–1.0.

**Debug logging** — set `"log_level": "DEBUG"` in the config and follow the
journal.

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgments

- Pimoroni for the Unicorn HAT Mini hardware and libraries
- The Raspberry Pi community
