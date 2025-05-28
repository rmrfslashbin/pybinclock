#!/usr/bin/env python3
"""
PyBinClock - Binary clock time conversion module.

This module provides functionality to convert current time into binary
representation for display on LED matrix or console output.
"""

from datetime import datetime
from time import sleep
from typing import Dict, List


class CurrentTime:
    """Manages current time and its binary representation."""

    def __init__(self) -> None:
        """Initialize CurrentTime with current time values."""
        self.now: datetime = datetime.now()
        self.binary: Dict[str, List[int]] = {}
        self.update()

    def update(self) -> None:
        """Update current time and recalculate all binary representations."""
        self.now = datetime.now()

        self.binary["hour"] = self.get_hour_bin()
        self.binary["minute"] = self.get_minute_bin()
        self.binary["second"] = self.get_second_bin()
        self.binary["month"] = self.get_month_bin()
        self.binary["day"] = self.get_day_bin()
        self.binary["year"] = self.get_year_bin()

    def get_hour_bin(self) -> List[int]:
        """Convert current hour to 5-bit binary representation (24-hour format).

        Returns:
            List of integers (0 or 1) representing binary digits.
        """
        return [int(x) for x in list("{0:05b}".format(self.now.hour))]

    def get_minute_bin(self) -> List[int]:
        """Convert current minute to 6-bit binary representation.

        Returns:
            List of integers (0 or 1) representing binary digits.
        """
        return [int(x) for x in list("{0:06b}".format(self.now.minute))]

    def get_second_bin(self) -> List[int]:
        """Convert current second to 6-bit binary representation.

        Returns:
            List of integers (0 or 1) representing binary digits.
        """
        return [int(x) for x in list("{0:06b}".format(self.now.second))]

    def get_month_bin(self) -> List[int]:
        """Convert current month to 4-bit binary representation.

        Returns:
            List of integers (0 or 1) representing binary digits.
        """
        return [int(x) for x in list("{0:04b}".format(self.now.month))]

    def get_day_bin(self) -> List[int]:
        """Convert current day to 5-bit binary representation.

        Returns:
            List of integers (0 or 1) representing binary digits.
        """
        return [int(x) for x in list("{0:05b}".format(self.now.day))]

    def get_year_bin(self) -> List[int]:
        """Convert current year to 11-bit binary representation.

        Returns:
            List of integers (0 or 1) representing binary digits.
        """
        return [int(x) for x in list("{0:011b}".format(self.now.year))]


def PyBinClock() -> None:
    """Main function to run the binary clock in console mode.

    Continuously updates and displays the current time in binary format
    to the console. Useful for testing and debugging.
    """
    ct = CurrentTime()

    try:
        while True:
            ct.update()
            print(f"\n{ct.now.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Year:   {' '.join(map(str, ct.binary['year']))}")
            print(f"Month:  {' '.join(map(str, ct.binary['month']))}")
            print(f"Day:    {' '.join(map(str, ct.binary['day']))}")
            print(f"Hour:   {' '.join(map(str, ct.binary['hour']))}")
            print(f"Minute: {' '.join(map(str, ct.binary['minute']))}")
            print(f"Second: {' '.join(map(str, ct.binary['second']))}")
            sleep(1)
    except KeyboardInterrupt:
        print("\nBinary clock stopped.")


if __name__ == "__main__":
    PyBinClock()
