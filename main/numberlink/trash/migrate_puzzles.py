#!/usr/bin/env python3
"""
パズルデータ移行スクリプト
- puzzles.py の組み込みパズルをJSONに変換
- 既存のJSONを新フォーマットに変換
- ファイル名を統一形式にリネーム
"""

import os
import json
from collections import defaultdict

# 既存の組み込みパズル（puzzles.pyから）
BUILTIN_PUZZLES = [
    {
        "id": "00",
        "name": "training",
        "size": 6,
        "numbers": {
            (5,0): 1, (5,5):1,
            (5,1): 2, (1,4):2,
            (3,0): 3, (2,2):3,
            (1,1): 4, (3,2):4 
        }
    },
    {
        "id": "01",
        "name": "01",
        "size": 10,
        "numbers": {
            (0,0): 1, (3,3): 1,
            (1,2): 2, (5,1): 2,
            (8,1): 3, (1,7): 3,
            (7,2): 4, (2,8): 4,
            (0,9): 5, (2,7): 5,
            (3,8): 6, (8,4): 6
        }
    },
    {
        "id": "02",
        "name": "02",
        "size": 10,
        "numbers": {
            (0,9): 1, (6,6): 1,
            (1,1): 2, (4,8): 2,
            (0,2): 3, (4,7): 3,
            (8,1): 4, (8,5): 4,
            (2,6): 5, (5,6): 5,
            (0,3): 6, (5,3): 6,
            (1,2): 7, (6,3): 7,
            (5,7): 8, (8,8): 8
        }
    },
    {
        "id": "03",
        "name": "03",
        "size": 10,
        "numbers": {
            (0,0): 1, (6,5): 1,
            (1,8): 2, (3,2): 2,
            (9,0): 3, (9,9): 3,
            (8,3): 4, (6,7): 4,
            (4,2): 5, (9,1): 5,
            (4,0): 6, (3,5): 6
        }
    },
    {
        "id": "04",
        "name": "04",
        "size": 10,
        "numbers": {
            (0,0): 1, (2,2): 1,
            (0,1): 2, (7,2): 2,
            (0,3): 3, (5,1): 3,
            (0,2): 4, (7,7): 4,
            (5,7): 5, (9,6): 5,
            (2,5): 6, (2,7): 6
        }
    },
    {
        "id": "05",
        "name": "05",
        "size": 10,
        "numbers": {
            (0,9): 1, (8,5): 1,
            (6,2): 2, (4,9): 2,
            (1,7): 3, (7,2): 3,
            (9,0): 4, (7,7): 4,
            (5,4): 5, (8,2): 5,
            (1,1): 6, (5,1): 6,
            (3,4): 7, (6,4): 7
        }
    },
    {
        "id": "06",
        "name": "06",
        "size": 10,
        "numbers": {
            (5,1): 1, (6,7): 1,
            (1,8): 2, (6,3): 2,
            (5,0): 3, (4,6): 3,
            (0,6): 4, (7,6): 4,
            (2,2): 5, (6,6): 5,
            (8,8): 6, (1,6): 6
        }
    },
    {
        "id": "07",
        "name": "07",
        "size": 10,
        "numbers": {
            (2,1): 1, (6,2): 1,
            (1,2): 2, (1,8): 2,
            (0,0): 3, (4,8): 3,
            (4,0): 4, (5,4): 4,
            (1,1): 5, (6,7): 5,
            (8,1): 6, (6,6): 6
        }
    },
    {
        "id": "08",
        "name": "08",
        "size": 10,
        "numbers": {
            (7,1): 1, (3,7): 1,
            (2,3): 2, (3,9): 2,
            (4,2): 3, (0,3): 3,
            (0,4): 4, (7,6): 4,
            (0,0): 5, (1,8): 5,
            (6,3): 6, (3,4): 6,
            (4,7): 7, (7,7): 7
        }
    },
]


def parse_coord_string(coord_str):
    """様々な形式の座標文字列をパース"""
    # "(r, c)" 形式
    if coord_str.startswith("("):
        coord_str = coord_str.strip("()").replace(" ", "")
    # "r,c" 形式
    parts = coord_str.split(",")
    return int(parts[0]), int(parts[1])


def convert_numbers_to_new_format(numbers):
    """数字辞書を新フォーマットに変換"""
    new_numbers = {}
    for key, value in numbers.items():
        if isinstance(key, tuple):
            # タプルの場合
            r, c = key
        else:
            # 文字列の場合
            r, c = parse_coord_string(key)
        new_numbers[f"{r},{c}"] = value
    return new_numbers


def load_existing_json(filepath):
    """既存のJSONファイルを読み込む"""
    with open(filepath, "r") as f:
        return json.load(f)


def get_size_from_puzzle(puzzle):
    """パズルからサイズを取得（正方形前提）"""
    size = puzzle.get("size", 10)
    if isinstance(size, list):
        return size
    return [size, size]


def main():
    # 出力ディレクトリの作成
    output_dir = "puzzles/data"
    os.makedirs(output_dir, exist_ok=True)
    
    # サイズごとにパズルを収集
    puzzles_by_size = defaultdict(list)
    
    # 1. 組み込みパズルを収集
    print("=== 組み込みパズル (puzzles.py) ===")
    for puzzle in BUILTIN_PUZZLES:
        size = get_size_from_puzzle(puzzle)
        size_key = f"{size[0]:02d}x{size[1]:02d}"
        
        new_puzzle = {
            "size": size,
            "numbers": convert_numbers_to_new_format(puzzle["numbers"])
        }
        puzzles_by_size[size_key].append(new_puzzle)
        print(f"  {puzzle['id']} -> {size_key}")
    
    # 2. 既存のJSONパズルを収集
    custom_dir = "custom_puzzles"
    if os.path.exists(custom_dir):
        print(f"\n=== カスタムパズル ({custom_dir}/) ===")
        for filename in sorted(os.listdir(custom_dir)):
            if not filename.endswith(".json"):
                continue
            
            filepath = os.path.join(custom_dir, filename)
            try:
                puzzle = load_existing_json(filepath)
                size = get_size_from_puzzle(puzzle)
                size_key = f"{size[0]:02d}x{size[1]:02d}"
                
                new_puzzle = {
                    "size": size,
                    "numbers": convert_numbers_to_new_format(puzzle["numbers"])
                }
                puzzles_by_size[size_key].append(new_puzzle)
                print(f"  {filename} -> {size_key}")
            except Exception as e:
                print(f"  {filename} -> ERROR: {e}")
    
    # 3. 新フォーマットで書き出し
    print(f"\n=== 出力 ({output_dir}/) ===")
    total_count = 0
    for size_key in sorted(puzzles_by_size.keys()):
        puzzles = puzzles_by_size[size_key]
        for i, puzzle in enumerate(puzzles, 1):
            puzzle_id = f"{size_key}_{i:03d}"
            new_filename = f"{puzzle_id}.json"
            
            output_data = {
                "id": puzzle_id,
                "size": puzzle["size"],
                "numbers": puzzle["numbers"]
            }
            
            output_path = os.path.join(output_dir, new_filename)
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)
            
            print(f"  {new_filename}")
            total_count += 1
    
    print(f"\n完了: {total_count}個のパズルを変換しました")


if __name__ == "__main__":
    main()
