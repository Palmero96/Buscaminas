import unittest

# Import the logic class, not the GUI app
from calculator import Calculator

class TestCalculator(unittest.TestCase):

    def setUp(self):
        """Set up a new Calculator instance before each test."""
        self.calc = Calculator()

    def test_initialization(self):
        """Test if the calculator initializes with an empty expression."""
        self.assertEqual(self.calc.expression, "")

    def test_press(self):
        """Test pressing number and operator buttons updates the expression."""
        self.calc.press('7')
        self.assertEqual(self.calc.expression, "7")

        self.calc.press('+')
        self.assertEqual(self.calc.expression, "7+")

        self.calc.press('5')
        self.assertEqual(self.calc.expression, "7+5")

    def test_clear(self):
        """Test that the clear method resets the expression."""
        self.calc.expression = "123+456"
        self.calc.clear()
        self.assertEqual(self.calc.expression, "")

    def test_calculate_success(self):
        """Test a successful calculation."""
        self.calc.expression = "9*3"
        result = self.calc.calculate()
        self.assertEqual(result, "27")
        # The expression should now hold the result
        self.assertEqual(self.calc.expression, "27")

    def test_calculate_division_by_zero(self):
        """Test that division by zero raises an error and clears the expression."""
        self.calc.expression = "5/0"
        with self.assertRaises(ZeroDivisionError):
            self.calc.calculate()
        # The expression should be cleared after an error
        self.assertEqual(self.calc.expression, "")

    def test_calculate_syntax_error(self):
        """Test that a syntax error raises an error and clears the expression."""
        self.calc.expression = "5+*3"
        with self.assertRaises(SyntaxError):
            self.calc.calculate()
        # The expression should be cleared after an error
        self.assertEqual(self.calc.expression, "")

    def test_chain_calculation(self):
        """Test that calculations can be chained."""
        self.calc.press("3")
        self.calc.press("*")
        self.calc.press("3")
        self.assertEqual(self.calc.calculate(), "9")
        self.calc.press("+")
        self.calc.press("1")
        self.assertEqual(self.calc.calculate(), "10")
        self.assertEqual(self.calc.expression, "10")

if __name__ == '__main__':
    unittest.main()
