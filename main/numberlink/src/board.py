import pyxel
from utils.colors import get_color_for_number, get_path_color, BLACK, WHITE, GRAY
from utils.grid import draw_grid, is_adjacent

class NumberlinkBoard:
    def __init__(self, grid_rows, grid_cols, number_cells, cell_size, offset_x, offset_y):
        # ゲーム設定
        self.GRID_ROWS = grid_rows
        self.GRID_COLS = grid_cols
        self.number_cells = number_cells
        self.CELL_SIZE = cell_size
        self.OFFSET_X = offset_x
        self.OFFSET_Y = offset_y
        
        # ゲーム状態の初期化
        self.paths = {}
        self.connected_numbers = {}
        
        # 初期化
        for pos, num in self.number_cells.items():
            self.connected_numbers[pos] = {num}
    
    def add_path(self, edge):
        # エッジを追加し、つながっている数字を更新
        pos1, pos2 = edge
        
        # エッジをパスに追加
        self.paths[edge] = 0  # デフォルトのパスID (色を決める前)
        
        # 接続情報を更新
        self.update_connections()
    
    def remove_path(self, edge):
        # エッジを削除
        if edge in self.paths:
            del self.paths[edge]
            
        # 接続情報を更新
        self.update_connections()
    
    def update_connections(self):
        # すべてのセルの接続情報をリセット (数字セルは除く)
        self.connected_numbers = {pos: {num} for pos, num in self.number_cells.items()}
        
        # エッジに基づいて接続情報を構築
        changed = True
        while changed:
            changed = False
            
            for edge in self.paths:
                pos1, pos2 = edge
                
                # 両方のセルが接続情報を持っているか確認
                set1 = self.connected_numbers.get(pos1, set())
                set2 = self.connected_numbers.get(pos2, set())
                
                # どちらかが空の場合は初期化
                if not set1 and not set2:
                    continue
                elif not set1:
                    self.connected_numbers[pos1] = set2.copy()
                    changed = True
                elif not set2:
                    self.connected_numbers[pos2] = set1.copy()
                    changed = True
                else:
                    # 両方に接続情報がある場合は結合
                    merged = set1.union(set2)
                    if len(merged) != len(set1) or len(merged) != len(set2):
                        self.connected_numbers[pos1] = merged
                        self.connected_numbers[pos2] = merged
                        changed = True
        
        # パスの色を決定
        self.update_path_colors()
    
    def update_path_colors(self):
        # エッジごとに色を決定
        for edge in self.paths:
            pos1, pos2 = edge
            connected_nums1 = self.connected_numbers.get(pos1, set())
            connected_nums2 = self.connected_numbers.get(pos2, set())
            
            # 両端が接続している数字のセット
            connected_nums = connected_nums1.union(connected_nums2)
            
            # 異なる数字に接続している場合は黒 (0)
            # 1つの数字に接続している場合はその数字の色
            # どの数字にも接続していない場合は黒 (0)
            if len(connected_nums) == 1:
                num = next(iter(connected_nums))
                self.paths[edge] = num
            else:
                self.paths[edge] = 0
    
    def has_connected_path(self, pos):
        """指定された位置に接続されたパスがあるかチェック"""
        for edge in self.paths:
            if pos == edge[0] or pos == edge[1]:
                return True
        return False
    
    def get_connected_path_color(self, pos):
        """指定された位置の接続状態に基づいて色を返す
        戻り値: (色, 正しく接続されているかどうか)
        """
        if pos not in self.number_cells:
            return 0, False
            
        number = self.number_cells[pos]
        connected_nums = self.connected_numbers.get(pos, set())
        
        # 接続されていない場合
        if len(connected_nums) == 0:
            return 0, False
            
        # 同じ数字のみ接続されている場合（接続はあるが完全ではない）
        if len(connected_nums) == 1 and number in connected_nums:
            # この数字が両端まで接続されているかチェック
            same_number_positions = [p for p, n in self.number_cells.items() if n == number]
            # 両端が接続されていれば正しく接続されている
            if self.are_connected(same_number_positions, number):
                return number, True
            return number, False
            
        # 異なる数字が接続されている場合（不正な接続）
        return 0, False
    
    def are_connected(self, positions, number):
        """同じ数字のすべての位置が接続されているかチェック"""
        # 位置が2つ未満なら接続できない
        if len(positions) < 2:
            return False
            
        # 最初の位置から他のすべての位置に到達できるかチェック
        start = positions[0]
        for end in positions[1:]:
            if not self.is_path_between(start, end, number):
                return False
        return True
    
    def is_path_between(self, start, end, num):
        """二つのセル間にパスが存在するか幅優先探索で確認する"""
        # 既に訪れたセル
        visited = set()
        # 探索するセルのキュー
        queue = [start]
        
        while queue:
            current = queue.pop(0)
            
            if current == end:
                return True
                
            if current in visited:
                continue
                
            visited.add(current)
            
            # 隣接するセルをチェック
            for edge in self.paths:
                cell1, cell2 = edge
                
                # 現在のセルに接続されているエッジを探す
                if cell1 == current and self.paths[edge] == num:
                    if cell2 not in visited:
                        queue.append(cell2)
                elif cell2 == current and self.paths[edge] == num:
                    if cell1 not in visited:
                        queue.append(cell1)
        
        # 終点に到達できなかった
        return False
    
    def get_potential_path_color(self, pos):
        """現在のカーソル位置にある可能性のある線の色を返す"""
        # 接続されている線が既にある場合はその色を返す
        for edge in self.paths:
            if pos == edge[0] or pos == edge[1]:
                return get_path_color(self.paths[edge])
        
        # 接続情報から可能性のある色を取得
        connected_nums = self.connected_numbers.get(pos, set())
        if len(connected_nums) == 1:
            num = next(iter(connected_nums))
            return get_path_color(num)
        
        # デフォルトは黒
        return BLACK
    
    def get_path_endpoint(self, r, c, next_r, next_c):
        """パスの端点座標を計算（数字セルの場合は円の縁から）"""
        # セルの中心座標
        center_x = self.OFFSET_X + c * self.CELL_SIZE + self.CELL_SIZE // 2
        center_y = self.OFFSET_Y + r * self.CELL_SIZE + self.CELL_SIZE // 2
        
        # 数字セルでない場合はそのまま中心を返す
        if (r, c) not in self.number_cells:
            return center_x, center_y
        
        # 数字セルの場合、線が接続されているか確認
        pos = (r, c)
        if self.has_connected_path(pos):
            # 数字セルの場合は円の縁からスタート
            radius = self.CELL_SIZE // 3
            
            # 次のセルへの方向ベクトル
            dir_x = next_c - c
            dir_y = next_r - r
            
            # 方向ベクトルの長さ
            length = (dir_x ** 2 + dir_y ** 2) ** 0.5
            
            # 方向ベクトルを正規化
            if length > 0:
                dir_x /= length
                dir_y /= length
            
            # 円の縁の座標を計算
            x = center_x + dir_x * radius
            y = center_y + dir_y * radius
            
            return int(x), int(y)
        else:
            # 線が接続されていない場合は中心点を返す
            return center_x, center_y
    
    def check_win(self):
        # クリア条件1: すべての数字が同じ数字と正しく接続されている
        number_connected = {}
        for num in set(self.number_cells.values()):
            number_connected[num] = False
            
            # 同じ数字のセルを集める
            num_cells = [pos for pos, n in self.number_cells.items() if n == num]
            
            # 接続されているか確認
            connected = True
            
            # すべてのセルが接続されているか確認
            for pos in num_cells:
                # セルが連結情報を持っていない場合（線が引かれていない）
                if pos not in self.connected_numbers:
                    connected = False
                    break
                    
                connected_nums = self.connected_numbers[pos]
                
                # 異なる数字と接続している場合はNG
                if len(connected_nums) != 1 or num not in connected_nums:
                    connected = False
                    break
            
            # 最初のセルから他のすべてのセルに到達できるか確認
            if connected and len(num_cells) >= 2:
                start_pos = num_cells[0]
                for end_pos in num_cells[1:]:
                    if not self.is_path_between(start_pos, end_pos, num):
                        connected = False
                        break
            
            number_connected[num] = connected
        
        # すべての数字が正しく接続されているか確認
        return all(number_connected.values())
    
    def would_create_crossing(self, pos1, pos2):
        """この2点間に線を引くと交差が発生するかチェック"""
        # 既に線があるセルの数をカウント
        cell_line_count = {}
        
        # 現在のパスから各セルの線の数をカウント
        for edge in self.paths:
            cell1, cell2 = edge
            cell_line_count[cell1] = cell_line_count.get(cell1, 0) + 1
            cell_line_count[cell2] = cell_line_count.get(cell2, 0) + 1
        
        # 新しい線を追加した場合の影響をチェック
        for pos in [pos1, pos2]:
            # 数字セルの場合は1本しか線を引けない
            if pos in self.number_cells:
                if cell_line_count.get(pos, 0) >= 1:
                    return True
            # 通常セルの場合は2本まで線を引ける
            else:
                if cell_line_count.get(pos, 0) >= 2:
                    return True
        
        # 特に問題なし
        return False
    
    def draw(self):
        # グリッドを描画
        draw_grid(self.OFFSET_X, self.OFFSET_Y, self.GRID_ROWS, self.GRID_COLS, self.CELL_SIZE)
        
        # パスを描画
        self.draw_paths()
        
        # 数字を描画
        self.draw_numbers()
    
    def draw_paths(self):
        # すべてのパスを描画
        for edge, num in self.paths.items():
            pos1, pos2 = edge
            r1, c1 = pos1
            r2, c2 = pos2
            
            # 線の色
            color = get_path_color(num)
            
            # 両端が同じ数字かつ完全に接続されているかチェック
            is_fully_connected = False
            if num != 0:  # 有効な数字の場合
                # 同じ数字のすべての位置を取得
                same_number_positions = [p for p, n in self.number_cells.items() if n == num]
                is_fully_connected = self.are_connected(same_number_positions, num)
            
            # 線の太さ - 完全に接続されているなら太く
            thickness = 3 if is_fully_connected else 1
            
            # 始点と終点の座標を計算（数字セルの場合は円の縁から始める）
            x1, y1 = self.get_path_endpoint(r1, c1, r2, c2)
            x2, y2 = self.get_path_endpoint(r2, c2, r1, c1)
            
            # 線を描画
            pyxel.line(x1, y1, x2, y2, color)
            
            # 太い線を描画する場合
            if thickness > 1:
                if r1 == r2:  # 水平線
                    for i in range(1, thickness):
                        offset = i // 2 * (1 if i % 2 else -1)
                        pyxel.line(x1, y1 + offset, x2, y2 + offset, color)
                else:  # 垂直線
                    for i in range(1, thickness):
                        offset = i // 2 * (1 if i % 2 else -1)
                        pyxel.line(x1 + offset, y1, x2 + offset, y2, color)
    
    def draw_numbers(self):
        # 数字を描画
        for pos, number in self.number_cells.items():
            r, c = pos
            # 数字の位置（オフセットを考慮）
            center_x = self.OFFSET_X + c * self.CELL_SIZE + self.CELL_SIZE // 2
            center_y = self.OFFSET_Y + r * self.CELL_SIZE + self.CELL_SIZE // 2
            
            # 数字の標準色
            base_color = get_color_for_number(number)
            
            # 線が接続されているかチェック
            has_connection = self.has_connected_path(pos)
            
            # 線が接続されている場合のみ円を描く
            if has_connection:
                # 接続状態に基づいて色を取得
                circle_color, is_fully_connected = self.get_connected_path_color(pos)
                circle_color = get_path_color(circle_color)
                
                # セルサイズが大きくなったため、半径を調整
                radius = self.CELL_SIZE // 3
                
                # 完全に接続されている場合は太い円を描く
                if is_fully_connected:
                    # 少し大きな半径で円を描く（数字の見やすさ向上）
                    outer_radius = radius + 1  # 外側の円を少し大きく
                    # 外側の円
                    pyxel.circb(center_x, center_y, outer_radius, circle_color)
                    # 内側の円（少し小さくして太く見せる）
                    pyxel.circb(center_x, center_y, outer_radius - 1, circle_color)
                elif circle_color == BLACK:
                    # 異なる数字に接続されている場合は黒い円を描く
                    pyxel.circb(center_x, center_y, radius, BLACK)
                else:
                    # 同じ数字に接続されているが完全ではない場合は通常の円
                    pyxel.circb(center_x, center_y, radius, circle_color)
                
                # 数字の背景に小さな円を描く（線が数字に重ならないように）
                pyxel.circ(center_x, center_y, radius - 1, WHITE)
            
            # 数字を描画（中央に配置）
            x = center_x - 2
            y = center_y - 2
            pyxel.text(x, y, str(number), base_color)
