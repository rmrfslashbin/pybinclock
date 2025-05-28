#!/usr/bin/env python3

import signal
import sys
from gpiozero import Button
from unicornhatmini import UnicornHATMini
from PIL import Image, ImageDraw, ImageFont
from time import sleep
from typing import Any, List
from loguru import logger
from pybinclock.PyBinClock import CurrentTime


class LEDController:
    def __enter__(self) -> "LEDController":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.hat.clear()
        self.hat.show()
        self.button_a.close()
        self.button_b.close()
        self.button_x.close()
        self.button_y.close()

    def __init__(self, rotation: int = 0, brightness: float = 0.1) -> None:
        self.hat = UnicornHATMini()
        self.hat.set_brightness(brightness)
        self.hat.set_rotation(rotation)
        self.width, self.height = self.hat.get_shape()
        self.field: List[List[List[int]]] = []

        self.OKAY = [0, 255, 0]
        self.ERROR = [255, 0, 0]
        self.WARN = [255, 255, 0]
        self.INFO = [0, 0, 255]

        self.button_a = Button(5)
        self.button_b = Button(6)
        self.button_x = Button(16)
        self.button_y = Button(24)

        self.button_a.when_pressed = self.togglePause
        self.button_b.when_pressed = self.toggleMode
        self.button_x.when_pressed = self.setExit

        self.paused = False
        self.mode = "binclock"
        self.exit = False

        self.status: dict[str, List[Any]] = {}
        self.status["okay"] = [0, 6, self.INFO]  # x, y, [r, g, b]
        self.status["paused"] = [1, 6, self.OKAY]  # x, y, [r, g, b]
        self.status["mode"] = [2, 6, self.OKAY]  # x, y, [r, g, b]

        self.reset()

    def reset(self) -> None:
        # Initialize the display
        self.field = [[[0, 0, 0] for x in range(17)] for y in range(7)]
        self.draw()

    def setStatus(self, status: str, color: list) -> None:
        if status == "okay":
            # logger.info('setting okay')
            self.status["okay"] = [0, 6, color]  # x, y, [r, g, b]

        if status == "paused":
            # logger.info('setting paused')
            self.status["paused"] = [1, 6, color]

        if status == "mode":
            # logger.info('setting mode')
            self.status["mode"] = [2, 6, color]

        self.draw()

    def draw(self) -> None:
        for s in self.status:
            self.field[self.status[s][1]][self.status[s][0]] = self.status[s][2]

        for yndx, row in enumerate(self.field):
            for xndx, rgb in enumerate(row):
                self.hat.set_pixel(xndx, yndx, *rgb)

        self.hat.show()

    def togglePause(self) -> None:
        self.paused = not self.paused

        if self.paused:
            logger.info("paused")
            self.setStatus("paused", self.ERROR)
        else:
            logger.info("unpaused")
            self.setStatus("paused", self.OKAY)

    def toggleMode(self) -> None:
        if self.mode == "binclock":
            logger.info("setting mode to scrollclock")
            self.mode = "scrollclock"
            self.setStatus("mode", self.INFO)
        else:
            logger.info("setting mode to binclock")
            self.mode = "binclock"
            self.setStatus("mode", self.WARN)

    def setExit(self) -> None:
        self.exit = True

    def writeExit(self) -> None:
        self.writeText("Shuting down!", self.OKAY)

    def writeText(self, text: str, color: list) -> None:
        logger.info("writing text: {}".format(text))
        font = ImageFont.truetype("/usr/local/lib/pybinclock/5x7.ttf", 8)
        left, top, right, bottom = font.getbbox(text)
        text_width = right - left
        image = Image.new("P", (text_width + self.width + self.width, self.height), 0)
        draw = ImageDraw.Draw(image)
        draw.text((self.width, -1), text, font=font, fill=255)

        offset_x = 0

        while True:
            for y in range(self.height):
                for x in range(self.width):
                    if image.getpixel((x + offset_x, y)) == 255:
                        self.hat.set_pixel(x, y, *color)
                    else:
                        self.hat.set_pixel(x, y, 0, 0, 0)

            offset_x += 1
            if offset_x + self.width > image.size[0]:
                break
                # offset_x = 0
            if self.mode == "binclock":
                break

            if not self.paused:
                self.hat.show()
                sleep(0.05)


def signal_handler(signum: int, frame: Any) -> None:
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    if "leds" in globals():
        leds.hat.clear()
        leds.hat.show()
        leds.button_a.close()
        leds.button_b.close()
        leds.button_x.close()
        leds.button_y.close()
    sys.exit(0)


@logger.catch
def BinClockLEDs() -> None:
    logger.info("starting BinClockLEDs")

    global leds

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    leds = LEDController(rotation=180)

    # Initialize the current time
    ct = CurrentTime()

    # try to catch ctrl-c and exit cleanly
    try:
        # loop forever
        while True:
            # check if we should exit
            if leds.exit:
                logger.info("button x pushed - exiting")
                leds.writeExit()
                break

            if leds.paused:
                continue

            if leds.mode == "scrollclock":
                leds.writeText(ct.now.replace(microsecond=0).isoformat(), leds.OKAY)
                sleep(1)
                continue

            # Update the current time
            ct.update()
            # print(ct.now)

            leds.setStatus("okay", leds.OKAY)

            # Reset the row int to 0
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
                # lastLED = 0
                # print(i)

                # Make little-endian
                i.reverse()
                for led in range(len(i)):
                    if i[led] == 1:
                        # Turn on the LED

                        # Randomize the color
                        # hue = (time() / 10.0)
                        # rgb = [int(c * 255) for c in hsv_to_rgb(hue, 1.0, 1.0)]

                        rgb = [255, 0, 0]
                        leds.field[row][16 - led] = rgb
                    else:
                        # Turn off the LED
                        leds.field[row][16 - led] = [0, 0, 0]

                    # Set the LED (on or off) and shift light to the right
                    # unicornhatmini.set_pixel(16 - led, row, *field[row][led])
                    # lastLED = led
                # unicornhatmini.set_pixel(lastLED + 1, row, 255, 255, 255)
                row = row + 1
            # Redraw the display
            # unicornhatmini.show()
            leds.draw()
            sleep(1)
            # print()
    except KeyboardInterrupt:
        logger.info("exiting BinClockLEDs")
        leds.hat.clear()
        leds.hat.show()
        raise SystemExit
    finally:
        # Ensure LEDs are cleared on exit
        logger.info("cleaning up LEDs")
        if "leds" in locals():
            leds.hat.clear()
            leds.hat.show()


if __name__ == "__main__":
    BinClockLEDs()
