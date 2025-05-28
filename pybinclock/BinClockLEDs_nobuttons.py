#!/usr/bin/env python3
"""
Binary clock display without button support for service mode.
This module is used when running as a systemd service where button
interaction is not needed or desired.
"""

import signal
import sys
from time import sleep
from unicornhatmini import UnicornHATMini
from loguru import logger
from pybinclock.PyBinClock import CurrentTime


class LEDControllerNoButtons:
    """LED controller for binary clock display without button support."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Clean up resources on exit."""
        self.hat.clear()
        self.hat.show()

    def __init__(self, rotation: int = 180, brightness: float = 0.1) -> None:
        """
        Initialize the LED controller.

        Args:
            rotation: Display rotation in degrees (0, 90, 180, 270)
            brightness: LED brightness from 0.0 to 1.0
        """
        self.hat = UnicornHATMini()
        self.hat.set_brightness(brightness)
        self.hat.set_rotation(rotation)
        self.width, self.height = self.hat.get_shape()
        self.field = []

        # Status indicator colors
        self.OKAY = [0, 255, 0]
        self.ERROR = [255, 0, 0]
        self.INFO = [0, 0, 255]

        # Status indicator positions
        self.status = {"heartbeat": [0, 6, self.INFO]}  # x, y, [r, g, b]

        self.reset()

    def reset(self) -> None:
        """Initialize the display field."""
        self.field = [[[0, 0, 0] for x in range(17)] for y in range(7)]
        self.draw()

    def setStatus(self, status: str, color: list) -> None:
        """
        Update status indicator.

        Args:
            status: Status type ('heartbeat')
            color: RGB color list [r, g, b]
        """
        if status in self.status:
            self.status[status][2] = color
            self.draw()

    def draw(self) -> None:
        """Update the LED display with current field values."""
        # Draw status indicators
        for s in self.status:
            self.field[self.status[s][1]][self.status[s][0]] = self.status[s][2]

        # Update all pixels
        for yndx, row in enumerate(self.field):
            for xndx, rgb in enumerate(row):
                self.hat.set_pixel(xndx, yndx, *rgb)

        self.hat.show()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    if "leds" in globals():
        leds.hat.clear()
        leds.hat.show()
    sys.exit(0)


@logger.catch
def BinClockLEDs():
    """Main entry point for the no-buttons binary clock display."""
    logger.info("Starting BinClockLEDs (no buttons mode)")

    global leds

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        leds = LEDControllerNoButtons(rotation=180)
        ct = CurrentTime()

        heartbeat_state = True

        while True:
            # Update the current time
            ct.update()

            # Toggle heartbeat indicator
            heartbeat_state = not heartbeat_state
            leds.setStatus("heartbeat", leds.OKAY if heartbeat_state else [0, 0, 0])

            # Reset the row counter
            row = 0

            # Build the display based on the current time
            for i in [
                ct.binary["year"],  # row 0
                ct.binary["month"],  # row 1
                ct.binary["day"],  # row 2
                ct.binary["hour"],  # row 3
                ct.binary["minute"],  # row 4
                ct.binary["second"],  # row 5
            ]:
                # Make little-endian
                i.reverse()
                for led in range(len(i)):
                    if i[led] == 1:
                        # Turn on the LED (red)
                        leds.field[row][16 - led] = [255, 0, 0]
                    else:
                        # Turn off the LED
                        leds.field[row][16 - led] = [0, 0, 0]

                row += 1

            # Update the display
            leds.draw()
            sleep(1)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Cleaning up LEDs")
        if "leds" in locals():
            leds.hat.clear()
            leds.hat.show()
        sys.exit(0)


if __name__ == "__main__":
    BinClockLEDs()
