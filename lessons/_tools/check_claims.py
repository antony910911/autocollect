"""核對「章節裡的數字」是不是真的出現在它所引的那篇文獻裡。

**這不是一個會給出對錯判決的工具，也不該當成 CI 關卡。** 單位換算、四捨五入、
我們自己算出來的數字都會被標成「找不到」。它的工作是把**要人工覆核的句子**挑出來，
以及告訴你「這門教材有多少數字其實查得到出處」。

怎麼用（三步，中間產物放在 repo 外的 .audit/，已經 gitignore）：

    python -I lessons/_tools/_audit_index.py lessons .audit    # 查哪些文獻有 OA 全文
    python -I lessons/_tools/_audit_fetch.py .audit            # 抓全文（Europe PMC）
    python -I lessons/_tools/check_claims.py lessons .audit    # 比對 + 統計

它只檢查「句子裡有引用標記 [n]、而且那筆文獻拿得到全文」的數字，
並且只看夠特別的數字（有小數點、≥100、或帶單位）——
像「2」「10」這種在任何論文裡都找得到，查了沒有意義。

2026-11 第一次全面跑的結果：86 個數字在全文裡找到、68 個在摘要裡找到、
8 個要人工覆核（全部覆核過，都是單位換算或我們自己算的，沒有錯）、
162 個因為付費牆而查不到。
"""

import json, re, sys
from pathlib import Path

LESSONS, AUD = Path(sys.argv[1]), Path(sys.argv[2])
D = json.loads((AUD / "refs.json").read_text("utf-8"))
OA = D["oa"]

DOI_RE = re.compile(r"https://doi\.org/(10\.\S+)")
REFLINE = re.compile(r"^\s*(\d+)\.\s+(.*)$")
CITE = re.compile(r"\[(\d+(?:\s*[,、]\s*\d+|\s*[–-]\s*\d+)*)\]")
NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(%|mg|g|kg|t\b|L\b|m²|m2|mM|mmol|°C|d\b|h\b|天|倍|年|小時|公頃|ha\b)?")

# 這些上下文裡的數字不是文獻宣稱
SKIP_CTX = [re.compile(p) for p in [
    r"第\s*\d+\s*[章節]", r"圖\s*\d+[-–]\d+", r"表\s*\d+", r"\(\d{4}\)", r"\d{4}\s*年",
]]


def text_of_xml(p: Path) -> str:
    x = p.read_text("utf-8", errors="ignore")
    x = re.sub(r"<[^>]+>", " ", x)
    return re.sub(r"\s+", " ", x)


CACHE = {}


def corpus_for(doi: str) -> tuple[str, str]:
    """回傳 (文字, 來源種類)。優先全文，其次摘要。"""
    if doi in CACHE:
        return CACHE[doi]
    v = OA.get(doi) or {}
    txt, kind = "", "none"
    pmcid = v.get("pmcid")
    if pmcid:
        f = AUD / "fetched" / f"{pmcid}.xml"
        if f.exists():
            txt, kind = text_of_xml(f), "fulltext"
    if not txt and v.get("abstract"):
        txt, kind = re.sub(r"<[^>]+>", " ", v["abstract"]), "abstract"
    CACHE[doi] = (txt, kind)
    return CACHE[doi]


def variants(n: str) -> list[str]:
    out = {n, n.replace(",", "")}
    try:
        f = float(n.replace(",", ""))
    except ValueError:
        return list(out)
    if f == int(f):
        out.add(str(int(f)))
    for dp in (0, 1, 2, 3):
        out.add(f"{f:.{dp}f}")
    s = f"{f}"
    if s.endswith(".0"):
        out.add(s[:-2])
    return [v for v in out if v]


def found(num: str, txt: str) -> bool:
    for v in variants(num):
        if re.search(r"(?<![\d.])" + re.escape(v) + r"(?![\d])", txt):
            return True
    return False


def refs_of(md: str) -> dict[int, str | None]:
    part = md.split("## 參考文獻", 1)
    if len(part) < 2:
        return {}
    out = {}
    for line in part[1].splitlines():
        m = REFLINE.match(line)
        if m:
            d = DOI_RE.search(line)
            out[int(m.group(1))] = d.group(1).rstrip("。，,）)") if d else None
    return out


def body_units(md: str) -> list[tuple[int, str]]:
    body = md.split("## 參考文獻", 1)[0]
    body = re.sub(r"```.*?```", " ", body, flags=re.S)       # 去掉程式碼
    units = []
    for i, line in enumerate(body.splitlines(), 1):
        if not CITE.search(line):
            continue
        # 表格列與條列就是一個單位；長段落再按句號切
        if line.lstrip().startswith("|") or line.lstrip().startswith(("-", "*", "・")) or len(line) < 160:
            units.append((i, line))
        else:
            for s in re.split(r"(?<=。)", line):
                if CITE.search(s):
                    units.append((i, s))
    return units


def cited_nums(unit: str) -> tuple[list[int], list[str]]:
    refs = []
    for m in CITE.finditer(unit):
        g = m.group(1)
        for part in re.split(r"[,、]", g):
            part = part.strip()
            if re.fullmatch(r"\d+\s*[–-]\s*\d+", part):
                a, b = re.split(r"[–-]", part)
                refs.extend(range(int(a), int(b) + 1))
            elif part.isdigit():
                refs.append(int(part))
    clean = CITE.sub(" ", unit)
    clean = re.sub(r"https?://\S+", " ", clean)          # 網址裡的數字不算
    for p in SKIP_CTX:
        clean = p.sub(" ", clean)
    nums = []
    for m in NUM.finditer(clean):
        n, unitstr = m.group(1), m.group(2)
        try:
            v = float(n.replace(",", ""))
        except ValueError:
            continue
        # 只查「夠特別」的數字：有小數點、或 >=100、或帶單位／百分比
        if "." in n or v >= 100 or unitstr:
            nums.append(n)
    return sorted(set(refs)), nums


from collections import defaultdict, Counter
stats = defaultdict(Counter)
rows = []
for course in sorted(p.parent for p in LESSONS.glob("*/course.yaml")):
    for md_path in sorted(course.glob("*.md")):
        md = md_path.read_text("utf-8")
        refmap = refs_of(md)
        if not refmap:
            continue
        for lineno, unit in body_units(md):
            refs, nums = cited_nums(unit)
            if not nums or not refs:
                continue
            dois = [refmap.get(r) for r in refs if refmap.get(r)]
            if not dois:
                continue
            corpora = [corpus_for(d) for d in dois]
            has_ft = any(k == "fulltext" for _, k in corpora)
            for n in nums:
                hit_ft = any(found(n, t) for t, k in corpora if k == "fulltext")
                hit_ab = any(found(n, t) for t, k in corpora if k == "abstract")
                if hit_ft:
                    stats[course.name]["全文確認"] += 1
                elif hit_ab:
                    stats[course.name]["摘要確認"] += 1
                elif has_ft:
                    stats[course.name]["全文找不到（要覆核）"] += 1
                else:
                    stats[course.name]["沒有全文可查"] += 1
            if has_ft:
                missing = [n for n in nums
                           if not any(found(n, t) for t, _ in corpora)]
                if missing:
                    rows.append(dict(course=course.name, file=md_path.name, line=lineno,
                                     refs=refs, dois=dois, missing=missing,
                                     kinds=[k for _, k in corpora], text=unit.strip()[:300]))

(AUD / "candidates.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), "utf-8")
(AUD / "stats.json").write_text(json.dumps({k: dict(v) for k, v in stats.items()},
                                           ensure_ascii=False, indent=1), "utf-8")
print(f"要人工覆核的句子：{len(rows)} 條")
for c, n in Counter(r["course"] for r in rows).most_common():
    print(f"  {c}: {n}")
print("\n各課程的數字證據：")
hdr = ["全文確認", "摘要確認", "全文找不到（要覆核）", "沒有全文可查"]
for c in sorted(stats):
    v = stats[c]
    print(f"  {c:<16} " + "  ".join(f"{h} {v[h]:>3}" for h in hdr))
