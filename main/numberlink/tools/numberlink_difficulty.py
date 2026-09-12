#!/usr/bin/env python3
"""
numberlink_difficulty.py — ナンバーリンク難易度指標分析ツール
============================================================

パズルから各種難易度指標を計算し、簡単/難しいの判別に
どの指標が有効かを探る。

指標カテゴリ:
  A. 構造的指標（パズル自体の形状から計算）
  B. SAT指標（ソルバーの内部統計）
  C. 伝播ベース指標（単位伝播だけでどこまで決まるか）

使用例:
  python numberlink_difficulty.py easy1.json easy2.json -- hard1.json hard2.json
  python numberlink_difficulty.py *.json
  python numberlink_difficulty.py puzzle.json -v
"""

import json
import sys
import os
import time
import math
import argparse
from collections import deque
from typing import List, Tuple, Dict, Set, Optional
from itertools import combinations

_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _dir)

try:
    from pysat.solvers import Minisat22
except ImportError:
    print("エラー: python-sat が必要です")
    sys.exit(1)

from numberlink_sat_checker import NumberLinkSAT, load_puzzle, parse_puzzle

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


# ══════════════════════════════════════════════════
#  A. 構造的指標
# ══════════════════════════════════════════════════

def structural_metrics(rows, cols, pairs, blocked, solution_grid=None):
    """パズルの構造的指標を計算"""
    metrics = {}

    num_pairs = len(pairs)
    total_cells = rows * cols
    usable_cells = total_cells - len(blocked)

    metrics["grid_size"] = f"{rows}x{cols}"
    metrics["num_pairs"] = num_pairs
    metrics["usable_cells"] = usable_cells
    metrics["blocked_cells"] = len(blocked)

    # ── 端点間のマンハッタン距離 ──
    manhattan_dists = []
    for pid, pts in pairs.items():
        if len(pts) >= 2:
            r0, c0 = pts[0]
            r1, c1 = pts[1]
            d = abs(r0 - r1) + abs(c0 - c1)
            manhattan_dists.append(d)

    metrics["manhattan_min"] = min(manhattan_dists) if manhattan_dists else 0
    metrics["manhattan_max"] = max(manhattan_dists) if manhattan_dists else 0
    metrics["manhattan_avg"] = (sum(manhattan_dists) / len(manhattan_dists)
                                if manhattan_dists else 0)

    # ── 端点の位置特性 ──
    # 辺・角にある端点の割合
    edge_count = 0
    corner_count = 0
    all_endpoints = []
    for pid, pts in pairs.items():
        for r, c in pts:
            all_endpoints.append((r, c))
            on_edge = (r == 0 or r == rows - 1 or
                       c == 0 or c == cols - 1)
            on_corner = ((r in (0, rows - 1)) and (c in (0, cols - 1)))
            if on_corner:
                corner_count += 1
            elif on_edge:
                edge_count += 1

    total_endpoints = len(all_endpoints)
    metrics["endpoints_on_edge_pct"] = ((edge_count + corner_count) /
                                        total_endpoints * 100
                                        if total_endpoints else 0)
    metrics["endpoints_on_corner"] = corner_count

    # ── 端点同士の近接度 ──
    # 異なるペアの端点間の最小距離
    min_inter_dist = float('inf')
    for i in range(total_endpoints):
        for j in range(i + 1, total_endpoints):
            r1, c1 = all_endpoints[i]
            r2, c2 = all_endpoints[j]
            # 同じペアならスキップ
            same_pair = False
            for pid, pts in pairs.items():
                if (r1, c1) in pts and (r2, c2) in pts:
                    same_pair = True
                    break
            if not same_pair:
                d = abs(r1 - r2) + abs(c1 - c2)
                min_inter_dist = min(min_inter_dist, d)

    metrics["min_inter_endpoint_dist"] = (min_inter_dist
                                          if min_inter_dist != float('inf')
                                          else 0)

    # ── ボトルネック（1セル幅の通路）──
    bottleneck_count = 0
    for r in range(rows):
        for c in range(cols):
            if (r, c) in blocked:
                continue
            is_endpoint = (r, c) in {pt for pts in pairs.values()
                                     for pt in pts}
            if is_endpoint:
                continue
            # 非ブロック隣接セル数
            free_neighbors = 0
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if (0 <= nr < rows and 0 <= nc < cols
                        and (nr, nc) not in blocked):
                    free_neighbors += 1
            if free_neighbors <= 2:
                bottleneck_count += 1

    metrics["bottleneck_cells"] = bottleneck_count
    metrics["bottleneck_pct"] = bottleneck_count / usable_cells * 100

    # ── 解がある場合の追加指標 ──
    if solution_grid is not None:
        path_lengths = {}
        for r in range(rows):
            for c in range(cols):
                v = solution_grid[r][c]
                if v > 0:
                    path_lengths[v] = path_lengths.get(v, 0) + 1

        lengths = list(path_lengths.values())
        if lengths:
            metrics["path_len_min"] = min(lengths)
            metrics["path_len_max"] = max(lengths)
            metrics["path_len_avg"] = sum(lengths) / len(lengths)
            metrics["path_len_std"] = (
                (sum((l - metrics["path_len_avg"]) ** 2
                     for l in lengths) / len(lengths)) ** 0.5)

            # マンハッタン距離と実際のパス長の比率（迂回度）
            detour_ratios = []
            for pid, pts in pairs.items():
                if len(pts) >= 2 and pid in path_lengths:
                    r0, c0 = pts[0]
                    r1, c1 = pts[1]
                    manhattan = abs(r0 - r1) + abs(c0 - c1)
                    actual = path_lengths[pid]
                    if manhattan > 0:
                        detour_ratios.append(actual / manhattan)

            if detour_ratios:
                metrics["detour_ratio_avg"] = (sum(detour_ratios) /
                                               len(detour_ratios))
                metrics["detour_ratio_max"] = max(detour_ratios)

            # パス間の接触度（異なるパスが隣接するセル数）
            contact_count = 0
            for r in range(rows):
                for c in range(cols):
                    v = solution_grid[r][c]
                    if v <= 0:
                        continue
                    for dr, dc in DIRS:
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < rows and 0 <= nc < cols):
                            nv = solution_grid[nr][nc]
                            if nv > 0 and nv != v:
                                contact_count += 1
            # 重複カウントを補正
            metrics["inter_path_contacts"] = contact_count // 2

            # 曲がり回数
            total_turns = 0
            for pid, pts in pairs.items():
                if pid not in path_lengths:
                    continue
                # パスのセルを順に辿る
                path_cells = _trace_path(solution_grid, rows, cols,
                                         pts[0], pid)
                if path_cells and len(path_cells) >= 3:
                    turns = 0
                    for i in range(1, len(path_cells) - 1):
                        pr, pc = path_cells[i - 1]
                        cr, cc = path_cells[i]
                        nr, nc = path_cells[i + 1]
                        dr1, dc1 = cr - pr, cc - pc
                        dr2, dc2 = nr - cr, nc - cc
                        if (dr1, dc1) != (dr2, dc2):
                            turns += 1
                    total_turns += turns

            metrics["total_turns"] = total_turns
            metrics["turns_per_cell"] = total_turns / usable_cells

    return metrics


def _trace_path(grid, rows, cols, start, pid):
    """解グリッド上でパスを端点から順に辿る"""
    path = [start]
    visited = {start}
    current = start

    while True:
        r, c = current
        found_next = False
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols
                    and (nr, nc) not in visited
                    and grid[nr][nc] == pid):
                path.append((nr, nc))
                visited.add((nr, nc))
                current = (nr, nc)
                found_next = True
                break
        if not found_next:
            break

    return path


# ══════════════════════════════════════════════════
#  B. SAT指標
# ══════════════════════════════════════════════════

def sat_metrics(rows, cols, pairs, blocked):
    """SATソルバーの内部統計を取得"""
    metrics = {}

    nlsat = NumberLinkSAT(rows, cols, pairs, blocked)

    # 基本制約 + 全セル充填
    clauses = nlsat._encode_base()
    for r, c in nlsat.empty_cells:
        clauses.append([nlsat._var(r, c, ki)
                        for ki in range(nlsat.K)])

    metrics["num_variables"] = nlsat._max_x_var
    metrics["num_clauses"] = len(clauses)

    solver = Minisat22()
    for cl in clauses:
        solver.add_clause(cl)

    t0 = time.time()
    result = solver.solve()
    solve_time = time.time() - t0

    metrics["solve_time_ms"] = solve_time * 1000

    # MiniSatの統計取得
    stats = solver.accum_stats()
    metrics["sat_decisions"] = stats.get("decisions", 0)
    metrics["sat_conflicts"] = stats.get("conflicts", 0)
    metrics["sat_propagations"] = stats.get("propagations", 0)
    metrics["sat_restarts"] = stats.get("restarts", 0)

    # 解を取得（構造的指標で使う）
    solution_grid = None
    if result:
        model = set(solver.get_model())
        solution_grid = nlsat._extract_grid(model)

    solver.delete()
    return metrics, solution_grid


# ══════════════════════════════════════════════════
#  C. 伝播ベース指標
# ══════════════════════════════════════════════════

def propagation_metrics(rows, cols, pairs, blocked):
    """人間的な制約伝播で、仮定なしにどこまで決まるかを測定。

    手筋:
      - 端点の隣に空きが1つしかない → そこに伸びる
      - あるセルに入れる数字が1種類しかない → 確定
      - ある数字がある方向にしか伸びられない → 確定
    これらを繰り返し適用し、確定セル数を数える。
    """
    metrics = {}

    K = len(pairs)
    pid_list = sorted(pairs.keys())
    pid_to_idx = {pid: i for i, pid in enumerate(pid_list)}

    # 各セルの候補集合を初期化
    # possible[r][c] = set of k_idx that could go here
    possible = [[set() for _ in range(cols)] for _ in range(rows)]
    determined = [[None for _ in range(cols)] for _ in range(rows)]

    endpoints = {}
    for pid, pts in pairs.items():
        k = pid_to_idx[pid]
        for r, c in pts:
            endpoints[(r, c)] = k

    for r in range(rows):
        for c in range(cols):
            if (r, c) in blocked:
                continue
            if (r, c) in endpoints:
                k = endpoints[(r, c)]
                determined[r][c] = k
                possible[r][c] = {k}
            else:
                possible[r][c] = set(range(K))

    def neighbors(r, c):
        result = []
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols
                    and (nr, nc) not in blocked):
                result.append((nr, nc))
        return result

    # 端点の接続状態を追跡: 各端点から何本出ているか
    # (簡略化: 確定セルの隣接で同じ数字の数)

    changed = True
    iterations = 0
    while changed:
        changed = False
        iterations += 1

        for r in range(rows):
            for c in range(cols):
                if (r, c) in blocked:
                    continue
                if determined[r][c] is not None:
                    continue

                nbs = neighbors(r, c)

                # 手筋1: 入れる数字が1種類しかない
                remaining = set()
                for k in possible[r][c]:
                    # kを入れるには、隣接に同じkが2つ以上可能
                    # （端点隣接なら1つ）
                    k_neighbors = sum(1 for nr, nc in nbs
                                      if k in possible[nr][nc])
                    if k_neighbors >= 2:
                        remaining.add(k)
                    elif k_neighbors == 1:
                        # 隣接が端点 or 確定セルで、
                        # そちらの延長先がここしかない場合
                        for nr, nc in nbs:
                            if (determined[nr][nc] == k and
                                    (nr, nc) in endpoints):
                                # 端点から1方向だけ→この方向で確定
                                ep_ext = sum(
                                    1 for nnr, nnc in neighbors(nr, nc)
                                    if k in possible[nnr][nnc]
                                    and (nnr, nnc) != (r, c))
                                if ep_ext == 0:
                                    remaining.add(k)

                if len(remaining) < len(possible[r][c]):
                    possible[r][c] = remaining
                    changed = True

                if len(remaining) == 1:
                    k = next(iter(remaining))
                    determined[r][c] = k
                    changed = True
                    continue

                # 手筋2: 隣接の確定セルから、ここにしか伸びられない
                for nr, nc in nbs:
                    dk = determined[nr][nc]
                    if dk is None:
                        continue
                    # この確定セルの同色隣接を数える
                    same_color_nbs = [
                        (nnr, nnc) for nnr, nnc in neighbors(nr, nc)
                        if determined[nnr][nnc] == dk]
                    undetermined_same = [
                        (nnr, nnc) for nnr, nnc in neighbors(nr, nc)
                        if (nnr, nnc) != (r, c)
                        and determined[nnr][nnc] is None
                        and dk in possible[nnr][nnc]]

                    is_ep = (nr, nc) in endpoints
                    needed = 1 if is_ep else 2

                    if (len(same_color_nbs) == needed - 1
                            and len(undetermined_same) == 0
                            and dk in possible[r][c]):
                        # ここにしか伸びられない
                        determined[r][c] = dk
                        possible[r][c] = {dk}
                        changed = True
                        break

        if iterations > rows * cols:
            break

    # 結果集計
    empty_cells = [(r, c) for r in range(rows) for c in range(cols)
                   if (r, c) not in blocked and (r, c) not in endpoints]
    total_empty = len(empty_cells)
    determined_count = sum(1 for r, c in empty_cells
                           if determined[r][c] is not None)

    # 候補が減った（が確定はしていない）セル数
    reduced_count = sum(1 for r, c in empty_cells
                        if determined[r][c] is None
                        and len(possible[r][c]) < K)

    # 候補が平均何個残っているか
    remaining_options = [len(possible[r][c]) for r, c in empty_cells
                         if determined[r][c] is None]
    avg_remaining = (sum(remaining_options) / len(remaining_options)
                     if remaining_options else 0)

    metrics["propagation_determined"] = determined_count
    metrics["propagation_total_empty"] = total_empty
    metrics["propagation_ratio"] = (determined_count / total_empty * 100
                                    if total_empty > 0 else 0)
    metrics["propagation_reduced"] = reduced_count
    metrics["propagation_avg_remaining"] = avg_remaining
    metrics["propagation_iterations"] = iterations

    return metrics


# ══════════════════════════════════════════════════
#  分析・表示
# ══════════════════════════════════════════════════

def analyze_puzzle(filepath: str, verbose: bool = False) -> dict:
    """1つのパズルの全指標を計算"""
    data = load_puzzle(filepath)
    rows, cols, pairs, blocked = parse_puzzle(data)

    # SAT指標（解も取得）
    sat_m, solution_grid = sat_metrics(rows, cols, pairs, blocked)

    # 構造的指標（解があれば追加指標も）
    struct_m = structural_metrics(rows, cols, pairs, blocked, solution_grid)

    # 伝播ベース指標
    prop_m = propagation_metrics(rows, cols, pairs, blocked)

    all_metrics = {}
    all_metrics.update(struct_m)
    all_metrics.update(sat_m)
    all_metrics.update(prop_m)
    all_metrics["file"] = os.path.basename(filepath)

    return all_metrics


def display_metrics(metrics: dict, label: str = ""):
    """指標を表示"""
    print(f"\n{'─' * 60}")
    if label:
        print(f"  [{label}] {metrics.get('file', '?')}")
    else:
        print(f"  {metrics.get('file', '?')}")
    print(f"{'─' * 60}")

    print(f"\n  ■ 基本情報")
    print(f"    サイズ: {metrics['grid_size']}, "
          f"ペア数: {metrics['num_pairs']}, "
          f"使用可能: {metrics['usable_cells']}セル")

    print(f"\n  ■ 構造的指標")
    print(f"    マンハッタン距離: "
          f"最小{metrics['manhattan_min']} "
          f"最大{metrics['manhattan_max']} "
          f"平均{metrics['manhattan_avg']:.1f}")
    print(f"    辺上の端点: {metrics['endpoints_on_edge_pct']:.0f}%"
          f"  角の端点: {metrics['endpoints_on_corner']}個")
    print(f"    異ペア端点間の最小距離: "
          f"{metrics['min_inter_endpoint_dist']}")
    print(f"    ボトルネックセル: {metrics['bottleneck_cells']}"
          f" ({metrics['bottleneck_pct']:.1f}%)")

    if "path_len_min" in metrics:
        print(f"\n  ■ パス指標（解から算出）")
        print(f"    パス長: {metrics['path_len_min']}～"
              f"{metrics['path_len_max']} "
              f"(平均{metrics['path_len_avg']:.1f}, "
              f"標準偏差{metrics['path_len_std']:.1f})")
        if "detour_ratio_avg" in metrics:
            print(f"    迂回度: 平均{metrics['detour_ratio_avg']:.2f} "
                  f"最大{metrics['detour_ratio_max']:.2f}")
        print(f"    パス間接触: {metrics['inter_path_contacts']}箇所")
        print(f"    曲がり回数: {metrics['total_turns']} "
              f"({metrics['turns_per_cell']:.2f}/セル)")

    print(f"\n  ■ SAT指標")
    print(f"    変数: {metrics['num_variables']}, "
          f"節: {metrics['num_clauses']}")
    print(f"    決定: {metrics['sat_decisions']}, "
          f"競合: {metrics['sat_conflicts']}, "
          f"伝播: {metrics['sat_propagations']}")
    print(f"    解答時間: {metrics['solve_time_ms']:.1f}ms")

    print(f"\n  ■ 伝播ベース指標（理詰めシミュレーション）")
    print(f"    仮定なしで確定: "
          f"{metrics['propagation_determined']}/"
          f"{metrics['propagation_total_empty']}セル "
          f"({metrics['propagation_ratio']:.1f}%)")
    print(f"    候補が減ったセル: {metrics['propagation_reduced']}")
    print(f"    未確定セルの平均候補数: "
          f"{metrics['propagation_avg_remaining']:.1f}")
    print(f"    伝播ラウンド数: {metrics['propagation_iterations']}")


def compare_groups(easy_metrics: list, hard_metrics: list):
    """簡単/難しいグループの指標を比較"""
    print(f"\n{'═' * 60}")
    print(f"  指標比較: 簡単 vs 難しい")
    print(f"{'═' * 60}")

    # 比較する数値指標
    compare_keys = [
        ("num_pairs", "ペア数"),
        ("manhattan_avg", "マンハッタン距離(平均)"),
        ("manhattan_max", "マンハッタン距離(最大)"),
        ("endpoints_on_edge_pct", "辺上の端点(%)"),
        ("min_inter_endpoint_dist", "異ペア端点最小距離"),
        ("bottleneck_pct", "ボトルネック(%)"),
        ("path_len_avg", "パス長(平均)"),
        ("path_len_max", "パス長(最大)"),
        ("path_len_std", "パス長(標準偏差)"),
        ("detour_ratio_avg", "迂回度(平均)"),
        ("detour_ratio_max", "迂回度(最大)"),
        ("inter_path_contacts", "パス間接触数"),
        ("total_turns", "曲がり回数"),
        ("turns_per_cell", "曲がり/セル"),
        ("sat_decisions", "SAT決定回数"),
        ("sat_conflicts", "SAT競合回数"),
        ("sat_propagations", "SAT伝播回数"),
        ("solve_time_ms", "SAT解答時間(ms)"),
        ("propagation_determined", "理詰め確定セル数"),
        ("propagation_ratio", "理詰め確定率(%)"),
        ("propagation_reduced", "候補減少セル数"),
        ("propagation_avg_remaining", "未確定の平均候補数"),
    ]

    def avg_val(group, key):
        vals = [m[key] for m in group if key in m]
        return sum(vals) / len(vals) if vals else None

    print(f"\n  {'指標':<24s} {'簡単':>10s} {'難しい':>10s} {'差':>10s}  判別力")
    print(f"  {'─' * 70}")

    discriminators = []

    for key, label in compare_keys:
        easy_avg = avg_val(easy_metrics, key)
        hard_avg = avg_val(hard_metrics, key)

        if easy_avg is None or hard_avg is None:
            continue

        diff = hard_avg - easy_avg

        # 判別力: 差の大きさを平均で正規化
        mid = (abs(easy_avg) + abs(hard_avg)) / 2
        if mid > 0:
            discrimination = abs(diff) / mid
        else:
            discrimination = 0

        # 星で判別力を表示
        if discrimination > 0.5:
            stars = "★★★"
        elif discrimination > 0.2:
            stars = "★★"
        elif discrimination > 0.1:
            stars = "★"
        else:
            stars = "  "

        discriminators.append((discrimination, label, easy_avg,
                               hard_avg, diff, stars))

        fmt_e = f"{easy_avg:.1f}" if isinstance(easy_avg, float) else str(easy_avg)
        fmt_h = f"{hard_avg:.1f}" if isinstance(hard_avg, float) else str(hard_avg)
        fmt_d = f"{diff:+.1f}" if isinstance(diff, float) else f"{diff:+d}"

        print(f"  {label:<24s} {fmt_e:>10s} {fmt_h:>10s} {fmt_d:>10s}  {stars}")

    # 判別力順にランキング
    discriminators.sort(key=lambda x: x[0], reverse=True)
    print(f"\n  ■ 判別力ランキング（上位）")
    for i, (disc, label, _, _, diff, _) in enumerate(discriminators[:8]):
        direction = "↑難" if diff > 0 else "↓難"
        print(f"    {i+1}. {label} (判別力{disc:.2f}, {direction})")


def main():
    parser = argparse.ArgumentParser(
        description="ナンバーリンク難易度指標分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
使用例:
  # 全指標を表示
  python numberlink_difficulty.py puzzle.json -v

  # 簡単/難しいを比較（--で区切る）
  python numberlink_difficulty.py easy1.json easy2.json -- hard1.json hard2.json

  # ラベル付きで複数分析
  python numberlink_difficulty.py *.json
""")
    parser.add_argument("files", nargs="+",
                        help="パズルJSONファイル（--で簡単/難しいを区切る）")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="全指標の詳細を表示")

    args = parser.parse_args()

    # argparseは--を食ってしまうので、sys.argvから直接検出
    raw_args = sys.argv[1:]
    has_separator = "--" in raw_args
    verbose = "-v" in raw_args or "--verbose" in raw_args

    if has_separator:
        sep = raw_args.index("--")
        easy_files = [f for f in raw_args[:sep]
                      if not f.startswith("-")]
        hard_files = [f for f in raw_args[sep + 1:]
                      if not f.startswith("-")]

        print(f"\n{'═' * 60}")
        print(f"  ナンバーリンク難易度分析")
        print(f"  簡単: {len(easy_files)}問, 難しい: {len(hard_files)}問")
        print(f"{'═' * 60}")

        easy_metrics = []
        for f in easy_files:
            m = analyze_puzzle(f, verbose=verbose)
            if verbose:
                display_metrics(m, "簡単")
            easy_metrics.append(m)

        hard_metrics = []
        for f in hard_files:
            m = analyze_puzzle(f, verbose=verbose)
            if verbose:
                display_metrics(m, "難しい")
            hard_metrics.append(m)

        compare_groups(easy_metrics, hard_metrics)

    else:
        all_files = [f for f in raw_args if not f.startswith("-")]
        for f in all_files:
            m = analyze_puzzle(f, verbose=True)
            display_metrics(m)


if __name__ == "__main__":
    main()
