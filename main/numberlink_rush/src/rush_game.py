import time
import pyxel
from board import NumberlinkBoard
from utils.colors import GRAY, DARK_GRAY, WHITE, BLACK, get_color_for_number
from utils.grid import is_adjacent
from puzzle_pool import PuzzleDeck, DIFFICULTIES
import bgm

TIME_LIMIT = 5 * 60          # 秒
HURRY_SEC = 30               # 残りこの秒数でテンポアップ
CLEAR_FLASH_FRAMES = 40      # クリア演出のフレーム数
COUNTDOWN_FRAMES = 3 * 60 + 30   # 開始前の 3・2・1（各1秒）＋ START（0.5秒）


class RushGame:
    """タイムアタック: 制限時間内に何問解けるか"""

    def __init__(self, app, difficulty):
        self.app = app
        self.difficulty = difficulty
        self.deck = PuzzleDeck(difficulty)

        self.cell_size = 16
        self.solved = 0
        self.skipped = 0
        self.start_time = None           # カウントダウン終了時に設定
        self.countdown = COUNTDOWN_FRAMES
        self.countdown_label = None
        self.hurry = False
        self.finished = False
        self.last_tick_sec = None

        # クリア演出
        self.clear_timer = 0

        self.board = None
        self.puzzle = None
        self.next_puzzle()

    # ──────────────────────────────────────
    #  問題の切り替え
    # ──────────────────────────────────────

    def next_puzzle(self):
        self.puzzle = self.deck.next()
        if self.puzzle is None:
            # プールが空
            self.board = NumberlinkBoard(10, 10, {}, self.cell_size, 40, 40)
            return
        rows, cols = self.puzzle["size"]
        offset_x = (self.app.WINDOW_WIDTH - cols * self.cell_size) // 2
        offset_y = self.app.BOARD_TOP
        self.board = NumberlinkBoard(rows, cols, self.puzzle["numbers"],
                                     self.cell_size, offset_x, offset_y)
        self.reset_cursor()

    def reset_cursor(self):
        self.cursor_pos = [0, 0]
        self.draw_mode = False
        self.invalid_move = False
        self.invalid_move_timer = 0
        self.invalid_move_target = None

    def reset_puzzle(self):
        self.board.paths = {}
        self.board.connected_numbers = {pos: {num} for pos, num in self.board.number_cells.items()}
        self.reset_cursor()

    # ──────────────────────────────────────
    #  時間
    # ──────────────────────────────────────

    def remaining(self):
        if self.start_time is None:
            return float(TIME_LIMIT)
        return max(0.0, TIME_LIMIT - (time.time() - self.start_time))

    def _countdown_text(self):
        """残りフレーム数から表示文字を返す（3 → 2 → 1 → START）"""
        if self.countdown > 150:
            return "3"
        if self.countdown > 90:
            return "2"
        if self.countdown > 30:
            return "1"
        return "START"

    def update_countdown(self):
        label = self._countdown_text()
        if label != self.countdown_label:
            self.countdown_label = label
            if label == "START":
                bgm.se_start()
            else:
                bgm.se_tick()
        self.countdown -= 1
        if self.countdown == 0:
            self.start_time = time.time()
            bgm.play_bgm(fast=False)

    # ──────────────────────────────────────
    #  更新
    # ──────────────────────────────────────

    def update(self):
        if self.finished:
            return

        if self.countdown > 0:
            self.update_countdown()
            return

        rem = self.remaining()
        if rem <= 0:
            self.finish()
            return

        # 残り30秒でテンポアップ、残り10秒は毎秒ティック音
        if not self.hurry and rem <= HURRY_SEC:
            self.hurry = True
            bgm.play_bgm(fast=True)
        if rem <= 10:
            sec = int(rem)
            if sec != self.last_tick_sec:
                self.last_tick_sec = sec
                bgm.se_tick()

        # クリア演出中は入力を受け付けず、終わったら次の問題へ
        if self.clear_timer > 0:
            self.clear_timer -= 1
            if self.clear_timer == 0:
                self.next_puzzle()
            return

        if self.invalid_move:
            self.invalid_move_timer += 1
            if self.invalid_move_timer >= 4:
                self.invalid_move = False
                self.invalid_move_timer = 0
                self.invalid_move_target = None
            return

        self.handle_input()

    def finish(self):
        self.finished = True
        bgm.stop_bgm()
        bgm.se_timeup()
        self.app.show_result(self.difficulty, self.solved, self.skipped)

    def handle_input(self):
        # 中断してタイトルへ (Mキー / ゲームパッドBACK)
        if pyxel.btnp(pyxel.KEY_M) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_BACK):
            bgm.stop_bgm()
            self.app.return_to_title()
            return

        # モード切替 (Space / A)
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A):
            self.draw_mode = not self.draw_mode

        # カーソル移動（長押しリピートあり）
        if pyxel.btnp(pyxel.KEY_UP, 10, 4) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP, 10, 4):
            self.try_move_cursor(0, -1)
        elif pyxel.btnp(pyxel.KEY_DOWN, 10, 4) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN, 10, 4):
            self.try_move_cursor(0, 1)
        elif pyxel.btnp(pyxel.KEY_LEFT, 10, 4) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT, 10, 4):
            self.try_move_cursor(-1, 0)
        elif pyxel.btnp(pyxel.KEY_RIGHT, 10, 4) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT, 10, 4):
            self.try_move_cursor(1, 0)

        # リセット (R / X)
        if pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_X):
            self.reset_puzzle()

        # スキップ (S / Y)
        if pyxel.btnp(pyxel.KEY_S) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_Y):
            self.skipped += 1
            bgm.se_skip()
            self.next_puzzle()

    # ──────────────────────────────────────
    #  カーソル移動と線の操作（本家ナンバーリンクと同じ挙動）
    # ──────────────────────────────────────

    def try_move_cursor(self, dx, dy):
        new_row = max(0, min(self.board.GRID_ROWS - 1, self.cursor_pos[0] + dy))
        new_col = max(0, min(self.board.GRID_COLS - 1, self.cursor_pos[1] + dx))
        new_pos = (new_row, new_col)
        old_pos = (self.cursor_pos[0], self.cursor_pos[1])
        if new_pos == old_pos:
            return

        if self.draw_mode and is_adjacent(old_pos, new_pos):
            edge = (min(old_pos, new_pos), max(old_pos, new_pos))
            if edge not in self.board.paths:
                if (self.board.would_create_crossing(old_pos, new_pos)
                        or self.would_connect_different_numbers(old_pos, new_pos)):
                    self.invalid_move = True
                    self.invalid_move_timer = 0
                    self.invalid_move_target = new_pos
                    bgm.se_invalid()
                    return

        self.move_cursor(dx, dy)

    def would_connect_different_numbers(self, pos1, pos2):
        if pos1 in self.board.number_cells and pos2 in self.board.number_cells:
            return self.board.number_cells[pos1] != self.board.number_cells[pos2]
        nums1 = self.board.connected_numbers.get(pos1, set())
        nums2 = self.board.connected_numbers.get(pos2, set())
        if not nums1 or not nums2:
            return False
        return nums1 != nums2

    def move_cursor(self, dx, dy):
        new_row = max(0, min(self.board.GRID_ROWS - 1, self.cursor_pos[0] + dy))
        new_col = max(0, min(self.board.GRID_COLS - 1, self.cursor_pos[1] + dx))
        old_pos = (self.cursor_pos[0], self.cursor_pos[1])
        new_pos = (new_row, new_col)
        if new_pos == old_pos:
            return

        changed = False
        if self.draw_mode and is_adjacent(old_pos, new_pos):
            edge = (min(old_pos, new_pos), max(old_pos, new_pos))
            if edge in self.board.paths:
                self.board.remove_path(edge)
            else:
                self.board.add_path(edge)
            changed = True

        self.cursor_pos = [new_row, new_col]
        bgm.se_draw() if changed else bgm.se_move()

        # 線が変わるたびにクリア判定（全マス埋め＋全ペア接続）
        if changed and self.board.check_win_full():
            self.solved += 1
            self.clear_timer = CLEAR_FLASH_FRAMES
            bgm.se_clear()

    # ──────────────────────────────────────
    #  描画
    # ──────────────────────────────────────

    def get_active_number(self):
        pos = (self.cursor_pos[0], self.cursor_pos[1])
        if pos in self.board.number_cells:
            return self.board.number_cells[pos]
        nums = self.board.connected_numbers.get(pos, set())
        if len(nums) == 1:
            return next(iter(nums))
        return None

    def draw_target_highlight(self):
        """カーソルが乗っている数字の両端を、点滅する点線の枠で強調（接続済みは除く）"""
        num = self.get_active_number()
        if num is None:
            return
        positions = [p for p, n in self.board.number_cells.items() if n == num]
        if self.board.are_connected(positions, num):
            return
        if (pyxel.frame_count // 30) % 2:
            return
        color = get_color_for_number(num)
        cell = self.board.CELL_SIZE
        for r, c in positions:
            x1 = self.board.OFFSET_X + c * cell + 1
            y1 = self.board.OFFSET_Y + r * cell + 1
            x2 = x1 + cell - 2
            y2 = y1 + cell - 2
            for px in range(x1, x2 + 1):
                for py in (y1, y2):
                    if (px + py) % 2 == 0:
                        pyxel.pset(px, py, color)
            for py in range(y1 + 1, y2):
                for px in (x1, x2):
                    if (px + py) % 2 == 0:
                        pyxel.pset(px, py, color)

    def draw_cursor(self):
        row, col = self.cursor_pos
        cell = self.board.CELL_SIZE
        if not self.invalid_move:
            color = 8 if self.draw_mode else 12
            x = self.board.OFFSET_X + col * cell
            y = self.board.OFFSET_Y + row * cell
            for i in range(2):
                pyxel.rectb(x + i, y + i, cell + 1 - i * 2, cell + 1 - i * 2, color)
            if self.draw_mode and (row, col) not in self.board.number_cells:
                dot_color = self.board.get_potential_path_color((row, col))
                pyxel.circ(x + cell // 2, y + cell // 2, 2, dot_color)
        else:
            t = 1.0 - self.invalid_move_timer / 4.0
            dir_row = dir_col = 0
            if self.invalid_move_target:
                tr, tc = self.invalid_move_target
                dir_row = (tr > row) - (tr < row)
                dir_col = (tc > col) - (tc < col)
            x = self.board.OFFSET_X + col * cell + dir_col * t * 2
            y = self.board.OFFSET_Y + row * cell + dir_row * t * 2
            for i in range(2):
                pyxel.rectb(int(x) + i, int(y) + i, cell + 1 - i * 2, cell + 1 - i * 2, 8)

    def draw_header(self):
        W = self.app.WINDOW_WIDTH
        rem = self.remaining()
        m, s = int(rem) // 60, int(rem) % 60
        timer_color = 8 if rem <= HURRY_SEC else BLACK
        pyxel.text(8, 6, f"TIME {m}:{s:02d}", timer_color)

        # 残り時間バー
        bar_x, bar_y, bar_w, bar_h = 8, 14, W - 16, 4
        pyxel.rectb(bar_x, bar_y, bar_w, bar_h, GRAY)
        fill = int((bar_w - 2) * rem / TIME_LIMIT)
        if fill > 0:
            pyxel.rect(bar_x + 1, bar_y + 1, fill, bar_h - 2, timer_color)

        # スコア
        score_text = f"SOLVED {self.solved}"
        pyxel.text(W - 8 - len(score_text) * 4, 6, score_text, 3)
        # 難易度
        label = next(d[1] for d in DIFFICULTIES if d[0] == self.difficulty)
        pyxel.text(8, 22, f"{label}  SKIP {self.skipped}", DARK_GRAY)

    def draw_footer(self):
        W = self.app.WINDOW_WIDTH
        y = self.board.OFFSET_Y + self.board.GRID_ROWS * self.board.CELL_SIZE + 8
        mode_text = "DRAW MODE" if self.draw_mode else "MOVE MODE"
        pyxel.text(W // 2 - len(mode_text) * 2, y, mode_text, 8 if self.draw_mode else 12)
        help1 = "SPACE/A:Mode R/X:Reset S/Y:Skip"
        help2 = "M/BACK:Quit"
        pyxel.text(W // 2 - len(help1) * 2, y + 10, help1, GRAY)
        pyxel.text(W // 2 - len(help2) * 2, y + 18, help2, GRAY)

    def draw_countdown(self):
        """盤面の中央に大きな文字で 3・2・1・START を表示"""
        if self.countdown <= 0:
            return
        label = self._countdown_text()
        scale = 4
        w, h = len(label) * 4 - 1, 5
        # 内蔵フォントを画像バンク2に描いて拡大コピーする（blt の scale は領域中心基準）
        img = pyxel.images[2]
        img.rect(0, 0, w + 2, h + 2, 0)
        img.text(1, 1, label, 8 if label != "START" else 3)
        W = self.app.WINDOW_WIDTH
        cx = W // 2
        cy = self.board.OFFSET_Y + self.board.GRID_ROWS * self.board.CELL_SIZE // 2
        bw, bh = (w + 2) * scale + 8, (h + 2) * scale + 8
        pyxel.rect(cx - bw // 2, cy - bh // 2, bw, bh, WHITE)
        pyxel.rectb(cx - bw // 2, cy - bh // 2, bw, bh, GRAY)
        pyxel.blt(cx - (w + 2) // 2, cy - (h + 2) // 2, img, 0, 0, w + 2, h + 2, 0, 0, scale)

    def draw_clear_flash(self):
        if self.clear_timer <= 0:
            return
        W = self.app.WINDOW_WIDTH
        y = self.board.OFFSET_Y + self.board.GRID_ROWS * self.board.CELL_SIZE // 2 - 8
        pyxel.rect(0, y, W, 16, WHITE)
        msg = "CLEAR!"
        pyxel.text(W // 2 - len(msg) * 2, y + 5, msg, 8 if (self.clear_timer // 4) % 2 else 10)

    def draw(self):
        if self.puzzle is None:
            pyxel.text(10, 60, "No puzzles found in data/", 8)
            return
        self.draw_header()
        self.board.draw()
        if self.clear_timer == 0 and self.countdown <= 0:
            self.draw_target_highlight()
            self.draw_cursor()
        self.draw_footer()
        self.draw_clear_flash()
        self.draw_countdown()
