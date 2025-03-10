import pyxel
from menu import MenuScreen
from game import NumberlinkGame

class NumberlinkApp:
    def __init__(self):
        # ウィンドウサイズの設定 - 10x10のグリッドを収めるサイズに調整
        # 10x10グリッド + 余白のために必要なサイズを計算
        # セルサイズ16px x 10マス = 160px + 左右の余白
        # UI領域の高さも考慮
        self.WINDOW_WIDTH = 240  # 160px + 左右40px余白
        self.WINDOW_HEIGHT = 240  # 160px + 上下40px余白 + UI領域40px
        
        # Pyxelの初期化
        pyxel.init(self.WINDOW_WIDTH, self.WINDOW_HEIGHT, title="Numberlink", fps=60)
        
        # メニュー画面の作成
        self.menu_screen = MenuScreen(self)
        
        # 現在の画面を設定
        self.current_screen = self.menu_screen
        
        # ゲーム開始
        pyxel.run(self.update, self.draw)
    
    def start_game(self, puzzle_id):
        """指定されたパズルでゲームを開始する"""
        self.current_screen = NumberlinkGame(self, puzzle_id)
    
    def return_to_menu(self):
        """メニュー画面に戻る"""
        self.current_screen = self.menu_screen
    
    def update(self):
        """ゲームの更新処理"""
        # ESCキーでゲーム終了
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()
        
        # 現在の画面の更新処理を呼び出す
        self.current_screen.update()
    
    def draw(self):
        """ゲームの描画処理"""
        # 画面をクリア
        pyxel.cls(7)  # 背景色（薄い灰色）
        
        # 現在の画面の描画処理を呼び出す
        self.current_screen.draw()

# メインエントリーポイント
if __name__ == "__main__":
    NumberlinkApp()
