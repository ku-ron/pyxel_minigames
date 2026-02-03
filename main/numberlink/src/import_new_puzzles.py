#!/usr/bin/env python3
"""
新しいパズルを整理してdataフォルダに追加するスクリプト

使い方:
    python import_new_puzzles.py

動作:
    1. new_pazzles/ から全JSONを読み込む
    2. puzzles/data/ の既存パズルの最大番号を確認
    3. 新パズルにidを付与し、連番を振り直す
    4. puzzles/data/ に出力
"""

import os
import json
from collections import defaultdict

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NEW_PUZZLES_DIR = os.path.join(SCRIPT_DIR, "new_pazzles")
DATA_DIR = os.path.join(SCRIPT_DIR, "puzzles", "data")


def get_size_key(size):
    """サイズからキーを生成 (例: [8, 8] -> "08x08")"""
    if isinstance(size, int):
        return f"{size:02d}x{size:02d}"
    return f"{size[0]:02d}x{size[1]:02d}"


def parse_existing_puzzles():
    """既存のパズルからサイズごとの最大番号を取得"""
    max_numbers = defaultdict(int)
    
    if not os.path.exists(DATA_DIR):
        return max_numbers
    
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".json"):
            continue
        
        # ファイル名から番号を抽出 (例: "08x08_012.json" -> size_key="08x08", num=12)
        name = filename.replace(".json", "")
        parts = name.split("_")
        if len(parts) == 2:
            size_key = parts[0]
            try:
                num = int(parts[1])
                max_numbers[size_key] = max(max_numbers[size_key], num)
            except ValueError:
                pass
    
    return max_numbers


def load_new_puzzle(filepath):
    """新しいパズルファイルを読み込む"""
    with open(filepath, "r") as f:
        data = json.load(f)
    return data


def convert_puzzle(puzzle_data, new_id):
    """パズルを新フォーマットに変換"""
    size = puzzle_data["size"]
    if isinstance(size, int):
        size = [size, size]
    
    return {
        "id": new_id,
        "size": size,
        "numbers": puzzle_data["numbers"]
    }


def save_puzzle(puzzle_data, filepath):
    """パズルをJSONファイルに保存"""
    with open(filepath, "w") as f:
        json.dump(puzzle_data, f, indent=2)


def main():
    print("=== パズルインポートスクリプト ===\n")
    
    # 1. 既存パズルの最大番号を取得
    print("1. 既存パズルの確認...")
    max_numbers = parse_existing_puzzles()
    for size_key, max_num in sorted(max_numbers.items()):
        print(f"   {size_key}: 最大番号 {max_num:03d}")
    
    # 2. 新パズルの読み込み
    print(f"\n2. 新パズルの読み込み ({NEW_PUZZLES_DIR})...")
    
    if not os.path.exists(NEW_PUZZLES_DIR):
        print(f"   エラー: {NEW_PUZZLES_DIR} が見つかりません")
        return
    
    # サイズごとにパズルを分類
    new_puzzles_by_size = defaultdict(list)
    
    for filename in sorted(os.listdir(NEW_PUZZLES_DIR)):
        if not filename.endswith(".json"):
            continue
        
        filepath = os.path.join(NEW_PUZZLES_DIR, filename)
        try:
            puzzle_data = load_new_puzzle(filepath)
            size_key = get_size_key(puzzle_data["size"])
            new_puzzles_by_size[size_key].append({
                "filename": filename,
                "data": puzzle_data
            })
        except Exception as e:
            print(f"   警告: {filename} の読み込みに失敗: {e}")
    
    for size_key, puzzles in sorted(new_puzzles_by_size.items()):
        print(f"   {size_key}: {len(puzzles)}個")
    
    # 3. 変換と保存
    print(f"\n3. 変換と保存 ({DATA_DIR})...")
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    total_saved = 0
    for size_key in sorted(new_puzzles_by_size.keys()):
        puzzles = new_puzzles_by_size[size_key]
        current_num = max_numbers.get(size_key, 0)
        
        for puzzle_info in puzzles:
            current_num += 1
            new_id = f"{size_key}_{current_num:03d}"
            new_filename = f"{new_id}.json"
            
            converted = convert_puzzle(puzzle_info["data"], new_id)
            output_path = os.path.join(DATA_DIR, new_filename)
            
            save_puzzle(converted, output_path)
            print(f"   {puzzle_info['filename']} -> {new_filename}")
            total_saved += 1
        
        # 更新後の最大番号を記録
        max_numbers[size_key] = current_num
    
    # 4. サマリー
    print(f"\n=== 完了 ===")
    print(f"追加されたパズル: {total_saved}個")
    print(f"\n最終的なパズル数:")
    for size_key, max_num in sorted(max_numbers.items()):
        print(f"   {size_key}: {max_num:03d}個")
    
    print(f"\n※ 元ファイル ({NEW_PUZZLES_DIR}) は手動で削除してください")


if __name__ == "__main__":
    main()
