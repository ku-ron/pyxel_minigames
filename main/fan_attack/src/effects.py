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
