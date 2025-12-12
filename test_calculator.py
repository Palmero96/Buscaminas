import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
from calculator import Calculator, LOG_FILE

class TestCalculatorOperations(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()

    def test_add_integers(self):
        self.assertEqual(self.calc.add(5, 3), 8)

    def test_subtract_floats(self):
        self.assertAlmostEqual(self.calc.subtract(10.5, 4.2), 6.3)

    def test_multiply_negative(self):
        self.assertEqual(self.calc.multiply(-2, 5), -10)

    def test_divide_success(self):
        self.assertEqual(self.calc.divide(10, 2), 5)

    def test_divide_by_zero(self):
        with self.assertRaisesRegex(ValueError, "Cannot divide by zero"):
            self.calc.divide(10, 0)

class TestHistoryManagement(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()
        # Ensure log file is clean before each test
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)

    def tearDown(self):
        # Clean up after tests
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)

    def _setup_datetime_mock(self, mock_datetime, timestamp_str):
        """Helper to set up the mock chain for datetime.now().strftime()."""
        # Mock the datetime object returned by datetime.now()
        mock_now = MagicMock()
        mock_datetime.now.return_value = mock_now
        
        # Mock the strftime method on the returned object
        mock_now.strftime.return_value = timestamp_str

    @patch('calculator.open', new_callable=mock_open)
    @patch('calculator.datetime')
    def test_log_operation_success(self, mock_datetime, mock_file):
        # Setup mock timestamp
        expected_timestamp = '2023-10-27 14:30:00'
        self._setup_datetime_mock(mock_datetime, expected_timestamp)
        
        # Perform operation
        self.calc.add(5.5, 3.0)
        
        # Define expected log entry
        expected_log_entry = f'{expected_timestamp}: 5.5 + 3.0 = 8.5\n'
        
        # Assert file was opened correctly
        mock_file.assert_called_once_with(LOG_FILE, 'a')
        
        # Assert content was written correctly
        mock_file().write.assert_called_once_with(expected_log_entry)

    @patch('calculator.open', new_callable=mock_open)
    @patch('calculator.datetime')
    def test_log_operation_subtraction_format(self, mock_datetime, mock_file):
        # Setup mock timestamp
        expected_timestamp = '2023-10-27 15:00:00'
        self._setup_datetime_mock(mock_datetime, expected_timestamp)
        
        # Perform operation
        self.calc.subtract(10, 4)
        
        # Define expected log entry
        expected_log_entry = f'{expected_timestamp}: 10 - 4 = 6\n'
        
        # Assert content was written correctly
        mock_file().write.assert_called_once_with(expected_log_entry)

    def test_clear_history_removes_file(self):
        # Create a dummy log file
        with open(LOG_FILE, 'w') as f:
            f.write("Test entry")
        
        self.assertTrue(os.path.exists(LOG_FILE))
        
        self.calc.clear_history()
        
        self.assertFalse(os.path.exists(LOG_FILE))

    def test_clear_history_no_file_exists(self):
        # Ensure file does not exist
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
            
        # Should run without error
        self.calc.clear_history()
        self.assertFalse(os.path.exists(LOG_FILE))