"""把 Europe PMC 上有全文的文獻抓下來存成 XML。
用法：python -I lessons/_tools/_audit_fetch.py <.audit 目錄>
"""
import json, sys, time
from pathlib import Path
import requests

AUD = Path(sys.argv[1])
d = json.loads((AUD / "refs.json").read_text("utf-8"))
oa = d["oa"]
out = AUD / "fetched"
out.mkdir(parents=True, exist_ok=True)
todo = [(doi, v["pmcid"]) for doi, v in oa.items() if v.get("pmcid") and v.get("in_epmc")]
print(f"要抓 {len(todo)} 篇全文")
sess = requests.Session()
ok = fail = skip = 0
for i, (doi, pmcid) in enumerate(todo, 1):
    f = out / f"{pmcid}.xml"
    if f.exists() and f.stat().st_size > 2000:
        skip += 1
        continue
    try:
        r = sess.get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML", timeout=60)
        if r.status_code == 200 and len(r.content) > 2000:
            f.write_bytes(r.content)
            ok += 1
        else:
            fail += 1
    except Exception:
        fail += 1
    if i % 20 == 0:
        print(f"  {i}/{len(todo)}  成功 {ok} 已有 {skip} 失敗 {fail}", flush=True)
    time.sleep(0.15)
print(f"完成：新抓 {ok}、已有 {skip}、抓不到 {fail}")
