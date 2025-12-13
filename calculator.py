class Calculator:
    """
    Handles the business logic of the calculator.
    It is completely independent of the GUI.
    """
    def __init__(self):
        self.expression = ""

    def press(self, button_value):
        """Appends a value to the current expression."""
        self.expression += str(button_value)

    def clear(self):
        """Clears the current expression."""
        self.expression = ""

    def calculate(self):
        """
        Evaluates the current expression.
        Returns the result as a string.
        Raises SyntaxError or ZeroDivisionError on failure.
        """
        try:
            # Using eval is simple for this PoC, but not safe for production apps
            result = str(eval(self.expression))
            self.expression = result
            return result
        except (SyntaxError, ZeroDivisionError):
            # Re-raise the specific exception to be handled by the caller
            self.expression = ""
            raise
        except Exception as e:
            # For other unexpected errors, wrap them
            self.expression = ""
            raise RuntimeError(f"An unexpected error occurred: {e}") from e


def main():
    """Initializes and runs the Tkinter GUI application."""
    import tkinter as tk
    from tkinter import messagebox

    class CalculatorApp:
        """
        A simple calculator application built with Tkinter.
        This class serves as the initial proof-of-concept before
        the project is pivoted to a Minesweeper game.
        """
        def __init__(self, root):
            self.calculator = Calculator() # Logic handler
            self.root = root
            self.root.title("Calculator")
            self.root.geometry("300x400")
            self.root.resizable(False, False)

            self.display_text = tk.StringVar()

            self._create_widgets()

        def _create_widgets(self):
            """Creates and lays out the GUI widgets for the calculator."""
            display_frame = tk.Frame(self.root, bd=10, relief=tk.RIDGE)
            display_frame.pack(pady=10)

            display_entry = tk.Entry(display_frame, textvariable=self.display_text, font=('arial', 20, 'bold'), bd=10, bg="#eee", justify='right', state='readonly')
            display_entry.pack()

            button_frame = tk.Frame(self.root)
            button_frame.pack()

            buttons = [
                '7', '8', '9', '/',
                '4', '5', '6', '*',
                '1', '2', '3', '-',
                'C', '0', '=', '+'
            ]

            row_val = 0
            col_val = 0
            for button_text in buttons:
                if button_text == '=':
                    btn = tk.Button(button_frame, text=button_text, padx=20, pady=20, font=('arial', 14, 'bold'), command=self._on_equals_press)
                elif button_text == 'C':
                    btn = tk.Button(button_frame, text=button_text, padx=20, pady=20, font=('arial', 14, 'bold'), command=self._on_clear_press)
                else:
                    btn = tk.Button(button_frame, text=button_text, padx=20, pady=20, font=('arial', 14, 'bold'), command=lambda text=button_text: self._on_button_press(text))

                btn.grid(row=row_val, column=col_val, sticky="nsew")
                col_val += 1
                if col_val > 3:
                    col_val = 0
                    row_val += 1

        def _on_button_press(self, value):
            """Handles clicks for numbers and operators."""
            self.calculator.press(value)
            self.display_text.set(self.calculator.expression)

        def _on_equals_press(self):
            """Calculates the result of the expression."""
            try:
                result = self.calculator.calculate()
                self.display_text.set(result)
            except (SyntaxError, ZeroDivisionError) as e:
                messagebox.showerror("Error", f"Invalid Expression: {e}")
                self.display_text.set("")
            except Exception as e:
                messagebox.showerror("Error", "An error occurred")
                self.display_text.set("")

        def _on_clear_press(self):
            """Clears the current expression and display."""
            self.calculator.clear()
            self.display_text.set("")

    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    # Main execution block
    main()
