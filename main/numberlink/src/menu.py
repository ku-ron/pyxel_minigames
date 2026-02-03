import pyxel
from puzzles.puzzle_loader import get_puzzle_list

# 色定数
COLOR_CLEARED = 11  # 緑色（クリア済み）
COLOR_NORMAL = 5    # 紫色（未クリア）
COLOR_SELECTED = 8  # 赤色（選択中）

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
        self.top_margin = 40     # 上マージン（タイトル下）
        
        # スクロール設定
        self.scroll_offset = 0   # 現在のスクロール位置
        self.visible_area_top = self.top_margin  # 表示領域の上端
        self.visible_area_bottom = app.WINDOW_HEIGHT - 40  # 表示領域の下端（説明欄の上）
        self.scroll_margin = 10  # スクロール時の余白
        
        # 各グループ・行のY座標を事前計算
        self._calculate_layout()
    
    def _get_size_key(self, puzzle):
        """パズルからサイズキーを取得"""
        size = puzzle["size"]
        return f"{size[0]:02d}x{size[1]:02d}"
    
    def _get_size_label(self, puzzle):
        """パズルからサイズラベルを取得（表示用）"""
        size = puzzle["size"]
        return f"{size[0]}x{size[1]}"
    
    def _group_puzzles_by_size(self):
        """パズルをサイズごとにグループ化する"""
        groups = {}
        for puzzle in self.puzzles:
            size_key = self._get_size_key(puzzle)
            if size_key not in groups:
                groups[size_key] = {
                    'size_label': self._get_size_label(puzzle),
                    'puzzles': []
                }
            groups[size_key]['puzzles'].append(puzzle)
        
        # サイズ順に並べ替えたグループのリストを返す
        sorted_groups = []
        for size_key in sorted(groups.keys()):
            sorted_groups.append(groups[size_key])
        
        return sorted_groups
    
    def _calculate_layout(self):
        """各グループと行のY座標を事前計算"""
        self.group_layouts = []
        y_pos = 0  # スクロール座標系での位置（0から開始）
        
        for group in self.puzzle_groups:
            group_layout = {
                'label_y': y_pos,
                'rows': []
            }
            y_pos += 8  # ラベルの高さ
            
            puzzles = group['puzzles']
            num_rows = (len(puzzles) + self.items_per_row - 1) // self.items_per_row
            
            for row in range(num_rows):
                group_layout['rows'].append(y_pos)
                y_pos += self.row_spacing
            
            y_pos += self.group_spacing - self.row_spacing  # グループ間の追加スペース
            self.group_layouts.append(group_layout)
        
        self.total_content_height = y_pos
    
    def _get_selected_y(self):
        """現在選択中のアイテムのY座標を取得"""
        if self.selected_group_index >= len(self.group_layouts):
            return 0
        
        group_layout = self.group_layouts[self.selected_group_index]
        current_row = self.selected_item_index // self.items_per_row
        
        if current_row < len(group_layout['rows']):
            return group_layout['rows'][current_row]
        return 0
    
    def _get_selected_group_label_y(self):
        """現在選択中のグループのラベルY座標を取得"""
        if self.selected_group_index >= len(self.group_layouts):
            return 0
        return self.group_layouts[self.selected_group_index]['label_y']
    
    def _adjust_scroll(self):
        """選択中のアイテムが見えるようにスクロール位置を調整"""
        selected_y = self._get_selected_y()
        group_label_y = self._get_selected_group_label_y()
        
        # 表示領域の高さ
        visible_height = self.visible_area_bottom - self.visible_area_top
        
        # 上にスクロールするとき: グループラベルが見えるようにする
        if group_label_y < self.scroll_offset:
            self.scroll_offset = group_label_y
        
        # 下にスクロールするとき: 選択アイテム + 余白が見えるようにする
        elif selected_y + self.row_spacing + self.scroll_margin > self.scroll_offset + visible_height:
            self.scroll_offset = selected_y + self.row_spacing + self.scroll_margin - visible_height
        
        # スクロール範囲を制限
        max_scroll = max(0, self.total_content_height - visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
    
    def _move_down(self):
        """下に移動"""
        current_group = self.puzzle_groups[self.selected_group_index]
        current_puzzles = current_group['puzzles']
        rows_in_current_group = (len(current_puzzles) + self.items_per_row - 1) // self.items_per_row
        
        current_row = self.selected_item_index // self.items_per_row
        current_col = self.selected_item_index % self.items_per_row
        
        if current_row < rows_in_current_group - 1:
            # 同じグループの次の行へ
            next_row = current_row + 1
            # 次の行の同じ列、またはその行の最後のアイテム
            next_row_start = next_row * self.items_per_row
            next_row_end = min((next_row + 1) * self.items_per_row, len(current_puzzles)) - 1
            
            # 同じ列位置か、その行の最後
            new_index = next_row_start + current_col
            if new_index > next_row_end:
                new_index = next_row_end
            
            self.selected_item_index = new_index
        
        elif self.selected_group_index < len(self.puzzle_groups) - 1:
            # 次のグループへ
            self.selected_group_index += 1
            next_group = self.puzzle_groups[self.selected_group_index]
            next_puzzles = next_group['puzzles']
            
            # 最初の行の同じ列位置か、その行の最後
            first_row_end = min(self.items_per_row, len(next_puzzles)) - 1
            new_index = min(current_col, first_row_end)
            self.selected_item_index = new_index
    
    def _move_up(self):
        """上に移動"""
        current_group = self.puzzle_groups[self.selected_group_index]
        current_puzzles = current_group['puzzles']
        
        current_row = self.selected_item_index // self.items_per_row
        current_col = self.selected_item_index % self.items_per_row
        
        if current_row > 0:
            # 同じグループの前の行へ
            prev_row = current_row - 1
            prev_row_start = prev_row * self.items_per_row
            prev_row_end = min((prev_row + 1) * self.items_per_row, len(current_puzzles)) - 1
            
            # 同じ列位置か、その行の最後
            new_index = prev_row_start + current_col
            if new_index > prev_row_end:
                new_index = prev_row_end
            
            self.selected_item_index = new_index
        
        elif self.selected_group_index > 0:
            # 前のグループへ
            self.selected_group_index -= 1
            prev_group = self.puzzle_groups[self.selected_group_index]
            prev_puzzles = prev_group['puzzles']
            
            # 最後の行の同じ列位置か、その行の最後
            num_rows = (len(prev_puzzles) + self.items_per_row - 1) // self.items_per_row
            last_row = num_rows - 1
            last_row_start = last_row * self.items_per_row
            last_row_end = len(prev_puzzles) - 1
            
            new_index = last_row_start + current_col
            if new_index > last_row_end:
                new_index = last_row_end
            
            self.selected_item_index = new_index
    
    def update(self):
        if not self.puzzle_groups:
            return
        
        current_group = self.puzzle_groups[self.selected_group_index]
        current_puzzles = current_group['puzzles']
        
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
            self._move_down()
        
        elif pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP):
            self._move_up()
        
        # スクロール位置を調整
        self._adjust_scroll()
        
        # Enterキーまたはゲームパッドのボタンで選択
        if (pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE) or
            pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)):
            selected_puzzle = current_puzzles[self.selected_item_index]["id"]
            self.app.start_game(selected_puzzle)
    
    def draw(self):
        # タイトル
        title = "NUMBERLINK PUZZLE"
        pyxel.text(self.app.WINDOW_WIDTH // 2 - len(title) * 2, 20, title, 8)
        
        if not self.puzzle_groups:
            pyxel.text(10, 60, "No puzzles found.", 8)
            return
        
        # クリッピング領域の設定（説明欄より上）
        clip_top = self.visible_area_top
        clip_bottom = self.visible_area_bottom
        
        # グループごとに問題を表示
        for group_idx, group in enumerate(self.puzzle_groups):
            group_layout = self.group_layouts[group_idx]
            
            # グループラベルのY座標（スクロールを考慮）
            label_y = self.top_margin + group_layout['label_y'] - self.scroll_offset
            
            # 表示領域内ならラベルを描画
            if clip_top <= label_y < clip_bottom:
                pyxel.text(10, label_y, group['size_label'], 8)
            
            # このグループの問題を表示
            puzzles = group['puzzles']
            
            for i, puzzle in enumerate(puzzles):
                row = i // self.items_per_row
                col = i % self.items_per_row
                
                # Y座標を計算（スクロールを考慮）
                if row < len(group_layout['rows']):
                    y_pos = self.top_margin + group_layout['rows'][row] - self.scroll_offset
                else:
                    continue
                
                # 表示領域外ならスキップ
                if y_pos < clip_top - self.row_spacing or y_pos >= clip_bottom:
                    continue
                
                # X座標を計算
                x = self.left_margin + col * self.item_width
                
                # 問題番号の表示 (IDから番号を抽出: "10x10_001" -> "001")
                puzzle_id = puzzle["id"]
                parts = puzzle_id.split("_")
                num_str = parts[1] if len(parts) == 2 else f"{i+1:03d}"
                
                # クリア済みかどうか確認
                is_cleared = self.app.is_puzzle_cleared(puzzle_id)
                
                # クリア済みなら * を付ける
                if is_cleared:
                    text = num_str + "*"
                else:
                    text = num_str
                
                # 選択中かどうかでカラーを変更
                is_selected = (group_idx == self.selected_group_index and i == self.selected_item_index)
                
                if is_selected:
                    color = COLOR_SELECTED  # 選択中は赤
                elif is_cleared:
                    color = COLOR_CLEARED   # クリア済みは緑
                else:
                    color = COLOR_NORMAL    # 未クリアは紫
                
                # 選択中アイテムの背景を描画
                if is_selected:
                    # クリア済みなら*の分だけ幅を広げる
                    box_width = 24 if is_cleared else 20
                    pyxel.rectb(x - 2, y_pos - 2, box_width, 10, COLOR_SELECTED)
                
                pyxel.text(x, y_pos, text, color)
        
        # 説明欄の背景（スクロール内容が見えないように）
        pyxel.rect(0, self.visible_area_bottom, self.app.WINDOW_WIDTH, 40, 7)
        
        # 操作方法
        instruction1 = "ARROWS: Select, ENTER/B: Start, ESC: Quit"
        instruction2 = "B: Toggle BGM ON/OFF"
        pyxel.text(10, self.app.WINDOW_HEIGHT - 30, instruction1, 5)
        pyxel.text(10, self.app.WINDOW_HEIGHT - 20, instruction2, 5)
        
        # スクロールインジケーター（上にスクロールできる場合）
        if self.scroll_offset > 0:
            pyxel.text(self.app.WINDOW_WIDTH - 15, self.top_margin, "^", 8)
        
        # スクロールインジケーター（下にスクロールできる場合）
        visible_height = self.visible_area_bottom - self.visible_area_top
        if self.scroll_offset + visible_height < self.total_content_height:
            pyxel.text(self.app.WINDOW_WIDTH - 15, self.visible_area_bottom - 10, "v", 8)
