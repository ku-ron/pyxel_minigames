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

        # 数字ごとのセル位置（ゲーム中は変わらないので一度だけ作る）
        self.cells_by_number = {}
        for pos, num in self.number_cells.items():
            self.cells_by_number.setdefault(num, []).append(pos)

        # ゲーム状態の初期化
        self.paths = {}
        self.update_connections()

    def reset(self):
        # すべての線を消して接続情報を作り直す
        self.paths = {}
        self.update_connections()

    def add_path(self, edge):
        # エッジを追加し、つながっている数字を更新
        self.paths[edge] = 0  # デフォルトのパスID (色を決める前)
        self.update_connections()

    def remove_path(self, edge):
        # エッジを削除
        if edge in self.paths:
            del self.paths[edge]
        self.update_connections()

    def update_connections(self):
        """線の追加・削除のたびに接続情報を作り直す。
        描画は毎フレーム走るので、ここで計算したものを読むだけにしておく。
        （以前は draw の中で線ごとに幅優先探索していて、線が増えるほど重くなっていた）"""
        # 隣接関係: セル -> {隣のセル: その辺の色}
        self.adjacency = {}
        for edge in self.paths:
            pos1, pos2 = edge
            self.adjacency.setdefault(pos1, {})[pos2] = 0
            self.adjacency.setdefault(pos2, {})[pos1] = 0

        # 線でつながったセルのまとまり（連結成分）ごとに、含まれる数字の集合を求める
        self.connected_numbers = {}
        visited = set()
        for start in self.adjacency:
            if start in visited:
                continue
            component = []
            queue = [start]
            visited.add(start)
            while queue:
                current = queue.pop()
                component.append(current)
                for neighbor in self.adjacency[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            nums = {self.number_cells[p] for p in component if p in self.number_cells}
            # どの数字にもつながっていないまとまりは接続情報を持たない
            if nums:
                for p in component:
                    self.connected_numbers[p] = nums

        # 線が引かれていない数字セルは自分の数字だけ
        for pos, num in self.number_cells.items():
            if pos not in self.connected_numbers:
                self.connected_numbers[pos] = {num}

        # パスの色を決定
        self.update_path_colors()

        # 両端まで正しくつながった数字の集合
        self.completed_numbers = set()
        for num, cells in self.cells_by_number.items():
            if len(cells) < 2:
                continue
            if all(self.connected_numbers.get(p) == {num} for p in cells):
                if self.are_connected(cells, num):
                    self.completed_numbers.add(num)

    def update_path_colors(self):
        # エッジごとに色を決定
        for edge in self.paths:
            pos1, pos2 = edge
            connected_nums = (self.connected_numbers.get(pos1, set())
                              | self.connected_numbers.get(pos2, set()))

            # 1つの数字にだけ接続している場合はその数字の色、それ以外は黒 (0)
            if len(connected_nums) == 1:
                num = next(iter(connected_nums))
            else:
                num = 0
            self.paths[edge] = num
            self.adjacency[pos1][pos2] = num
            self.adjacency[pos2][pos1] = num

    def has_connected_path(self, pos):
        """指定された位置に接続されたパスがあるかチェック"""
        return pos in self.adjacency

    def is_number_completed(self, number):
        """その数字の両端が正しくつながっているか"""
        return number in self.completed_numbers

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
            return number, number in self.completed_numbers

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
        """二つのセル間に num 色の線が通っているか幅優先探索で確認する"""
        visited = {start}
        queue = [start]

        while queue:
            current = queue.pop()
            if current == end:
                return True
            for neighbor, color in self.adjacency.get(current, {}).items():
                if color == num and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        # 終点に到達できなかった
        return False

    def get_potential_path_color(self, pos):
        """現在のカーソル位置にある可能性のある線の色を返す"""
        # 接続されている線が既にある場合はその色を返す
        neighbors = self.adjacency.get(pos)
        if neighbors:
            return get_path_color(next(iter(neighbors.values())))

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
        # クリア条件: すべての数字が同じ数字と正しく接続されている
        for num, cells in self.cells_by_number.items():
            if num in self.completed_numbers:
                continue
            # 数字が1つしかない場合は、他の数字とつながっていなければOK
            if len(cells) < 2 and all(self.connected_numbers.get(p) == {num} for p in cells):
                continue
            return False
        return True

    def check_win_full(self):
        """タイムアタック用のクリア判定:
        全ペアが正しく接続され、かつ全マスがちょうど1つの数字の線で埋まっている
        （どの数字にもつながらない線や閉じたループ、空きマスがあれば不可）"""
        if not self.check_win():
            return False
        for r in range(self.GRID_ROWS):
            for c in range(self.GRID_COLS):
                if len(self.connected_numbers.get((r, c), set())) != 1:
                    return False
        return True

    def would_create_crossing(self, pos1, pos2):
        """この2点間に線を引くと交差が発生するかチェック"""
        for pos in [pos1, pos2]:
            line_count = len(self.adjacency.get(pos, {}))
            # 数字セルの場合は1本しか線を引けない
            if pos in self.number_cells:
                if line_count >= 1:
                    return True
            # 通常セルの場合は2本まで線を引ける
            else:
                if line_count >= 2:
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

            # 両端が同じ数字かつ完全に接続されているなら太く
            is_fully_connected = num != 0 and num in self.completed_numbers
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
            # 内蔵フォントは1文字3px幅+1px間隔なので、文字列幅 = 4*桁数-1
            text = str(number)
            x = center_x - (4 * len(text) - 1) // 2
            y = center_y - 2
            pyxel.text(x, y, text, base_color)
