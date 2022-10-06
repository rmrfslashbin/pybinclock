#!/usr/bin/env python3

from datetime import date, datetime
from time import sleep


class CurrentTime:
    def __init__(self):
        self.now = None
        self.binary = {}
        self.update()

    def update(self):
        self.now = datetime.now()
        self.now = datetime.now()
        if self.now.year > 2048:
            raise ValueError("Year is too high")

        self.binary["hour"] = self.get_hour_bin()
        self.binary["minute"] = self.get_minute_bin()
        self.binary["second"] = self.get_second_bin()
        self.binary["month"] = self.get_month_bin()
        self.binary["day"] = self.get_day_bin()
        self.binary["year"] = self.get_year_bin()

    def get_hour_bin(self):
        return [int(x) for x in list('{0:05b}'.format(self.now.hour))]

    def get_minute_bin(self):
        return [int(x) for x in list('{0:06b}'.format(self.now.minute))]

    def get_second_bin(self):
        return [int(x) for x in list('{0:06b}'.format(self.now.second))]

    def get_month_bin(self):
        return [int(x) for x in list('{0:04b}'.format(self.now.month))]

    def get_day_bin(self):
        return [int(x) for x in list('{0:05b}'.format(self.now.day))]

    def get_year_bin(self):
        return [int(x) for x in list('{0:011b}'.format(self.now.year))]


def PyBinClock():
    ct = CurrentTime()
    while True:
        ct.update()
        print(ct.now)
        print(ct.binary['year'])
        print(ct.binary['month'])
        print(ct.binary['day'])
        print(ct.binary['hour'])
        print(ct.binary['minute'])
        print(ct.binary['second'])
        sleep(1)


if __name__ == "__main__":
    PyBinClock()
