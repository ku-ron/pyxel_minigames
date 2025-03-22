import pyxel
from puzzles.puzzle_loader import get_puzzle_list

class MenuScreen:
    def __init__(self, app):
        self.app = app
        self.puzzles = get_puzzle_list()
        
        # パズルをサイズごとにグループ化
        self.puzzle_groups = self._group_puzzles_by_size()
        
        # グループとグループ内の位置を追跡するための変数
        self.selected_group_index = 0  # 現在選択されているグループのインデックス
        self.selected_item_index = 0   # 現在選択されているグループ内のアイテムのインデックス
        
        # 表示設定
        self.items_per_row = 10  # 1行あたりの問題数
        self.item_width = 22     # 各問題表示の幅
        self.item_height = 10    # 各問題表示の高さ
        self.group_spacing = 16  # グループ間の縦方向の間隔
        self.row_spacing = 10    # 行間の間隔
        self.left_margin = 20    # 左マージン
        self.top_margin = 40     # 上マージン
    
    def _group_puzzles_by_size(self):
        """パズルをサイズごとにグループ化する"""
        groups = {}
        for puzzle in self.puzzles:
            size_key = f"{puzzle['size']}x{puzzle['size']}"
            if size_key not in groups:
                groups[size_key] = []
            groups[size_key].append(puzzle)
        
        # サイズ順に並べ替えたグループのリストを返す
        sorted_groups = []
        for size_key in sorted(groups.keys(), key=lambda k: int(k.split('x')[0])):
            sorted_groups.append({
                'size_label': size_key,
                'puzzles': groups[size_key]
            })
        
        return sorted_groups
    
    def update(self):
        current_group = self.puzzle_groups[self.selected_group_index]
        current_puzzles = current_group['puzzles']
        rows_in_current_group = (len(current_puzzles) + self.items_per_row - 1) // self.items_per_row
        
        # キー入力による移動処理
        if pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT):
            # 右に移動（同じグループ内で）
            if self.selected_item_index < len(current_puzzles) - 1:
                self.selected_item_index += 1
        
        elif pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT):
            # 左に移動（同じグループ内で）
            if self.selected_item_index > 0:
                self.selected_item_index -= 1
        
        elif pyxel.btnp(pyxel.KEY_DOWN) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN):
            # 下に移動（次の行または次のグループへ）
            current_row = self.selected_item_index // self.items_per_row
            if current_row < rows_in_current_group - 1:
                # 同じグループの次の行へ
                new_index = self.selected_item_index + self.items_per_row
                if new_index < len(current_puzzles):
                    self.selected_item_index = new_index
            elif self.selected_group_index < len(self.puzzle_groups) - 1:
                # 次のグループへ
                self.selected_group_index += 1
                self.selected_item_index = 0
        
        elif pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP):
            # 上に移動（前の行または前のグループへ）
            current_row = self.selected_item_index // self.items_per_row
            if current_row > 0:
                # 同じグループの前の行へ
                self.selected_item_index -= self.items_per_row
            elif self.selected_group_index > 0:
                # 前のグループへ
                self.selected_group_index -= 1
                prev_group_puzzles = self.puzzle_groups[self.selected_group_index]['puzzles']
                # 前のグループの最後の行の最初のアイテムを選択
                rows = (len(prev_group_puzzles) + self.items_per_row - 1) // self.items_per_row
                self.selected_item_index = min((rows - 1) * self.items_per_row, len(prev_group_puzzles) - 1)
        
        # Enterキーまたはゲームパッドのボタンで選択
        if (pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE) or
            pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)):
            selected_puzzle = current_puzzles[self.selected_item_index]["id"]
            self.app.start_game(selected_puzzle)
    
    def draw(self):
        # タイトル
        title = "NUMBERLINK PUZZLE"
        pyxel.text(self.app.WINDOW_WIDTH // 2 - len(title) * 2, 20, title, 8)
        
        y_pos = self.top_margin
        
        # グループごとに問題を表示
        for group_idx, group in enumerate(self.puzzle_groups):
            # グループラベル（サイズ）を表示
            pyxel.text(10, y_pos, group['size_label'], 8)
            y_pos += 8
            
            # このグループの問題を表示
            puzzles = group['puzzles']
            row = 0
            for i, puzzle in enumerate(puzzles):
                # 行の計算
                if i > 0 and i % self.items_per_row == 0:
                    row += 1
                    y_pos += self.row_spacing
                
                # 位置の計算
                col = i % self.items_per_row
                x = self.left_margin + col * self.item_width
                
                # 問題番号の表示
                text = f"{i+1:02d}"
                
                # 選択中かどうかでカラーを変更
                is_selected = (group_idx == self.selected_group_index and i == self.selected_item_index)
                color = 8 if is_selected else 5
                
                # 選択中アイテムの背景を描画
                if is_selected:
                    pyxel.rectb(x - 2, y_pos - 2, 20, 10, 8)
                
                pyxel.text(x, y_pos, text, color)
            
            # 次のグループの開始位置
            y_pos += self.group_spacing
        
        # 操作方法
        instruction1 = "ARROWS: Select, ENTER/B: Start, ESC: Quit"
        instruction2 = "B: Toggle BGM ON/OFF"
        pyxel.text(10, self.app.WINDOW_HEIGHT - 30, instruction1, 5)
        pyxel.text(10, self.app.WINDOW_HEIGHT - 20, instruction2, 5)
