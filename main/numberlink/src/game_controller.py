import pyxel
from utils.colors import GRAY, DARK_GRAY, WHITE, BLACK
from utils.grid import is_adjacent

class NumberlinkController:
    def __init__(self, game, board, puzzle_id):
        self.game = game
        self.board = board
        self.puzzle_id = puzzle_id
        
        # ゲーム状態の初期化
        self.initialize_game()
    
    def initialize_game(self):
        # カーソル位置
        self.cursor_pos = [0, 0]
        # 線を引くモードか移動モードか
        self.draw_mode = False
        
        # アニメーション用の状態変数
        self.invalid_move = False
        self.invalid_move_timer = 0
        self.invalid_move_target = None
        
        # クリア状態
        self.is_cleared = False
        self.show_clear_message = False
    
    def update(self):
        # 無効な移動アニメーションの処理
        if self.invalid_move:
            self.invalid_move_timer += 1
            if self.invalid_move_timer >= 4:
                self.invalid_move = False
                self.invalid_move_timer = 0
                self.invalid_move_target = None
            return
        
        # キー入力処理
        self.handle_input()
    
    def handle_input(self):
        # クリア表示中にENTERキーまたはBボタンでメニューに戻る
        if self.is_cleared and self.show_clear_message:
            if (pyxel.btnp(pyxel.KEY_RETURN) or 
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B)):
                self.game.return_to_menu()
                return

        # モード切替 (SpaceキーまたはAボタン)
        if (pyxel.btnp(pyxel.KEY_SPACE) or 
            pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)):
            # 描画モードから移動モードに切り替わるとき
            if self.draw_mode:
                # クリアチェックを行う
                self.check_clear_when_mode_change()
            
            # モード切替
            self.draw_mode = not self.draw_mode
        
        # カーソル移動 - 速度を遅くするため、btnpのパラメータを調整
        # hold=10 (長押し検出まで10フレーム), period=4 (長押し中は4フレームごとに入力)
        if (pyxel.btnp(pyxel.KEY_UP, 10, 4) or 
            pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP, 10, 4)):
            self.try_move_cursor(0, -1)
        elif (pyxel.btnp(pyxel.KEY_DOWN, 10, 4) or 
              pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN, 10, 4)):
            self.try_move_cursor(0, 1)
        elif (pyxel.btnp(pyxel.KEY_LEFT, 10, 4) or 
              pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT, 10, 4)):
            self.try_move_cursor(-1, 0)
        elif (pyxel.btnp(pyxel.KEY_RIGHT, 10, 4) or 
              pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT, 10, 4)):
            self.try_move_cursor(1, 0)
        
        # リセット (RキーまたはXボタン)
        if (pyxel.btnp(pyxel.KEY_R) or 
            pyxel.btnp(pyxel.GAMEPAD1_BUTTON_X)):
            self.initialize_game()
            self.board.paths = {}
            self.board.connected_numbers = {pos: {num} for pos, num in self.board.number_cells.items()}
        
        # クリアチェック (Cキー) - 手動チェック用に残しておく
        if pyxel.btnp(pyxel.KEY_C):
            # クリア状態をチェック
            self.is_cleared = self.board.check_win()
            # クリアしていなくても常にメッセージ表示（デバッグ用）
            self.show_clear_message = True
            # クリアしていたら記録
            if self.is_cleared:
                self.game.app.mark_puzzle_cleared(self.puzzle_id)
        
        # メニューに戻る (MキーまたはYボタン)
        if (pyxel.btnp(pyxel.KEY_M) or 
            pyxel.btnp(pyxel.GAMEPAD1_BUTTON_Y)):
            self.game.return_to_menu()
    
    def check_clear_when_mode_change(self):
        """モード切替時のクリアチェック - クリア時のみメッセージ表示"""
        self.is_cleared = self.board.check_win()
        
        # クリアしている場合のみメッセージを表示
        if self.is_cleared:
            self.show_clear_message = True
            # クリア済みとして記録
            self.game.app.mark_puzzle_cleared(self.puzzle_id)
    
    def try_move_cursor(self, dx, dy):
        # グリッド内に収まるように座標を制限
        new_row = max(0, min(self.board.GRID_ROWS - 1, self.cursor_pos[0] + dy))
        new_col = max(0, min(self.board.GRID_COLS - 1, self.cursor_pos[1] + dx))
        
        new_pos = (new_row, new_col)
        old_pos = (self.cursor_pos[0], self.cursor_pos[1])
        
        # 位置が変わらない場合は何もしない
        if new_pos == old_pos:
            return
        
        # 線を引くモードで隣接するセルへの移動の場合
        if self.draw_mode and is_adjacent(old_pos, new_pos):
            edge = (min(old_pos, new_pos), max(old_pos, new_pos))
            
            # 既存の線があれば問題なし（消すだけなので）
            if edge in self.board.paths:
                self.move_cursor(dx, dy)
                return
            
            # 線を追加して交差が発生するかチェック
            if self.board.would_create_crossing(old_pos, new_pos):
                # 無効な移動としてアニメーション設定
                self.invalid_move = True
                self.invalid_move_timer = 0
                self.invalid_move_target = new_pos
                return
                
            # 異なる数字同士の接続をチェック
            if self.would_connect_different_numbers(old_pos, new_pos):
                # 無効な移動としてアニメーション設定
                self.invalid_move = True
                self.invalid_move_timer = 0
                self.invalid_move_target = new_pos
                return
        
        # 移動実行
        self.move_cursor(dx, dy)
    
    def would_connect_different_numbers(self, pos1, pos2):
        """異なる数字に関連付けられたセル/線を接続しようとしているかチェック"""
        # 両方が数字セルの場合は常に接続不可
        if pos1 in self.board.number_cells and pos2 in self.board.number_cells:
            num1 = self.board.number_cells[pos1]
            num2 = self.board.number_cells[pos2]
            return num1 != num2
            
        # 数字セルと線をつなげようとする場合
        connected_numbers1 = set()
        connected_numbers2 = set()
        
        # pos1に関連する数字を取得
        if pos1 in self.board.connected_numbers:
            connected_numbers1 = self.board.connected_numbers[pos1]
        
        # pos2に関連する数字を取得
        if pos2 in self.board.connected_numbers:
            connected_numbers2 = self.board.connected_numbers[pos2]
        
        # どちらかが空（まだ何にも接続されていない）場合は接続可能
        if not connected_numbers1 or not connected_numbers2:
            return False
            
        # どちらも数字に接続されている場合、同じ数字かどうかチェック
        return connected_numbers1 != connected_numbers2
    
    def move_cursor(self, dx, dy):
        new_row = max(0, min(self.board.GRID_ROWS - 1, self.cursor_pos[0] + dy))
        new_col = max(0, min(self.board.GRID_COLS - 1, self.cursor_pos[1] + dx))
        
        # 位置が変わる場合のみ処理
        if new_row != self.cursor_pos[0] or new_col != self.cursor_pos[1]:
            old_pos = (self.cursor_pos[0], self.cursor_pos[1])
            new_pos = (new_row, new_col)
            
            # 線を引くモードの場合、隣接セル間で線の操作
            if self.draw_mode and is_adjacent(old_pos, new_pos):
                edge = (min(old_pos, new_pos), max(old_pos, new_pos))
                
                # 既存の線があれば消す
                if edge in self.board.paths:
                    self.board.remove_path(edge)
                else:
                    # 新しい線を引く
                    self.board.add_path(edge)
            
            # カーソル位置を更新
            self.cursor_pos = [new_row, new_col]
    
    def _get_puzzle_display_info(self):
        """パズルIDから表示用の情報を取得"""
        # ID形式: "10x10_001" -> size="10x10", number="001"
        parts = self.puzzle_id.split("_")
        if len(parts) == 2:
            size_part = parts[0]
            num_part = parts[1]
            return size_part, num_part
        # フォールバック
        return f"{self.board.GRID_ROWS}x{self.board.GRID_COLS}", "???"
    
    def draw(self):
        # カーソル描画
        self.draw_cursor()
        
        # UIステータス表示
        self.draw_status()
        
        # クリアメッセージ表示（必要な場合）
        if self.show_clear_message and self.is_cleared:
            self.draw_clear_message()
    
    def draw_cursor(self):
        row, col = self.cursor_pos
        
        # 標準カーソル（アニメーションなし）
        if not self.invalid_move:
            # カーソルの色を決定
            cursor_color = 8 if self.draw_mode else 12  # 赤または紫
            
            # カーソル位置計算
            cursor_x = self.board.OFFSET_X + col * self.board.CELL_SIZE
            cursor_y = self.board.OFFSET_Y + row * self.board.CELL_SIZE
            
            # カーソル中心座標
            center_x = cursor_x + self.board.CELL_SIZE // 2
            center_y = cursor_y + self.board.CELL_SIZE // 2
            
            # カーソル枠を描画
            for i in range(2):  # 2ピクセル太さ
                offset = i
                width = self.board.CELL_SIZE + 1 - i * 2
                height = self.board.CELL_SIZE + 1 - i * 2
                
                pyxel.rectb(
                    cursor_x + offset,
                    cursor_y + offset,
                    width,
                    height,
                    cursor_color
                )
            
            # 描画モードで数字セルでない場合は小さな丸を表示
            current_pos = (row, col)
            if self.draw_mode and current_pos not in self.board.number_cells:
                dot_color = self.board.get_potential_path_color(current_pos)
                pyxel.circ(center_x, center_y, 2, dot_color)
        else:
            # 無効移動アニメーション
            progress = self.invalid_move_timer / 4.0
            t = 1.0 - progress
            
            # 移動方向を計算
            if self.invalid_move_target:
                target_row, target_col = self.invalid_move_target
                dir_row = 1 if target_row > row else (-1 if target_row < row else 0)
                dir_col = 1 if target_col > col else (-1 if target_col < col else 0)
            else:
                dir_row, dir_col = 0, 0
            
            # アニメーション移動量
            max_move = 2
            move_x = dir_col * t * max_move
            move_y = dir_row * t * max_move
            
            # 赤いカーソル描画
            cursor_x = self.board.OFFSET_X + col * self.board.CELL_SIZE + move_x
            cursor_y = self.board.OFFSET_Y + row * self.board.CELL_SIZE + move_y
            
            # カーソル枠を描画
            for i in range(2):
                offset = i
                width = self.board.CELL_SIZE + 1 - i * 2
                height = self.board.CELL_SIZE + 1 - i * 2
                
                pyxel.rectb(
                    int(cursor_x) + offset,
                    int(cursor_y) + offset,
                    width,
                    height,
                    8  # 赤色
                )
    
    def draw_status(self):
        # モード表示
        mode_text = "DRAW MODE" if self.draw_mode else "MOVE MODE"
        text_x = self.game.app.WINDOW_WIDTH // 2 - len(mode_text) * 2
        text_y = self.board.OFFSET_Y + self.board.GRID_ROWS * self.board.CELL_SIZE + 10
        
        mode_color = 8 if self.draw_mode else 12
        pyxel.text(text_x, text_y, mode_text, mode_color)
        
        # 操作方法 (キーボードとゲームパッド)
        ctrl_text = "SPACE/A: Toggle Mode  R/X: Reset  M/Y: Menu"
        ctrl_x = self.game.app.WINDOW_WIDTH // 2 - len(ctrl_text) * 2
        ctrl_y = text_y + 10
        pyxel.text(ctrl_x, ctrl_y, ctrl_text, GRAY)
        
        # パズル情報表示 (例: "10x10 No.001")
        size_str, num_str = self._get_puzzle_display_info()
        puzzle_text = f"{size_str} No.{num_str}"
        puzzle_x = self.game.app.WINDOW_WIDTH // 2 - len(puzzle_text) * 2
        puzzle_y = text_y + 20
        pyxel.text(puzzle_x, puzzle_y, puzzle_text, DARK_GRAY)
    
    def draw_clear_message(self):
        # ステータスエリアの位置を取得（グリッド領域の下）
        status_y = self.board.OFFSET_Y + self.board.GRID_ROWS * self.board.CELL_SIZE + 10
        
        # クリアメッセージ（通常サイズで表示）
        message = "CLEARED!"
        color = 11  # 黄色
        
        # 背景を描画
        bg_y = status_y
        bg_height = 30
        bg_width = self.game.app.WINDOW_WIDTH
        pyxel.rect(0, bg_y, bg_width, bg_height, WHITE)
        
        # 通常サイズの文字で中央に表示
        text_x = self.game.app.WINDOW_WIDTH // 2 - len(message) * 2  # 中央寄せの計算
        text_y = status_y + 10  # 背景の中央あたりに配置
        pyxel.text(text_x, text_y, message, color)
        
        # ENTERキーまたはBボタンの案内
        enter_text = "Press ENTER/B to return to menu"
        enter_x = self.game.app.WINDOW_WIDTH // 2 - len(enter_text) * 2
        enter_y = text_y + 10
        pyxel.text(enter_x, enter_y, enter_text, DARK_GRAY)
