#!/usr/bin/env python3
"""Unit tests for LED controller classes."""

from unittest.mock import Mock, patch, MagicMock
import pytest

from pybinclock.config import Config


class TestLEDControllerNoButtons:
    """Test cases for LEDControllerNoButtons class."""
    
    @patch('pybinclock.BinClockLEDs_nobuttons.UnicornHATMini')
    def test_initialization(self, mock_hat_class):
        """Test that LEDControllerNoButtons initializes correctly."""
        from pybinclock.BinClockLEDs_nobuttons import LEDControllerNoButtons
        
        # Setup mock
        mock_hat = Mock()
        mock_hat.get_shape.return_value = (17, 7)
        mock_hat_class.return_value = mock_hat
        
        # Create controller
        controller = LEDControllerNoButtons(rotation=180, brightness=0.1)
        
        # Verify initialization
        assert controller.hat == mock_hat
        assert controller.width == 17
        assert controller.height == 7
        assert controller.field is not None
        assert len(controller.field) == 7
        assert len(controller.field[0]) == 17
        
        # Verify HAT configuration
        mock_hat.set_brightness.assert_called_once_with(0.1)
        mock_hat.set_rotation.assert_called_once_with(180)
    
    @patch('pybinclock.BinClockLEDs_nobuttons.UnicornHATMini')
    def test_context_manager(self, mock_hat_class):
        """Test context manager functionality."""
        from pybinclock.BinClockLEDs_nobuttons import LEDControllerNoButtons
        
        mock_hat = Mock()
        mock_hat.get_shape.return_value = (17, 7)
        mock_hat_class.return_value = mock_hat
        
        with LEDControllerNoButtons() as controller:
            assert controller is not None
        
        # Verify cleanup
        mock_hat.clear.assert_called_once()
        mock_hat.show.assert_called()
    
    @patch('pybinclock.BinClockLEDs_nobuttons.UnicornHATMini')
    def test_set_status(self, mock_hat_class):
        """Test status indicator setting."""
        from pybinclock.BinClockLEDs_nobuttons import LEDControllerNoButtons
        
        mock_hat = Mock()
        mock_hat.get_shape.return_value = (17, 7)
        mock_hat_class.return_value = mock_hat
        
        controller = LEDControllerNoButtons()
        
        # Test setting status
        test_color = [255, 0, 0]
        controller.setStatus("heartbeat", test_color)
        
        # Verify the status color was updated
        assert controller.status["heartbeat"][2] == test_color
        
        # Verify draw was called
        mock_hat.set_pixel.assert_called()
        mock_hat.show.assert_called()
    
    @patch('pybinclock.BinClockLEDs_nobuttons.UnicornHATMini')
    def test_draw(self, mock_hat_class):
        """Test draw functionality."""
        from pybinclock.BinClockLEDs_nobuttons import LEDControllerNoButtons
        
        mock_hat = Mock()
        mock_hat.get_shape.return_value = (17, 7)
        mock_hat_class.return_value = mock_hat
        
        controller = LEDControllerNoButtons()
        
        # Set a pixel
        controller.field[0][0] = [255, 255, 255]
        controller.draw()
        
        # Verify pixel was set
        mock_hat.set_pixel.assert_any_call(0, 0, 255, 255, 255)
        mock_hat.show.assert_called()


class TestLEDControllerWithButtons:
    """Test cases for main LEDController class with buttons."""
    
    @patch('pybinclock.BinClockLEDs.Button')
    @patch('pybinclock.BinClockLEDs.UnicornHATMini')
    def test_initialization_with_buttons(self, mock_hat_class, mock_button_class):
        """Test LEDController initialization with buttons."""
        from pybinclock.BinClockLEDs import LEDController
        
        # Setup mocks
        mock_hat = Mock()
        mock_hat.get_shape.return_value = (17, 7)
        mock_hat_class.return_value = mock_hat
        
        mock_buttons = [Mock() for _ in range(4)]
        mock_button_class.side_effect = mock_buttons
        
        # Create controller
        controller = LEDController(rotation=90)
        
        # Verify button creation
        assert mock_button_class.call_count == 4
        mock_button_class.assert_any_call(5)  # button A
        mock_button_class.assert_any_call(6)  # button B
        mock_button_class.assert_any_call(16) # button X
        mock_button_class.assert_any_call(24) # button Y
        
        # Verify button callbacks were set
        assert mock_buttons[0].when_pressed is not None
        assert mock_buttons[1].when_pressed is not None
        assert mock_buttons[2].when_pressed is not None
    
    @patch('pybinclock.BinClockLEDs.Button')
    @patch('pybinclock.BinClockLEDs.UnicornHATMini')
    def test_toggle_pause(self, mock_hat_class, mock_button_class):
        """Test pause toggle functionality."""
        from pybinclock.BinClockLEDs import LEDController
        
        mock_hat = Mock()
        mock_hat.get_shape.return_value = (17, 7)
        mock_hat_class.return_value = mock_hat
        
        controller = LEDController()
        
        # Test toggling pause
        assert controller.paused is False
        controller.togglePause()
        assert controller.paused is True
        controller.togglePause()
        assert controller.paused is False
    
    @patch('pybinclock.BinClockLEDs.Button')
    @patch('pybinclock.BinClockLEDs.UnicornHATMini')
    def test_toggle_mode(self, mock_hat_class, mock_button_class):
        """Test mode toggle functionality."""
        from pybinclock.BinClockLEDs import LEDController
        
        mock_hat = Mock()
        mock_hat.get_shape.return_value = (17, 7)
        mock_hat_class.return_value = mock_hat
        
        controller = LEDController()
        
        # Test toggling mode
        assert controller.mode == "binclock"
        controller.toggleMode()
        assert controller.mode == "scrollclock"
        controller.toggleMode()
        assert controller.mode == "binclock"


class TestImprovedLEDController:
    """Test cases for improved LED controller with config support."""
    
    def test_mock_hat(self):
        """Test MockHAT functionality."""
        from pybinclock.BinClockLEDs_improved import MockHAT
        
        hat = MockHAT()
        
        # Test initialization
        assert hat.brightness == 0.1
        assert hat.rotation == 0
        assert hat.get_shape() == (17, 7)
        
        # Test pixel setting
        hat.set_pixel(5, 3, 255, 0, 0)
        assert hat.pixels[(5, 3)] == (255, 0, 0)
        
        # Test clear
        hat.clear()
        assert len(hat.pixels) == 0
    
    def test_mock_button(self):
        """Test MockButton functionality."""
        from pybinclock.BinClockLEDs_improved import MockButton
        
        button = MockButton(5)
        assert button.pin == 5
        assert button.when_pressed is None
        
        # Test callback assignment
        def callback():
            pass
        button.when_pressed = callback
        assert button.when_pressed == callback
    
    @patch('pybinclock.BinClockLEDs_improved.HARDWARE_AVAILABLE', False)
    def test_controller_with_mock_hardware(self):
        """Test controller with mock hardware."""
        from pybinclock.BinClockLEDs_improved import LEDController
        
        config = Config()
        controller = LEDController(config)
        
        # Verify mock hardware is used
        assert controller.hat is not None
        assert hasattr(controller.hat, 'pixels')  # MockHAT has pixels attribute
        
        # Test basic operations
        controller.reset()
        controller.set_status('okay', [0, 255, 0])
        controller.draw()