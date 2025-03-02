import math
from effects import create_explosion, create_small_explosion

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
