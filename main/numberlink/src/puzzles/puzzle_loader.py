import os
import json

# パズルデータのディレクトリ
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _parse_numbers(numbers_dict):
    """座標文字列をタプルに変換"""
    result = {}
    for str_pos, num in numbers_dict.items():
        # "r,c" 形式
        parts = str_pos.split(",")
        r, c = int(parts[0]), int(parts[1])
        result[(r, c)] = num
    return result


def _load_all_puzzles():
    """全パズルをロードしてキャッシュ"""
    puzzles = []
    
    if not os.path.exists(DATA_DIR):
        return puzzles
    
    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.endswith(".json"):
            continue
        
        filepath = os.path.join(DATA_DIR, filename)
        try:
            with open(filepath, "r") as f:
                puzzle_data = json.load(f)
            
            # 必要なフィールドの確認
            if "id" not in puzzle_data or "size" not in puzzle_data or "numbers" not in puzzle_data:
                continue
            
            # サイズの正規化 (int -> [int, int])
            size = puzzle_data["size"]
            if isinstance(size, int):
                size = [size, size]
            
            puzzles.append({
                "id": puzzle_data["id"],
                "size": size,
                "numbers": _parse_numbers(puzzle_data["numbers"])
            })
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue
    
    return puzzles


# モジュール読み込み時にキャッシュ
_PUZZLE_CACHE = None


def _get_puzzles():
    """キャッシュされたパズルリストを取得"""
    global _PUZZLE_CACHE
    if _PUZZLE_CACHE is None:
        _PUZZLE_CACHE = _load_all_puzzles()
    return _PUZZLE_CACHE


def get_puzzle_list():
    """利用可能なパズルのリストを返す"""
    puzzles = _get_puzzles()
    return [{"id": p["id"], "size": p["size"]} for p in puzzles]


def load_puzzle(puzzle_id):
    """指定されたIDのパズルデータを読み込む"""
    puzzles = _get_puzzles()
    for puzzle in puzzles:
        if puzzle["id"] == puzzle_id:
            return puzzle
    return None
