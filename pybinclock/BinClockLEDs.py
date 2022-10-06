#!/usr/bin/env python3

from colorsys import hsv_to_rgb
from unicornhatmini import UnicornHATMini
from time import sleep, time
from PyBinClock import CurrentTime

unicornhatmini = UnicornHATMini()
unicornhatmini.set_brightness(0.1)
unicornhatmini.set_rotation(180)
width, height = unicornhatmini.get_shape()

field = [[0 for x in range(width)] for y in range(height)]

ct = CurrentTime()
try:
    while True:
        ct.update()
        print(ct.now)

        row = 0
        for i in [
            ct.binary['year'],
            ct.binary['month'],
            ct.binary['day'],
            ct.binary['hour'],
            ct.binary['minute'],
            ct.binary['second']
        ]:
            lastLED = 0
            print(i)
            i.reverse()
            for led in range(len(i)):
                if i[led] == 1:
                    # hue = (time() / 10.0)
                    # [int(c * 255) for c in hsv_to_rgb(hue, 1.0, 1.0)]
                    field[row][led] = [255, 0, 0]
                else:
                    field[row][led] = (0, 0, 0)
                unicornhatmini.set_pixel(16 - led, row, *field[row][led])
                lastLED = led
            # unicornhatmini.set_pixel(lastLED + 1, row, 255, 255, 255)
            row = row + 1
        unicornhatmini.show()
        sleep(1)
        print()
except KeyboardInterrupt:
    raise SystemExit
