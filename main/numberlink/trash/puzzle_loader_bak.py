from main.numberlink.trash.puzzles import PUZZLES

def get_puzzle_list():
    """利用可能なパズルのリストを返す"""
    return [{"id": puzzle["id"], "name": puzzle["name"], "size": puzzle["size"]} for puzzle in PUZZLES]

def load_puzzle(puzzle_id):
    """指定されたIDのパズルデータを読み込む"""
    for puzzle in PUZZLES:
        if puzzle["id"] == puzzle_id:
            return puzzle
    return None
