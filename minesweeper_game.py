import random

class MinesweeperGame:
    """
    Core logic for the Minesweeper game.
    """
    def __init__(self, rows, cols, num_mines):
        if not (1 <= rows <= 50 and 1 <= cols <= 50 and 0 <= num_mines < rows * cols):
            raise ValueError("Invalid board dimensions or mine count.")

        self.rows = rows
        self.cols = cols
        self.num_mines = num_mines
        self.board = self._initialize_board()
        self.state = 'playing'  # 'playing', 'won', 'lost'
        self.revealed_count = 0
        self.total_safe_cells = rows * cols - num_mines

    def _initialize_board(self):
        """Creates the initial board structure."""
        # Board structure: list of lists, where each element is a dictionary
        # {'is_mine': bool, 'is_revealed': bool, 'is_flagged': bool, 'value': int (0-8)}
        board = [
            [
                {'is_mine': False, 'is_revealed': False, 'is_flagged': False, 'value': 0}
                for _ in range(self.cols)
            ]
            for _ in range(self.rows)
        ]
        return board

    def _place_mines(self, start_r, start_c):
        """Places mines randomly, ensuring the starting cell is safe."""
        
        # Create a list of all possible coordinates
        all_coords = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        
        # Exclude the starting cell and its neighbors (3x3 area)
        safe_zone = set()
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                r, c = start_r + dr, start_c + dc
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    safe_zone.add((r, c))

        mine_candidates = [coord for coord in all_coords if coord not in safe_zone]
        
        if len(mine_candidates) < self.num_mines:
            # Fallback: if the board is too small, just ensure the start cell is safe
            mine_candidates = [coord for coord in all_coords if coord != (start_r, start_c)]
            if len(mine_candidates) < self.num_mines:
                 raise RuntimeError("Cannot place required number of mines safely.")


        mine_locations = random.sample(mine_candidates, self.num_mines)

        for r, c in mine_locations:
            self.board[r][c]['is_mine'] = True

        self._calculate_neighbor_values()

    def _calculate_neighbor_values(self):
        """Calculates the number of adjacent mines for every non-mine cell."""
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.board[r][c]['is_mine']:
                    count = 0
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                                if self.board[nr][nc]['is_mine']:
                                    count += 1
                    self.board[r][c]['value'] = count

    def toggle_flag(self, r, c):
        """Toggles the flag state of a cell."""
        if self.state != 'playing' or self.board[r][c]['is_revealed']:
            return False
        
        self.board[r][c]['is_flagged'] = not self.board[r][c]['is_flagged']
        return True

    def reveal_cell(self, r, c):
        """
        Reveals a cell. Handles first click mine placement and recursive revealing.
        Returns True if the game state changed (e.g., won/lost), False otherwise.
        """
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return False
        
        cell = self.board[r][c]

        if self.state != 'playing' or cell['is_revealed'] or cell['is_flagged']:
            return False

        # Handle first click: place mines away from the starting cell
        if self.revealed_count == 0 and self.num_mines > 0:
            self._place_mines(r, c)

        if cell['is_mine']:
            self.state = 'lost'
            self._reveal_all_mines()
            return True
        
        # Recursive reveal for zero-value cells
        self._recursive_reveal(r, c)
        
        # Check win condition
        if self.revealed_count == self.total_safe_cells:
            self.state = 'won'
            return True
            
        return False

    def _recursive_reveal(self, r, c):
        """Helper function for recursive revealing of safe cells."""
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return
        
        cell = self.board[r][c]
        
        if cell['is_revealed'] or cell['is_mine'] or cell['is_flagged']:
            return

        cell['is_revealed'] = True
        self.revealed_count += 1

        # If the cell has a value > 0, stop recursion here
        if cell['value'] > 0:
            return

        # Recurse to neighbors
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                self._recursive_reveal(r + dr, c + dc)

    def _reveal_all_mines(self):
        """Reveals all mine locations when the game ends."""
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c]['is_mine']:
                    self.board[r][c]['is_revealed'] = True

    def get_cell_state(self, r, c):
        """Returns the current display state of a cell."""
        cell = self.board[r][c]
        
        if cell['is_revealed']:
            if cell['is_mine']:
                return 'mine'
            else:
                return cell['value'] # 0-8
        elif cell['is_flagged']:
            return 'flagged'
        else:
            return 'unrevealed'

    def get_game_state(self): 
        """Returns the current state of the game ('playing', 'won', 'lost')."""
        return self.state

    def get_board_dimensions(self):
        """Returns (rows, cols)."""
        return self.rows, self.cols

# Example usage (for testing purposes, not part of the class)
if __name__ == '__main__':
    game = MinesweeperGame(rows=5, cols=5, num_mines=5)
    print(f"Initial state: {game.get_game_state()}")
    
    # Simulate a first click (guaranteed safe)
    game.reveal_cell(0, 0)
    print(f"After first click. Revealed count: {game.revealed_count}")
    
    # Print a simplified view of the board
    for r in range(game.rows):
        row_display = []
        for c in range(game.cols):
            state = game.get_cell_state(r, c)
            if state == 'unrevealed':
                row_display.append('?')
            elif state == 'flagged':
                row_display.append('F')
            elif state == 'mine':
                row_display.append('M')
            else:
                row_display.append(str(state))
        print(' '.join(row_display))