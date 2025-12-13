import tkinter as tk
from tkinter import messagebox
from minesweeper_game import MinesweeperGame

class MinesweeperGUI:
    
    CONFIGS = {
        "Beginner": (9, 9, 10),
        "Intermediate": (16, 16, 40),
        "Expert": (16, 30, 99)
    }
    
    # Colors for numbers 1 through 8
    NUMBER_COLORS = {
        1: 'blue', 2: 'green', 3: 'red', 4: 'darkblue',
        5: 'darkred', 6: 'teal', 7: 'black', 8: 'gray'
    }
    
    def __init__(self, master):
        self.master = master
        master.title("Minesweeper")
        
        self.game = None
        self.buttons = []
        
        self.main_frame = tk.Frame(master)
        self.main_frame.pack(padx=10, pady=10)
        
        self.status_label = tk.Label(self.main_frame, text="Select Difficulty", font=('Arial', 14))
        self.status_label.pack(pady=5)
        
        self.start_screen()

    def start_screen(self):
        """Displays the difficulty selection screen."""
        
        # Clear previous widgets if any
        for widget in self.main_frame.winfo_children():
            if widget != self.status_label:
                widget.destroy()
        
        self.status_label.config(text="Select Difficulty", fg='black')
        
        config_frame = tk.Frame(self.main_frame)
        config_frame.pack(pady=20)
        
        for name, (r, c, m) in self.CONFIGS.items():
            btn = tk.Button(config_frame, text=f"{name}\n({r}x{c}, {m} mines)", 
                            command=lambda r=r, c=c, m=m: self.start_game(r, c, m),
                            width=15, height=3)
            btn.pack(side=tk.LEFT, padx=10)

    def start_game(self, rows, cols, num_mines):
        """Initializes the game and switches to the game board view."""
        try:
            self.game = MinesweeperGame(rows, cols, num_mines)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        self.rows = rows
        self.cols = cols
        
        # Clear configuration screen widgets
        for widget in self.main_frame.winfo_children():
            if widget != self.status_label:
                widget.destroy()
        
        self.status_label.config(text="Game in Progress", fg='black')
        self.create_board_gui()

    def create_board_gui(self):
        """Creates the grid of buttons for the game board."""
        
        board_frame = tk.Frame(self.main_frame)
        board_frame.pack()
        
        self.buttons = []
        for r in range(self.rows):
            row_buttons = []
            for c in range(self.cols):
                btn = tk.Button(board_frame, text=" ", width=2, height=1, 
                                command=lambda r=r, c=c: self.handle_click(r, c, 'left'),
                                relief=tk.RAISED, bg='lightgray')
                
                # Bind right click (Button-3) for flagging
                btn.bind("<Button-3>", lambda event, r=r, c=c: self.handle_click(r, c, 'right'))
                
                btn.grid(row=r, column=c)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)
            
        # Add restart button
        restart_btn = tk.Button(self.main_frame, text="Restart", command=self.start_screen)
        restart_btn.pack(pady=10)

    def handle_click(self, r, c, button_type):
        """Handles user interaction (left click to reveal, right click to flag)."""
        if self.game.get_game_state() != 'playing':
            return

        if button_type == 'left':
            game_state_changed = self.game.reveal_cell(r, c)
        elif button_type == 'right':
            self.game.toggle_flag(r, c)
            game_state_changed = False # Flagging doesn't change game state immediately

        self.update_gui()
        
        if game_state_changed:
            self.end_game_message()

    def update_gui(self):
        """Updates the appearance of all buttons based on the current game state."""
        for r in range(self.rows):
            for c in range(self.cols):
                state = self.game.get_cell_state(r, c)
                btn = self.buttons[r][c]
                
                if state == 'unrevealed':
                    btn.config(text=" ", relief=tk.RAISED, bg='lightgray', fg='black')
                elif state == 'flagged':
                    btn.config(text="F", relief=tk.RAISED, bg='lightgray', fg='red')
                elif state == 'mine':
                    btn.config(text="*", relief=tk.SUNKEN, bg='red', fg='black')
                elif state == 0:
                    btn.config(text=" ", relief=tk.SUNKEN, bg='white')
                elif isinstance(state, int) and 1 <= state <= 8:
                    btn.config(text=str(state), relief=tk.SUNKEN, bg='white', 
                               fg=self.NUMBER_COLORS.get(state, 'black'), font=('Arial', 8, 'bold'))

    def end_game_message(self):
        """Displays the win/loss message and updates the status label."""
        state = self.game.get_game_state()
        
        if state == 'won':
            self.status_label.config(text="YOU WON!", fg='green')
            messagebox.showinfo("Game Over", "Congratulations! You cleared the field.")
        elif state == 'lost':
            self.status_label.config(text="GAME OVER", fg='red')
            messagebox.showinfo("Game Over", "KABOOM! You hit a mine.")
            
        # Ensure all mines are revealed on loss
        self.update_gui()

if __name__ == '__main__':
    root = tk.Tk()
    app = MinesweeperGUI(root)
    root.mainloop()