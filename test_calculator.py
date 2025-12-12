import unittest
from unittest.mock import patch, mock_open
import os
from datetime import datetime

# Assuming calculator.py is in the same directory and contains the Calculator class
from calculator import Calculator, LOG_FILE

class TestCalculator(unittest.TestCase):

    def setUp(self):
        """Set up a new Calculator instance before each test."""
        self.calc = Calculator()

    @patch('calculator.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_add_with_logging(self, mock_file, mock_datetime):
        """Test the add method and verify logging using mock_open."""
        # Arrange: Mock the timestamp for a predictable log entry
        mock_dt_instance = datetime(2023, 10, 27, 10, 30, 0)
        mock_datetime.now.return_value = mock_dt_instance
        timestamp = mock_dt_instance.strftime('%Y-%m-%d %H:%M:%S')
        
        # Act
        result = self.calc.add(15, 5)

        # Assert: Check the calculation result
        self.assertEqual(result, 20)

        # Assert: Check that open was called correctly
        mock_file.assert_called_once_with(LOG_FILE, 'a')
        
        # Assert: Check that the correct log entry was written
        handle = mock_file()
        expected_log = f"{timestamp}: 15 + 5 = 20\n"
        handle.write.assert_called_once_with(expected_log)

    @patch('calculator.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_subtract_with_logging(self, mock_file, mock_datetime):
        """Test the subtract method and verify logging using mock_open."""
        # Arrange
        mock_dt_instance = datetime(2023, 10, 27, 11, 0, 0)
        mock_datetime.now.return_value = mock_dt_instance
        timestamp = mock_dt_instance.strftime('%Y-%m-%d %H:%M:%S')

        # Act
        result = self.calc.subtract(10, 4)

        # Assert
        self.assertEqual(result, 6)
        mock_file.assert_called_once_with(LOG_FILE, 'a')
        handle = mock_file()
        expected_log = f"{timestamp}: 10 - 4 = 6\n"
        handle.write.assert_called_once_with(expected_log)

    @patch('calculator.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_multiply_with_logging(self, mock_file, mock_datetime):
        """Test the multiply method and verify logging using mock_open."""
        # Arrange
        mock_dt_instance = datetime(2023, 10, 27, 12, 0, 0)
        mock_datetime.now.return_value = mock_dt_instance
        timestamp = mock_dt_instance.strftime('%Y-%m-%d %H:%M:%S')

        # Act
        result = self.calc.multiply(7, 6)

        # Assert
        self.assertEqual(result, 42)
        mock_file.assert_called_once_with(LOG_FILE, 'a')
        handle = mock_file()
        expected_log = f"{timestamp}: 7 * 6 = 42\n"
        handle.write.assert_called_once_with(expected_log)

    @patch('calculator.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_divide_with_logging(self, mock_file, mock_datetime):
        """Test the divide method and verify logging using mock_open."""
        # Arrange
        mock_dt_instance = datetime(2023, 10, 27, 13, 0, 0)
        mock_datetime.now.return_value = mock_dt_instance
        timestamp = mock_dt_instance.strftime('%Y-%m-%d %H:%M:%S')

        # Act
        result = self.calc.divide(20, 4)

        # Assert
        self.assertEqual(result, 5)
        mock_file.assert_called_once_with(LOG_FILE, 'a')
        handle = mock_file()
        expected_log = f"{timestamp}: 20 / 4 = 5.0\n"
        handle.write.assert_called_once_with(expected_log)

    @patch('builtins.open', new_callable=mock_open)
    def test_divide_by_zero_does_not_log(self, mock_file):
        """Test that dividing by zero raises ValueError and does not log."""
        with self.assertRaises(ValueError):
            self.calc.divide(10, 0)
        
        # Assert that no file operation was attempted
        mock_file.assert_not_called()

    @patch('os.remove')
    @patch('os.path.exists', return_value=True)
    def test_clear_history_if_file_exists(self, mock_exists, mock_remove):
        """Test clear_history calls os.remove when the log file exists."""
        self.calc.clear_history()
        mock_exists.assert_called_once_with(LOG_FILE)
        mock_remove.assert_called_once_with(LOG_FILE)

    @patch('os.remove')
    @patch('os.path.exists', return_value=False)
    def test_clear_history_if_file_does_not_exist(self, mock_exists, mock_remove):
        """Test clear_history does not call os.remove when file doesn't exist."""
        self.calc.clear_history()
        mock_exists.assert_called_once_with(LOG_FILE)
        mock_remove.assert_not_called()

if __name__ == '__main__':
    unittest.main(verbosity=2)
