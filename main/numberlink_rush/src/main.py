import pyxel
from utils.colors import GRAY, DARK_GRAY, WHITE, BLACK
from puzzle_pool import DIFFICULTIES, pool_size
from rush_game import RushGame, TIME_LIMIT
import bgm


class TitleScreen:
    def __init__(self, app):
        self.app = app
        self.index = 0
        bgm.set_track(app.bgm_index)
        bgm.play_bgm(fast=False)   # タイトルで選択中の曲を試聴

    def change_bgm(self, delta):
        n = len(bgm.track_names())
        self.app.bgm_index = (self.app.bgm_index + delta) % n
        bgm.set_track(self.app.bgm_index)
        bgm.play_bgm(fast=False)
        bgm.se_select()

    def update(self):
        if pyxel.btnp(pyxel.KEY_LEFT, 10, 4) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT, 10, 4):
            self.change_bgm(-1)
        elif pyxel.btnp(pyxel.KEY_RIGHT, 10, 4) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT, 10, 4):
            self.change_bgm(1)
        if pyxel.btnp(pyxel.KEY_UP, 10, 4) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP, 10, 4):
            self.index = (self.index - 1) % len(DIFFICULTIES)
            bgm.se_select()
        elif pyxel.btnp(pyxel.KEY_DOWN, 10, 4) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN, 10, 4):
            self.index = (self.index + 1) % len(DIFFICULTIES)
            bgm.se_select()
        if (pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE)
                or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)):
            key = DIFFICULTIES[self.index][0]
            if pool_size(key) > 0:
                bgm.stop_bgm()
                self.app.start_game(key)

    def draw(self):
        W = self.app.WINDOW_WIDTH
        title = "NUMBERLINK RUSH"
        pyxel.text(W // 2 - len(title) * 2, 30, title, 8)
        sub = f"How many can you solve in {TIME_LIMIT // 60} minutes?"
        pyxel.text(W // 2 - len(sub) * 2, 42, sub, DARK_GRAY)

        y = 80
        for i, (key, label, desc) in enumerate(DIFFICULTIES):
            selected = i == self.index
            best = self.app.best.get(key)
            best_text = f"best {best}" if best is not None else ""
            color = 8 if selected else BLACK
            prefix = "> " if selected else "  "
            pyxel.text(40, y, f"{prefix}{label}", color)
            pyxel.text(110, y, best_text, 3)
            pyxel.text(52, y + 8, desc, GRAY if not selected else DARK_GRAY)
            pyxel.text(52, y + 16, f"{pool_size(key)} puzzles", GRAY)
            y += 32

        # BGM 選択（左右キー）
        names = bgm.track_names()
        x = 40
        pyxel.text(x, y + 4, "BGM:", DARK_GRAY)
        x += 24
        for i, name in enumerate(names):
            selected = i == self.app.bgm_index
            label = f"{i + 1}" if i < len(names) - 1 else "OFF"
            pyxel.text(x, y + 4, ("[" if selected else " ") + label + ("]" if selected else " "),
                       8 if selected else GRAY)
            x += (len(label) + 2) * 4 + 4
        cur = names[self.app.bgm_index]
        pyxel.text(40 + 24, y + 12, cur if cur != "OFF" else "no music", DARK_GRAY)

        help1 = "UP/DOWN: select  LEFT/RIGHT: BGM"
        help2 = "ENTER/B: start"
        pyxel.text(W // 2 - len(help1) * 2, self.app.WINDOW_HEIGHT - 40, help1, GRAY)
        pyxel.text(W // 2 - len(help2) * 2, self.app.WINDOW_HEIGHT - 30, help2, GRAY)


class ResultScreen:
    def __init__(self, app, difficulty, solved, skipped, is_best):
        self.app = app
        self.difficulty = difficulty
        self.solved = solved
        self.skipped = skipped
        self.is_best = is_best
        self.wait = 60  # 誤操作防止: 1秒はキーを受け付けない

    def update(self):
        if self.wait > 0:
            self.wait -= 1
            return
        if (pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE)
                or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)):
            self.app.return_to_title()

    def draw(self):
        W = self.app.WINDOW_WIDTH
        label = next(d[1] for d in DIFFICULTIES if d[0] == self.difficulty)
        msg = "TIME UP!"
        pyxel.text(W // 2 - len(msg) * 2, 50, msg, 8)
        pyxel.text(W // 2 - len(label) * 2, 66, label, DARK_GRAY)

        score = f"SOLVED  {self.solved}"
        pyxel.text(W // 2 - len(score) * 2, 96, score, BLACK)
        skip = f"SKIPPED {self.skipped}"
        pyxel.text(W // 2 - len(skip) * 2, 108, skip, GRAY)
        if self.is_best and self.solved > 0:
            nb = "NEW BEST!"
            if (pyxel.frame_count // 15) % 2:
                pyxel.text(W // 2 - len(nb) * 2, 124, nb, 10)

        if self.wait == 0:
            back = "ENTER/B: back to title"
            pyxel.text(W // 2 - len(back) * 2, self.app.WINDOW_HEIGHT - 40, back, GRAY)


class RushApp:
    def __init__(self):
        # 10x10 (160px) + 上のヘッダ40px + 下のフッタ40px
        self.WINDOW_WIDTH = 240
        self.WINDOW_HEIGHT = 280
        self.BOARD_TOP = 36
        self.best = {}  # 難易度 → 最高スコア（起動中のみ保持）
        self.bgm_index = 0  # 選択中の BGM（最後の番号は OFF）

        pyxel.init(self.WINDOW_WIDTH, self.WINDOW_HEIGHT, title="Numberlink Rush", fps=60)
        self.current_screen = TitleScreen(self)
        pyxel.run(self.update, self.draw)

    def start_game(self, difficulty):
        self.current_screen = RushGame(self, difficulty)

    def show_result(self, difficulty, solved, skipped):
        is_best = solved > self.best.get(difficulty, -1)
        if is_best:
            self.best[difficulty] = solved
        self.current_screen = ResultScreen(self, difficulty, solved, skipped, is_best)

    def return_to_title(self):
        self.current_screen = TitleScreen(self)

    def update(self):
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()
        self.current_screen.update()

    def draw(self):
        pyxel.cls(7)
        self.current_screen.draw()


if __name__ == "__main__":
    RushApp()
