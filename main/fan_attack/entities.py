import math
from random import random, randint
from effects import create_explosion, create_small_explosion

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
