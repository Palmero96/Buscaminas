import tkinter as tk
from minesweeper_gui import MinesweeperGUI

def main():
    root = tk.Tk()
    app = MinesweeperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()