#!/usr/bin/env python3
"""
Configuration module for PyBinClock.

Provides configuration management with defaults and user overrides.
"""

import json
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field, fields
from loguru import logger

# Bitmap font for scrolling-text mode, shipped inside the package.
BUNDLED_FONT = Path(__file__).with_name("5x7.ttf")


def running_on_pi() -> bool:
    """Return True on Linux/ARM, i.e. where the LED hardware is expected."""
    return sys.platform == "linux" and platform.machine() in (
        "aarch64",
        "armv7l",
        "armv6l",
    )


def _filter_known_fields(cls: type, data: Dict[str, Any]) -> Dict[str, Any]:
    """Return only the keys of ``data`` that are fields of the dataclass ``cls``.

    Silently drops comment keys (``_comment``) and any settings that are not
    recognized so that older or annotated config files load without crashing.

    Args:
        cls: A dataclass type to match keys against.
        data: Raw dictionary loaded from a config file.

    Returns:
        A dictionary containing only recognized field names.
    """
    valid = {f.name for f in fields(cls)}
    return {k: v for k, v in data.items() if k in valid}


@dataclass
class ColorScheme:
    """Color scheme configuration for the display."""

    on_color: List[int] = field(default_factory=lambda: [255, 0, 0])  # Red
    off_color: List[int] = field(default_factory=lambda: [0, 0, 0])  # Off
    status_okay: List[int] = field(default_factory=lambda: [0, 255, 0])  # Green
    status_error: List[int] = field(default_factory=lambda: [255, 0, 0])  # Red
    status_warn: List[int] = field(default_factory=lambda: [255, 255, 0])  # Yellow
    status_info: List[int] = field(default_factory=lambda: [0, 0, 255])  # Blue

    def __post_init__(self) -> None:
        """Validate that every color is an [R, G, B] triple of 0-255 ints."""
        for f in fields(self):
            value = getattr(self, f.name)
            if (
                not isinstance(value, list)
                or len(value) != 3
                or not all(
                    isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 255
                    for c in value
                )
            ):
                raise ValueError(
                    f"Invalid color {f.name}: {value!r}. "
                    "Must be [R, G, B] with integers 0-255."
                )


@dataclass
class DisplayConfig:
    """Display configuration settings.

    Note: the physical panel dimensions are read directly from the hardware
    via ``get_shape()``; only rotation, brightness, and refresh rate are
    configurable here.
    """

    rotation: int = 180
    brightness: float = 0.1
    refresh_rate: float = 1.0

    def __post_init__(self) -> None:
        """Validate display settings."""
        if self.rotation not in [0, 90, 180, 270]:
            raise ValueError(
                f"Invalid rotation: {self.rotation}. Must be 0, 90, 180, or 270."
            )
        if not 0.0 <= self.brightness <= 1.0:
            raise ValueError(
                f"Invalid brightness: {self.brightness}. Must be between 0.0 and 1.0."
            )
        if self.refresh_rate <= 0:
            raise ValueError(
                f"Invalid refresh rate: {self.refresh_rate}. Must be positive."
            )


@dataclass
class ButtonConfig:
    """Button configuration settings."""

    button_a_pin: int = 5
    button_b_pin: int = 6
    button_x_pin: int = 16
    button_y_pin: int = 24
    debounce_time: float = 0.3


@dataclass
class Config:
    """Main configuration class for PyBinClock."""

    display: DisplayConfig = field(default_factory=DisplayConfig)
    colors: ColorScheme = field(default_factory=ColorScheme)
    buttons: ButtonConfig = field(default_factory=ButtonConfig)
    font_path: str = str(BUNDLED_FONT)
    log_level: str = "INFO"
    # Off by default: a headless clock must never claim the button pins, and a
    # rejected config falls back to these defaults.
    enable_buttons: bool = False
    # On a Pi, refuse to fall back to mock hardware (which runs with the panel
    # dark while the service looks healthy). Off-Pi, mocks are expected.
    require_hardware: bool = field(default_factory=running_on_pi)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """
        Load configuration from file or use defaults.

        Args:
            config_path: Path to configuration file. If None, searches in
                standard locations.

        Returns:
            Config instance with loaded settings.
        """
        # Search for config file in standard locations
        if config_path is None:
            search_paths = [
                Path.home() / ".config" / "pybinclock" / "config.json",
                Path("/etc/pybinclock/config.json"),
                Path("/usr/local/etc/pybinclock/config.json"),
                Path.cwd() / "config.json",
            ]

            for path in search_paths:
                if path.exists():
                    config_path = str(path)
                    logger.info(f"Found config file at: {config_path}")
                    break

        # Load config if found
        if config_path and Path(config_path).exists():
            try:
                config = cls()
                with open(config_path, "r") as f:
                    data = json.load(f)

                # Load display config
                if "display" in data:
                    config.display = DisplayConfig(
                        **_filter_known_fields(DisplayConfig, data["display"])
                    )

                # Load color scheme
                if "colors" in data:
                    config.colors = ColorScheme(
                        **_filter_known_fields(ColorScheme, data["colors"])
                    )

                # Load button config
                if "buttons" in data:
                    config.buttons = ButtonConfig(
                        **_filter_known_fields(ButtonConfig, data["buttons"])
                    )

                # Load other settings
                config.font_path = data.get("font_path", config.font_path)
                config.log_level = data.get("log_level", config.log_level)
                for key in ("enable_buttons", "require_hardware"):
                    value = data.get(key, getattr(config, key))
                    if not isinstance(value, bool):
                        raise ValueError(
                            f"Invalid {key}: {value!r}. Must be true or false."
                        )
                    setattr(config, key, value)

                logger.info(f"Loaded configuration from: {config_path}")
                return config
            except Exception as e:
                # Never run on a half-applied config: fall back to defaults.
                logger.error(f"Error loading config from {config_path}: {e}")
                logger.warning("Using default configuration")
        elif config_path:
            logger.warning(f"Config file not found: {config_path}; using defaults")
        else:
            logger.info("No config file found, using defaults")

        return cls()

    def save(self, config_path: str) -> None:
        """
        Save configuration to file.

        Args:
            config_path: Path where to save the configuration.
        """
        data = {
            "display": asdict(self.display),
            "colors": asdict(self.colors),
            "buttons": asdict(self.buttons),
            "font_path": self.font_path,
            "log_level": self.log_level,
            "enable_buttons": self.enable_buttons,
            "require_hardware": self.require_hardware,
        }

        # Create directory if it doesn't exist
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved configuration to: {config_path}")

    def create_sample_config(self, config_path: str) -> None:
        """
        Create a sample configuration file with comments.

        Args:
            config_path: Path where to save the sample configuration.
        """
        sample = {
            "_comment": "PyBinClock configuration file",
            "display": {
                "_comment": "Display settings",
                "rotation": 180,
                "brightness": 0.1,
                "refresh_rate": 1.0,
            },
            "colors": {
                "_comment": "RGB color values [R, G, B] (0-255)",
                "on_color": [255, 0, 0],
                "off_color": [0, 0, 0],
                "status_okay": [0, 255, 0],
                "status_error": [255, 0, 0],
                "status_warn": [255, 255, 0],
                "status_info": [0, 0, 255],
            },
            "buttons": {
                "_comment": "GPIO pin assignments",
                "button_a_pin": 5,
                "button_b_pin": 6,
                "button_x_pin": 16,
                "button_y_pin": 24,
                "debounce_time": 0.3,
            },
            "log_level": "INFO",
            "enable_buttons": False,
        }

        # Create directory if it doesn't exist
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(sample, f, indent=2)

        logger.info(f"Created sample configuration at: {config_path}")
