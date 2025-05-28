#!/usr/bin/env python3
"""Unit tests for CurrentTime class."""

from datetime import datetime
from unittest.mock import patch

from pybinclock.PyBinClock import CurrentTime


class TestCurrentTime:
    """Test cases for CurrentTime class."""

    def test_initialization(self):
        """Test that CurrentTime initializes correctly."""
        ct = CurrentTime()

        assert ct.now is not None
        assert isinstance(ct.now, datetime)
        assert isinstance(ct.binary, dict)
        assert all(
            key in ct.binary
            for key in ["year", "month", "day", "hour", "minute", "second"]
        )

    @patch("pybinclock.PyBinClock.datetime")
    def test_update(self, mock_datetime):
        """Test update method with fixed time."""
        # Set up mock datetime
        fixed_time = datetime(2024, 12, 25, 13, 45, 30)
        mock_datetime.now.return_value = fixed_time

        ct = CurrentTime()
        ct.update()

        assert ct.now == fixed_time
        assert mock_datetime.now.call_count >= 2  # Called in __init__ and update

    def test_hour_binary_conversion(self):
        """Test hour to binary conversion (24-hour format)."""
        ct = CurrentTime()

        # Test specific hours
        test_cases = [
            (0, [0, 0, 0, 0, 0]),  # 00:00
            (12, [0, 1, 1, 0, 0]),  # 12:00
            (23, [1, 0, 1, 1, 1]),  # 23:00
        ]

        for hour, expected in test_cases:
            ct.now = datetime(2024, 1, 1, hour, 0, 0)
            assert ct.get_hour_bin() == expected, f"Failed for hour {hour}"

    def test_minute_binary_conversion(self):
        """Test minute to binary conversion."""
        ct = CurrentTime()

        test_cases = [
            (0, [0, 0, 0, 0, 0, 0]),  # 0 minutes
            (30, [0, 1, 1, 1, 1, 0]),  # 30 minutes
            (59, [1, 1, 1, 0, 1, 1]),  # 59 minutes
        ]

        for minute, expected in test_cases:
            ct.now = datetime(2024, 1, 1, 0, minute, 0)
            assert ct.get_minute_bin() == expected, f"Failed for minute {minute}"

    def test_second_binary_conversion(self):
        """Test second to binary conversion."""
        ct = CurrentTime()

        test_cases = [
            (0, [0, 0, 0, 0, 0, 0]),  # 0 seconds
            (45, [1, 0, 1, 1, 0, 1]),  # 45 seconds
            (59, [1, 1, 1, 0, 1, 1]),  # 59 seconds
        ]

        for second, expected in test_cases:
            ct.now = datetime(2024, 1, 1, 0, 0, second)
            assert ct.get_second_bin() == expected, f"Failed for second {second}"

    def test_month_binary_conversion(self):
        """Test month to binary conversion."""
        ct = CurrentTime()

        test_cases = [
            (1, [0, 0, 0, 1]),  # January
            (6, [0, 1, 1, 0]),  # June
            (12, [1, 1, 0, 0]),  # December
        ]

        for month, expected in test_cases:
            ct.now = datetime(2024, month, 1, 0, 0, 0)
            assert ct.get_month_bin() == expected, f"Failed for month {month}"

    def test_day_binary_conversion(self):
        """Test day to binary conversion."""
        ct = CurrentTime()

        test_cases = [
            (1, [0, 0, 0, 0, 1]),  # 1st
            (15, [0, 1, 1, 1, 1]),  # 15th
            (31, [1, 1, 1, 1, 1]),  # 31st
        ]

        for day, expected in test_cases:
            ct.now = datetime(2024, 1, day, 0, 0, 0)
            assert ct.get_day_bin() == expected, f"Failed for day {day}"

    def test_year_binary_conversion(self):
        """Test year to binary conversion."""
        ct = CurrentTime()

        test_cases = [
            (2000, [1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0]),  # 2000 = 0b11111010000
            (2024, [1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0]),  # 2024 = 0b11111101000
            (2047, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),  # 2047 = 0b11111111111
        ]

        for year, expected in test_cases:
            ct.now = datetime(year, 1, 1, 0, 0, 0)
            assert ct.get_year_bin() == expected, f"Failed for year {year}"

    def test_binary_values_range(self):
        """Test that all binary values are 0 or 1."""
        ct = CurrentTime()

        for key, binary_list in ct.binary.items():
            assert all(
                bit in [0, 1] for bit in binary_list
            ), f"Invalid binary values in {key}: {binary_list}"

    def test_binary_list_lengths(self):
        """Test that binary lists have correct lengths."""
        ct = CurrentTime()

        expected_lengths = {
            "year": 11,
            "month": 4,
            "day": 5,
            "hour": 5,
            "minute": 6,
            "second": 6,
        }

        for key, expected_length in expected_lengths.items():
            actual_length = len(ct.binary[key])
            assert (
                actual_length == expected_length
            ), f"{key} has wrong length: {actual_length} (expected {expected_length})"
