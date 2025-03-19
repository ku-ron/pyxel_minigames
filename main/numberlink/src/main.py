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
        
        # 音楽再生状態を管理するフラグ
        self.music_enabled = True
        
        # Pyxelの初期化（マウス操作を有効化）
        # pyxel.init(self.WINDOW_WIDTH, self.WINDOW_HEIGHT, title="Numberlink", fps=60, mouse=True)
        pyxel.init(self.WINDOW_WIDTH, self.WINDOW_HEIGHT, title="Numberlink", fps=60)
        
        # リソースファイルの読み込み
        pyxel.load("music_numberlink.pyxres")
        
        # BGM再生開始
        self.play_music()
        
        # メニュー画面の作成
        self.menu_screen = MenuScreen(self)
        
        # 現在の画面を設定
        self.current_screen = self.menu_screen
        
        # ゲーム開始
        pyxel.run(self.update, self.draw)
    
    def play_music(self):
        """BGMを再生する"""
        if self.music_enabled:
            pyxel.playm(0, loop=True)
    
    def stop_music(self):
        """BGMを停止する"""
        pyxel.stop()
    
    def toggle_music(self):
        """BGMのオン/オフを切り替える"""
        self.music_enabled = not self.music_enabled
        if self.music_enabled:
            self.play_music()
        else:
            self.stop_music()
    
    def draw_music_button(self):
        """BGMオン/オフボタンを描画する"""
        # ボタンの位置とサイズ
        self.btn_x = self.WINDOW_WIDTH - 60
        self.btn_y = 5
        self.btn_width = 55
        self.btn_height = 15
        
        # ボタンの背景
        btn_color = 12 if self.music_enabled else 5  # 有効時は水色、無効時は紫色
        pyxel.rect(self.btn_x, self.btn_y, self.btn_width, self.btn_height, btn_color)
        
        # ボタンの枠線
        pyxel.rectb(self.btn_x, self.btn_y, self.btn_width, self.btn_height, 7)
        
        # ボタンのテキスト
        status = "BGM: ON" if self.music_enabled else "BGM: OFF"
        text_x = self.btn_x + (self.btn_width - len(status) * 4) // 2
        text_y = self.btn_y + 5
        pyxel.text(text_x, text_y, status, 0)  # 黒色テキスト
    
    def is_mouse_on_button(self):
        """マウスがBGMボタン上にあるかチェック"""
        return (self.btn_x <= pyxel.mouse_x <= self.btn_x + self.btn_width and 
                self.btn_y <= pyxel.mouse_y <= self.btn_y + self.btn_height)
    
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
        
        # Bキーで音楽のオン/オフを切り替え
        if pyxel.btnp(pyxel.KEY_B) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_X):
            self.toggle_music()
        
        # マウスクリックでBGMボタンを操作
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            if self.is_mouse_on_button():
                self.toggle_music()
                # クリック効果音（音楽切り替え時にわかりやすく）
                pyxel.play(3, 0)  # チャンネル3で効果音0番を再生
        
        # 現在の画面の更新処理を呼び出す
        self.current_screen.update()
    
    def draw(self):
        """ゲームの描画処理"""
        # 画面をクリア
        pyxel.cls(7)  # 背景色（薄い灰色）
        
        # 現在の画面の描画処理を呼び出す
        self.current_screen.draw()
        
        # BGMオン/オフボタンの描画
        self.draw_music_button()

# メインエントリーポイント
if __name__ == "__main__":
    NumberlinkApp()
