"""讀 NCBI blastp 的 XML 結果，回答「插入點旁邊那個基因是什麼」。

這支程式不連網。你在 <https://blast.ncbi.nlm.nih.gov/> 把
`insertion-neighbours/downstream.faa`（或 `upstream.faa`）貼進去跑 blastp，
下載 **Single-file XML**，再用這支程式解讀：

    python blast_neighbours.py insertion-neighbours/g_05721-blastp-nr.xml \
        --faa insertion-neighbours/downstream.faa -o blast_neighbours.json

它會算四件事（第 17.11 節引用的數字全部由這裡產生）：

1. **命中表**：相似度、查詢覆蓋率、E 值；並標出有沒有「真的有名字」的命中。
2. **起始密碼子對不對**：如果好幾筆同種命中都從對方的第 1 個胺基酸開始對齊，
   代表我們的基因模型沒有少掉 N 端——這件事直接決定「插入是在基因外面還是裡面」。
3. **保守核心在哪**：只拿「種以外」的遠緣命中算每個位置被蓋到幾次。
   種內命中一定全長都像，看不出哪一段重要；遠緣命中才看得出來。
4. **低複雜度區**：胺基酸組成與 Kyte-Doolittle 疏水性。
   富含 Pro／Ser 的低複雜度區會讓自動註解亂安名字（例如 Leishmania 的
   proteophosphoglycan），看到這種名字要先確認是不是這個原因。

**這支程式只整理證據，不會給你功能。** 如果所有命中都是 hypothetical protein，
那就是學界也還不知道——那是結論，不是失敗。
"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

# Kyte-Doolittle 疏水性指數
KD = dict(zip("AILMFVPGWSTCYNQDEKRH",
               (1.8, 4.5, 3.8, 1.9, 2.8, 4.2, -1.6, -0.4, -0.9, -0.8,
                -0.7, 2.5, -1.3, -3.5, -3.5, -3.5, -3.5, -3.9, -4.5, -3.2)))
WINDOW = 19          # 跨膜螺旋大約的長度
TM_CUT = 1.6         # 疏水性門檻；2.5 以上才算強訊號
# 自動註解最常亂安的名字：看到要先懷疑是低複雜度區造成的
SUSPECT = ("proteophosphoglycan", "ppg", "mucin", "collagen", "titin")
VAGUE = ("hypothetical", "uncharacterized", "unnamed", "predicted protein")
# 只有基因座編號、沒有任何描述的定義（例如 BQ2448_5666），一樣等於沒有名字
LOCUS_ONLY = re.compile(r"^[A-Za-z]{0,6}[0-9][A-Za-z0-9_.\-]*\s*(\[|$)")


def has_name(defn: str) -> bool:
    """這筆命中有沒有真的講出功能（而不是 hypothetical 或一串基因座編號）。"""
    return not (any(v in defn.lower() for v in VAGUE) or LOCUS_ONLY.match(defn))


def read_faa(path: Path) -> str:
    return "".join(l.strip() for l in path.read_text("utf-8").splitlines()
                   if not l.startswith(">")).rstrip("*")


def parse(xml: Path) -> dict:
    root = ET.parse(xml).getroot()
    qlen = int(root.findtext("BlastOutput_query-len"))
    hits = []
    for h in root.findall(".//Hit"):
        hsps = [{"qf": int(x.findtext("Hsp_query-from")), "qt": int(x.findtext("Hsp_query-to")),
                 "hf": int(x.findtext("Hsp_hit-from")), "ht": int(x.findtext("Hsp_hit-to")),
                 "ident": int(x.findtext("Hsp_identity")),
                 "alen": int(x.findtext("Hsp_align-len")),
                 "evalue": float(x.findtext("Hsp_evalue"))}
                for x in h.findall(".//Hsp")]
        d = h.findtext("Hit_def")
        sp = re.search(r"\[([^\]]+)\]", d)
        hits.append({
            "num": int(h.findtext("Hit_num")), "defn": d,
            "accession": h.findtext("Hit_accession"), "hit_len": int(h.findtext("Hit_len")),
            "species": sp.group(1) if sp else "",
            "ident_pct": round(100 * sum(x["ident"] for x in hsps)
                               / sum(x["alen"] for x in hsps), 1),
            "qcov_pct": round(100 * sum(x["qt"] - x["qf"] + 1 for x in hsps) / qlen, 1),
            "evalue": min(x["evalue"] for x in hsps),
            "starts_at_1": any(x["hf"] == 1 and x["qf"] == 1 for x in hsps),
            "hsps": hsps,
        })
    return {"program": root.findtext("BlastOutput_program"),
            "db": root.findtext("BlastOutput_db"), "query_len": qlen, "hits": hits}


def conservation(res: dict, same_species: str | None) -> dict:
    """只用「種以外」的命中算保守度剖面。種內命中全長都像，看不出重點。"""
    far = [h for h in res["hits"]
           if not (same_species and same_species.lower() in h["species"].lower())]
    depth = [0] * (res["query_len"] + 1)
    for h in far:
        cov = set()
        for x in h["hsps"]:
            cov |= set(range(x["qf"], x["qt"] + 1))
        for i in cov:
            depth[i] += 1
    n = len(far) or 1
    blocks, start = [], None
    for i in range(1, res["query_len"] + 2):
        deep = i <= res["query_len"] and depth[i] >= n * 0.5
        if deep and start is None:
            start = i
        elif not deep and start is not None:
            if i - start >= 50:
                blocks.append([start, i - 1])
            start = None
    return {"n_far_hits": n, "core_blocks": blocks,
            "profile": [round(sum(depth[s:s + 40]) / (len(depth[s:s + 40]) * n), 2)
                        for s in range(1, res["query_len"] + 1, 40)]}


def composition(seq: str, a: int, b: int) -> dict:
    sub, c = seq[a - 1:b], Counter(seq[a - 1:b])
    n = len(sub)
    return {"from": a, "to": b, "len": n,
            "top": [[x, round(100 * k / n, 1)] for x, k in c.most_common(6)],
            "spta_pct": round(100 * sum(c[x] for x in "SPTA") / n, 1),
            "charged_pct": round(100 * sum(c[x] for x in "DEKR") / n, 1),
            "hydrophobic_pct": round(100 * sum(c[x] for x in "ILVFMW") / n, 1)}


def hydrophobic(seq: str) -> list[dict]:
    sc = [sum(KD.get(c, 0) for c in seq[i:i + WINDOW]) / WINDOW
          for i in range(len(seq) - WINDOW + 1)]
    out, i = [], 0
    while i < len(sc):
        if sc[i] >= TM_CUT:
            j = i
            while j < len(sc) and sc[j] >= TM_CUT:
                j += 1
            out.append({"from": i + 1, "to": j + WINDOW - 1,
                        "peak": round(max(sc[i:j]), 2), "seq": seq[i:j + WINDOW - 1]})
            i = j
        else:
            i += 1
    return out


def report(res: dict, seq: str, cons: dict, species: str | None) -> None:
    print(f"{res['program']} vs {res['db']}：{len(res['hits'])} 筆命中，"
          f"查詢長度 {res['query_len']} aa")
    print(f"\n{'#':>3} {'相似%':>6} {'覆蓋%':>6} {'E':>9} {'長度':>6}  定義")
    for h in res["hits"][:12]:
        print(f"{h['num']:>3} {h['ident_pct']:6.1f} {h['qcov_pct']:6.1f} "
              f"{h['evalue']:9.1e} {h['hit_len']:>6}  {h['defn'][:76]}")
    if len(res["hits"]) > 12:
        print(f"    …還有 {len(res['hits']) - 12} 筆")

    named = [h for h in res["hits"] if has_name(h["defn"])]
    print(f"\n有名字的命中：{len(named)} / {len(res['hits'])}")
    for h in named:
        flag = "（低複雜度區造成的誤標，要查證）" if any(
            s in h["defn"].lower() for s in SUSPECT) else ""
        print(f"  #{h['num']} {h['ident_pct']}% {h['defn'][:70]} {flag}")
    if not named:
        print("  全部都是 hypothetical／uncharacterized —— 這個蛋白質學界也還不知道是什麼。")

    genera = Counter(h["species"].split()[0] for h in res["hits"] if h["species"])
    print(f"\n命中落在 {len(genera)} 個屬："
          + "、".join(f"{g} {n}" for g, n in genera.most_common()))
    print("  （分佈範圍就是「為什麼查不到功能」的答案：沒有模式生物的同源基因可以借名字）")

    same = [h for h in res["hits"]
            if species and species.lower() in h["species"].lower() and h["starts_at_1"]]
    print(f"\n起始密碼子：{len(same)} 筆同種命中從對方第 1 個胺基酸開始對齊"
          f"{'——N 端沒有少掉' if len(same) >= 2 else '——證據不足，要再查'}")

    print(f"\n保守核心（只用 {cons['n_far_hits']} 筆遠緣命中算）：")
    for a, b in cons["core_blocks"]:
        print(f"  {a}–{b}（{b - a + 1} aa）")
    print("  每 40 aa 一格：" + "".join(
        " ▁▂▃▄▅▆▇█"[min(8, int(f * 8.99))] for f in cons["profile"]))

    bounds = [(1, cons["core_blocks"][0][0] - 1)] + [tuple(b) for b in cons["core_blocks"]] \
        if cons["core_blocks"] else [(1, len(seq))]
    print("\n胺基酸組成：")
    for a, b in bounds:
        c = composition(seq, a, b)
        print(f"  {a}–{b}（{c['len']} aa）S+P+T+A {c['spta_pct']}%、"
              f"帶電 {c['charged_pct']}%、疏水 {c['hydrophobic_pct']}%；"
              f"最多的是 " + "、".join(f"{x} {p}%" for x, p in c["top"][:3]))

    tm = hydrophobic(seq)
    print(f"\n疏水區（窗寬 {WINDOW}、門檻 {TM_CUT}；2.5 以上才算強訊號）：")
    for t in tm or []:
        print(f"  {t['from']}–{t['to']}　峰值 {t['peak']}　{t['seq'][:40]}")
    if not tm:
        print("  沒有")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xml", type=Path, help="NCBI blastp 的 Single-file XML")
    ap.add_argument("--faa", type=Path, required=True, help="送去比對的那條蛋白質序列")
    ap.add_argument("--species", default="Rhodotorula toruloides",
                    help="自己這一種的學名；用來分「種內／種外」命中")
    ap.add_argument("-o", "--out", type=Path, help="把結果存成 JSON")
    a = ap.parse_args()

    seq = read_faa(a.faa)
    res = parse(a.xml)
    if len(seq) != res["query_len"]:
        print(f"※ 注意：faa 是 {len(seq)} aa，XML 說查詢是 {res['query_len']} aa。"
              f"差 1 通常是終止密碼子，差更多就是檔案對不上。\n")
    cons = conservation(res, a.species)
    report(res, seq, cons, a.species)

    if a.out:
        blocks = cons["core_blocks"]
        a.out.write_text(json.dumps({
            "query": {"file": a.faa.name, "len": len(seq)},
            "blast": {k: res[k] for k in ("program", "db", "query_len")},
            "n_hits": len(res["hits"]),
            "hits": [{k: h[k] for k in
                      ("num", "defn", "accession", "species", "hit_len",
                       "ident_pct", "qcov_pct", "evalue", "starts_at_1")}
                     for h in res["hits"]],
            "named_hits": [h["defn"] for h in res["hits"] if has_name(h["defn"])],
            "genera": dict(Counter(h["species"].split()[0]
                                   for h in res["hits"] if h["species"]).most_common()),
            "conservation": cons,
            "composition": [composition(seq, *b) for b in
                            ([[1, blocks[0][0] - 1]] + blocks if blocks else [[1, len(seq)]])],
            "hydrophobic": hydrophobic(seq),
        }, ensure_ascii=False, indent=2), "utf-8")
        print(f"\n寫入 {a.out}")


if __name__ == "__main__":
    main()
