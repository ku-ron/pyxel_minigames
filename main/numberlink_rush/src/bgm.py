"""
MML による BGM と効果音（リソースファイルなし、Pyxel の MML 機能を使用）

チャンネル: 0=メロディ, 1=ベース, 2=アルペジオ/ドラム, 3=効果音
BGM は 3 曲 + OFF。set_track() で選び、play_bgm() で鳴らす。
"""
import pyxel

# ══════════════════════════════════════════════════
#  曲データ（新しい Pyxel の MML 文法: V0-127, Q0-100, O-1〜9, [ ]繰り返し）
# ══════════════════════════════════════════════════

TRACKS = [
    {
        # 曲1: 明るいループ（ハ長調）
        "name": "BRIGHT",
        "tempo": 128,
        "fast": 160,
        "parts": [
            # メロディ: パルス波
            "Q85 @2 V85 O5 L8 ["
            " E G A G E D C D"
            " E G A B >C< B A G"
            " F A B A F E D E"
            " G B >C D E D C< B"
            " E G A G E D C D"
            " E G A B >C< B A G"
            " A >C D C< A G F G"
            " E4 D4 C2"
            " ]",
            # ベース: 三角波
            "Q90 @0 V110 O3 L8 ["
            " C C G G C C G G"
            " A A E E A A E E"
            " F F C C F F C C"
            " G G D D G G D D"
            " C C G G C C G G"
            " A A E E A A E E"
            " F F C C G G D D"
            " C4 G4 C2"
            " ]",
            # アルペジオ: 矩形波（小さめ）
            "Q70 @1 V40 O4 L16 ["
            " [C E G E]4"
            " [A >C E C<]4"
            " [F A >C< A]4"
            " [G B >D< B]4"
            " [C E G E]4"
            " [A >C E C<]4"
            " [F A >C< A]2 [G B >D< B]2"
            " [C E G E]2 C8 E8 G4"
            " ]",
        ],
    },
    {
        # 曲2: モーダル（D ドリアン、Dm7 と G7 のヴァンプ）。音数を減らし、裏拍で入る
        "name": "DORIAN",
        "tempo": 120,
        "fast": 150,
        "parts": [
            # メロディ: パルス波。表拍は休符、「〜と」で入る
            "Q80 @2 V80 O5 L8 ["
            " R D R F R A R >C<"
            " R B R >D< R4 A R"
            " R F R A R >C4.<"
            " R4 R B R A F4"
            " R >D< R A R F R E"
            " R D R E R4 F G"
            " R A R >C< R D R C"
            " R4 A4. R F4"
            " ]",
            # ベース: 三角波。ルートと7度を少なめに
            "Q85 @0 V110 O2 L8 ["
            " D4 R D R4 A4"
            " G4 R G R4 F4"
            " D4 R D R4 A4"
            " G4 R G R4 F4"
            " D4 R D R4 A4"
            " G4 R G R4 F4"
            " D4 R D R4 >C4<"
            " G4 R G R4 F4"
            " ]",
            # コンピング: 矩形波、7th を含むアルペジオ（裏から）
            "Q60 @1 V30 O4 L8 ["
            " R D F A >C< R A F"
            " R G B >D F< R D B"
            " R D F A >C< R A F"
            " R G B >D F< R D B"
            " R F A >C E< R >C< A"
            " R B >D F< R >F D< B"
            " R D F A >C< R A F"
            " R G B >D F< R D B"
            " ]",
        ],
    },
    {
        # 曲3: 長調の J-POP 風（ハ長調、16小節）。前半 A メロ（王道進行 F G Em Am）、
        #       後半サビ（高い音域、Dm G C で締める）
        "name": "POP",
        "tempo": 128,
        "fast": 158,
        "parts": [
            # メロディ: パルス波
            "Q85 @2 V85 O5 L8 ["
            # A メロ
            " C D E F G4 A4"
            " G4. F E D4 R"
            " E G B >C< B G E G"
            " A4. G E C4 R"
            " F F E F A4 G A"
            " B4. >C< B A G4"
            " E4 G4 >C4.< R"
            " R4 E F G A B"
            # サビ
            " >C4 C< A >C4 D4<"
            " >E4 D C< B >C< B A"
            " G4 >E4 D C< B G"
            " A2 R4 A B"
            " >D4 D C< A >D4 C<"
            " B4 G4 A4 B4"
            " >C2. D C<"
            " E4 D4 C2"
            " ]",
            # ベース: 三角波、ルートと5度
            "Q85 @0 V110 O3 L8 ["
            " F R F F >C< R F >C<"
            " G R G G >D< R G >D<"
            " E R E E B R E B"
            " A R A A >E< R A >E<"
            " F R F F >C< R F >C<"
            " G R G G >D< R G >D<"
            " C R C C G R C G"
            " C R C C G R C G"
            " F R F F >C< R F >C<"
            " G R G G >D< R G >D<"
            " E R E E B R E B"
            " A R A A >E< R A >E<"
            " D R D D A R D A"
            " G R G G >D< R G >D<"
            " C R C C G R C G"
            " C R C C G R C G"
            " ]",
            # コンピング: 矩形波。A メロは8分、サビは16分で盛り上げる
            "Q70 @1 V38 O4 ["
            " L8"
            " [F A >C< A]2"
            " [G B >D< B]2"
            " [E G B G]2"
            " [A >C E C<]2"
            " [F A >C< A]2"
            " [G B >D< B]2"
            " [C E G E]2"
            " [C E G E]2"
            " L16"
            " [F A >C< A]4"
            " [G B >D< B]4"
            " [E G B G]4"
            " [A >C E C<]4"
            " [D F A F]4"
            " [G B >D< B]4"
            " [C E G E]4"
            " [C E G E]2 C8 E8 G4"
            " ]",
        ],
    },
]

# ── 効果音 ──
SND_CLEAR, SND_INVALID, SND_SKIP, SND_TICK, SND_TIMEUP, SND_SELECT = 32, 33, 34, 35, 36, 37
SND_MOVE, SND_DRAW, SND_START = 38, 39, 40

_SE = {
    SND_CLEAR:   "T180 @1 V100 O5 L16 C E G >C E4",
    SND_INVALID: "T180 @3 V50 O3 L32 C",
    SND_SKIP:    "T180 @2 V70 O5 L16 G E C",
    SND_TICK:    "T180 @1 V60 O6 L32 C",
    SND_TIMEUP:  "T120 @2 V100 O4 L8 G E C4 <G2",
    SND_SELECT:  "T180 @1 V60 O5 L32 C E",
    SND_MOVE:    "T180 @1 V25 O5 L64 C",       # カーソル移動: ごく短く小さく
    SND_DRAW:    "T180 @1 V35 O5 L64 E",       # 線を引く: 移動より少し高い音
    SND_START:   "T160 @2 V90 O5 L8 G >C4",     # カウントダウン後の START
}

# 効果音は 1 チャンネル（3）を共有するので優先度をつける。
# 重要な音（クリア・タイムアップ・スキップ・無効・START）は常に鳴らし、
# 小さな音（移動・描画・ティック・選択）は重要な音の再生中には鳴らさない。
_IMPORTANT = {SND_CLEAR, SND_INVALID, SND_SKIP, SND_TIMEUP, SND_START}
_last_se = None

_initialized = False
_track = 0          # 選択中の曲番号。None なら OFF


# ══════════════════════════════════════════════════
#  MML の方言差の吸収
# ══════════════════════════════════════════════════
# 上の MML は新しい Pyxel（Web Launcher が使う最新版）の文法で書いてある。
# 古い Pyxel（2.3.x）は V0-7, Q1-8, O0-4 で繰り返しがないので、
# 登録に失敗したら変換してから登録し直す。

def _expand_repeats(code):
    """[ ... ]n を展開する（入れ子対応。回数省略は 2 回とみなす）"""
    while "[" in code:
        end = code.index("]")
        start = code.rindex("[", 0, end)
        j = end + 1
        while j < len(code) and code[j].isdigit():
            j += 1
        count = int(code[end + 1:j]) if j > end + 1 else 2
        code = code[:start] + (" " + code[start + 1:end] + " ") * count + code[j:]
    return code


def _to_old_dialect(code):
    import re
    code = re.sub(r"@ENV\d+\s*\{[^}]*\}", "", code)   # エンベロープは旧版にない
    code = re.sub(r"@ENV\d+", "", code)
    code = _expand_repeats(code)
    code = re.sub(r"V(\d+)", lambda m: f"V{max(0, min(7, int(m.group(1)) * 7 // 127))}", code)
    code = re.sub(r"Q(\d+)", lambda m: f"Q{max(1, min(8, int(m.group(1)) * 8 // 100))}", code)
    code = re.sub(r"O(\d+)", lambda m: f"O{max(0, min(4, int(m.group(1)) - 2))}", code)
    return code


def _register(n, code):
    try:
        pyxel.sounds[n].mml(code)
    except BaseException:            # 古い Pyxel は Rust 側の panic を投げる
        pyxel.sounds[n].mml(_to_old_dialect(code))


def _slot(track, part, fast):
    """曲 track のパート part（0-2）のサウンド番号。通常/速いテンポで 3 つずつ"""
    return track * 6 + (3 if fast else 0) + part


def init():
    """MML をサウンドに登録する（pyxel.init の後に一度だけ呼ぶ）"""
    global _initialized
    if _initialized:
        return
    for t, tr in enumerate(TRACKS):
        for p, code in enumerate(tr["parts"]):
            _register(_slot(t, p, False), f"T{tr['tempo']} {code}")
            _register(_slot(t, p, True), f"T{tr['fast']} {code}")
    for n, code in _SE.items():
        _register(n, code)
    _initialized = True


# ══════════════════════════════════════════════════
#  BGM
# ══════════════════════════════════════════════════

def track_names():
    """選択肢の表示名（曲名 + OFF）"""
    return [tr["name"] for tr in TRACKS] + ["OFF"]


def set_track(index):
    """曲を選ぶ。len(TRACKS) 以上（または None）なら OFF"""
    global _track
    _track = None if index is None or index >= len(TRACKS) else index


def get_track():
    return _track


def play_bgm(fast=False):
    init()
    stop_bgm()
    if _track is None:
        return
    for p in range(len(TRACKS[_track]["parts"])):
        pyxel.play(p, _slot(_track, p, fast), loop=True)


def stop_bgm():
    for ch in range(3):
        pyxel.stop(ch)


# ══════════════════════════════════════════════════
#  効果音（チャンネル3）
# ══════════════════════════════════════════════════

def _se(n):
    global _last_se
    init()
    if n not in _IMPORTANT:
        playing = pyxel.play_pos(3) is not None
        if playing and _last_se in _IMPORTANT:
            return  # 重要な音を途中で切らない
    _last_se = n
    pyxel.play(3, n, loop=False)


def se_clear():
    _se(SND_CLEAR)


def se_invalid():
    _se(SND_INVALID)


def se_skip():
    _se(SND_SKIP)


def se_tick():
    _se(SND_TICK)


def se_timeup():
    _se(SND_TIMEUP)


def se_select():
    _se(SND_SELECT)


def se_move():
    _se(SND_MOVE)


def se_draw():
    _se(SND_DRAW)


def se_start():
    _se(SND_START)
