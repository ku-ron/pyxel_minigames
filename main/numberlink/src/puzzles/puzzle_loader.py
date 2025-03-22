import os
import json
from puzzles.puzzles import PUZZLES

def load_custom_puzzles():
    """カスタムパズルをロードする関数"""
    custom_puzzles = []
    
    # カスタムパズルディレクトリの確認
    if not os.path.exists("custom_puzzles"):
        return custom_puzzles
    
    # ディレクトリ内のJSONファイルをロード
    for filename in os.listdir("custom_puzzles"):
        if filename.endswith(".json"):
            filepath = os.path.join("custom_puzzles", filename)
            try:
                with open(filepath, "r") as f:
                    puzzle_data = json.load(f)
                
                # 必要なフィールドの確認
                if all(key in puzzle_data for key in ["id", "name", "size", "numbers"]):
                    # 数字データを変換（文字列キーをタプルに）
                    number_cells = {}
                    for str_pos, num in puzzle_data["numbers"].items():
                        # "(r, c)" 形式の文字列からタプルに変換
                        try:
                            str_pos = str_pos.strip("()").replace(" ", "")
                            r, c = map(int, str_pos.split(","))
                            number_cells[(r, c)] = num
                        except:
                            # 変換に失敗した場合はスキップ
                            continue
                    
                    # 変換後のデータで置き換え
                    puzzle_data["numbers"] = number_cells
                    custom_puzzles.append(puzzle_data)
            except:
                # 読み込みエラーは無視
                pass
    
    return custom_puzzles

def get_all_puzzles():
    """組み込みパズルとカスタムパズルを結合したリストを返す"""
    # カスタムパズルをロード
    custom_puzzles = load_custom_puzzles()
    
    # 組み込みパズルとカスタムパズルを結合
    all_puzzles = PUZZLES.copy() + custom_puzzles
    
    return all_puzzles

def get_puzzle_list():
    """利用可能なパズルのリストを返す（カスタムパズルを含む）"""
    all_puzzles = get_all_puzzles()
    return [{"id": puzzle["id"], "name": puzzle["name"], "size": puzzle["size"]} for puzzle in all_puzzles]

def load_puzzle(puzzle_id):
    """指定されたIDのパズルデータを読み込む（カスタムパズルを含む）"""
    # すべてのパズルから検索
    all_puzzles = get_all_puzzles()
    for puzzle in all_puzzles:
        if puzzle["id"] == puzzle_id:
            return puzzle
    return None
