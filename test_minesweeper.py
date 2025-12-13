import unittest
import random
from minesweeper_game import MinesweeperGame

class TestMinesweeperGame(unittest.TestCase):

    def test_initialization(self):
        game = MinesweeperGame(rows=5, cols=5, num_mines=5)
        self.assertEqual(game.rows, 5)
        self.assertEqual(game.cols, 5)
        self.assertEqual(game.num_mines, 5)
        self.assertEqual(game.get_game_state(), 'playing')
        self.assertEqual(game.total_safe_cells, 20)
        
        # Test invalid initialization
        with self.assertRaises(ValueError):
            MinesweeperGame(1, 1, 1) # Too many mines
        with self.assertRaises(ValueError):
            MinesweeperGame(0, 5, 1) # Invalid dimensions

    def test_mine_placement_on_first_click(self):
        # Use a fixed seed for deterministic testing of placement logic
        random.seed(42) 
        
        R, C, M = 10, 10, 10
        game = MinesweeperGame(R, C, M)
        
        # Before first click, no mines are placed
        mine_count = sum(1 for r in range(R) for c in range(C) if game.board[r][c]['is_mine'])
        self.assertEqual(mine_count, 0)
        
        # Simulate first click at (0, 0)
        game.reveal_cell(0, 0)
        
        # After first click, mines should be placed
        mine_count = sum(1 for r in range(R) for c in range(C) if game.board[r][c]['is_mine'])
        self.assertEqual(mine_count, M)
        
        # Check that the clicked cell (0, 0) is safe and revealed
        self.assertFalse(game.board[0][0]['is_mine'])
        self.assertTrue(game.board[0][0]['is_revealed'])
        
        # Check that the 3x3 area around (0, 0) is safe (if possible)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                r, c = 0 + dr, 0 + dc
                if 0 <= r < R and 0 <= c < C:
                    self.assertFalse(game.board[r][c]['is_mine'], f"Mine found at safe zone ({r}, {c})")

    def test_reveal_mine_loses_game(self):
        # Use a fixed seed and larger board to prevent accidental win on first click
        random.seed(10) 
        R, C, M = 5, 5, 5
        game = MinesweeperGame(R, C, M)
        
        # Simulate first click at (0, 0) to place mines
        game.reveal_cell(0, 0)
        
        # Ensure the game is still playing after the first click
        self.assertEqual(game.get_game_state(), 'playing')
        
        # Find a mine location
        mine_r, mine_c = -1, -1
        for r in range(R):
            for c in range(C):
                if game.board[r][c]['is_mine']:
                    mine_r, mine_c = r, c
                    break
            if mine_r != -1:
                break
        
        # Check that a mine was actually placed
        self.assertNotEqual(mine_r, -1)
        
        # Click the mine
        game.reveal_cell(mine_r, mine_c)
        
        self.assertEqual(game.get_game_state(), 'lost')
        self.assertTrue(game.board[mine_r][mine_c]['is_revealed'])
        
    def test_flagging(self):
        game = MinesweeperGame(5, 5, 5)
        
        # Flagging an unrevealed cell
        game.toggle_flag(1, 1)
        self.assertTrue(game.board[1][1]['is_flagged'])
        self.assertEqual(game.get_cell_state(1, 1), 'flagged')
        
        # Unflagging
        game.toggle_flag(1, 1)
        self.assertFalse(game.board[1][1]['is_flagged'])
        self.assertEqual(game.get_cell_state(1, 1), 'unrevealed')
        
        # Cannot flag a revealed cell
        game.reveal_cell(0, 0) # First click
        r, c = 0, 0
        self.assertTrue(game.board[r][c]['is_revealed'])
        game.toggle_flag(r, c)
        self.assertFalse(game.board[r][c]['is_flagged'])

    def test_recursive_reveal(self):
        # Create a small board with a guaranteed large safe area
        R, C, M = 5, 5, 1
        game = MinesweeperGame(R, C, M)
        
        # Simulate first click at (0, 0)
        game.reveal_cell(0, 0)
        
        # If (0, 0) is 0, it should reveal a large area
        if game.board[0][0]['value'] == 0:
            # Check if many cells were revealed
            self.assertGreater(game.revealed_count, 1)
            
            # Check that all revealed cells are safe
            for r in range(R):
                for c in range(C):
                    if game.board[r][c]['is_revealed']:
                        self.assertFalse(game.board[r][c]['is_mine'])
        else:
            # If (0, 0) is a number, only one cell should be revealed
            self.assertEqual(game.revealed_count, 1)

    def test_win_condition(self):
        # Create a tiny board where winning is easy
        R, C, M = 2, 2, 1
        game = MinesweeperGame(R, C, M)
        
        # Total safe cells = 3
        
        # Click (0, 0) to place mines
        game.reveal_cell(0, 0)
        
        safe_coords = []
        for r in range(R):
            for c in range(C):
                if not game.board[r][c]['is_mine']:
                    safe_coords.append((r, c))
        
        # Reveal all remaining safe cells one by one
        for r, c in safe_coords:
            if not game.board[r][c]['is_revealed']:
                game.reveal_cell(r, c)
        
        self.assertEqual(game.get_game_state(), 'won')
        self.assertEqual(game.revealed_count, game.total_safe_cells)

if __name__ == '__main__':
    unittest.main()