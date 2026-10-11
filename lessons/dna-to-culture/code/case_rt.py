"""第 17 章的案例計算：把「設計的構築」對回兩份定序組裝，算出圖裡的每一個數字。

這支程式跑的是真實資料——使用者送驗的 *Rhodotorula toruloides* 野生株與基改株
全基因體組裝，加上從 Benchling 匯出的 11,647 bp 構築序列。因為那三個檔案不屬於
這個 repo（是使用者的未發表資料），所以：

  • 有檔案時：`python case_rt.py --wt A.fasta --mut B.fasta --construct C.fasta`
    會重新計算並覆寫 case_rt.json。
  • 沒有檔案時：第 17 章的圖直接讀 case_rt.json，裡面是上一次真實執行的輸出。

JSON 的 `provenance` 欄位記下了當時的輸入檔名、長度與參數，方便日後核對。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import genome_tools as gt

HERE = Path(__file__).resolve().parent
JSON = HERE / "case_rt.json"

# AFS CDS 在構築上的位置（由 ORF 掃描得到：576 aa ＋ 終止密碼子）
AFS_CDS = (1366, 3097)
# 構築上的元件。逐字比對已知序列得到的標 confirmed，依模體推定的標 inferred。
ELEMENTS = [
    (125, 150, "LB", "border", "confirmed"),
    (164, 182, "pUC／M13 殘跡", "vector", "confirmed"),
    (150, 1366, "啟動子 P1", "promoter", "unknown"),
    (1366, 3097, "α-farnesene 合成酶 576 aa", "gene", "confirmed"),
    (3097, 3180, "nos terminator", "terminator", "confirmed"),
    (3215, 3350, "nos promoter", "promoter", "confirmed"),
    (3353, 3374, "多選殖位 MCS", "vector", "confirmed"),
    (3374, 4190, "啟動子 P2", "promoter", "unknown"),
    (4190, 4766, "篩選標記 GNAT", "gene", "inferred"),
    (4766, 5570, "終止子", "terminator", "unknown"),
    (5597, 5622, "RB", "border", "confirmed"),
    (5902, 6718, "KanR 271 aa", "gene", "inferred"),
    (6812, 6960, "pUC／pBR ori", "ori", "confirmed"),
    (8330, 9437, "骨架 ORF 368 aa", "gene", "unknown"),
    (9831, 10461, "ParA 209 aa", "gene", "inferred"),
    (10759, 11446, "重組酶 228 aa", "gene", "inferred"),
]


def assembly_stats(path) -> dict:
    recs = gt.read_fasta(path)
    lens = sorted((len(s) for _, s in recs), reverse=True)
    total = sum(lens)
    acc, n50 = 0, 0
    for L in lens:
        acc += L
        if acc >= total / 2:
            n50 = L
            break
    seq = "".join(s for _, s in recs).upper()
    return {"contigs": len(recs), "total_bp": total, "n50": n50, "longest": lens[0],
            "gc_pct": round(gt.gc_pct(seq), 2), "n_bases": seq.count("N")}


def kmer_overlap(wt, mut, k: int = 31) -> dict:
    a, b = gt.kmer_set(wt, k), gt.kmer_set(mut, k)
    shared = int(gt.contains(a, b).sum())
    return {"k": k, "wt_unique_kmers": int(len(a)), "mut_unique_kmers": int(len(b)),
            "shared": shared, "only_in_wt": int(len(a)) - shared, "only_in_mut": int(len(b)) - shared,
            "shared_frac_of_mut": round(shared / len(b), 5)}


def trace(construct: str, genome_path, k: int = 25, gap: int = 60, min_anchor: int = 20):
    """用構築上唯一的 k-mer 當錨點，逐鹼基追蹤基因體與構築的對應關係。"""
    L = len(construct)
    idx = gt._anchor_index(construct, k)
    cov = np.zeros(L, dtype=int)
    segs = []
    for ctg, seq in gt.read_fasta(genome_path):
        seq = seq.upper()
        cur = None
        for g in range(len(seq) - k + 1):
            hit = idx.get(seq[g:g + k])
            if hit is None:
                continue
            c, s = hit
            if (cur and s == cur["s"] and g - cur["g1"] <= gap
                    and (c - cur["c1"]) * s == g - cur["g1"]):
                cur["g1"], cur["c1"], cur["n"] = g, c, cur["n"] + 1
            else:
                if cur and cur["n"] >= min_anchor:
                    segs.append(cur)
                cur = {"ctg": ctg, "g0": g, "g1": g, "c0": c, "c1": c, "s": s, "n": 1}
        if cur and cur["n"] >= min_anchor:
            segs.append(cur)
    out = []
    for sg in segs:
        lo, hi = sorted((sg["c0"], sg["c1"]))
        cov[lo:hi] += 1
        out.append({"contig": sg["ctg"], "g0": sg["g0"], "g1": sg["g1"] + k,
                    "c0": sg["c0"], "c1": sg["c1"], "strand": int(sg["s"]),
                    "len": sg["g1"] - sg["g0"] + k})
    runs = []
    st = 0
    for i in range(1, L + 1):
        if i == L or cov[i] != cov[st]:
            runs.append({"c0": st, "c1": i, "copies": int(cov[st])})
            st = i
    return out, runs


def afs_copies(construct: str, genome_path) -> list[dict]:
    """逐一取出基因體上每個 AFS 拷貝，與構築逐鹼基比對。

    注意方向：探針若命中負股，必須取反向互補再轉譯，否則會得到假的突變與假的
    提前終止——這個坑我們實際踩過一次。
    """
    s0, s1 = AFS_CDS
    ref = construct[s0:s1]
    probe = construct[s0:s0 + 60]
    rprobe = gt.rc(probe)
    found = []
    for ctg, seq in gt.read_fasta(genome_path):
        seq = seq.upper()
        for strand, p in [(1, probe), (-1, rprobe)]:
            start = 0
            while True:
                i = seq.find(p, start)
                if i < 0:
                    break
                start = i + 1
                if strand > 0:
                    cds = seq[i:i + len(ref)]
                else:
                    cds = gt.rc(seq[i + 60 - len(ref):i + 60])
                aa = gt.translate(cds)
                stop = aa.find("*")
                diffs = [j for j in range(min(len(cds), len(ref))) if cds[j] != ref[j]]
                found.append({"contig": ctg, "pos": i, "strand": strand,
                              "diff_bp": len(diffs),
                              "first_diff": diffs[0] if diffs else None,
                              "protein_aa": stop if stop >= 0 else len(aa),
                              "stop_codon": stop + 1 if stop >= 0 else None,
                              "intact": len(diffs) == 0 and stop == len(ref) // 3 - 1})
    found.sort(key=lambda d: (d["contig"], d["pos"]))
    return found


def flank_hit(absent_genome, carrier_path, contig: str, array_g0: int, array_g1: int, flank: int = 2000):
    """插入點：陣列左右側翼落在「沒有插入的那一株」的哪裡。

    兩側側翼若落在同一條 contig 的相鄰位置，就是單一插入位點、沒有染色體重排。
    """
    import mappy as mp
    aln = mp.Aligner(absent_genome, preset="asm10", n_threads=4)
    seq = dict(gt.read_fasta(carrier_path))[contig].upper()
    out = {"query_contig": contig}
    for side, (a, b) in {"left": (max(0, array_g0 - flank), array_g0),
                         "right": (array_g1, array_g1 + flank)}.items():
        best = None
        for h in aln.map(seq[a:b]):
            if best is None or h.mlen > best.mlen:
                best = h
        out[side] = ({"contig": best.ctg, "start": best.r_st, "end": best.r_en,
                      "strand": int(best.strand), "mlen": best.mlen} if best else None)
    if out["left"] and out["right"] and out["left"]["contig"] == out["right"]["contig"]:
        lo = min(out["left"]["end"], out["right"]["end"])
        hi = max(out["left"]["start"], out["right"]["start"])
        out["gap_bp"] = max(0, hi - lo)
        out["same_contig"] = True
    else:
        out["same_contig"] = False
    return out


def load() -> dict:
    return json.loads(JSON.read_text("utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wt", required=True, help="標示為野生株的組裝")
    ap.add_argument("--mut", required=True, help="標示為基改株的組裝")
    ap.add_argument("--construct", required=True, help="設計的構築（單一條，視為環狀）")
    ap.add_argument("--k", type=int, default=25)
    ap.add_argument("--kmer-k", type=int, default=31)
    ap.add_argument("--out", default=str(JSON))
    args = ap.parse_args(argv)

    cname, con = gt.read_fasta(args.construct)[0]
    con = con.upper()
    print(f"構築 {cname}：{len(con):,} bp，GC {gt.gc_pct(con):.1f}%")

    res = {"provenance": {
        "construct_name": cname, "construct_bp": len(con),
        "construct_gc_pct": round(gt.gc_pct(con), 1),
        "wt_file": Path(args.wt).name, "mut_file": Path(args.mut).name,
        "anchor_k": args.k, "kmer_k": args.kmer_k,
    }, "elements": [{"c0": a, "c1": b, "name": n, "kind": t, "evidence": e}
                    for a, b, n, t, e in ELEMENTS], "afs_cds": list(AFS_CDS)}

    print("組裝統計…", flush=True)
    res["assembly"] = {"wt": assembly_stats(args.wt), "mut": assembly_stats(args.mut)}
    print("k-mer 共有比例…", flush=True)
    res["kmer"] = kmer_overlap(args.wt, args.mut, args.kmer_k)

    for tag, path in (("wt", args.wt), ("mut", args.mut)):
        print(f"把構築對回 {tag}…", flush=True)
        segs, runs = trace(con, path, k=args.k)
        copies = afs_copies(con, path)
        res[tag + "_trace"] = {"segments": segs, "coverage": runs}
        res[tag + "_afs_copies"] = copies
        print(f"  {len(segs)} 段整合片段、{len(copies)} 個 AFS 拷貝")

    host = "mut" if not res["mut_trace"]["segments"] else "wt"
    carrier = "wt" if host == "mut" else "mut"
    segs = res[carrier + "_trace"]["segments"]
    if segs:
        g0, g1 = min(s["g0"] for s in segs), max(s["g1"] for s in segs)
        res["array"] = {"carrier": carrier, "contig": segs[0]["contig"], "g0": g0, "g1": g1,
                        "span": g1 - g0,
                        "mapped_bp": sum(s["len"] for s in segs)}
        print("定位插入點…", flush=True)
        paths = {"wt": args.wt, "mut": args.mut}
        res["array"]["junction"] = flank_hit(paths[host], paths[carrier],
                                             res["array"]["contig"], g0, g1)

    Path(args.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), "utf-8")
    print(f"\n寫入 {args.out}")


if __name__ == "__main__":
    main()
