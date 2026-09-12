import pyxel
from utils.colors import GRAY

def draw_grid(offset_x, offset_y, grid_rows, grid_cols, cell_size):
    """グリッドを描画する共通関数"""
    # 縦線を描画
    for i in range(grid_cols + 1):
        # 周囲の縁（最初と最後の線）は実線
        if i == 0 or i == grid_cols:
            pyxel.line(
                offset_x + i * cell_size, 
                offset_y, 
                offset_x + i * cell_size, 
                offset_y + grid_rows * cell_size, 
                GRAY)
        else:
            # 内側のグリッド線は点線に
            for j in range(0, grid_rows * cell_size, 4):
                pyxel.pset(offset_x + i * cell_size, offset_y + j, GRAY)
    
    # 横線を描画
    for i in range(grid_rows + 1):
        # 周囲の縁（最初と最後の線）は実線
        if i == 0 or i == grid_rows:
            pyxel.line(
                offset_x, 
                offset_y + i * cell_size, 
                offset_x + grid_cols * cell_size, 
                offset_y + i * cell_size, 
                GRAY)
        else:
            # 内側のグリッド線は点線に
            for j in range(0, grid_cols * cell_size, 4):
                pyxel.pset(offset_x + j, offset_y + i * cell_size, GRAY)

def is_adjacent(pos1, pos2):
    """2つの位置が隣接しているかをチェック（上下左右）"""
    r1, c1 = pos1
    r2, c2 = pos2
    return (abs(r1 - r2) == 1 and c1 == c2) or (r1 == r2 and abs(c1 - c2) == 1)

def is_position_valid(row, col, grid_rows, grid_cols):
    """指定された位置がグリッド内かどうかをチェック"""
    return 0 <= row < grid_rows and 0 <= col < grid_cols
