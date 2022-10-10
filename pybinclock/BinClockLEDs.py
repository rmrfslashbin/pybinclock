#!/usr/bin/env python3

from colorsys import hsv_to_rgb
from gpiozero import Button
from unicornhatmini import UnicornHATMini
from time import sleep, time
from loguru import logger
from pybinclock.PyBinClock import CurrentTime


class LEDController:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
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
        self.field = []

        self.OKAY = [0, 255, 0]
        self.ERROR = [255, 0, 0]
        self.WARN = [255, 255, 0]
        self.INFO = [0, 0, 255]

        self.button_a = Button(5)
        self.button_b = Button(6)
        self.button_x = Button(16)
        self.button_y = Button(24)

        self.button_a.when_pressed = self.togglePause

        self.paused = False

        self.status = {}
        self.status['okay'] = [0, 6, self.INFO]  # x, y, [r, g, b]
        self.status['paused'] = [1, 6, self.OKAY]  # x, y, [r, g, b]

        self.reset()

    def reset(self) -> None:
        # Initialize the display
        self.field = [
            [[0, 0, 0] for x in range(17)]
            for y in range(7)
        ]
        self.draw()

    def setStatus(self, status: str, color: list) -> None:
        if status == 'okay':
            self.status['okay'] = [0, 6, color]  # x, y, [r, g, b]

        if status == 'paused':
            logger.info('Setting paused')
            self.status['paused'] = [1, 6, color]

        self.draw()

    def draw(self) -> None:
        for s in self.status:
            self.field[self.status[s][1]
                       ][self.status[s][0]] = self.status[s][2]

        for yndx, row in enumerate(self.field):
            for xndx, rgb in enumerate(row):
                self.hat.set_pixel(xndx, yndx, *rgb)

        self.hat.show()

    def togglePause(self) -> None:
        self.paused = not self.paused

        if self.paused:
            logger.info('Paused')
            self.setStatus('paused', self.ERROR)
        else:
            logger.info('Unpaused')
            self.setStatus('paused', self.OKAY)


@logger.catch
def BinClockLEDs():
    logger.info("Starting BinClockLEDs")

    leds = LEDController(rotation=180)

    # Initialize the current time
    ct = CurrentTime()

    # try to catch ctrl-c and exit cleanly
    try:
        # loop forever
        while True:
            if leds.paused:
                continue
            # Update the current time
            ct.update()
            # print(ct.now)

            leds.setStatus('okay', leds.OKAY)

            # Reset the row int to 0
            row = 0
            # Build the display based on the current time
            for i in [
                ct.binary['year'],   # row 0
                ct.binary['month'],  # row 1
                ct.binary['day'],    # row 2
                ct.binary['hour'],   # row 3
                ct.binary['minute'],  # row 4
                ct.binary['second']  # row 5
            ]:
                #lastLED = 0
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

                    # Set the LED (on or off) and shift light to the right (little endian)
                    #unicornhatmini.set_pixel(16 - led, row, *field[row][led])
                    #lastLED = led
                # unicornhatmini.set_pixel(lastLED + 1, row, 255, 255, 255)
                row = row + 1
            # Redraw the display
            # unicornhatmini.show()
            leds.draw()
            sleep(1)
            # print()
    except KeyboardInterrupt:
        logger.info("Exiting BinClockLEDs")
        raise SystemExit


if __name__ == '__main__':
    BinClockLEDs()
