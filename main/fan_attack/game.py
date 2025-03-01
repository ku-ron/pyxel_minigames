import pyxel
import math
from entities import create_enemy, create_lurker, update_enemies, enemy_types
from effects import update_explosions, create_explosion
from weapons import attack_types, check_attack_damage
from ui import draw_ui, draw_fan

class Game:
    def __init__(self):
        # ゲーム画面の初期化（200x200の正方形）
        pyxel.init(200, 200, title="扇型攻撃ゲーム")
        
        self.reset_game()
        
        # ゲームループの開始
        pyxel.run(self.update, self.draw)
    
    def reset_game(self):
        # プレイヤーの初期設定
        self.player_x = 100
        self.player_y = 100
        self.player_radius = 5
        self.player_color = 11  # 青色
        self.player_health = 100
        
        # 攻撃の設定
        self.attack_angle = 0  # 攻撃の角度
        self.attack_active = False
        self.attack_timer = 0
        self.attack_duration = 10  # 攻撃が続くフレーム数
        self.damage_dealt = False  # 攻撃がダメージを与えたかどうかのフラグ
        
        # 現在の攻撃タイプ
        self.current_attack_type = "wide"
        
        # 敵の初期設定
        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemy_spawn_rate = 30  # 30フレームごとに敵が出現
        
        # Lurker敵の連続出現設定
        self.lurker_spawn_chain = False
        self.lurker_spawn_count = 0
        self.lurker_max_chain = 5  # 最大連続出現数を5に変更
        
        # 爆発エフェクトのリスト
        self.explosions = []
        
        # 待機中のLurker敵の数
        self.waiting_lurkers = 0
        
        self.score = 0
        self.game_over = False
    
    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
            
        if self.game_over:
            if pyxel.btnp(pyxel.KEY_R):
                self.reset_game()
                return
            return
        
        # 攻撃タイプの切り替え
        if pyxel.btnp(pyxel.KEY_SPACE):
            if self.current_attack_type == "wide":
                self.current_attack_type = "long"
            else:
                self.current_attack_type = "wide"
            
        # プレイヤーの向きの制御（マウスの位置へ向ける）
        mouse_x = pyxel.mouse_x
        mouse_y = pyxel.mouse_y
        self.attack_angle = math.atan2(mouse_y - self.player_y, mouse_x - self.player_x)
        
        # 攻撃の処理
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.attack_active = True
            self.attack_timer = self.attack_duration
            self.damage_dealt = False  # 新しい攻撃のためにフラグをリセット
        
        if self.attack_active:
            # 攻撃が始まってダメージをまだ与えていなければ、ダメージ判定を実行
            if not self.damage_dealt:
                check_attack_damage(self)
                self.damage_dealt = True  # 一度だけダメージを与えたことをマーク
            
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attack_active = False
        
        # 敵の生成
        self.enemy_spawn_timer += 1
        
        # Lurker連続出現モード中はLurkerを優先的に出す
        if self.lurker_spawn_chain:
            if self.enemy_spawn_timer >= max(15, self.enemy_spawn_rate - 5):  # 間隔を少し長めに変更
                self.enemy_spawn_timer = 0
                create_lurker(self)
                self.lurker_spawn_count += 1
                
                # 連続出現終了判定
                if self.lurker_spawn_count >= self.lurker_max_chain:
                    self.lurker_spawn_chain = False
                    self.lurker_spawn_count = 0
        else:
            if self.enemy_spawn_timer >= self.enemy_spawn_rate:
                self.enemy_spawn_timer = 0
                self.spawn_enemy()
        
        # 敵の更新と当たり判定
        update_enemies(self)
        
        # 爆発エフェクトの更新
        update_explosions(self)
    
    def spawn_enemy(self):
        from random import randint
        # 重み付けによるランダム選択
        weights = [enemy_types[t]["spawn_weight"] for t in enemy_types]
        total_weight = sum(weights)
        r = randint(1, total_weight)
        
        cumulative_weight = 0
        selected_type = None
        for enemy_type, props in enemy_types.items():
            cumulative_weight += props["spawn_weight"]
            if r <= cumulative_weight:
                selected_type = enemy_type
                break
        
        # Lurker出現時に連続出現モードに入る
        if selected_type == "lurker" and not self.lurker_spawn_chain:
            self.lurker_spawn_chain = True
            self.lurker_spawn_count = 1
        
        # 敵を生成
        create_enemy(self, selected_type)
    
    def draw(self):
        pyxel.cls(0)  # 画面をクリア
        
        # 現在の攻撃タイプのプロパティを取得
        attack_props = attack_types[self.current_attack_type]
        attack_span = attack_props["span"]
        attack_range = attack_props["range"]
        display_color = attack_props["attack_color"] if self.attack_active else attack_props["display_color"]
        
        # 攻撃範囲の表示（常に表示）
        draw_fan(self.player_x, self.player_y, attack_range, self.attack_angle, 
                 math.radians(attack_span), display_color)
                      
        # カーソル/照準の表示
        cursor_x = pyxel.mouse_x
        cursor_y = pyxel.mouse_y
        cursor_size = 4
        cursor_color = 7  # 白色
        
        # 十字の照準を描画
        pyxel.line(cursor_x - cursor_size, cursor_y, cursor_x + cursor_size, cursor_y, cursor_color)
        pyxel.line(cursor_x, cursor_y - cursor_size, cursor_x, cursor_y + cursor_size, cursor_color)
        
        # 円形の照準外枠（輪郭のみ）
        pyxel.circb(cursor_x, cursor_y, cursor_size, cursor_color)
        
        # エフェクトや敵、UIの描画
        draw_ui(self)
