"""
扇型攻撃ゲーム - 統合版

このファイルは以下のファイルを統合したものです：
- effects.py
- weapons.py
- entities.py
- ui.py
- game.py
- main.py
"""

# 外部ライブラリのインポート
from random import random, randint
import math
import pyxel

# ======= effects.py の内容 =======
import pyxel
import math

def create_explosion(game, x, y):
    """爆発エフェクトを作成"""
    # 爆発エフェクトを追加
    game.explosions.append({
        "x": x,
        "y": y,
        "radius": 5,  # 初期半径
        "max_radius": 100,  # 最大半径を画面の半分程度に増加（元は20）
        "timer": 20,  # エフェクト持続時間
        "color": 10,  # 黄色
        "expanding_speed": 5,  # 拡大速度を追加
        "affected_enemies": set(),  # 既に爆発の影響を受けた敵のIDを記録
        "id": len(game.explosions)  # 爆発に一意のIDを付与
    })

def create_small_explosion(game, x, y):
    """小さな爆発エフェクトを作成（視覚効果のみ）"""
    # 小さな爆発エフェクトを追加
    game.explosions.append({
        "x": x,
        "y": y,
        "radius": 2,  # 初期半径を小さく
        "max_radius": 15,  # 最大半径も小さく
        "timer": 10,  # エフェクト持続時間を短く
        "color": 9,  # オレンジ色
        "expanding_speed": 3,  # 拡大速度
        "affected_enemies": set(),  # 影響を受ける敵はいない（視覚効果のみ）
        "id": len(game.explosions),  # 爆発に一意のIDを付与
        "visual_only": True  # 視覚効果のみを示すフラグ
    })

def update_explosions(game):
    """爆発エフェクトの更新と判定"""
    enemies_to_explode = []
    
    # 爆発エフェクトの寿命を減らし、終了したものを削除
    for explosion in game.explosions[:]:
        # 現在の爆発半径を計算
        if explosion.get("visual_only", False):
            progress = 1 - (explosion["timer"] / 10)
        else:
            progress = 1 - (explosion["timer"] / 20)
        current_radius = explosion["radius"] + (explosion["max_radius"] - explosion["radius"]) * (progress ** 0.6)
        
        # 視覚効果のみでない場合は通常の爆発ダメージ判定
        if not explosion.get("visual_only", False):
            check_explosion_damage(game, explosion, current_radius, enemies_to_explode)
        else:
            # 小さな爆発でも1ダメージを与える
            check_small_explosion_damage(game, explosion, current_radius, enemies_to_explode)
        
        # タイマー更新
        explosion["timer"] -= 1
        if explosion["timer"] <= 0:
            game.explosions.remove(explosion)
    
    # 二次爆発を処理（すべての爆発の判定後に実行）
    for x, y in enemies_to_explode:
        create_explosion(game, x, y)

def check_explosion_damage(game, explosion, current_radius, enemies_to_explode):
    """現在の爆発半径で敵との当たり判定を行う（通常の大きな爆発）"""
    enemies_to_remove = []
    
    for enemy in game.enemies:
        # 既に処理した敵はスキップ
        enemy_id = id(enemy)
        if enemy_id in explosion["affected_enemies"]:
            continue
        
        # 爆発と敵の距離を計算
        distance = math.sqrt((enemy["x"] - explosion["x"])**2 + (enemy["y"] - explosion["y"])**2)
        
        # 現在の爆発半径内に敵が入っているか判定
        if distance < current_radius + enemy["radius"]:
            # 爆発範囲内の敵は体力に関わらず倒す
            enemy["health"] = 0
            game.score += enemy["score"]
            
            # この敵を処理済みとしてマーク
            explosion["affected_enemies"].add(enemy_id)
            
            # Lurker敵が倒された場合、カウンターを更新
            if enemy.get("type") == "lurker" and enemy.get("state") == "waiting":
                game.waiting_lurkers -= 1
            
            # 爆発する敵は二次爆発する
            if enemy.get("explodes", False):
                enemies_to_explode.append((enemy["x"], enemy["y"]))
            else:
                # 爆発しない敵でも小さな爆発エフェクトを作成
                create_small_explosion(game, enemy["x"], enemy["y"])
            
            enemies_to_remove.append(enemy)
    
    # 敵を削除
    for enemy in enemies_to_remove:
        if enemy in game.enemies:  # 既に削除されていないか確認
            game.enemies.remove(enemy)

def check_small_explosion_damage(game, explosion, current_radius, enemies_to_explode):
    """小さな爆発の当たり判定（1ダメージを与える）"""
    enemies_to_remove = []
    
    for enemy in game.enemies:
        # 既に処理した敵はスキップ
        enemy_id = id(enemy)
        if enemy_id in explosion["affected_enemies"]:
            continue
        
        # 爆発と敵の距離を計算
        distance = math.sqrt((enemy["x"] - explosion["x"])**2 + (enemy["y"] - explosion["y"])**2)
        
        # 現在の爆発半径内に敵が入っているか判定
        if distance < current_radius + enemy["radius"]:
            # 敵に1ダメージを与える
            enemy["health"] -= 1
            
            # この敵を処理済みとしてマーク
            explosion["affected_enemies"].add(enemy_id)
            
            # 敵の体力が0以下になったかチェック
            if enemy["health"] <= 0:
                game.score += enemy["score"]
                
                # Lurker敵が倒された場合、カウンターを更新
                if enemy.get("type") == "lurker" and enemy.get("state") == "waiting":
                    game.waiting_lurkers -= 1
                
                # 爆発する敵は二次爆発する
                if enemy.get("explodes", False):
                    enemies_to_explode.append((enemy["x"], enemy["y"]))
                else:
                    # 爆発しない敵でも小さな爆発エフェクトを作成
                    create_small_explosion(game, enemy["x"], enemy["y"])
                
                enemies_to_remove.append(enemy)
    
    # 敵を削除
    for enemy in enemies_to_remove:
        if enemy in game.enemies:  # 既に削除されていないか確認
            game.enemies.remove(enemy)

def draw_explosions(game):
    """爆発エフェクトの描画"""
    for explosion in game.explosions:
        # タイマーに基づいて半径を計算（より早く拡大するようにカーブを調整）
        progress = 1 - (explosion["timer"] / (20 if not explosion.get("visual_only", False) else 10))
        # より激しい爆発エフェクトのために、非線形な拡大を行う
        current_radius = explosion["radius"] + (explosion["max_radius"] - explosion["radius"]) * (progress ** 0.6)
        
        # 視覚効果のみの小さな爆発の場合はシンプルに描画
        if explosion.get("visual_only", False):
            # 爆発の外側の円
            pyxel.circ(explosion["x"], explosion["y"], current_radius, explosion["color"])
            
            # 爆発の内側の円（明るい色）
            inner_radius = current_radius * 0.7
            pyxel.circ(explosion["x"], explosion["y"], inner_radius, 10)  # 黄色
            
            # 爆発の中心（白色）
            core_radius = current_radius * 0.3
            pyxel.circ(explosion["x"], explosion["y"], core_radius, 7)  # 白色
        else:
            # 大きな爆発の場合は複数の同心円で描画
            # 爆発の外側の円
            pyxel.circ(explosion["x"], explosion["y"], current_radius, explosion["color"])
            
            # 爆発の中間の円（オレンジ色）
            middle_radius = current_radius * 0.8
            pyxel.circ(explosion["x"], explosion["y"], middle_radius, 9)  # オレンジ
            
            # 爆発の内側の円（より明るい色）
            inner_radius = current_radius * 0.6
            pyxel.circ(explosion["x"], explosion["y"], inner_radius, 7)  # 白色
            
            # 爆発の中心（もっと明るい色）
            core_radius = current_radius * 0.2
            pyxel.circ(explosion["x"], explosion["y"], core_radius, 10)  # 黄色

# ======= weapons.py の内容 =======
import math


# 攻撃タイプの設定
attack_types = {
    "wide": {
        "name": "Wide Fan",
        "span": 60,     # 扇の角度の幅（度）
        "range": 40,    # 攻撃の届く距離
        "display_color": 5,  # 通常時の表示色（紫）
        "attack_color": 10   # 攻撃時の色（黄色）
    },
    "long": {
        "name": "Long Beam",
        "span": 20 / 3,  # さらに狭い角度
        "range": 80,     # より長い距離
        "display_color": 3,  # 通常時の表示色（暗い緑）
        "attack_color": 11   # 攻撃時の色（水色）
    }
}

def check_attack_damage(game):
    """攻撃のダメージ判定を行う"""
    # 攻撃のダメージ判定を一度だけ行う
    enemies_to_explode = []
    
    # 現在の攻撃タイプのプロパティを取得
    attack_props = attack_types[game.current_attack_type]
    attack_span = attack_props["span"]
    attack_range = attack_props["range"]
    
    for i, enemy in enumerate(game.enemies[:]):
        distance = math.sqrt((enemy["x"] - game.player_x)**2 + (enemy["y"] - game.player_y)**2)
        if distance < attack_range + enemy["radius"]:
            # 敵の角度を計算
            angle_to_enemy = math.atan2(enemy["y"] - game.player_y, enemy["x"] - game.player_x)
            # 攻撃の角度との差を計算
            angle_diff = math.degrees(abs(game.attack_angle - angle_to_enemy)) % 360
            angle_diff = min(angle_diff, 360 - angle_diff)
            
            # 扇型の範囲内にいるかチェック
            if angle_diff <= attack_span / 2:
                enemy["health"] -= 1
                if enemy["health"] <= 0:
                    game.score += enemy["score"]
                    
                    # Lurker敵が倒された場合、カウンターを更新
                    if enemy.get("type") == "lurker" and enemy.get("state") == "waiting":
                        game.waiting_lurkers -= 1
                    
                    # 爆発する敵の場合は爆発処理を予約
                    if enemy.get("explodes", False):
                        enemies_to_explode.append((enemy["x"], enemy["y"]))
                    else:
                        # 爆発しない敵でも小さな爆発エフェクトを作成
                        create_small_explosion(game, enemy["x"], enemy["y"])
                    
                    game.enemies.remove(enemy)
    
    # 爆発する敵の処理（敵リストの変更後に実行）
    for x, y in enemies_to_explode:
        create_explosion(game, x, y)

# ======= entities.py の内容 =======
import math
from random import random, randint


# 敵の種類を定義
enemy_types = {
    "normal": {
        "color": 8,          # 赤色
        "radius": 4,         # 通常サイズ
        "speed": 0.7,        # 速度を上げる
        "health": 1,         # 1発で倒せる
        "damage": 10,        # 通常ダメージ
        "score": 10,         # 通常スコア
        "spawn_weight": 60   # 出現確率の重み
    },
    "speedy": {
        "color": 9,          # オレンジ色
        "radius": 2,         # 小さい
        "speed": 1.2,        # 速い
        "health": 1,         # 1発で倒せる
        "damage": 5,         # 弱いダメージ
        "score": 15,         # 倒すと少し高いスコア
        "spawn_weight": 20   # 出現確率の重み
    },
    "tank": {
        "color": 12,         # 濃い赤色
        "radius": 6,         # 大きい
        "speed": 0.3,        # 遅い
        "health": 8,         # 耐久度を8に増加
        "damage": 20,        # 大きいダメージ
        "score": 30,         # 倒すと高いスコア
        "spawn_weight": 15   # 出現確率の重み
    },
    "exploder": {
        "color": 14,         # ピンク色
        "radius": 3,         # やや小さい
        "speed": 0.7,        # やや速い
        "health": 1,         # 1発で倒せる
        "damage": 15,        # ダメージ大きめ
        "score": 20,         # 倒すとそこそこスコア
        "spawn_weight": 5,   # 出現確率は低め
        "explodes": True     # 爆発する特殊能力
    },
    "lurker": {
        "color": 13,         # 紫色
        "radius": 4,         # 通常サイズ
        "speed": 0.1,        # 初期速度を大幅に下げる
        "health": 2,         # 2発必要
        "damage": 15,        # ダメージ大きめ
        "score": 25,         # 高スコア
        "spawn_weight": 10,  # 出現確率中程度
        "distance_to_stop": 70,  # さらに近い位置に停止
        "attack_threshold": 5,   # 攻撃開始する仲間の数
        "spawn_chain": True  # 連続出現フラグ
    }
}

def create_enemy(game, enemy_type):
    """敵を生成する関数"""
    # 敵の配置場所（確実に画面外になるように計算）
    # 画面のどの位置にいても確実に画面外になる距離を計算
    screen_width, screen_height = 200, 200
    max_distance = max(
        math.sqrt((game.player_x)**2 + (game.player_y)**2),  # 左上までの距離
        math.sqrt((screen_width - game.player_x)**2 + (game.player_y)**2),  # 右上までの距離
        math.sqrt((game.player_x)**2 + (screen_height - game.player_y)**2),  # 左下までの距離
        math.sqrt((screen_width - game.player_x)**2 + (screen_height - game.player_y)**2)  # 右下までの距離
    )
    
    spawn_distance = max_distance + 20  # 余裕を持たせる
    angle = random() * 2 * math.pi
    enemy_x = game.player_x + math.cos(angle) * spawn_distance
    enemy_y = game.player_y + math.sin(angle) * spawn_distance
    
    # 選択された種類の敵を作成
    enemy_props = enemy_types[enemy_type]
    
    enemy = {
        "type": enemy_type,
        "x": enemy_x,
        "y": enemy_y,
        "radius": enemy_props["radius"],
        "color": enemy_props["color"],
        "speed": enemy_props["speed"],
        "health": enemy_props["health"],
        "damage": enemy_props["damage"],
        "score": enemy_props["score"],
        "explodes": enemy_props.get("explodes", False)
    }
    
    # Lurker敵の場合、追加のプロパティを設定
    if enemy_type == "lurker":
        enemy.update({
            "state": "approaching",  # 状態: approaching, slowing, waiting, attacking
            "distance_to_stop": enemy_props["distance_to_stop"],
            "original_speed": enemy_props["speed"],
            "slowdown_distance": 15,  # 減速開始する距離（短くして急減速に）
            "acceleration": 0,        # 加速度（減速時はマイナス）
            "attack_speed": 2.0       # 攻撃時の速度を上げる
        })
    
    game.enemies.append(enemy)
    return enemy

def create_lurker(game):
    """Lurker敵を生成する関数（連続出現モード用）"""
    # 敵の配置場所（確実に画面外になるように計算）
    # 画面のどの位置にいても確実に画面外になる距離を計算
    screen_width, screen_height = 200, 200
    max_distance = max(
        math.sqrt((game.player_x)**2 + (game.player_y)**2),  # 左上までの距離
        math.sqrt((screen_width - game.player_x)**2 + (game.player_y)**2),  # 右上までの距離
        math.sqrt((game.player_x)**2 + (screen_height - game.player_y)**2),  # 左下までの距離
        math.sqrt((screen_width - game.player_x)**2 + (screen_height - game.player_y)**2)  # 右下までの距離
    )
    
    spawn_distance = max_distance + 20  # 余裕を持たせる
    angle = random() * 2 * math.pi
    enemy_x = game.player_x + math.cos(angle) * spawn_distance
    enemy_y = game.player_y + math.sin(angle) * spawn_distance
    
    # Lurker敵のプロパティを取得
    enemy_props = enemy_types["lurker"]
    
    enemy = {
        "type": "lurker",
        "x": enemy_x,
        "y": enemy_y,
        "radius": enemy_props["radius"],
        "color": enemy_props["color"],
        "speed": enemy_props["speed"],
        "health": enemy_props["health"],
        "damage": enemy_props["damage"],
        "score": enemy_props["score"],
        "state": "approaching",
        "distance_to_stop": enemy_props["distance_to_stop"],
        "original_speed": enemy_props["speed"],
        "slowdown_distance": 15,  # 減速開始する距離（短くして急減速に）
        "acceleration": 0.08,     # 初期加速度を設定して徐々に加速
        "attack_speed": 2.0       # 攻撃時の速度を上げる
    }
    
    game.enemies.append(enemy)
    return enemy

def update_enemies(game):
    """敵の更新と当たり判定"""
    enemies_to_explode = []
    active_lurkers = False
    
    for enemy in game.enemies[:]:
        # Lurker敵の特別な動き
        if enemy.get("type") == "lurker":
            if enemy["state"] == "approaching":
                # 加速（最低速度を保証）
                enemy["speed"] = max(0.3, enemy["speed"] + enemy["acceleration"])
                
                # 速度の上限（接近時は1.0まで）
                if enemy["speed"] > 1.0:
                    enemy["speed"] = 1.0
                
                # プレイヤーからの距離を計算
                distance_to_player = math.sqrt((enemy["x"] - game.player_x)**2 + (enemy["y"] - game.player_y)**2)
                
                # 停止距離に近づいたら減速開始
                if distance_to_player < enemy["distance_to_stop"] + enemy["slowdown_distance"]:
                    enemy["state"] = "slowing"
                    # 急減速のための加速度を計算
                    remaining_distance = distance_to_player - enemy["distance_to_stop"]
                    if remaining_distance > 0:
                        # より強い急減速のための加速度
                        enemy["acceleration"] = -(enemy["speed"] * enemy["speed"]) / (1.2 * remaining_distance)
                    else:
                        enemy["acceleration"] = -0.15  # さらに急減速
                
                # 通常移動（プレイヤーに向かう）
                angle_to_player = math.atan2(game.player_y - enemy["y"], game.player_x - enemy["x"])
                enemy["x"] += math.cos(angle_to_player) * enemy["speed"]
                enemy["y"] += math.sin(angle_to_player) * enemy["speed"]
            
            elif enemy["state"] == "slowing":
                # 速度を減速（より急激に）
                enemy["speed"] += enemy["acceleration"]
                if enemy["speed"] <= 0:
                    enemy["speed"] = 0
                    enemy["state"] = "waiting"
                    game.waiting_lurkers += 1
                
                # 移動（減速中）
                angle_to_player = math.atan2(game.player_y - enemy["y"], game.player_x - enemy["x"])
                enemy["x"] += math.cos(angle_to_player) * enemy["speed"]
                enemy["y"] += math.sin(angle_to_player) * enemy["speed"]
            
            elif enemy["state"] == "waiting":
                # 待機中（動かない）
                # 待機中のLurker数が閾値に達したら全て攻撃状態に
                if game.waiting_lurkers >= enemy_types["lurker"]["attack_threshold"]:
                    active_lurkers = True
            
            elif enemy["state"] == "attacking":
                # 攻撃中（加速度をつけて高速でプレイヤーに向かう）
                # 加速度を大きくして、上限なしで加速を続ける
                enemy["speed"] += 0.04
                
                angle_to_player = math.atan2(game.player_y - enemy["y"], game.player_x - enemy["x"])
                enemy["x"] += math.cos(angle_to_player) * enemy["speed"]
                enemy["y"] += math.sin(angle_to_player) * enemy["speed"]
        else:
            # 通常の敵の移動
            angle_to_player = math.atan2(game.player_y - enemy["y"], game.player_x - enemy["x"])
            enemy["x"] += math.cos(angle_to_player) * enemy["speed"]
            enemy["y"] += math.sin(angle_to_player) * enemy["speed"]
        
        # プレイヤーとの衝突判定
        distance = math.sqrt((enemy["x"] - game.player_x)**2 + (enemy["y"] - game.player_y)**2)
        if distance < game.player_radius + enemy["radius"]:
            game.player_health -= enemy["damage"]
            
            # Lurker敵が倒された場合、カウンターを更新
            if enemy.get("type") == "lurker" and enemy.get("state") == "waiting":
                game.waiting_lurkers -= 1
            
            # 爆発する敵の場合は爆発処理を予約
            if enemy.get("explodes", False):
                enemies_to_explode.append((enemy["x"], enemy["y"]))
            else:
                # 爆発しない敵でも小さな爆発エフェクトを作成
                create_small_explosion(game, enemy["x"], enemy["y"])
            
            game.enemies.remove(enemy)
            
            if game.player_health <= 0:
                game.game_over = True
    
    # 待機中のLurkerを攻撃状態に変更
    if active_lurkers:
        for enemy in game.enemies:
            if enemy.get("type") == "lurker" and enemy.get("state") == "waiting":
                enemy["state"] = "attacking"
                enemy["speed"] = 0.0  # 攻撃時の初期速度を0に設定
        game.waiting_lurkers = 0
    
    # 爆発する敵の処理（敵リストの変更後に実行）
    for x, y in enemies_to_explode:
        create_explosion(game, x, y)

def draw_enemies(game):
    """敵の描画処理"""
    import pyxel
    
    for enemy in game.enemies:
        pyxel.circ(enemy["x"], enemy["y"], enemy["radius"], enemy["color"])
        
        # 体力が2以上の敵には体力を表示
        if enemy["health"] > 1:
            hp_x = int(enemy["x"] - 1)
            hp_y = int(enemy["y"] - enemy["radius"] - 4)
            pyxel.text(hp_x, hp_y, str(enemy["health"]), 7)
        
        # 爆発する敵には特殊マーク
        if enemy.get("explodes", False):
            mark_x = int(enemy["x"] - 1)
            mark_y = int(enemy["y"] - 1)
            pyxel.pset(mark_x, mark_y, 7)  # 白い点で表示
            
            # 爆発する敵をより目立たせるための表示を追加
            radius = enemy["radius"] + 1
            num_points = 4
            for i in range(num_points):
                angle = i * (2 * math.pi / num_points)
                point_x = enemy["x"] + math.cos(angle) * radius
                point_y = enemy["y"] + math.sin(angle) * radius
                pyxel.pset(point_x, point_y, 10)  # 黄色の点
        
        # Lurker敵の状態表示
        if enemy.get("type") == "lurker":
            # 待機状態の場合は特別な表示
            if enemy.get("state") == "waiting":
                # 円の周りに点線の円を描画
                radius = enemy["radius"] + 2
                num_points = 8
                for i in range(num_points):
                    angle = i * (2 * math.pi / num_points)
                    point_x = enemy["x"] + math.cos(angle) * radius
                    point_y = enemy["y"] + math.sin(angle) * radius
                    pyxel.pset(point_x, point_y, 7)

# ======= ui.py の内容 =======
import pyxel
import math




def draw_ui(game):
    """ゲームのUI全体を描画する関数"""
    # プレイヤーの描画
    pyxel.circ(game.player_x, game.player_y, game.player_radius, game.player_color)
    
    # 敵の描画
    draw_enemies(game)
    
    # 爆発エフェクトの描画
    draw_explosions(game)
    
    # 現在の攻撃タイプの簡易表示（画面端に配置）
    # 攻撃タイプに基づく色だけを使用（攻撃状態による色変化なし）
    type_color = attack_types[game.current_attack_type]["display_color"]
    if game.current_attack_type == "wide":
        attack_text = "Wide [SPACE]"
    else:
        attack_text = "Long [SPACE]"
    pyxel.text(5, 190, attack_text, type_color)
    
    # ステータスUIの描画
    pyxel.text(5, 5, f"Score: {game.score}", 7)
    pyxel.text(5, 15, f"Health: {game.player_health}", 11 if game.player_health > 30 else 8)
    
    # ゲームオーバー表示
    if game.game_over:
        pyxel.text(70, 85, "GAME OVER", 8)
        pyxel.text(55, 100, f"Final Score: {game.score}", 7)
        pyxel.text(50, 115, "Press R to restart", 7)

def draw_fan(x, y, radius, angle, span, color):
    """扇型を描画する関数"""
    # 扇型を描画
    span_half = span / 2
    steps = 20
    for i in range(steps):
        angle1 = angle - span_half + span * i / steps
        angle2 = angle - span_half + span * (i + 1) / steps
        draw_fan_segment(x, y, radius, angle1, angle2, color)

def draw_fan_segment(x, y, radius, angle1, angle2, color):
    """扇型の1セグメントを描画する関数"""
    x1 = x + math.cos(angle1) * radius
    y1 = y + math.sin(angle1) * radius
    x2 = x + math.cos(angle2) * radius
    y2 = y + math.sin(angle2) * radius
    pyxel.tri(x, y, x1, y1, x2, y2, color)

# ======= game.py の内容 =======
import pyxel
import math





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

# ======= main.py の内容 =======


if __name__ == "__main__":
    Game()
