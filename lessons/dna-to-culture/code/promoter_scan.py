"""第 17 章：在不能連資料庫的情況下，從啟動子序列本身能看出什麼。

為什麼要有這支程式：構築上的兩個啟動子**不在宿主基因體裡**，所以不知道是哪個
基因的啟動子，也就不知道它是組成型還是受調控——而這件事會決定分階段培養要不要
限氮（第 6、17 章）。BLAST 要連網，這個環境做不到。

退而求其次能做的是：數出啟動子上幾個關鍵轉錄因子結合模體的數量，並和**宿主自己
的基因體**隨機抽樣的同長度片段比較，看是不是顯著偏多。這是線索，不是答案：
模體序列很短，隨機序列本來就會出現，所以一定要和背景比，而且**結論仍然要用
BLAST 與 RT-qPCR 確認**。

執行：python promoter_scan.py --construct construct.fasta --genome MUT.fasta
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
from pathlib import Path

import genome_tools as gt

HERE = Path(__file__).resolve().parent

# 真菌啟動子上意義明確、而且和「要不要限氮」直接相關的幾個模體。
MOTIFS = [
    ("TATA box", r"TATA[AT]A[AT]", "基礎轉錄起始；強組成型啟動子常見"),
    ("GATA（AreA／Nit2）", r"[ACT]GATA[AG]", "**氮代謝阻遏的總開關**；氮限制時 AreA 活化這類位點"),
    ("CCAAT（Hap 複合體）", r"CCAAT", "呼吸／碳源相關的通用活化元件"),
    ("STRE（AGGGG）", r"AGGGG", "逆境與進入靜止期時活化（Msn2/4 類）"),
    ("CreA／碳代謝阻遏", r"[CG][CT]GG[AG]G", "葡萄糖存在時抑制"),
]
GATA_CORE = r"[ACT]GATA[AG]"
PAIR_WINDOW = 50   # AreA 要兩個鄰近的 GATA 位點才有強活化力


def count_both_strands(seq: str, pattern: str) -> int:
    """正負股都數，允許重疊（用 lookahead）。"""
    rx = re.compile("(?=(" + pattern + "))")
    return len(rx.findall(seq)) + len(rx.findall(gt.rc(seq)))


def gata_pairs(seq: str, window: int = PAIR_WINDOW) -> int:
    pos = []
    for s in (seq, gt.rc(seq)):
        pos += [m.start() for m in re.finditer("(?=(" + GATA_CORE + "))", s)]
    pos.sort()
    return sum(1 for a, b in zip(pos, pos[1:]) if b - a <= window)


def background(genome_path, length: int, n: int, seed: int = 0):
    """從宿主基因體隨機抽 n 段同樣長度的序列當背景。"""
    rng = random.Random(seed)
    contigs = [(name, s.upper()) for name, s in gt.read_fasta(genome_path) if len(s) > length * 4]
    weights = [len(s) for _, s in contigs]
    out = []
    for _ in range(n):
        _, s = rng.choices(contigs, weights=weights)[0]
        i = rng.randrange(0, len(s) - length)
        frag = s[i:i + length]
        if frag.count("N") == 0:
            out.append(frag)
    return out


def describe(name: str, seq: str, bg: list[str]) -> dict:
    row = {"name": name, "length": len(seq), "gc_pct": round(gt.gc_pct(seq), 1), "motifs": []}
    for label, pat, why in MOTIFS:
        obs = count_both_strands(seq, pat)
        vals = sorted(count_both_strands(b, pat) for b in bg)
        row["motifs"].append({"motif": label, "why": why, "observed": obs,
                              "bg_median": statistics.median(vals),
                              "bg_p95": vals[int(0.95 * len(vals))],
                              "bg_frac_le": round(sum(1 for v in vals if v <= obs) / len(vals), 3),
                              "bg_frac_ge": round(sum(1 for v in vals if v >= obs) / len(vals), 3)})
    obs = gata_pairs(seq)
    vals = sorted(gata_pairs(b) for b in bg)
    row["gata_pairs"] = {"observed": obs, "bg_median": statistics.median(vals),
                         "bg_p95": vals[int(0.95 * len(vals))],
                         "bg_frac_le": round(sum(1 for v in vals if v <= obs) / len(vals), 3),
                         "bg_frac_ge": round(sum(1 for v in vals if v >= obs) / len(vals), 3)}
    return row


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--construct", required=True)
    ap.add_argument("--genome", required=True, help="宿主基因體（拿來當背景分布）")
    ap.add_argument("--regions", nargs="+", default=["P1:366:1366", "P2:3374:4190"],
                    help="要掃的區段，格式 名稱:起:迄（構築座標）")
    ap.add_argument("--n", type=int, default=2000, help="背景抽樣數")
    ap.add_argument("--out", default=str(HERE / "promoter_scan.json"))
    args = ap.parse_args(argv)

    con = gt.read_fasta(args.construct)[0][1].upper()
    rows = []
    for spec in args.regions:
        name, a, b = spec.split(":")
        a, b = int(a), int(b)
        seq = con[a:b]
        bg = background(args.genome, len(seq), args.n)
        print(f"\n=== {name}　構築 {a:,}–{b:,}（{len(seq):,} bp，GC {gt.gc_pct(seq):.1f}%）"
              f"　背景：宿主隨機 {len(bg)} 段 ===")
        row = describe(name, seq, bg)
        row.update({"c0": a, "c1": b})
        print(f'{"模體":22s}{"實測":>6s}{"背景中位數":>10s}{"背景 p95":>9s}'
              f'{"背景≤實測":>11s}{"背景≥實測":>11s}')
        for m in row["motifs"] + [dict(motif="GATA 成對（≤50 bp）", **row["gata_pairs"])]:
            print(f'{m["motif"]:22s}{m["observed"]:6d}{m["bg_median"]:10.1f}{m["bg_p95"]:9d}'
                  f'{m["bg_frac_le"] * 100:10.1f}%{m["bg_frac_ge"] * 100:10.1f}%')
        rows.append(row)

    Path(args.out).write_text(json.dumps({"regions": rows, "n_background": args.n,
                                          "motifs": [{"motif": m, "pattern": p, "why": w}
                                                     for m, p, w in MOTIFS]},
                                         ensure_ascii=False, indent=1), "utf-8")
    print(f"\n寫入 {args.out}")
    print("提醒：模體只有 5–6 bp，隨機序列本來就會出現，所以百分位才是重點。"
          "\n就算某個模體顯著偏多，也只是線索——啟動子的身分要靠 BLASTn，"
          "\n實際受不受氮調控要靠不同 C/N 下的 RT-qPCR。")


if __name__ == "__main__":
    main()
