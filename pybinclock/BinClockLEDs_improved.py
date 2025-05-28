#!/usr/bin/env python3
"""
Improved Binary Clock LED Display Module.

This module provides an enhanced version of the binary clock display
with better error handling, configuration support, and optimized performance.
"""

import signal
import sys
from contextlib import contextmanager
from time import sleep, time
from typing import List, Tuple, Optional, Dict
from colorsys import hsv_to_rgb

from loguru import logger
from PIL import Image, ImageDraw, ImageFont

try:
    from gpiozero import Button
    from unicornhatmini import UnicornHATMini
    HARDWARE_AVAILABLE = True
except ImportError:
    logger.warning("Hardware libraries not available, running in simulation mode")
    HARDWARE_AVAILABLE = False

from pybinclock.PyBinClock import CurrentTime
from pybinclock.config import Config


class MockHAT:
    """Mock HAT for testing without hardware."""
    def __init__(self):
        self.pixels = {}
        self.brightness = 0.1
        self.rotation = 0
        
    def set_brightness(self, brightness: float) -> None:
        self.brightness = brightness
        
    def set_rotation(self, rotation: int) -> None:
        self.rotation = rotation
        
    def get_shape(self) -> Tuple[int, int]:
        return (17, 7)
        
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        self.pixels[(x, y)] = (r, g, b)
        
    def show(self) -> None:
        pass
        
    def clear(self) -> None:
        self.pixels = {}


class MockButton:
    """Mock Button for testing without hardware."""
    def __init__(self, pin: int):
        self.pin = pin
        self.when_pressed = None
        
    def close(self) -> None:
        pass


class LEDController:
    """Enhanced LED controller with configuration and error handling."""
    
    def __init__(self, config: Config):
        """
        Initialize the LED controller with configuration.
        
        Args:
            config: Configuration object with display and color settings.
        """
        self.config = config
        self.hat = None
        self.buttons = {}
        self.field = []
        self.paused = False
        self.mode = 'binclock'
        self.exit = False
        self.last_time_update = {}
        
        # Initialize hardware
        self._init_hardware()
        
        # Status indicators
        self.status = {
            'okay': [0, 6, self.config.colors.status_info],
            'paused': [1, 6, self.config.colors.status_okay],
            'mode': [2, 6, self.config.colors.status_okay]
        }
        
        self.reset()
    
    def _init_hardware(self) -> None:
        """Initialize hardware components with error handling."""
        try:
            if HARDWARE_AVAILABLE:
                self.hat = UnicornHATMini()
                self.hat.set_brightness(self.config.display.brightness)
                self.hat.set_rotation(self.config.display.rotation)
                
                if self.config.enable_buttons:
                    self.buttons['a'] = Button(
                        self.config.buttons.button_a_pin,
                        bounce_time=self.config.buttons.debounce_time
                    )
                    self.buttons['b'] = Button(
                        self.config.buttons.button_b_pin,
                        bounce_time=self.config.buttons.debounce_time
                    )
                    self.buttons['x'] = Button(
                        self.config.buttons.button_x_pin,
                        bounce_time=self.config.buttons.debounce_time
                    )
                    self.buttons['y'] = Button(
                        self.config.buttons.button_y_pin,
                        bounce_time=self.config.buttons.debounce_time
                    )
                    
                    self.buttons['a'].when_pressed = self.toggle_pause
                    self.buttons['b'].when_pressed = self.toggle_mode
                    self.buttons['x'].when_pressed = self.set_exit
            else:
                # Use mock hardware for testing
                self.hat = MockHAT()
                self.hat.set_brightness(self.config.display.brightness)
                self.hat.set_rotation(self.config.display.rotation)
                
                if self.config.enable_buttons:
                    self.buttons['a'] = MockButton(self.config.buttons.button_a_pin)
                    self.buttons['b'] = MockButton(self.config.buttons.button_b_pin)
                    self.buttons['x'] = MockButton(self.config.buttons.button_x_pin)
                    self.buttons['y'] = MockButton(self.config.buttons.button_y_pin)
            
            self.width, self.height = self.hat.get_shape()
            
        except Exception as e:
            logger.error(f"Failed to initialize hardware: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Context manager exit with cleanup."""
        self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up all resources."""
        try:
            if self.hat:
                self.hat.clear()
                self.hat.show()
            
            for button in self.buttons.values():
                if button:
                    button.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def reset(self) -> None:
        """Initialize the display field."""
        self.field = [
            [[0, 0, 0] for x in range(self.width)]
            for y in range(self.height)
        ]
        self.draw()
    
    def set_status(self, status: str, color: List[int]) -> None:
        """
        Update status indicator.
        
        Args:
            status: Status type ('okay', 'paused', 'mode')
            color: RGB color list [r, g, b]
        """
        if status in self.status:
            self.status[status][2] = color
            self.draw()
    
    def draw(self) -> None:
        """Update the LED display with optimized rendering."""
        try:
            # Draw status indicators
            for s in self.status:
                x, y, color = self.status[s]
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.field[y][x] = color
            
            # Update only changed pixels
            for y, row in enumerate(self.field):
                for x, rgb in enumerate(row):
                    self.hat.set_pixel(x, y, *rgb)
            
            self.hat.show()
            
        except Exception as e:
            logger.error(f"Error updating display: {e}")
    
    def toggle_pause(self) -> None:
        """Toggle pause state."""
        self.paused = not self.paused
        logger.info(f"Clock {'paused' if self.paused else 'resumed'}")
        self.set_status('paused', 
                       self.config.colors.status_error if self.paused 
                       else self.config.colors.status_okay)
    
    def toggle_mode(self) -> None:
        """Toggle between binary clock and scrolling text mode."""
        if self.mode == 'binclock':
            self.mode = 'scrollclock'
            self.set_status('mode', self.config.colors.status_info)
        else:
            self.mode = 'binclock'
            self.set_status('mode', self.config.colors.status_warn)
        logger.info(f"Mode changed to: {self.mode}")
    
    def set_exit(self) -> None:
        """Set exit flag."""
        self.exit = True
        logger.info("Exit requested")
    
    def write_text(self, text: str, color: List[int]) -> None:
        """
        Scroll text across the display.
        
        Args:
            text: Text to display
            color: RGB color for the text
        """
        try:
            font = ImageFont.truetype(self.config.font_path, 8)
            left, top, right, bottom = font.getbbox(text)
            text_width = right - left
            
            image = Image.new('P', 
                            (text_width + self.width + self.width, self.height), 
                            0)
            draw = ImageDraw.Draw(image)
            draw.text((self.width, -1), text, font=font, fill=255)
            
            offset_x = 0
            
            while offset_x + self.width <= image.size[0]:
                if self.mode != 'scrollclock' or self.exit:
                    break
                
                for y in range(self.height):
                    for x in range(self.width):
                        if image.getpixel((x + offset_x, y)) == 255:
                            self.hat.set_pixel(x, y, *color)
                        else:
                            self.hat.set_pixel(x, y, 0, 0, 0)
                
                if not self.paused:
                    self.hat.show()
                    sleep(0.05)
                
                offset_x += 1
                
        except Exception as e:
            logger.error(f"Error displaying text: {e}")
    
    def update_binary_display(self, ct: CurrentTime) -> None:
        """
        Update display with binary time representation.
        
        Args:
            ct: CurrentTime object with binary data
        """
        row = 0
        time_components = [
            ('year', ct.binary['year']),
            ('month', ct.binary['month']),
            ('day', ct.binary['day']),
            ('hour', ct.binary['hour']),
            ('minute', ct.binary['minute']),
            ('second', ct.binary['second'])
        ]
        
        for component_name, binary_data in time_components:
            # Only update if changed
            if self.last_time_update.get(component_name) != binary_data:
                self.last_time_update[component_name] = binary_data.copy()
                
                # Make little-endian
                binary_data.reverse()
                
                for led in range(len(binary_data)):
                    x = 16 - led
                    if 0 <= x < self.width:
                        if binary_data[led] == 1:
                            self.field[row][x] = self.config.colors.on_color
                        else:
                            self.field[row][x] = self.config.colors.off_color
            
            row += 1


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    if 'controller' in globals() and controller:
        controller.cleanup()
    sys.exit(0)


@logger.catch
def BinClockLEDs(config_path: Optional[str] = None) -> None:
    """
    Main entry point for the binary clock LED display.
    
    Args:
        config_path: Optional path to configuration file
    """
    global controller
    controller = None
    
    # Load configuration
    config = Config.load(config_path)
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level=config.log_level)
    logger.info("Starting BinClockLEDs")
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        with LEDController(config) as controller:
            ct = CurrentTime()
            
            while True:
                if controller.exit:
                    logger.info("Exit requested, shutting down")
                    controller.write_text("Shutting down!", 
                                        config.colors.status_okay)
                    break
                
                if controller.paused:
                    sleep(0.1)
                    continue
                
                if controller.mode == 'scrollclock':
                    controller.write_text(
                        ct.now.replace(microsecond=0).isoformat(),
                        config.colors.status_okay
                    )
                    sleep(1)
                    continue
                
                # Update time and display
                ct.update()
                controller.set_status('okay', config.colors.status_okay)
                controller.update_binary_display(ct)
                controller.draw()
                
                sleep(config.display.refresh_rate)
                
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        if controller:
            controller.cleanup()


if __name__ == '__main__':
    BinClockLEDs()