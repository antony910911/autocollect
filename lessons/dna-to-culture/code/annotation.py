"""把定序廠的註解包（GFF／faa／xlsx）變成可以用的東西。

這支程式處理的是「拿到註解之後」的三件事：

1. `summary`  —— 統計兩株的註解，並用 Pfam 家族計數獨立驗證轉殖基因的拷貝數。
                 產出 `annotation.json`，第 17 章的數字都引用它。
2. `fix-gff`  —— 修正轉殖基因的基因模型。AUGUSTUS 會在 cDNA 來源的外源基因裡
                 預測出不存在的內含子，直接拿去做 RNA-seq 計數會算錯。
3. `gem-map`  —— 產生「把 rhto-GEM 的基因 ID 對到你的 g_##### ID」所需的輸入與指令。
                 **比對本身要下載 rhto-GEM 與參考蛋白質序列，這一步請在自己的電腦上跑。**

用法（註解包解開後的資料夾，裡面要有 .gff / .faa / 基因註解列表 .xlsx）：

    python annotation.py summary --wt <Rt_WT 資料夾> --mut <A13_4 資料夾> -o annotation.json
    python annotation.py fix-gff --gff Rt_WT.gff --copies case_rt.json -o Rt_WT.fixed.gff
    python annotation.py gem-map --faa Rt_WT.faa -o gem-map/

需要 openpyxl（只有 summary 用得到）：pip install openpyxl
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

# 轉殖構築上的 AFS CDS 在構築座標的位置（和 case_rt.py 的 AFS_CDS 一致）
AFS_CDS = (1366, 3097)
AFS_LEN = AFS_CDS[1] - AFS_CDS[0]      # 1731 bp＝576 個密碼子 ＋ 終止碼
PROBE = 60                              # case_rt.py 用 60 bp 探針定位，座標換算要用到

# 要單獨計數的 Pfam 家族。選這幾個是因為它們能獨立驗證「插進去了什麼」：
# 萜類合成酶＝AFS 本體、GNAT＝篩選標記、其餘三個＝質體骨架。
FAMILIES = {
    "terpene_synthase": (("PF01397", "PF03936"), "萜類合成酶（AFS 本體）"),
    "gnat": (("PF00583",), "GNAT 乙醯轉移酶（篩選標記；宿主本來也有）"),
    "rep_initiator": (("PF10134",), "Replication initiator protein A（質體骨架）"),
    "resolvase": (("PF00239",), "Resolvase（質體骨架）"),
    "para": (("PF01656",), "ParA（質體骨架）"),
}


# ────────────────────────── 讀檔 ──────────────────────────
def _pick(folder: Path, *suffixes: str) -> Path:
    """在資料夾裡（含子資料夾）找唯一一個符合副檔名的檔案。"""
    hits = [p for p in sorted(folder.rglob("*")) if p.suffix.lower() in suffixes]
    if not hits:
        raise SystemExit(f"{folder} 裡找不到 {'／'.join(suffixes)} 檔")
    if len(hits) > 1:
        raise SystemExit(f"{folder} 裡有多個 {'／'.join(suffixes)} 檔：{[p.name for p in hits]}")
    return hits[0]


def read_cds_table(xlsx: Path) -> list[dict]:
    """讀「基因註解列表」的 CDS 分頁，回傳每個基因一個 dict。"""
    import openpyxl
    ws = openpyxl.load_workbook(xlsx, read_only=True)["CDS"]
    rows = ws.iter_rows(values_only=True)
    hdr = [h for h in next(rows) if h is not None]
    out = []
    for r in rows:
        d = {k: ("" if v in (None, "-") else str(v)) for k, v in zip(hdr, r)}
        if d.get("Gene ID"):
            out.append(d)
    return out


def read_summary_sheet(xlsx: Path) -> dict:
    """讀「Annotation Summary」分頁的那一列統計。"""
    import openpyxl
    ws = openpyxl.load_workbook(xlsx, read_only=True)["Annotation Summary"]
    rows = list(ws.iter_rows(values_only=True))
    labels = [x for x in rows[1] if x is not None]
    values = [x for x in rows[2] if x is not None][1:]   # 第一欄是 "CDS" 這個列名
    return dict(zip(labels, values))


def read_faa_lengths(faa: Path) -> dict[str, int]:
    """每個基因的預測蛋白質長度（胺基酸數）。"""
    lens, cur = {}, None
    for line in faa.open():
        if line.startswith(">"):
            cur = re.split(r"[\s|]", line[1:].strip())[0]
            cur = re.sub(r"_(mRNA|CDS|protein).*$", "", cur)
            lens[cur] = 0
        elif cur:
            lens[cur] += len(line.strip())
    return lens


def read_gff(gff: Path):
    """回傳 (基因列表, 每個基因的 exon 數)。只收 gene 這一層。"""
    genes, exons = [], Counter()
    for line in gff.open():
        if line.startswith("#"):
            continue
        p = line.rstrip("\n").split("\t")
        if len(p) < 9:
            continue
        tag = re.search(r"locus_tag=([^;]+)", p[8])
        if not tag:
            continue
        if p[2] == "gene":
            genes.append({"id": tag.group(1), "contig": p[0],
                          "start": int(p[3]), "end": int(p[4]), "strand": p[6]})
        elif p[2] == "exon":
            exons[tag.group(1)] += 1
    return genes, exons


# ────────────────────────── summary ──────────────────────────
def family_of(row: dict) -> str | None:
    pf = row.get("Pfam", "")
    for name, (ids, _) in FAMILIES.items():
        if any(i in pf for i in ids):
            return name
    return None


def profile(folder: Path) -> dict:
    xlsx = _pick(folder, ".xlsx")
    gff = _pick(folder, ".gff")
    faa = _pick(folder, ".faa")
    rows = read_cds_table(xlsx)
    summ = read_summary_sheet(xlsx)
    genes, exons = read_gff(gff)
    lens = read_faa_lengths(faa)
    pos = {g["id"]: g for g in genes}

    fam = defaultdict(list)
    for r in rows:
        f = family_of(r)
        if f:
            g = r["Gene ID"]
            fam[f].append({"id": g, "ko": r.get("KEGG Orthology", ""),
                           "pathway": r.get("KEGG Pathway ID", ""),
                           "aa": lens.get(g), "exons": exons.get(g),
                           **{k: pos[g][k] for k in ("contig", "start", "end", "strand")
                              if g in pos}})
    for v in fam.values():
        v.sort(key=lambda d: (d.get("contig", ""), d.get("start", 0)))

    hit = lambda a, b: {"hit": summ.get(a), "no_hit": summ.get(b)}  # noqa: E731
    return {
        "source": {"xlsx": xlsx.name, "gff": gff.name, "faa": faa.name},
        "counts": {
            "cds": summ.get("Total CDS"), "known_cds": summ.get("Known CDS"),
            "hypothetical_cds": summ.get("Hypothetical CDS"),
            "rna": summ.get("Total RNA"), "rrna": summ.get("rRNA"), "trna": summ.get("tRNA"),
            "gff_gene_features": len(genes),
        },
        "coverage": {"kegg": hit("Hit", "No hit"), "pfam_rows": len(rows)},
        "families": {k: {"n": len(v), "what": FAMILIES[k][1], "genes": v} for k, v in fam.items()},
    }


def cmd_summary(args):
    wt, mut = profile(Path(args.wt)), profile(Path(args.mut))
    # 兩株相減＝插進去的東西。宿主自己也有 GNAT，所以要用差值而不是絕對數。
    delta = {k: {"wt": wt["families"].get(k, {}).get("n", 0),
                 "mut": mut["families"].get(k, {}).get("n", 0),
                 "what": FAMILIES[k][1]} for k in FAMILIES}
    for v in delta.values():
        v["delta"] = v["wt"] - v["mut"]

    ts = wt["families"].get("terpene_synthase", {}).get("genes", [])
    out = {
        "note": "由定序廠註解包產生；只用 Pfam／KEGG 家族計數，沒有用到 k-mer 分析的任何結果。",
        "wt": wt, "mut": mut, "delta": delta,
        "insertion_site": (site_neighbours(Path(args.site_gff), args.site_contig,
                                          args.site_start, args.site_end)
                           if args.site_gff else None),
        "afs_predicted": {
            "n": len(ts),
            "aa_counts": dict(Counter(g["aa"] for g in ts if g["aa"])),
            "exon_counts": dict(Counter(g["exons"] for g in ts if g["exons"])),
            "true_aa": AFS_LEN // 3 - 1,
            "true_exons": 1,
        },
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"寫入 {args.out}")
    for k, v in delta.items():
        print(f"  {v['what']}：WT {v['wt']}、MUT {v['mut']}、差 {v['delta']}")
    s = out.get("insertion_site")
    if s:
        if s["disrupts_gene"]:
            print(f"  插入點打斷了 {len(s['disrupts_gene'])} 個基因："
                  f"{[g['id'] for g in s['disrupts_gene']]}")
        else:
            u, d = s["upstream"], s["downstream"]
            print(f"  插入點落在基因之間：上游 {u['id']} 距 {u['distance_bp']} bp、"
                  f"下游 {d['id']} 距 {d['distance_bp']} bp")
    a = out["afs_predicted"]
    print(f"  AFS 預測長度分布 {a['aa_counts']}（正確應為 {a['true_aa']} aa）"
          f"、exon 數分布 {a['exon_counts']}（正確應為 1）")



# ────────────────────────── 插入點旁邊有什麼 ──────────────────────────
def site_neighbours(folder: Path, contig: str, g0: int, g1: int, window: int = 20000) -> dict:
    """插入點落在哪裡：打斷了基因，還是落在基因之間？

    要用**沒有插入的那一株**的註解來看——有插入的那一株在這個位置是 76 kb 的陣列，
    看不出原本長什麼樣子。
    """
    import openpyxl
    genes, _ = read_gff(_pick(folder, ".gff"))
    near = [g for g in genes if g["contig"] == contig
            and g["start"] < g1 + window and g["end"] > g0 - window]
    near.sort(key=lambda g: g["start"])
    inside = [g for g in near if g["start"] <= g1 and g["end"] >= g0]
    left = [g for g in near if g["end"] < g0]
    right = [g for g in near if g["start"] > g1]

    func = {}
    ws = openpyxl.load_workbook(_pick(folder, ".xlsx"), read_only=True)["CDS"]
    rows = ws.iter_rows(values_only=True)
    hdr = [h for h in next(rows) if h is not None]
    want = {g["id"] for g in near}
    for r in rows:
        d = dict(zip(hdr, r))
        if d.get("Gene ID") in want:
            func[d["Gene ID"]] = {k: ("" if d.get(k) in (None, "-") else d[k])
                                  for k in ("KEGG Orthology", "KEGG Pathway ID",
                                            "GO - Biological Process ID", "Pfam", "Pfam ID")}

    def pack(g, dist):
        return {**g, "distance_bp": dist, "annotated": bool(any(func.get(g["id"], {}).values())),
                "function": func.get(g["id"], {})}

    return {
        "contig": contig, "start": g0, "end": g1,
        "disrupts_gene": [pack(g, 0) for g in inside],
        "upstream": pack(left[-1], g0 - left[-1]["end"]) if left else None,
        "downstream": pack(right[0], right[0]["start"] - g1) if right else None,
    }


# ────────────────────────── fix-gff ──────────────────────────
def copy_cds_interval(copy: dict) -> tuple[int, int, str]:
    """把 case_rt.py 的探針命中位置換算成 GFF 的 1-based CDS 區間。

    case_rt.py 用構築上 AFS CDS 開頭的 60 bp 當探針。正股命中時 pos 就是 CDS 起點；
    負股命中的是反向互補的探針，所以 CDS 落在 [pos+60-len, pos+60)（0-based）。
    """
    i = copy["pos"]
    if copy["strand"] > 0:
        a0, a1 = i, i + AFS_LEN
        strand = "+"
    else:
        a0, a1 = i + PROBE - AFS_LEN, i + PROBE
        strand = "-"
    return a0 + 1, a1, strand           # 轉成 1-based 閉區間


def cmd_fix_gff(args):
    copies = json.loads(Path(args.copies).read_text())["wt_afs_copies"]
    if not copies:
        raise SystemExit("case_rt.json 裡沒有 AFS 拷貝——是不是指到了沒有插入的那一株？")
    fixed = [dict(c, **dict(zip(("g0", "g1", "sign"), copy_cds_interval(c)))) for c in copies]

    # 先找出和拷貝重疊的原始基因，把它們整段換掉
    drop, kept = set(), []
    for line in Path(args.gff).open():
        if line.startswith("#"):
            kept.append(line)
            continue
        p = line.rstrip("\n").split("\t")
        if len(p) < 9:
            kept.append(line)
            continue
        tag = re.search(r"locus_tag=([^;]+)", p[8])
        hit = any(p[0] == c["contig"] and int(p[3]) <= c["g1"] and int(p[4]) >= c["g0"]
                  for c in fixed)
        if hit and tag:
            drop.add(tag.group(1))
        else:
            kept.append(line)

    rows = []
    for n, c in enumerate(fixed, 1):
        gid = f"AFS_{n:02d}"
        attrs = (f"locus_tag={gid};product=alpha-farnesene synthase (transgene);"
                 f"note=single exon cDNA, copy intact={c['intact']}, "
                 f"protein_aa={c['protein_aa']}")
        for feat, pid in (("gene", f"ID={gid}_gene;"), ("mRNA", f"ID={gid}_mRNA;Parent={gid}_gene;"),
                          ("exon", f"ID={gid}_exon1;Parent={gid}_mRNA;"),
                          ("CDS", f"ID={gid}_CDS1;Parent={gid}_mRNA;")):
            frame = "0" if feat == "CDS" else "."
            rows.append("\t".join([c["contig"], "transgene_fix", feat, str(c["g0"]), str(c["g1"]),
                                   ".", c["sign"], frame, pid + attrs]) + "\n")
    Path(args.out).write_text("".join(kept + rows))
    print(f"寫入 {args.out}")
    print(f"  移除原本和陣列重疊的 {len(drop)} 個基因模型：{sorted(drop)}")
    print(f"  換成 {len(fixed)} 個單 exon 的 AFS 模型（每個 {AFS_LEN} bp）")
    print("  之後做 RNA-seq 計數請用這份修過的 GFF；"
          "注意 11 個完全相同的拷貝彼此是多重對應，計數工具要設定成「整個陣列當一個單位」。")



# ────────────────────────── 把插入點旁邊的鄰居抽出來 ──────────────────────────
NEIGHBOUR_README = """# 插入點旁邊那兩個基因

那段外來 DNA 插進去的地方，是兩個基因中間的空地。兩個基因本身都**沒有被壓到**，
但右邊那個的「開關區」被蓋掉了大半（只剩 {gap} bp 原生序列）。

問題是：**這兩個基因是做什麼的，定序廠的註解查不出來**——
KEGG、GO、Pfam 三個資料庫都沒有命中。
所以這裡把它們的蛋白質序列抽出來，讓你拿去查。

## 怎麼查（在你自己的電腦或瀏覽器上）

### 最快的一條：網頁版 BLAST

1. 開 <https://blast.ncbi.nlm.nih.gov/Blast.cgi>，選 **blastp**。
2. 把 `downstream.faa` 的內容整個貼進去（就是開關被蓋掉的那一個，比較重要）。
3. Database 選 `nr`，按 BLAST。等一兩分鐘。
4. 看前幾名的 **Description** 和 **Per. Ident**：
   - 命中紅酵母或近緣真菌、相似度 >70% → 名稱大致可信
   - 只命中「hypothetical protein」→ 這個蛋白質學界也還不知道是什麼
   - 完全沒有像樣的命中 → 可能是這株菌特有的

### 另一條：去 JGI 查同一個基因

這株菌的參考基因體 `Rhoto_IFO0880_4` 在 JGI MycoCosm
（<https://mycocosm.jgi.doe.gov/Rhoto_IFO0880_4/>，要註冊）。
那份註解做得比定序廠這份好。把序列貼進它的 BLAST 介面，
找到對應的基因編號之後，就能看到 JGI 給的功能描述與表現量資料。

## 查到之後要回頭看什麼

如果 `downstream` 那個基因是**代謝相關**的（酵素、轉運蛋白），
那它的開關被動到就可能直接影響代謝，要列進實驗要量的項目。

如果它是**調控蛋白**（轉錄因子、訊息傳遞），影響可能更廣但更難預測。

如果它是**功能不明或非必需**的，那這件事就可以放下，專心處理拷貝數與前驅物競爭。

不管答案是哪一個，最直接的驗證都是同一件事：
**用 RNA-seq 比較兩株這個基因的表現量差多少。**
"""


def cmd_neighbours(args):
    """把插入點上下游那兩個基因的蛋白質序列抽出來，附上怎麼查的說明。"""
    folder = Path(args.dir)
    lens = read_faa_lengths(_pick(folder, ".faa"))
    seqs, cur = {}, None
    for line in _pick(folder, ".faa").open():
        if line.startswith(">"):
            cur = re.sub(r"_(mRNA|CDS|protein).*$", "",
                         re.split(r"[\s|]", line[1:].strip())[0])
            seqs[cur] = []
        elif cur:
            seqs[cur].append(line.strip())
    seqs = {k: "".join(v) for k, v in seqs.items()}

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for tag, gid, what in (("upstream", args.upstream, "插入點上游；3' 端朝著插入點"),
                           ("downstream", args.downstream, "插入點下游；開關區被蓋掉的就是這個")):
        key = next((k for k in seqs if k.startswith(gid)), None)
        if key is None:
            raise SystemExit(f"{folder} 的蛋白質檔裡找不到 {gid}")
        s = seqs[key]
        body = "\n".join(s[i:i + 60] for i in range(0, len(s), 60))
        (out / f"{tag}.faa").write_text(f">{gid} {len(s)}aa | {what}\n{body}\n")
        print(f"寫入 {out}/{tag}.faa（{gid}，{len(s)} aa）")
    (out / "README.md").write_text(NEIGHBOUR_README.format(gap=args.gap))
    print(f"寫入 {out}/README.md")


# ────────────────────────── gem-map ──────────────────────────
GEM_README = """# 把 rhto-GEM 的基因對到你的 g_##### ID

這一步要下載檔案，**請在自己的電腦上跑**（教材的容器沒有對外網路）。

## 你需要先下載兩樣東西

1. **rhto-GEM**：<https://github.com/SysBioChalmers/rhto-GEM>
   模型檔是 `model/rhto.xml`（SBML）。它的基因 ID 是 IFO 0880 的 `RHTO_#####`。
2. **IFO 0880 的蛋白質序列**：JGI MycoCosm 的 `Rhoto_IFO0880_4`
   （<https://mycocosm.jgi.doe.gov/Rhoto_IFO0880_4/>，要註冊帳號）。
   下載 `*_GeneCatalog_proteins_*.fasta.gz`。

## 步驟

```bash
pip install cobra biopython
conda install -c bioconda diamond        # 或 brew install diamond

# 1. 建索引（參考 = IFO 0880 的蛋白質）
diamond makedb --in Rhoto_IFO0880_4_proteins.fasta -d ifo0880

# 2. 你的蛋白質 → IFO 0880（正向）
diamond blastp -q QUERY_FAA -d ifo0880 -o fwd.tsv \\
  --outfmt 6 qseqid sseqid pident length evalue bitscore --max-target-seqs 1 --evalue 1e-10

# 3. 反向（互為最佳命中才算數；單向命中會把旁系同源當成直系同源）
diamond makedb --in QUERY_FAA -d mine
diamond blastp -q Rhoto_IFO0880_4_proteins.fasta -d mine -o rev.tsv \\
  --outfmt 6 qseqid sseqid pident length evalue bitscore --max-target-seqs 1 --evalue 1e-10

# 4. 取互為最佳命中，並列出模型裡對不到的基因
python rbh.py fwd.tsv rev.tsv rhto.xml -o gene_map.json
```

## 產出

`gene_map.json` 有三塊：

- `map`：`RHTO_##### ↔ g_#####` 的對照（互為最佳命中）
- `model_only`：模型裡有、你的菌株對不到的基因 → 這些反應的基因關聯在你的菌株上**不成立**，
  要決定是留著還是關掉
- `mine_only`：你的菌株有、模型裡沒有的基因 → 多半是模型沒收錄的代謝，不一定要處理

**轉殖基因不會出現在對照表裡**，因為 rhto-GEM 沒有 AFS。那條反應要自己加（第 16 章）。

## 一句話提醒

互為最佳命中只是起點，不是真理。二倍體、近期重複的基因家族（這株菌的萜類與脂質
相關家族都有）常常一對多。對照表裡 `ambiguous` 標成 true 的，要自己看過再用。
"""

RBH_PY = '''"""互為最佳命中（reciprocal best hit）＋ 列出模型裡對不到的基因。在自己的電腦上跑。"""
import argparse, json, re, sys


def best(path):
    out = {}
    for line in open(path):
        q, s, pid, ln, ev, bs = line.split("\\t")[:6]
        bs = float(bs)
        if q not in out or bs > out[q][1]:
            out[q] = (s, bs, float(pid))
    return out


def model_genes(xml):
    txt = open(xml).read()
    return sorted(set(re.findall(r'fbc:geneProduct[^>]*fbc:label="([^"]+)"', txt))
                  or set(re.findall(r'id="G_([A-Za-z0-9_]+)"', txt)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fwd"); ap.add_argument("rev"); ap.add_argument("model")
    ap.add_argument("-o", default="gene_map.json")
    a = ap.parse_args()
    f, r = best(a.fwd), best(a.rev)
    pairs, seen = {}, {}
    for q, (s, _, pid) in f.items():
        if r.get(s, (None,))[0] == q:
            pairs[s] = {"mine": q, "pident": pid}
            seen.setdefault(q, []).append(s)
    for s, d in pairs.items():
        d["ambiguous"] = len(seen[d["mine"]]) > 1
    genes = model_genes(a.model)
    out = {"map": pairs,
           "model_only": [g for g in genes if g not in pairs],
           "mine_only": sorted(set(f) - {d["mine"] for d in pairs.values()}),
           "n_model_genes": len(genes)}
    json.dump(out, open(a.o, "w"), ensure_ascii=False, indent=2)
    print(f"模型基因 {len(genes)} 個；對到 {len(pairs)} 個、對不到 {len(out['model_only'])} 個")
    amb = sum(1 for d in pairs.values() if d["ambiguous"])
    print(f"其中 {amb} 個是一對多（ambiguous=true），要自己看過再用")


if __name__ == "__main__":
    main()
'''


def cmd_gem_map(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    faa = Path(args.faa)
    (out / "README.md").write_text(GEM_README.replace("QUERY_FAA", faa.name))
    (out / "rbh.py").write_text(RBH_PY)
    print(f"寫入 {out}/README.md 與 {out}/rbh.py")
    print(f"  把 {faa} 和下載好的 rhto-GEM、IFO 0880 蛋白質序列放在一起，照 README 跑。")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("summary", help="統計兩株的註解並比對 Pfam 家族計數")
    s.add_argument("--wt", required=True)
    s.add_argument("--mut", required=True)
    s.add_argument("-o", "--out", default="annotation.json")
    s.add_argument("--site-gff", help="沒有插入的那一株的資料夾（看插入點原本長什麼樣子）")
    s.add_argument("--site-contig", default="Contig4")
    s.add_argument("--site-start", type=int, default=942770)
    s.add_argument("--site-end", type=int, default=942830)
    s.set_defaults(fn=cmd_summary)

    s = sub.add_parser("fix-gff", help="把轉殖基因換成正確的單 exon 模型")
    s.add_argument("--gff", required=True)
    s.add_argument("--copies", default="case_rt.json", help="case_rt.py 的輸出")
    s.add_argument("-o", "--out", required=True)
    s.set_defaults(fn=cmd_fix_gff)

    s = sub.add_parser("neighbours", help="抽出插入點上下游兩個基因的蛋白質序列")
    s.add_argument("--dir", required=True, help="沒有插入的那一株的註解資料夾")
    s.add_argument("--upstream", default="g_05720")
    s.add_argument("--downstream", default="g_05721")
    s.add_argument("--gap", type=int, default=39, help="下游基因還剩幾 bp 原生序列")
    s.add_argument("-o", "--out", default="insertion-neighbours")
    s.set_defaults(fn=cmd_neighbours)

    s = sub.add_parser("gem-map", help="產生 rhto-GEM 基因對照所需的指令與腳本")
    s.add_argument("--faa", required=True)
    s.add_argument("-o", "--out", default="gem-map")
    s.set_defaults(fn=cmd_gem_map)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
