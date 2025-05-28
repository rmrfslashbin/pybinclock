#!/usr/bin/env python3
"""Unit tests for configuration module."""

import pytest
import json
import tempfile
from pathlib import Path

from pybinclock.config import Config, DisplayConfig, ColorScheme, ButtonConfig


class TestColorScheme:
    """Test cases for ColorScheme dataclass."""
    
    def test_default_colors(self):
        """Test that default colors are set correctly."""
        colors = ColorScheme()
        
        assert colors.on_color == [255, 0, 0]
        assert colors.off_color == [0, 0, 0]
        assert colors.status_okay == [0, 255, 0]
        assert colors.status_error == [255, 0, 0]
        assert colors.status_warn == [255, 255, 0]
        assert colors.status_info == [0, 0, 255]
    
    def test_custom_colors(self):
        """Test custom color initialization."""
        custom_on = [100, 200, 50]
        colors = ColorScheme(on_color=custom_on)
        
        assert colors.on_color == custom_on
        assert colors.off_color == [0, 0, 0]  # Should still be default


class TestDisplayConfig:
    """Test cases for DisplayConfig dataclass."""
    
    def test_default_values(self):
        """Test default display configuration."""
        display = DisplayConfig()
        
        assert display.rotation == 180
        assert display.brightness == 0.1
        assert display.width == 17
        assert display.height == 7
        assert display.refresh_rate == 1.0
    
    def test_valid_rotations(self):
        """Test valid rotation values."""
        for rotation in [0, 90, 180, 270]:
            display = DisplayConfig(rotation=rotation)
            assert display.rotation == rotation
    
    def test_invalid_rotation(self):
        """Test that invalid rotation raises ValueError."""
        with pytest.raises(ValueError, match="Invalid rotation"):
            DisplayConfig(rotation=45)
    
    def test_brightness_range(self):
        """Test brightness validation."""
        # Valid brightness values
        DisplayConfig(brightness=0.0)
        DisplayConfig(brightness=0.5)
        DisplayConfig(brightness=1.0)
        
        # Invalid brightness values
        with pytest.raises(ValueError, match="Invalid brightness"):
            DisplayConfig(brightness=-0.1)
        
        with pytest.raises(ValueError, match="Invalid brightness"):
            DisplayConfig(brightness=1.1)
    
    def test_refresh_rate_validation(self):
        """Test refresh rate validation."""
        DisplayConfig(refresh_rate=0.1)
        DisplayConfig(refresh_rate=2.0)
        
        with pytest.raises(ValueError, match="Invalid refresh rate"):
            DisplayConfig(refresh_rate=0)
        
        with pytest.raises(ValueError, match="Invalid refresh rate"):
            DisplayConfig(refresh_rate=-1)


class TestButtonConfig:
    """Test cases for ButtonConfig dataclass."""
    
    def test_default_pins(self):
        """Test default button pin assignments."""
        buttons = ButtonConfig()
        
        assert buttons.button_a_pin == 5
        assert buttons.button_b_pin == 6
        assert buttons.button_x_pin == 16
        assert buttons.button_y_pin == 24
        assert buttons.debounce_time == 0.3
    
    def test_custom_pins(self):
        """Test custom pin configuration."""
        buttons = ButtonConfig(button_a_pin=10, debounce_time=0.5)
        
        assert buttons.button_a_pin == 10
        assert buttons.button_b_pin == 6  # Should still be default
        assert buttons.debounce_time == 0.5


class TestConfig:
    """Test cases for main Config class."""
    
    def test_default_initialization(self):
        """Test that Config initializes with defaults."""
        config = Config()
        
        assert isinstance(config.display, DisplayConfig)
        assert isinstance(config.colors, ColorScheme)
        assert isinstance(config.buttons, ButtonConfig)
        assert config.font_path == "/usr/local/lib/pybinclock/5x7.ttf"
        assert config.log_level == "INFO"
        assert config.enable_buttons is True
    
    def test_load_nonexistent_file(self):
        """Test loading when no config file exists."""
        config = Config.load("/nonexistent/path/config.json")
        
        # Should use defaults
        assert config.display.rotation == 180
        assert config.colors.on_color == [255, 0, 0]
    
    def test_load_from_file(self):
        """Test loading configuration from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "display": {
                    "rotation": 90,
                    "brightness": 0.5
                },
                "colors": {
                    "on_color": [0, 255, 0]
                },
                "log_level": "DEBUG"
            }
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = Config.load(temp_path)
            
            assert config.display.rotation == 90
            assert config.display.brightness == 0.5
            assert config.colors.on_color == [0, 255, 0]
            assert config.log_level == "DEBUG"
            
            # Other values should be defaults
            assert config.display.width == 17
            assert config.colors.off_color == [0, 0, 0]
            
        finally:
            Path(temp_path).unlink()
    
    def test_save_config(self):
        """Test saving configuration to file."""
        config = Config()
        config.display.brightness = 0.7
        config.colors.on_color = [128, 128, 128]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            config.save(temp_path)
            
            # Load the saved file
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data['display']['brightness'] == 0.7
            assert saved_data['colors']['on_color'] == [128, 128, 128]
            assert 'log_level' in saved_data
            
        finally:
            Path(temp_path).unlink()
    
    def test_create_sample_config(self):
        """Test creating a sample configuration file."""
        config = Config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            config.create_sample_config(temp_path)
            
            # Check file exists and has expected content
            assert Path(temp_path).exists()
            
            with open(temp_path, 'r') as f:
                sample_data = json.load(f)
            
            assert '_comment' in sample_data
            assert 'display' in sample_data
            assert 'colors' in sample_data
            assert 'buttons' in sample_data
            
        finally:
            Path(temp_path).unlink()
    
    def test_invalid_config_file(self):
        """Test handling of invalid JSON in config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            # Should fall back to defaults without crashing
            config = Config.load(temp_path)
            assert config.display.rotation == 180
            
        finally:
            Path(temp_path).unlink()