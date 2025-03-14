# ナンバーリンク(パズルゲーム)

このゲームは、Pyxelを使用したナンバーリンクというパズルゲームです。同じ数字を繋ぎます。

## スクリーンショット


## ブラウザ上での実行
- こちらからプレイできます。[ブラウザで遊ぶ](https://kitao.github.io/pyxel/wasm/launcher/?play=ku-ron.pyxel_minigames.main.numberlink.numberlink_v1_0&gamepad=enabled)

## ゲームのルール
- 同じ数字のペアを線で繋ぎます。
- 線は分岐や交差はできません。
- 全部の数字のペアを線で繋げばクリアです。

## 操作方法

- キーボード
   - **矢印キー**: カーソルの移動。
   - **エンターキー**: メニュー画面等での決定。
   - **スペースキー**: 移動モードと描画モードの切り替え。描画モードのときに移動すると線が引けます。
   - **R**: ゲーム中のリセット。
   - **M**: ゲーム中からメニューに戻る。
   - **ESC**: ゲーム終了

- バーチャルゲームパッド
   - **十字キー**: カーソルの移動。
   - **Bボタン(右ボタン)**: メニュー画面等での決定。
   - **Aボタン(下ボタン)**: 移動モードと描画モードの切り替え。描画モードのときに移動すると線が引けます。
   - **Yボタン(上ボタン)**: ゲーム中からメニューに戻る。
   - **Xボタン(左ボタン)**: ゲーム中のリセット。


## 制作者の実行環境

- Python 3.11.0 (割と古くても大丈夫だと思います)
- Pyxel 2.3.6

## インストールと実行

1. Pyxelをインストール
   ```
   pip install pyxel
   ```

2. ゲームを実行
   - srcフォルダから実行する場合
      ```
      python main.py
      ```
   - pyxappから実行する場合(バージョン番号は適宜置き換えてください。)
      ```
       pyxel play numberlink_v1_0.pyxapp      
      ```
