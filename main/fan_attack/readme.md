# 扇型攻撃ゲーム

このゲームは、Pyxelを使用した2Dのシューティングゲームです。プレイヤーは画面中央に位置し、マウスを使って敵に扇型の攻撃を放ちます。

## ブラウザ上での実行
- こちらからプレイできます。[ブラウザで遊ぶ](https://kitao.github.io/pyxel/wasm/launcher/?play=ku-ron.pyxel_minigames.main.fan_attack.fan_attack)
   - ソースから実行テスト
      - [Launcher版](https://kitao.github.io/pyxel/wasm/launcher/?run=ku-ron.pyxel_minigames.main.fan_attack.src.main)
      - [カスタムタグhtmlの読み込み](https://ku-ron.github.io/pyxel_minigames/main/fan_attack/src/fan_attack.html)

## ゲームの特徴

- マウスでプレイヤーの照準と攻撃方向を制御
- 2種類の攻撃タイプ（広範囲の「Wide Fan」と長距離の「Long Beam」）
- 5種類の敵キャラクター（Normal, Speedy, Tank, Exploder, Lurker）
- 強力な爆発エフェクト（Exploderを倒すと発生）

## 操作方法

- **マウス移動**: 照準の移動と攻撃方向の設定
- **左クリック**: 攻撃実行
- **スペースキー**: 攻撃タイプの切り替え
- **R**: ゲームオーバー時のリスタート
- **Q**: ゲーム終了

## 敵の種類

1. **Normal**: 標準的な敵
2. **Speedy**: 小さく速い敵
3. **Tank**: 遅いが体力が高い敵
4. **Exploder**: 倒すと大爆発を起こし、範囲内の敵も倒せる
5. **Lurker**: 特殊な動きをする敵。一定数集まると一斉に攻撃する

## ファイル構成

- **main.py**: ゲーム起動ファイル
- **game.py**: ゲームのメインクラス
- **entities.py**: 敵などのエンティティ処理
- **effects.py**: 爆発などのエフェクト処理
- **weapons.py**: 武器と攻撃の処理
- **ui.py**: UIと描画関連の処理

## 必要環境

- Python 3.7以上
- Pyxel 1.9.0以上

## インストールと実行

1. Pyxelをインストール
   ```
   pip install pyxel
   ```

2. ゲームを実行
   ```
   python main.py
   ```

## 改良点

- exploderの爆発範囲を画面の半分程度に拡大
- 爆発に巻き込まれた敵は体力に関わらず一撃で倒せるように変更
- 爆発エフェクトを複数の色の同心円で表現し、より派手に
