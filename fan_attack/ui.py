import pyxel
import math
from entities import draw_enemies
from effects import draw_explosions
from weapons import attack_types

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
