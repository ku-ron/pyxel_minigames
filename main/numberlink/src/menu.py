import pyxel
from puzzles.puzzle_loader import get_puzzle_list

class MenuScreen:
    def __init__(self, app):
        self.app = app
        self.puzzles = get_puzzle_list()
        self.selected_index = 0
    
    def update(self):
        # 上下キーまたは十字キーで選択変更
        if (pyxel.btnp(pyxel.KEY_UP) or
            pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP)) and self.selected_index > 0:
            self.selected_index -= 1
        elif (pyxel.btnp(pyxel.KEY_DOWN) or
              pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN)) and self.selected_index < len(self.puzzles) - 1:
            self.selected_index += 1
        
        # Enterキーまたはゲームパッドのボタンで選択(スペースでも、ゲームパッドの他のボタンでも可)
        if (pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE) or
            pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)):
            selected_puzzle = self.puzzles[self.selected_index]["id"]
            self.app.start_game(selected_puzzle)
    
    def draw(self):
        # タイトル
        title = "NUMBERLINK PUZZLE"
        pyxel.text(self.app.WINDOW_WIDTH // 2 - len(title) * 2, 20, title, 8)
        
        # 問題リスト
        for i, puzzle in enumerate(self.puzzles):
            text = f"{puzzle['name']} ({puzzle['size']}x{puzzle['size']})"
            color = 8 if i == self.selected_index else 5
            pyxel.text(30, 50 + i * 10, text, color)
        
        # カーソル表示
        pyxel.text(20, 50 + self.selected_index * 10, ">", 8)
        
        # 操作方法
        instruction1 = "UP/DOWN: Select, ENTER/B: Start, ESC: Quit"
        instruction2 = "B: Toggle BGM ON/OFF"
        pyxel.text(10, self.app.WINDOW_HEIGHT - 30, instruction1, 5)
        pyxel.text(10, self.app.WINDOW_HEIGHT - 20, instruction2, 5)