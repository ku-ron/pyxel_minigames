# 数字と色のマッピング
# （多くの数字に対応するため、色をローテーションする）
def get_color_for_number(number):
    """数字に対応する色を返す（ローテーション）"""
    colors = [8, 3, 12, 2, 9, 14, 5, 10, 4]  # 赤, 濃い緑, 水色, 濃い紫, オレンジ, ピンク, 暗い青灰色, 黄色, 茶色
    return colors[(number - 1) % len(colors)]

# 色定数
BLACK = 0
WHITE = 7
GRAY = 5
DARK_GRAY = 6

# 数字の色を取得
def get_path_color(num):
    """パス番号から色を取得"""
    if num == 0:
        return BLACK
    return get_color_for_number(num)
