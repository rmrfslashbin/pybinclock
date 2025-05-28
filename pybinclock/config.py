#!/usr/bin/env python3
"""
Configuration module for PyBinClock.

Provides configuration management with defaults and user overrides.
"""

import json
from pathlib import Path
from typing import List, Optional, Union
from dataclasses import dataclass, asdict, field
from loguru import logger


@dataclass
class ColorScheme:
    """Color scheme configuration for the display."""

    on_color: Optional[List[int]] = None
    off_color: Optional[List[int]] = None
    status_okay: Optional[List[int]] = None
    status_error: Optional[List[int]] = None
    status_warn: Optional[List[int]] = None
    status_info: Optional[List[int]] = None

    def __post_init__(self) -> None:
        """Set default colors if not provided."""
        if self.on_color is None:
            self.on_color = [255, 0, 0]  # Red
        if self.off_color is None:
            self.off_color = [0, 0, 0]  # Black (off)
        if self.status_okay is None:
            self.status_okay = [0, 255, 0]  # Green
        if self.status_error is None:
            self.status_error = [255, 0, 0]  # Red
        if self.status_warn is None:
            self.status_warn = [255, 255, 0]  # Yellow
        if self.status_info is None:
            self.status_info = [0, 0, 255]  # Blue


@dataclass
class DisplayConfig:
    """Display configuration settings."""

    rotation: int = 180
    brightness: float = 0.1
    width: int = 17
    height: int = 7
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
    font_path: str = "/usr/local/lib/pybinclock/5x7.ttf"
    log_level: str = "INFO"
    enable_buttons: bool = True

    def __post_init__(self) -> None:
        """Initialize sub-configurations if not provided."""
        # No longer needed as we use default_factory

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
        config = cls()

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
                with open(config_path, "r") as f:
                    data = json.load(f)

                # Load display config
                if "display" in data:
                    display_data = {k: v for k, v in data["display"].items() if not k.startswith("_")}
                    config.display = DisplayConfig(**display_data)

                # Load color scheme
                if "colors" in data:
                    colors_data = {k: v for k, v in data["colors"].items() if not k.startswith("_")}
                    config.colors = ColorScheme(**colors_data)

                # Load button config
                if "buttons" in data:
                    buttons_data = {k: v for k, v in data["buttons"].items() if not k.startswith("_")}
                    config.buttons = ButtonConfig(**buttons_data)

                # Load other settings
                config.font_path = data.get("font_path", config.font_path)
                config.log_level = data.get("log_level", config.log_level)
                config.enable_buttons = data.get(
                    "enable_buttons", config.enable_buttons
                )

                logger.info(f"Loaded configuration from: {config_path}")
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {e}")
                logger.warning("Using default configuration")
        else:
            logger.info("No config file found, using defaults")

        return config

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
                "width": 17,
                "height": 7,
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
            "font_path": "/usr/local/lib/pybinclock/5x7.ttf",
            "log_level": "INFO",
            "enable_buttons": True,
        }

        # Create directory if it doesn't exist
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(sample, f, indent=2)

        logger.info(f"Created sample configuration at: {config_path}")
