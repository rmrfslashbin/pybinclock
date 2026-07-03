#!/usr/bin/env python3
"""Unit tests for the unified LED controller."""

from unittest.mock import Mock, patch

from pybinclock.config import Config
from pybinclock.PyBinClock import CurrentTime


class TestMockHardware:
    """Test the mock hardware used for hardware-free testing."""

    def test_mock_hat(self):
        """MockHAT stores brightness, rotation, shape and pixels."""
        from pybinclock.BinClockLEDs import MockHAT

        hat = MockHAT()
        assert hat.brightness == 0.1
        assert hat.rotation == 0
        assert hat.get_shape() == (17, 7)

        hat.set_pixel(5, 3, 255, 0, 0)
        assert hat.pixels[(5, 3)] == (255, 0, 0)

        hat.clear()
        assert len(hat.pixels) == 0

    def test_mock_button(self):
        """MockButton records its pin and callback."""
        from pybinclock.BinClockLEDs import MockButton

        button = MockButton(5)
        assert button.pin == 5
        assert button.when_pressed is None

        def callback():
            pass

        button.when_pressed = callback
        assert button.when_pressed == callback


class TestLEDControllerMockHardware:
    """Test the controller running against mock hardware."""

    @patch("pybinclock.BinClockLEDs.HARDWARE_AVAILABLE", False)
    def test_initialization(self):
        """Controller initializes with mock hardware and a blank field."""
        from pybinclock.BinClockLEDs import LEDController

        controller = LEDController(Config())

        assert controller.hat is not None
        assert hasattr(controller.hat, "pixels")  # MockHAT
        assert controller.width == 17
        assert controller.height == 7
        assert len(controller.field) == 7
        assert len(controller.field[0]) == 17

    @patch("pybinclock.BinClockLEDs.HARDWARE_AVAILABLE", False)
    def test_buttons_enabled_by_default(self):
        """Buttons are created (as mocks) when enable_buttons is True."""
        from pybinclock.BinClockLEDs import LEDController

        controller = LEDController(Config())
        assert set(controller.buttons) == {"a", "b", "x", "y"}

    @patch("pybinclock.BinClockLEDs.HARDWARE_AVAILABLE", False)
    def test_buttons_disabled(self):
        """No buttons are created when enable_buttons is False (service mode)."""
        from pybinclock.BinClockLEDs import LEDController

        config = Config()
        config.enable_buttons = False
        controller = LEDController(config)
        assert controller.buttons == {}

    @patch("pybinclock.BinClockLEDs.HARDWARE_AVAILABLE", False)
    def test_context_manager_cleans_up(self):
        """Exiting the context manager clears the display."""
        from pybinclock.BinClockLEDs import LEDController

        with LEDController(Config()) as controller:
            assert controller is not None
        # After cleanup the mock HAT has been cleared.
        assert controller.hat.pixels == {}

    @patch("pybinclock.BinClockLEDs.HARDWARE_AVAILABLE", False)
    def test_set_status_and_draw(self):
        """set_status updates the indicator color and renders it."""
        from pybinclock.BinClockLEDs import LEDController

        controller = LEDController(Config())
        controller.set_status("okay", [1, 2, 3])
        assert controller.status["okay"][2] == [1, 2, 3]
        # Status pixel okay is at (x=0, y=6).
        assert controller.hat.pixels[(0, 6)] == (1, 2, 3)

    @patch("pybinclock.BinClockLEDs.HARDWARE_AVAILABLE", False)
    def test_toggle_pause(self):
        """toggle_pause flips the paused flag."""
        from pybinclock.BinClockLEDs import LEDController

        controller = LEDController(Config())
        assert controller.paused is False
        controller.toggle_pause()
        assert controller.paused is True
        controller.toggle_pause()
        assert controller.paused is False

    @patch("pybinclock.BinClockLEDs.HARDWARE_AVAILABLE", False)
    def test_toggle_mode(self):
        """toggle_mode switches between binclock and scrollclock."""
        from pybinclock.BinClockLEDs import LEDController

        controller = LEDController(Config())
        assert controller.mode == "binclock"
        controller.toggle_mode()
        assert controller.mode == "scrollclock"
        controller.toggle_mode()
        assert controller.mode == "binclock"

    @patch("pybinclock.BinClockLEDs.HARDWARE_AVAILABLE", False)
    def test_update_binary_display_does_not_mutate_input(self):
        """Rendering the time must not mutate the CurrentTime binary lists."""
        from pybinclock.BinClockLEDs import LEDController

        controller = LEDController(Config())
        ct = CurrentTime()
        original = {k: list(v) for k, v in ct.binary.items()}

        controller.update_binary_display(ct)

        assert ct.binary == original  # not reversed in place

    @patch("pybinclock.BinClockLEDs.HARDWARE_AVAILABLE", False)
    def test_update_binary_display_lights_expected_pixels(self):
        """A set bit lights the on_color; a clear bit uses off_color."""
        from pybinclock.BinClockLEDs import LEDController

        config = Config()
        config.colors.on_color = [255, 0, 0]
        config.colors.off_color = [0, 0, 0]
        controller = LEDController(config)

        ct = CurrentTime()
        # Force a known hour value: 1 -> 5 bits 00001, LSB at far right (x=16).
        ct.binary["hour"] = [0, 0, 0, 0, 1]
        controller.update_binary_display(ct)

        # Hour is row 3; the LSB (x=16) should be on.
        assert controller.field[3][16] == [255, 0, 0]
        assert controller.field[3][15] == [0, 0, 0]


class TestLEDControllerRealHardwarePath:
    """Test the hardware code path with the hardware libraries patched out."""

    @patch("pybinclock.BinClockLEDs.HARDWARE_AVAILABLE", True)
    @patch("pybinclock.BinClockLEDs.Button")
    @patch("pybinclock.BinClockLEDs.UnicornHATMini")
    def test_hardware_initialization_with_buttons(self, mock_hat_class, mock_button):
        """Real hardware path wires the HAT and the four buttons."""
        from pybinclock.BinClockLEDs import LEDController

        mock_hat = Mock()
        mock_hat.get_shape.return_value = (17, 7)
        mock_hat_class.return_value = mock_hat

        controller = LEDController(Config())
        assert controller is not None

        mock_hat.set_brightness.assert_called_once()
        mock_hat.set_rotation.assert_called_once()
        # Four buttons: a, b, x, y.
        assert mock_button.call_count == 4
        called_pins = {call.args[0] for call in mock_button.call_args_list}
        assert called_pins == {5, 6, 16, 24}
