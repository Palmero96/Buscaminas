from datetime import datetime
import os

LOG_FILE = 'history.log'

class Calculator:
    """A simple calculator class with history logging and basic arithmetic operations."""

    def __init__(self):
        pass

    def _get_timestamp(self):
        """Returns the current formatted timestamp."""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _log_operation(self, operand1, operator, operand2, result):
        """Logs the operation to the history file."""
        timestamp = self._get_timestamp()
        
        # Rely on Python's default string conversion for logging operands and results
        log_entry = f"{timestamp}: {operand1} {operator} {operand2} = {result}\n"
        
        try:
            # Use 'a' for append mode
            with open(LOG_FILE, 'a') as f:
                f.write(log_entry)
        except IOError:
            # Handle potential file writing errors silently
            pass 

    def add(self, a, b):
        result = a + b
        self._log_operation(a, '+', b, result)
        return result

    def subtract(self, a, b):
        result = a - b
        self._log_operation(a, '-', b, result)
        return result

    def multiply(self, a, b):
        result = a * b
        self._log_operation(a, '*', b, result)
        return result

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self._log_operation(a, '/', b, result)
        return result

    def clear_history(self):
        """Clears the history log file."""
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
