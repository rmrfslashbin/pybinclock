#!/usr/bin/env python3

from colorsys import hsv_to_rgb
from unicornhatmini import UnicornHATMini
from time import sleep, time
from pybinclock.PyBinClock import CurrentTime


def BinClockLEDs():
    print("Starting BinClockLEDs")
    # Set up the Unicorn HAT Mini
    unicornhatmini = UnicornHATMini()
    unicornhatmini.set_brightness(0.1)
    # Rotate the display 180 degrees
    unicornhatmini.set_rotation(180)

    # Get the width and high of the display
    width, height = unicornhatmini.get_shape()

    # Initialize the display
    field = [[0 for x in range(width)] for y in range(height)]

    # Initialize the current time
    ct = CurrentTime()

    # try to catch ctrl-c and exit cleanly
    try:
        # loop forever
        while True:
            # Update the current time
            ct.update()
            # print(ct.now)

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
                        field[row][led] = rgb
                    else:
                        # Turn off the LED
                        field[row][led] = (0, 0, 0)

                    # Set the LED (on or off) and shift light to the right (little endian)
                    unicornhatmini.set_pixel(16 - led, row, *field[row][led])
                    #lastLED = led
                # unicornhatmini.set_pixel(lastLED + 1, row, 255, 255, 255)
                row = row + 1
            # Redraw the display
            unicornhatmini.show()
            sleep(1)
            # print()
    except KeyboardInterrupt:
        print("Exiting BinClockLEDs")
        raise SystemExit


if __name__ == '__main__':
    BinClockLEDs()
