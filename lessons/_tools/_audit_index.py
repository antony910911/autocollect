"""盤點參考文獻 + 批次查 Europe PMC（一次問 20 個 DOI）。可續跑。
用法：python -I lessons/_tools/_audit_index.py <lessons 目錄> <.audit 目錄>
"""
import json, re, sys, time
from pathlib import Path
import requests

LESSONS, OUT = Path(sys.argv[1]), Path(sys.argv[2])
DOI = re.compile(r"https://doi\.org/(10\.\S+)")
REFLINE = re.compile(r"^\s*(\d+)\.\s+(.*)$")
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def refs_of(md):
    part = md.split("## 參考文獻", 1)
    if len(part) < 2:
        return []
    out = []
    for line in part[1].splitlines():
        m = REFLINE.match(line)
        if not m:
            continue
        d = DOI.search(line)
        out.append(dict(no=int(m.group(1)), line=m.group(2).strip(),
                        doi=d.group(1).rstrip("。，,）)") if d else None))
    return out


records = []
for course in sorted(p.parent for p in LESSONS.glob("*/course.yaml")):
    for md in sorted(course.glob("*.md")):
        for r in refs_of(md.read_text("utf-8")):
            records.append(dict(course=course.name, file=md.name, **r))
dois = sorted({r["doi"] for r in records if r["doi"]})
print(f"{len(records)} 筆條目、{len(dois)} 個相異 DOI", flush=True)

OUT.mkdir(parents=True, exist_ok=True)
CACHE = OUT / "oa_cache.json"
oa = json.loads(CACHE.read_text("utf-8")) if CACHE.exists() else {}
todo = [d for d in dois if d not in oa]
print(f"已有 {len(oa)}，要查 {len(todo)}", flush=True)

sess = requests.Session()
B = 20
for i in range(0, len(todo), B):
    batch = todo[i:i + B]
    q = " OR ".join(f'DOI:"{d}"' for d in batch)
    try:
        r = sess.get(EPMC, params=dict(query=q, resultType="core", format="json", pageSize=100), timeout=90)
        res = (r.json().get("resultList") or {}).get("result") or []
    except Exception as e:
        print("  批次失敗：", str(e)[:100], flush=True)
        res = []
    by_doi = {}
    for x in res:
        d = (x.get("doi") or "").lower()
        if d and d not in by_doi:
            by_doi[d] = x
    for d in batch:
        x = by_doi.get(d.lower())
        if not x:
            oa[d] = dict(found=False)
            continue
        ft = x.get("fullTextUrlList", {}).get("fullTextUrl", [])
        oa[d] = dict(found=True, pmcid=x.get("pmcid"), pmid=x.get("pmid"),
                     title=x.get("title"), year=x.get("pubYear"),
                     is_oa=x.get("isOpenAccess") == "Y", in_epmc=x.get("inEPMC") == "Y",
                     has_abs=bool(x.get("abstractText")), abstract=x.get("abstractText"),
                     ft_urls=[u.get("url") for u in ft if u.get("availability") in ("Open access", "Free")])
    CACHE.write_text(json.dumps(oa, ensure_ascii=False), "utf-8")
    print(f"  {min(i+B, len(todo))}/{len(todo)}", flush=True)
    time.sleep(0.2)

(OUT / "refs.json").write_text(json.dumps(dict(records=records, oa=oa), ensure_ascii=False, indent=1), "utf-8")
print(f"\n可抓全文：{sum(1 for v in oa.values() if v.get('pmcid') and v.get('in_epmc'))}")
print(f"只有摘要：{sum(1 for v in oa.values() if v.get('has_abs') and not (v.get('pmcid') and v.get('in_epmc')))}")
print(f"查不到：{sum(1 for v in oa.values() if not v.get('found'))}")
