import os
import json
import random

# 問題プール: data/pool_<難易度>.json に [{"id", "size", "numbers"}, ...] の形で同梱
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

DIFFICULTIES = [
    # (キー, 表示名, 説明)
    ("A", "EASY",   "numbers on edges, may touch"),
    ("B", "NORMAL", "numbers on edges, no touching"),
    ("C", "HARD",   "no edges, no touching"),
]


def _parse_numbers(numbers_dict):
    """"r,c" 形式の座標文字列をタプルに変換"""
    result = {}
    for str_pos, num in numbers_dict.items():
        r, c = str_pos.split(",")
        result[(int(r), int(c))] = num
    return result


_CACHE = {}


def load_pool(difficulty):
    """難易度キー(A/B/C)のプールを読み込んでキャッシュ"""
    if difficulty in _CACHE:
        return _CACHE[difficulty]
    path = os.path.join(DATA_DIR, f"pool_{difficulty}.json")
    puzzles = []
    if os.path.exists(path):
        with open(path, "r") as f:
            for p in json.load(f):
                size = p["size"]
                if isinstance(size, int):
                    size = [size, size]
                puzzles.append({
                    "id": p["id"],
                    "size": size,
                    "numbers": _parse_numbers(p["numbers"]),
                })
    _CACHE[difficulty] = puzzles
    return puzzles


def pool_size(difficulty):
    return len(load_pool(difficulty))


class PuzzleDeck:
    """1回のプレイ用に問題をシャッフルして順に配る（使い切ったら再シャッフル）"""

    def __init__(self, difficulty):
        self.pool = load_pool(difficulty)
        self.order = []
        self.pos = 0

    def next(self):
        if not self.pool:
            return None
        if self.pos >= len(self.order):
            self.order = list(range(len(self.pool)))
            random.shuffle(self.order)
            self.pos = 0
        puzzle = self.pool[self.order[self.pos]]
        self.pos += 1
        return puzzle
