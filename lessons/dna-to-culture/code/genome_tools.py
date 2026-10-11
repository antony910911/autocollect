"""從定序組裝到註解：教材第 2、15、16 章的實作工具。

這支程式做的是「不需要連網、不需要幾十 GB 資料庫」就能做完的那一段：

  stats     組裝品質（contig 數、N50、GC、N 含量）
  compare   野生株 vs 基改株：用 k-mer 找出「只有其中一邊有」的序列
  orfs      在序列中找 ORF、轉譯成蛋白質、標出保守模體、判斷像不像外來 DNA
  cassette  從 compare 的結果推斷插入位置、拷貝數與側翼序列
  plan      產生「在你自己電腦上跑完整功能註解」的指令稿

**為什麼註解分成兩段？**
基因預測與功能註解（BRAKER、eggNOG-mapper、KEGG、InterProScan）需要下載數十 GB 的
資料庫，而且多半只能在 Linux 上跑。這支程式負責的是：
  (1) 這裡就能做完、而且對「找出基改插在哪裡」最關鍵的部分；
  (2) 幫你把剩下那段的指令寫好，你在自己的機器或伺服器上貼上去就能跑。

用法：
  python genome_tools.py stats    WT.fasta [MUT.fasta ...]
  python genome_tools.py compare  WT.fasta MUT.fasta [--k 31] [--min 200] [--out novel.fasta]
  python genome_tools.py orfs     novel.fasta [--minaa 80]
  python genome_tools.py cassette WT.fasta MUT.fasta novel.fasta [--flank 2000]
  python genome_tools.py plan     --genome MUT.fasta --species "Rhodotorula toruloides" --out annotate.sh
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

# ───────────────────────── 基本工具 ─────────────────────────
COMP = str.maketrans("ACGTacgtNn", "TGCAtgcaNn")
CODON_TABLE = {}
_B = "TCAG"
_AA = "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"
_i = 0
for _b1 in _B:
    for _b2 in _B:
        for _b3 in _B:
            CODON_TABLE[_b1 + _b2 + _b3] = _AA[_i]
            _i += 1


def rc(s: str) -> str:
    return s.translate(COMP)[::-1]


def translate(s: str) -> str:
    return "".join(CODON_TABLE.get(s[i:i + 3].upper(), "X") for i in range(0, len(s) - 2, 3))


def read_fasta(path) -> list[tuple[str, str]]:
    name, buf, out = None, [], []
    with open(path) as fh:
        for line in fh:
            if line.startswith(">"):
                if name is not None:
                    out.append((name, "".join(buf)))
                name, buf = line[1:].strip(), []
            else:
                buf.append(line.strip())
    if name is not None:
        out.append((name, "".join(buf)))
    return out


def write_fasta(path, records, width: int = 70):
    with open(path, "w") as fh:
        for name, seq in records:
            fh.write(f">{name}\n")
            for i in range(0, len(seq), width):
                fh.write(seq[i:i + width] + "\n")


def gc_pct(s: str) -> float:
    u = s.upper()
    n = u.count("A") + u.count("C") + u.count("G") + u.count("T")
    return (u.count("G") + u.count("C")) / n * 100 if n else 0.0


def complexity(s: str, w: int = 12) -> float:
    """低複雜度檢查：取樣視窗內不同 k=4 子字串的比例。1.0 = 複雜，接近 0 = 重複序列。"""
    u = s.upper()
    if len(u) < w * 2:
        return 1.0
    step = max(1, len(u) // 400)
    vals = []
    for i in range(0, len(u) - w, step):
        win = u[i:i + w]
        vals.append(len({win[j:j + 4] for j in range(w - 3)}) / (w - 3))
    return float(np.mean(vals)) if vals else 1.0


# ───────────────────────── k-mer ─────────────────────────
_TBL = np.full(256, 255, np.uint8)
for _i, _b in enumerate(b"ACGT"):
    _TBL[_b] = _i
    _TBL[_b + 32] = _i


def kmers(seq: str, k: int):
    """回傳 (正準 k-mer, 有效遮罩)。正準＝取正反股較小者，這樣方向不影響比對。"""
    a = _TBL[np.frombuffer(seq.encode(), np.uint8)]
    valid = a != 255
    a = np.where(valid, a, 0).astype(np.uint64)
    n = len(a) - k + 1
    if n <= 0:
        return np.empty(0, np.uint64), np.empty(0, bool)
    fwd = np.zeros(n, np.uint64)
    rev = np.zeros(n, np.uint64)
    ok = np.ones(n, bool)
    for j in range(k):
        fwd = (fwd << np.uint64(2)) | a[j:j + n]
        rev |= (np.uint64(3) - a[j:j + n]) << np.uint64(2 * j)
        ok &= valid[j:j + n]
    return np.minimum(fwd, rev), ok


def kmer_set(path, k: int) -> np.ndarray:
    parts = []
    for _, s in read_fasta(path):
        km, ok = kmers(s, k)
        parts.append(km[ok])
    allk = np.concatenate(parts) if parts else np.empty(0, np.uint64)
    allk.sort()
    return np.unique(allk)


def contains(ref_sorted: np.ndarray, q: np.ndarray) -> np.ndarray:
    """二分搜尋：q 的每個元素是否存在於已排序的 ref_sorted。"""
    if len(ref_sorted) == 0:
        return np.zeros(len(q), bool)
    i = np.searchsorted(ref_sorted, q)
    i[i == len(ref_sorted)] = 0
    return ref_sorted[i] == q


# ───────────────────────── 子指令 ─────────────────────────
def cmd_stats(args):
    for path in args.fasta:
        recs = read_fasta(path)
        lens = sorted((len(s) for _, s in recs), reverse=True)
        total = sum(lens)
        acc = 0
        n50 = l50 = 0
        for i, L in enumerate(lens, 1):
            acc += L
            if acc >= total / 2:
                n50, l50 = L, i
                break
        seqs = "".join(s for _, s in recs).upper()
        ns = seqs.count("N")
        print(f"\n── {Path(path).name} ──")
        print(f"  contig 數    {len(recs):,}")
        print(f"  總長         {total:,} bp")
        print(f"  N50          {n50:,} bp（L50 = {l50}）")
        print(f"  最長 / 最短  {lens[0]:,} / {lens[-1]:,} bp")
        print(f"  GC           {gc_pct(seqs):.2f}%")
        print(f"  N            {ns:,}（{ns / total * 100:.4f}%）")
        print(f"  前 5 長度    {', '.join(f'{x:,}' for x in lens[:5])}")


def cmd_compare(args):
    k, minlen = args.k, args.min
    print(f"k = {k}；只回報連續 ≥ {minlen} bp 的差異\n")
    print("建立野生株的 k-mer 集合…", flush=True)
    wt = kmer_set(args.wt, k)
    print(f"  {len(wt):,} 個獨特 {k}-mer", flush=True)
    print("建立基改株的 k-mer 集合…", flush=True)
    mu = kmer_set(args.mut, k)
    print(f"  {len(mu):,} 個獨特 {k}-mer\n", flush=True)

    only_mut = int(len(mu) - contains(wt, mu).sum())
    only_wt = int(len(wt) - contains(mu, wt).sum())
    shared = len(mu) - only_mut
    print(f"  兩邊共有          {shared:,}")
    print(f"  只在基改株        {only_mut:,}（佔基改株 {only_mut / len(mu) * 100:.3f}%）")
    print(f"  只在野生株        {only_wt:,}（佔野生株 {only_wt / len(wt) * 100:.3f}%）\n")

    rows = []
    for name, s in read_fasta(args.mut):
        km, ok = kmers(s, k)
        if len(km) == 0:
            continue
        absent = (~contains(wt, km)) & ok
        edges = np.flatnonzero(np.diff(np.concatenate(([0], absent.view(np.int8), [0]))))
        for st, en in zip(edges[::2], edges[1::2]):
            length = int(en - st + k - 1)
            if length >= minlen:
                seq = s[int(st):int(st) + length]
                rows.append({"contig": name, "start": int(st), "end": int(st) + length,
                             "len": length, "gc": gc_pct(seq), "cplx": complexity(seq), "seq": seq})
    rows.sort(key=lambda r: -r["len"])
    print(f"=== 基改株上「野生株完全沒有」的區段：{len(rows)} 段 ===\n")
    print(f"  {'contig':<12}{'起':>10}{'迄':>10}{'長度':>9}{'GC%':>7}{'複雜度':>8}  判讀")
    for r in rows[:30]:
        if r["cplx"] < 0.5:
            verdict = "低複雜度重複序列（多半是組裝差異）"
        elif abs(r["gc"] - 61) > 10:
            verdict = "★ GC 偏離基因體平均，可能是外來 DNA"
        else:
            verdict = "GC 與基因體相近（可能是菌株間差異）"
        print(f"  {r['contig']:<12}{r['start']:>10,}{r['end']:>10,}{r['len']:>9,}"
              f"{r['gc']:>7.1f}{r['cplx']:>8.2f}  {verdict}")
    if args.out:
        write_fasta(args.out, [(f"{r['contig']}_{r['start']}_{r['end']}_len{r['len']}_GC{r['gc']:.0f}", r["seq"])
                               for r in rows])
        print(f"\n全部 {len(rows)} 段寫入 {args.out}")
    print("\n提醒：GC 偏離 ＋ 複雜度正常 ＋ 有完整 ORF，三者同時成立才比較可能是插入的外源基因。"
          "\n      下一步用 orfs 子指令看有沒有 ORF，再把蛋白質序列貼到 NCBI BLASTp 確認身分。")


# 常見保守模體（用來初步判斷蛋白質種類；不是確定答案）
MOTIFS = [
    ("DDxxD", "萜類合成酶的受質鎂離子結合模體（terpene synthase）", lambda p: [
        i + 1 for i in range(len(p) - 4) if p[i] == "D" and p[i + 1] == "D" and p[i + 4] == "D"]),
    ("NSE/DTE", "萜類合成酶的第二個金屬結合模體", lambda p: [
        i + 1 for i in range(len(p) - 8)
        if p[i] in "ND" and p[i + 3] in "ST" and p[i + 4] == "E" and p[i + 7] == "E"]),
    ("GxGxxG", "核苷酸／FAD 結合（Rossmann fold）", lambda p: [
        i + 1 for i in range(len(p) - 5)
        if p[i] == "G" and p[i + 2] == "G" and p[i + 5] == "G"]),
]


def cmd_orfs(args):
    for name, s in read_fasta(args.fasta):
        found = []
        for strand, seq in (("+", s), ("-", rc(s))):
            for frame in range(3):
                prot = translate(seq[frame:])
                pos = 0
                for part in prot.split("*"):
                    m = part.find("M")
                    if m >= 0 and len(part) - m >= args.minaa:
                        aa = part[m:]
                        found.append((len(aa), strand, frame + (pos + m) * 3, aa))
                    pos += len(part) + 1
        found.sort(reverse=True)
        if not found:
            continue
        print(f"\n=== {name} ===")
        for L, strand, pos, aa in found[:args.top]:
            lc = complexity(aa, w=12)
            flag = "  ⚠ 低複雜度，多半不是真的基因" if lc < 0.55 else ""
            print(f"  ORF {L} aa（{L * 3} bp）股 {strand} 位置 {pos}{flag}")
            hits = []
            for label, desc, fn in MOTIFS:
                p = fn(aa)
                if p:
                    hits.append(f"{label}@{p[0]}")
            if hits and not flag:
                print(f"    模體：{'、'.join(hits)}")
            if not flag:
                print(f"    {aa[:70]}")
                if L > 70:
                    print(f"    …{aa[-50:]}")
        if args.prot:
            write_fasta(args.prot, [(f"{name}_orf{i + 1}_{L}aa", aa)
                                    for i, (L, _, _, aa) in enumerate(found[:args.top])], width=60)
    if args.prot:
        print(f"\n蛋白質序列寫入 {args.prot}"
              f"\n→ 貼到 https://blast.ncbi.nlm.nih.gov/ 選 blastp，就能知道它們是什麼。")


def cmd_cassette(args):
    """用新增區段的側翼序列，定位插入點落在野生株的哪裡。"""
    import mappy as mp
    print("建立野生株索引…", flush=True)
    aln = mp.Aligner(args.wt, preset="asm10", n_threads=4, best_n=10)
    if not aln:
        sys.exit("索引失敗")
    mut = dict(read_fasta(args.mut))
    print(f"\n{'新增區段':<34}{'左側翼落點':<34}{'右側翼落點'}")
    for name, seq in read_fasta(args.novel):
        parts = name.split("_")
        try:
            contig, st, en = "_".join(parts[:-4]), int(parts[-4]), int(parts[-3])
        except (ValueError, IndexError):
            print(f"  {name}：名稱不含座標，略過")
            continue
        full = mut.get(contig)
        if full is None:
            continue
        left = full[max(0, st - args.flank):st]
        right = full[en:en + args.flank]

        def locate(frag):
            if len(frag) < 200:
                return "（太短）"
            best = None
            for h in aln.map(frag):
                if best is None or h.mlen > best.mlen:
                    best = h
            if best is None:
                return "無法定位"
            return f"{best.ctg}:{best.r_st:,}-{best.r_en:,}({'+' if best.strand > 0 else '-'})"

        print(f"  {contig}:{st:,}-{en:,}".ljust(34) + locate(left).ljust(34) + locate(right))
    print("\n左右側翼落在野生株的同一個位置附近 → 那就是插入點。"
          "\n落在不同位置 → 可能伴隨染色體重排，或這段不是單純的插入。")


ANNOTATE_SH = """#!/usr/bin/env bash
# 真菌基因體功能註解流程（在你自己的 Linux 機器或伺服器上執行）
# 由 genome_tools.py plan 產生。物種：{species}
set -euo pipefail

GENOME={genome}
THREADS=${{THREADS:-8}}
OUT=annotation

# ── 0. 安裝（建議用 conda／mamba，一次裝好）──
# mamba create -n annot -c conda-forge -c bioconda \\
#     busco augustus braker2 eggnog-mapper interproscan hmmer diamond funannotate
# conda activate annot

# ── 1. 組裝完整度：BUSCO（真菌用 fungi_odb10；酵母菌可用 saccharomycetes_odb10）──
#     注意：Rhodotorula 屬於擔子菌，用 basidiomycota_odb10 更合適
busco -i "$GENOME" -l basidiomycota_odb10 -m genome -c "$THREADS" -o "$OUT/busco"

# ── 2. 基因預測（真核：一定要能處理內含子，不能用 Prokka／Bakta）──
#     方式 A：Funannotate（整合流程，最省事）
# funannotate clean -i "$GENOME" -o genome_clean.fa
# funannotate sort  -i genome_clean.fa -o genome_sorted.fa
# funannotate mask  -i genome_sorted.fa -o genome_masked.fa --cpus "$THREADS"
# funannotate predict -i genome_masked.fa -o "$OUT/funannotate" \\
#     --species "{species}" --cpus "$THREADS" --busco_seed_species ustilago
#
#     方式 B：BRAKER3（有 RNA-seq 時最準）
# braker.pl --genome="$GENOME" --prot_seq=proteins.fa --threads="$THREADS" \\
#     --workingdir="$OUT/braker" --fungus

# 預測完成後會得到蛋白質檔，後面以這個變數代表：
PROTEINS="$OUT/funannotate/predict_results/{tag}.proteins.fa"

# ── 3. 功能註解 ──
# 3a. eggNOG-mapper：直系同源群、GO、KEGG KO、COG
#     第一次要先下載資料庫（約 50 GB）：download_eggnog_data.py
emapper.py -i "$PROTEINS" -o "$OUT/eggnog" --cpu "$THREADS" -m diamond

# 3b. InterProScan：蛋白質結構域與家族
interproscan.sh -i "$PROTEINS" -d "$OUT/interpro" -cpu "$THREADS" -goterms -pa

# 3c. KEGG 路徑完整度（不想裝資料庫的話，用網頁版 BlastKOALA／KofamKOALA 上傳 $PROTEINS）
#     https://www.kegg.jp/blastkoala/

# ── 4. 基改菌株：確認插入片段 ──
# 4a. 把讀段（不是組裝）比對回參考，找 split-read 來定位插入點
# minimap2 -ax map-ont reference.fa reads.fq.gz | samtools sort -o reads.bam
# samtools index reads.bam
# 4b. 用載體序列當參考，看有多少讀段落在上面（估拷貝數）
# minimap2 -ax map-ont vector.fa reads.fq.gz | samtools view -c -F 0x904

# ── 5. 代謝模型 ──
# Rhodotorula toruloides 已有現成模型 rhto-GEM，不必從頭建：
#   git clone https://github.com/SysBioChalmers/rhto-GEM
#   python lessons/dna-to-culture/code/yeast.py rhto-GEM/model/rhto-GEM.xml
# S. cerevisiae 用 yeast-GEM：https://github.com/SysBioChalmers/yeast-GEM
# 沒有現成模型時，用 RAVEN 以近緣物種的模型當模板建草稿。

echo "完成。結果在 $OUT/"
"""


def cmd_plan(args):
    tag = Path(args.genome).stem.replace(".", "_")
    text = ANNOTATE_SH.format(species=args.species, genome=args.genome, tag=tag)
    Path(args.out).write_text(text, "utf-8")
    Path(args.out).chmod(0o755)
    print(f"寫入 {args.out}")
    print("\n這份指令稿要在你自己的機器上跑，因為：")
    print("  • eggNOG-mapper 的資料庫約 50 GB，InterProScan 也有數十 GB")
    print("  • BRAKER／AUGUSTUS／Funannotate 依賴多，建議用 conda 安裝")
    print("  • 教材的執行環境沒有對外網路，下載不了")
    print("\n不想自己架環境的替代方案：")
    print("  • KEGG 的網頁版 BlastKOALA／KofamKOALA：上傳蛋白質檔即可，免安裝")
    print("  • NCBI 網頁版 BLAST：確認單一基因的身分最快")
    print("  • 定序公司的分析套餐，或國網中心的運算資源")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("stats", help="組裝品質統計")
    p.add_argument("fasta", nargs="+")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("compare", help="野生株 vs 基改株的 k-mer 差異")
    p.add_argument("wt")
    p.add_argument("mut")
    p.add_argument("--k", type=int, default=31)
    p.add_argument("--min", type=int, default=200)
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("orfs", help="找 ORF、轉譯、標出模體")
    p.add_argument("fasta")
    p.add_argument("--minaa", type=int, default=80)
    p.add_argument("--top", type=int, default=3)
    p.add_argument("--prot", default=None, help="把蛋白質序列寫出來（可直接貼到 BLASTp）")
    p.set_defaults(func=cmd_orfs)

    p = sub.add_parser("cassette", help="用側翼序列定位插入點")
    p.add_argument("wt")
    p.add_argument("mut")
    p.add_argument("novel")
    p.add_argument("--flank", type=int, default=2000)
    p.set_defaults(func=cmd_cassette)

    p = sub.add_parser("plan", help="產生完整註解流程的指令稿")
    p.add_argument("--genome", required=True)
    p.add_argument("--species", default="Rhodotorula toruloides")
    p.add_argument("--out", default="annotate.sh")
    p.set_defaults(func=cmd_plan)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
