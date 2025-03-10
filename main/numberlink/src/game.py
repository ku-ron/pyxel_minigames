import pyxel
from puzzles.puzzle_loader import load_puzzle
from board import NumberlinkBoard
from game_controller import NumberlinkController

class NumberlinkGame:
    def __init__(self, app, puzzle_id):
        self.app = app
        
        # パズルデータのロード
        puzzle_data = load_puzzle(puzzle_id)
        if not puzzle_data:
            raise ValueError(f"Puzzle with ID {puzzle_id} not found")
        
        # パズル情報の設定
        self.puzzle_id = puzzle_id
        grid_size = puzzle_data["size"]
        number_cells = puzzle_data["numbers"]
        
        # ゲーム設定 - セルサイズは固定
        cell_size = 16  # 元のセルサイズに戻す
        offset_x = (app.WINDOW_WIDTH - grid_size * cell_size) // 2
        offset_y = (app.WINDOW_HEIGHT - 40 - grid_size * cell_size) // 2
        
        # ボードとコントローラーの初期化
        self.board = NumberlinkBoard(grid_size, number_cells, cell_size, offset_x, offset_y)
        self.controller = NumberlinkController(self, self.board)
    
    def initialize_game(self):
        self.controller.initialize_game()
    
    def update(self):
        self.controller.update()
    
    def draw(self):
        self.board.draw()
        self.controller.draw()
    
    def return_to_menu(self):
        self.app.return_to_menu()
