#!/usr/bin/env python3
"""
numberlink_sat_checker.py — SATベース ナンバーリンク 関西解・一意性チェッカー
==========================================================================

MiniSat (python-sat経由) を使って以下を高速に判定:
  1. 関西解（全マスを使わない解）の存在チェック
  2. 解の一意性チェック
  3. パズルの解探索

SATエンコーディング:
  各セル(r,c)×各数字kにブール変数 X[r,c,k] を用意。
  - 端点: 数字確定 + 隣接ちょうど1つが同じ数字
  - 空きセル: 数字が入る場合、隣接ちょうど2つが同じ数字
  - 隣接で同じ数字は高々2つ（無条件）

  参考: jkr2255「爆速ナンバーリンクソルバー」
  https://qiita.com/jkr_2255/items/bb7cb2eee35e285a17a2

依存:
  pip install python-sat

使用例:
  python numberlink_sat_checker.py puzzle.json
  python numberlink_sat_checker.py puzzle.json -v
  python numberlink_sat_checker.py *.json
  python numberlink_sat_checker.py puzzle.json --solve
"""

import json
import argparse
import time
import sys
from itertools import combinations
from typing import List, Tuple, Dict, Set, Optional

try:
    from pysat.solvers import Minisat22
except ImportError:
    print("エラー: python-satパッケージが必要です")
    print("  pip install python-sat")
    sys.exit(1)


DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def load_puzzle(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_puzzle(data: dict):
    size = data["size"]
    if isinstance(size, list):
        rows, cols = size
    else:
        rows = cols = size

    pairs: Dict[int, List[Tuple[int, int]]] = {}
    for key, val in data["numbers"].items():
        r, c = map(int, key.split(","))
        pairs.setdefault(val, []).append((r, c))

    blocked: Set[Tuple[int, int]] = set()
    for key in data.get("blocked", []):
        r, c = map(int, key.split(","))
        blocked.add((r, c))

    return rows, cols, pairs, blocked


class NumberLinkSAT:
    """SATベースのナンバーリンクソルバー・チェッカー"""

    def __init__(self, rows: int, cols: int,
                 pairs: Dict[int, List[Tuple[int, int]]],
                 blocked: Set[Tuple[int, int]]):
        self.rows = rows
        self.cols = cols
        self.blocked = blocked

        # 数字ID → 0-indexed
        self.pid_list = sorted(pairs.keys())
        self.pid_to_idx = {pid: i for i, pid in enumerate(self.pid_list)}
        self.K = len(self.pid_list)  # 数字の種類数
        self.pairs = pairs

        # 端点マップ: (r,c) → k_idx
        self.endpoints: Dict[Tuple[int, int], int] = {}
        for pid, pts in pairs.items():
            k_idx = self.pid_to_idx[pid]
            for r, c in pts:
                self.endpoints[(r, c)] = k_idx

        # 空きセル一覧（非ブロック・非端点）
        self.empty_cells: List[Tuple[int, int]] = []
        for r in range(rows):
            for c in range(cols):
                if (r, c) not in blocked and (r, c) not in self.endpoints:
                    self.empty_cells.append((r, c))

        # SAT変数: X[r,c,k] = r*cols*K + c*K + k + 1  (1-indexed)
        self._max_x_var = rows * cols * self.K

    def _var(self, r: int, c: int, k_idx: int) -> int:
        """セル(r,c)に数字k_idxが入る ⇔ この変数がTrue"""
        return r * self.cols * self.K + c * self.K + k_idx + 1

    def _neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """隣接する非ブロックセル"""
        result = []
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if (0 <= nr < self.rows and 0 <= nc < self.cols
                    and (nr, nc) not in self.blocked):
                result.append((nr, nc))
        return result

    def _encode_base(self) -> List[List[int]]:
        """
        基本制約のCNF節を生成。
        全セル充填の at_least_1 は含まない（呼び出し側で追加）。
        """
        clauses: List[List[int]] = []

        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) in self.blocked:
                    # ■セル: 全変数False
                    for ki in range(self.K):
                        clauses.append([-self._var(r, c, ki)])
                    continue

                nbs = self._neighbors(r, c)

                # ── 各セルに高々1つの数字 ──
                for ki in range(self.K):
                    for kj in range(ki + 1, self.K):
                        clauses.append([-self._var(r, c, ki),
                                        -self._var(r, c, kj)])

                if (r, c) in self.endpoints:
                    k_idx = self.endpoints[(r, c)]

                    # 数字確定
                    clauses.append([self._var(r, c, k_idx)])
                    for ki in range(self.K):
                        if ki != k_idx:
                            clauses.append([-self._var(r, c, ki)])

                    # 隣接でちょうど1つが同じ数字
                    nb_k = [self._var(nr, nc, k_idx) for nr, nc in nbs]
                    if nb_k:
                        clauses.append(nb_k[:])  # at_least_1
                    for i in range(len(nb_k)):
                        for j in range(i + 1, len(nb_k)):
                            clauses.append([-nb_k[i], -nb_k[j]])  # at_most_1

                else:
                    # ── 空きセル ──
                    for ki in range(self.K):
                        x = self._var(r, c, ki)
                        nb_k = [self._var(nr, nc, ki) for nr, nc in nbs]
                        n = len(nb_k)

                        # x → 隣接のうち少なくとも2つがki
                        # CNF: 各1つを除いた残りのOR に ¬x を追加
                        if n >= 2:
                            for i in range(n):
                                clause = [-x]
                                for j in range(n):
                                    if j != i:
                                        clause.append(nb_k[j])
                                clauses.append(clause)
                        else:
                            # 隣接2未満 → この数字は入れない
                            clauses.append([-x])

                    # ── 隣接で同じ数字は高々2つ（全数字・無条件）──
                    for ki in range(self.K):
                        nb_k = [self._var(nr, nc, ki) for nr, nc in nbs]
                        if len(nb_k) >= 3:
                            for combo in combinations(range(len(nb_k)), 3):
                                clauses.append([-nb_k[idx] for idx in combo])

        return clauses

    # ──────────────────────────────────────────────
    #  関西解（短絡解）チェック
    # ──────────────────────────────────────────────

    def check_shortcut(self) -> Optional[List[List[int]]]:
        """
        関西解（全セルを使わずに全ペア接続可能な解）が存在するかチェック。

        Returns:
            関西解のgrid（見つかった場合）、None（見つからない場合）
        """
        if not self.empty_cells:
            return None  # 空きセルがなければ関西解は不可能

        clauses = self._encode_base()

        # 空きセルは埋めなくてもよい（at_least_1 を追加しない）
        # 「少なくとも1つの空きセルが未使用」を強制する補助変数
        next_aux = self._max_x_var + 1
        y_vars = []
        for r, c in self.empty_cells:
            y = next_aux
            next_aux += 1
            y_vars.append(y)
            # y=True → このセルの全X変数がFalse（セルは空のまま）
            for ki in range(self.K):
                clauses.append([-y, -self._var(r, c, ki)])

        # 少なくとも1つのYがTrue
        clauses.append(y_vars[:])

        solver = Minisat22()
        for cl in clauses:
            solver.add_clause(cl)

        grid = None
        if solver.solve():
            model = set(solver.get_model())
            grid = self._extract_grid(model)

        solver.delete()
        return grid

    # ──────────────────────────────────────────────
    #  解探索（全セル充填）
    # ──────────────────────────────────────────────

    def solve(self) -> Optional[List[List[int]]]:
        """
        全セル充填解を探索。

        Returns:
            解のgrid（見つかった場合）、None（見つからない場合）
        """
        clauses = self._encode_base()

        # 全空きセル充填を要求
        for r, c in self.empty_cells:
            clauses.append([self._var(r, c, ki) for ki in range(self.K)])

        solver = Minisat22()
        for cl in clauses:
            solver.add_clause(cl)

        grid = None
        if solver.solve():
            model = set(solver.get_model())
            grid = self._extract_grid(model)

        solver.delete()
        return grid

    # ──────────────────────────────────────────────
    #  一意性チェック
    # ──────────────────────────────────────────────

    def check_unique(self) -> Tuple[Optional[List[List[int]]], bool]:
        """
        解が一意かチェック。

        Returns:
            (solution_grid, is_unique)
            解なしの場合 (None, True)
        """
        clauses = self._encode_base()

        # 全空きセル充填を要求
        for r, c in self.empty_cells:
            clauses.append([self._var(r, c, ki) for ki in range(self.K)])

        solver = Minisat22()
        for cl in clauses:
            solver.add_clause(cl)

        if not solver.solve():
            solver.delete()
            return None, True

        model1 = set(solver.get_model())
        grid1 = self._extract_grid(model1)

        # 解1をブロック: 空きセルの割り当てのうち少なくとも1つを変える
        blocking = []
        for r, c in self.empty_cells:
            for ki in range(self.K):
                v = self._var(r, c, ki)
                if v in model1:
                    blocking.append(-v)

        if blocking:
            solver.add_clause(blocking)
            is_unique = not solver.solve()
        else:
            is_unique = True  # 空きセルがない場合は自明に一意

        solver.delete()
        return grid1, is_unique

    # ──────────────────────────────────────────────
    #  ユーティリティ
    # ──────────────────────────────────────────────

    def _extract_grid(self, model: set) -> List[List[int]]:
        """SAT解からグリッドを復元"""
        grid = [[0] * self.cols for _ in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) in self.blocked:
                    grid[r][c] = -1
                    continue
                for ki in range(self.K):
                    v = self._var(r, c, ki)
                    if v in model:
                        grid[r][c] = self.pid_list[ki]
                        break
        return grid


# ══════════════════════════════════════════════════
#  表示・CLI
# ══════════════════════════════════════════════════

def display_grid(grid: List[List[int]], rows: int, cols: int):
    """グリッドをテキスト表示"""
    max_val = 0
    for row in grid:
        for c in row:
            max_val = max(max_val, abs(c))
    w = max(2, len(str(max_val)) + 1)
    for row in grid:
        cells = []
        for c in row:
            if c == -1:
                cells.append(f"{'■':>{w}}")
            elif c == 0:
                cells.append(f"{'.':>{w}}")
            else:
                cells.append(f"{c:>{w}}")
        print('  ' + ' '.join(cells))


def check_one(filepath: str, verbose: bool = False,
              solve_only: bool = False) -> dict:
    """1つのパズルをチェック"""
    data = load_puzzle(filepath)
    rows, cols, pairs, blocked = parse_puzzle(data)
    num_pairs = len(pairs)
    usable = rows * cols - len(blocked)

    print(f"\n{'─' * 56}")
    print(f"  {filepath}")
    print(f"  {rows}x{cols}, {num_pairs}ペア, "
          f"使用可能{usable}セル"
          f"{f', ■{len(blocked)}マス' if blocked else ''}")
    print(f"{'─' * 56}")

    nlsat = NumberLinkSAT(rows, cols, pairs, blocked)

    if solve_only:
        t0 = time.time()
        grid = nlsat.solve()
        elapsed = time.time() - t0
        if grid:
            print(f"  ✅ 解あり ({elapsed:.3f}秒)")
            if verbose:
                display_grid(grid, rows, cols)
        else:
            print(f"  ❌ 解なし ({elapsed:.3f}秒)")
        return {"solvable": grid is not None}

    # ── 関西解チェック ──
    t0 = time.time()
    shortcut = nlsat.check_shortcut()
    t_sc = time.time() - t0
    has_shortcut = shortcut is not None

    if has_shortcut:
        used = sum(1 for r in range(rows) for c in range(cols)
                   if shortcut[r][c] > 0)
        余り = usable - used
        print(f"  ⚠️  関西解あり: {used}/{usable}セル使用"
              f" ({余り}セル余り) [{t_sc:.3f}秒]")
        if verbose:
            display_grid(shortcut, rows, cols)
    else:
        print(f"  ✅ 関西解なし [{t_sc:.3f}秒]")

    # ── 一意性チェック ──
    t0 = time.time()
    solution, is_unique = nlsat.check_unique()
    t_uq = time.time() - t0

    if solution is None:
        print(f"  ❌ 解なし [{t_uq:.3f}秒]")
    elif is_unique:
        print(f"  ✅ 解は一意 [{t_uq:.3f}秒]")
        if verbose:
            display_grid(solution, rows, cols)
    else:
        print(f"  ⚠️  複数解あり [{t_uq:.3f}秒]")
        if verbose:
            display_grid(solution, rows, cols)

    is_good = (not has_shortcut and is_unique
               and solution is not None)
    return {
        "has_shortcut": has_shortcut,
        "is_unique": is_unique,
        "has_solution": solution is not None,
        "is_good": is_good,
    }


def main():
    parser = argparse.ArgumentParser(
        description="SATベース ナンバーリンク 関西解・一意性チェッカー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
使用例:
  python numberlink_sat_checker.py puzzle.json           品質チェック
  python numberlink_sat_checker.py puzzle.json -v        詳細表示
  python numberlink_sat_checker.py *.json                一括チェック
  python numberlink_sat_checker.py puzzle.json --solve   解探索のみ
""")
    parser.add_argument("files", nargs="+", help="パズルJSONファイル")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="グリッド詳細を表示")
    parser.add_argument("--solve", action="store_true",
                        help="解探索のみ（品質チェックなし）")

    args = parser.parse_args()

    total = 0
    good = 0
    shortcuts = 0
    not_unique = 0
    no_solution = 0

    for filepath in args.files:
        total += 1
        result = check_one(filepath, verbose=args.verbose,
                           solve_only=args.solve)

        if args.solve:
            if result.get("solvable"):
                good += 1
            else:
                no_solution += 1
        else:
            if result.get("is_good"):
                good += 1
            if result.get("has_shortcut"):
                shortcuts += 1
            if not result.get("is_unique", True):
                not_unique += 1
            if not result.get("has_solution", True):
                no_solution += 1

    if total > 1:
        print(f"\n{'═' * 56}")
        print(f"  合計: {total}問")
        if args.solve:
            print(f"  ✅ 解あり: {good}")
            if no_solution:
                print(f"  ❌ 解なし: {no_solution}")
        else:
            print(f"  ✅ 良問（関西解なし＋一意解）: {good}")
            if shortcuts:
                print(f"  ⚠️  関西解あり: {shortcuts}")
            if not_unique:
                print(f"  ⚠️  複数解: {not_unique}")
            if no_solution:
                print(f"  ❌ 解なし: {no_solution}")
        print(f"{'═' * 56}")


if __name__ == "__main__":
    main()
