#!/usr/bin/env python3
"""
Binary Clock LED Display Module.

Drives a Pimoroni Unicorn HAT Mini to show the current date and time as a
binary matrix. Behaviour is driven entirely by a :class:`~pybinclock.config.Config`:

* ``enable_buttons`` toggles the physical button controls (pause / mode /
  exit). Disable it for headless systemd service use.
* When the hardware libraries are unavailable the controller transparently
  falls back to mock devices so the module can be imported and tested on any
  machine.
"""

import signal
import sys
import threading
from pathlib import Path
from time import sleep, time
from typing import Any, Dict, List, Optional, Tuple, Union

from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from pybinclock.PyBinClock import CurrentTime
from pybinclock.config import Config

# RPi.GPIO raises RuntimeError (not ImportError) on unsupported boards.
HARDWARE_IMPORT_ERROR: Optional[BaseException] = None
try:
    from gpiozero import Button
    from unicornhatmini import UnicornHATMini

    HARDWARE_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    HARDWARE_IMPORT_ERROR = e
    HARDWARE_AVAILABLE = False

# systemd-timesyncd creates <dir>/synchronized once the clock is NTP-synced.
TIMESYNC_DIR = Path("/run/systemd/timesync")


def clock_synchronized(sync_dir: Path = TIMESYNC_DIR) -> bool:
    """Return True once the system clock is known to be synchronized.

    Hosts without systemd-timesyncd (no ``sync_dir``) have nothing to wait
    for, so they count as synchronized rather than blocking the clock forever.
    """
    if not sync_dir.is_dir():
        return True
    return (sync_dir / "synchronized").exists()


class MockHAT:
    """Mock Unicorn HAT Mini for running without hardware."""

    def __init__(self) -> None:
        self.pixels: Dict[Tuple[int, int], Tuple[int, int, int]] = {}
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
    """Mock button for running without hardware."""

    def __init__(self, pin: int) -> None:
        self.pin = pin
        self.when_pressed: Any = None

    def close(self) -> None:
        pass


class LEDController:
    """LED controller with configuration, mock-hardware and error handling."""

    def __init__(self, config: Config) -> None:
        """
        Initialize the LED controller with configuration.

        Args:
            config: Configuration object with display and color settings.
        """
        self.config = config
        self.hat: Union[Any, MockHAT]
        self.buttons: Dict[str, Union[Any, MockButton]] = {}
        self.width = 17
        self.height = 7
        self.field: List[List[List[int]]] = []
        self.paused = False
        self.mode = "binclock"
        self.exit = False
        self.last_time_update: Dict[str, List[int]] = {}
        # Button callbacks run on gpiozero's thread; serialize display writes.
        self._lock = threading.RLock()

        # Initialize hardware (sets self.hat, self.buttons, width/height)
        self._init_hardware()

        # Status indicators: name -> [x, y, [r, g, b]]
        self.status: Dict[str, List[Any]] = {
            "okay": [0, 6, self.config.colors.status_info],
            "paused": [1, 6, self.config.colors.status_okay],
            "mode": [2, 6, self.config.colors.status_okay],
        }

        self.reset()

    def _init_hardware(self) -> None:
        """Initialize hardware components with error handling."""
        if not HARDWARE_AVAILABLE:
            if self.config.require_hardware:
                raise RuntimeError(
                    "LED hardware libraries failed to import "
                    f"({HARDWARE_IMPORT_ERROR!r}) and require_hardware is set; "
                    "refusing to run on mock hardware with the panel dark."
                )
            logger.warning(
                "Hardware libraries not available "
                f"({HARDWARE_IMPORT_ERROR!r}); running in simulation mode"
            )

        try:
            if HARDWARE_AVAILABLE:
                self.hat = UnicornHATMini()
                self.hat.set_brightness(self.config.display.brightness)
                self.hat.set_rotation(self.config.display.rotation)

                if self.config.enable_buttons:
                    pins = {
                        "a": self.config.buttons.button_a_pin,
                        "b": self.config.buttons.button_b_pin,
                        "x": self.config.buttons.button_x_pin,
                        "y": self.config.buttons.button_y_pin,
                    }
                    for name, pin in pins.items():
                        self.buttons[name] = Button(
                            pin, bounce_time=self.config.buttons.debounce_time
                        )
                    self.buttons["a"].when_pressed = self.toggle_pause
                    self.buttons["b"].when_pressed = self.toggle_mode
                    self.buttons["x"].when_pressed = self.set_exit
            else:
                self.hat = MockHAT()
                self.hat.set_brightness(self.config.display.brightness)
                self.hat.set_rotation(self.config.display.rotation)

                if self.config.enable_buttons:
                    self.buttons = {
                        "a": MockButton(self.config.buttons.button_a_pin),
                        "b": MockButton(self.config.buttons.button_b_pin),
                        "x": MockButton(self.config.buttons.button_x_pin),
                        "y": MockButton(self.config.buttons.button_y_pin),
                    }

            self.width, self.height = self.hat.get_shape()

        except Exception as e:
            logger.error(f"Failed to initialize hardware: {e}")
            raise

    def __enter__(self) -> "LEDController":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Context manager exit with cleanup."""
        self.cleanup()

    def cleanup(self) -> None:
        """Clean up all resources."""
        try:
            self.hat.clear()
            self.hat.show()

            for button in self.buttons.values():
                button.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def reset(self) -> None:
        """Initialize the display field to all-off."""
        self.field = [
            [[0, 0, 0] for _ in range(self.width)] for _ in range(self.height)
        ]
        self.draw()

    def set_status(self, status: str, color: List[int]) -> None:
        """
        Update a status indicator pixel.

        Args:
            status: Status type ('okay', 'paused', 'mode')
            color: RGB color list [r, g, b]
        """
        if status in self.status:
            self.status[status][2] = color
            self.draw()

    def draw(self) -> None:
        """Render the current field (plus status pixels) to the display."""
        try:
            with self._lock:
                for s in self.status:
                    x, y, color = self.status[s]
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.field[y][x] = color

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
        self.set_status(
            "paused",
            (
                self.config.colors.status_error
                if self.paused
                else self.config.colors.status_okay
            ),
        )

    def toggle_mode(self) -> None:
        """Toggle between binary clock and scrolling text mode."""
        if self.mode == "binclock":
            self.mode = "scrollclock"
            self.set_status("mode", self.config.colors.status_info)
        else:
            self.mode = "binclock"
            self.set_status("mode", self.config.colors.status_okay)
        logger.info(f"Mode changed to: {self.mode}")

    def set_exit(self) -> None:
        """Set the exit flag."""
        self.exit = True
        logger.info("Exit requested")

    def write_text(
        self, text: str, color: List[int], interruptible: bool = True
    ) -> None:
        """
        Scroll text across the display.

        Args:
            text: Text to display
            color: RGB color for the text
            interruptible: When True, stop scrolling as soon as the mode leaves
                ``scrollclock`` or exit is requested. Pass False for messages
                that must play out in full (e.g. the shutdown notice).
        """
        try:
            font = ImageFont.truetype(self.config.font_path, 8)
            left, top, right, bottom = font.getbbox(text)
            text_width = int(right - left)

            image = Image.new("P", (text_width + 2 * self.width, self.height), 0)
            draw = ImageDraw.Draw(image)
            draw.text((self.width, -1), text, font=font, fill=255)

            offset_x = 0

            while offset_x + self.width <= image.size[0]:
                if interruptible and (self.mode != "scrollclock" or self.exit):
                    break

                # Freeze the scroll in place while paused.
                if interruptible and self.paused:
                    sleep(0.1)
                    continue

                with self._lock:
                    for y in range(self.height):
                        for x in range(self.width):
                            if image.getpixel((x + offset_x, y)) == 255:
                                self.hat.set_pixel(x, y, *color)
                            else:
                                self.hat.set_pixel(x, y, 0, 0, 0)
                    self.hat.show()

                sleep(0.05)
                offset_x += 1

        except Exception as e:
            logger.error(f"Error displaying text: {e}")

    def update_binary_display(self, ct: CurrentTime) -> None:
        """
        Update the field with the binary time representation.

        Args:
            ct: CurrentTime object with binary data
        """
        time_components = [
            "year",  # row 0
            "month",  # row 1
            "day",  # row 2
            "hour",  # row 3
            "minute",  # row 4
            "second",  # row 5
        ]

        for row, name in enumerate(time_components):
            binary_data = ct.binary[name]

            # Skip rows that have not changed since the last tick.
            if self.last_time_update.get(name) == binary_data:
                continue
            self.last_time_update[name] = list(binary_data)

            # Right-align the bits (little-endian, LSB at the far right).
            for offset, bit in enumerate(reversed(binary_data)):
                x = self.width - 1 - offset
                if 0 <= x < self.width:
                    self.field[row][x] = (
                        self.config.colors.on_color
                        if bit == 1
                        else self.config.colors.off_color
                    )


def signal_handler(signum: int, frame: Any) -> None:
    """Handle shutdown signals by unwinding the main loop.

    Raising ``SystemExit`` lets the controller's context manager clear the
    display and release the buttons exactly once.
    """
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


def _fatal(_exc: BaseException) -> None:
    """Exit non-zero after logger.catch has logged a fatal error."""
    sys.exit(1)


# How far past each tick to wake. Waking a hair after the boundary means
# ``ct.update()`` reads the new second rather than the tail of the old one.
TICK_GUARD_SECONDS = 0.005


def seconds_until_next_tick(period: float, now: Optional[float] = None) -> float:
    """
    Seconds to sleep so the next frame lands just after a wall-clock boundary.

    A flat ``sleep(period)`` after drawing adds the render time to every pass,
    so the frame drifts against the second and the display shows a second that
    began up to a whole period ago
    (ISSUE code.rmrfslashbin.net/rmrfslashbin/pybinclock#12).
    Sleeping to the next multiple of ``period`` on the epoch keeps each frame
    within a few milliseconds of the second it shows.

    Args:
        period: The refresh period in seconds (``display.refresh_rate``).
        now: The current epoch time; defaults to ``time.time()``.
    """
    if now is None:
        now = time()
    remaining = period - (now % period)
    return remaining + TICK_GUARD_SECONDS


# onerror: log the traceback once, then exit 1 so systemd sees a failure
# (plain @logger.catch swallows the exception and the process exits 0).
@logger.catch(onerror=_fatal)
def BinClockLEDs(config_path: Optional[str] = None) -> None:
    """
    Main entry point for the binary clock LED display.

    Args:
        config_path: Optional path to a configuration file. When ``None`` the
            standard config search locations are used.
    """
    # Load configuration
    config = Config.load(config_path)

    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level=config.log_level)
    logger.info("Starting BinClockLEDs")

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        with LEDController(config) as controller:
            ct = CurrentTime()
            synced = False

            while True:
                if controller.exit:
                    logger.info("Exit requested, shutting down")
                    controller.write_text(
                        "Shutting down!",
                        config.colors.status_okay,
                        interruptible=False,
                    )
                    break

                if controller.paused:
                    sleep(0.1)
                    continue

                # Until NTP has synced, say so instead of showing a wrong time.
                # Checked every pass until true, then never again.
                if not synced:
                    synced = clock_synchronized(TIMESYNC_DIR)
                    if not synced:
                        controller.write_text(
                            "NTP SYNC",
                            config.colors.status_warn,
                            interruptible=False,
                        )
                        continue
                    logger.info("System clock synchronized")

                if controller.mode == "scrollclock":
                    ct.update()
                    controller.write_text(
                        ct.now.replace(microsecond=0).isoformat(),
                        config.colors.status_okay,
                    )
                    sleep(1)
                    continue

                # Update time and display
                ct.update()
                controller.set_status("okay", config.colors.status_okay)
                controller.update_binary_display(ct)
                controller.draw()

                sleep(seconds_until_next_tick(config.display.refresh_rate))

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")


if __name__ == "__main__":
    BinClockLEDs()
