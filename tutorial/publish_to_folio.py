"""把 tutorial/ 的章節寫進 Folio「Claude圖解教材」筆記本（沿用 autocollect/folio.py 的格式）。

用法（在 autocollect 儲存庫根目錄，環境變數 FOLIO_SYNC_TOKEN 已設定）：
    python tutorial/publish_to_folio.py
筆記本、分區、頁面只在不存在時建立；章節內容文字框每次執行會更新。
Folio 裡已有同名筆記本（你手動建的）時，章節會放進那一本；
分區或頁面原本在別處時，會搬過去。
"""
import json, os, sys, time
from pathlib import Path
import requests
sys.path.insert(0, os.getcwd())
from autocollect.folio import CREATE_ONLY_REV, DEFAULT_URL, DEVICE, encode_token, make_rev, md_to_html, publish

HERE = Path(__file__).parent
NB = {"id": "nb-claude-tutorial", "name": "Claude圖解教材"}
# 分區：(id, 名稱, 顏色, 這次之前自動取過的名稱——仍是舊名時才改名，你在 Folio 改過的名稱不動)
SECTIONS = [
    ("sc-microbe-dna", "微生物 1｜全貌與基因註解", "#2f7fbf", ["微生物DNA功能分析"]),
    ("sc-microbe-model", "微生物 2｜代謝模型與動態模擬", "#1f7a5c", []),
    ("sc-microbe-opt", "微生物 3｜分階段最適化與實驗設計", "#b06a10", []),
    ("sc-microbe-build", "微生物 4｜分工、介面與行動計畫", "#7b3fa0", []),
]
SC = {"id": SECTIONS[0][0], "name": SECTIONS[0][1]}
# 章節：(slug, 檔名, 分區 id, 順序, 這次之前自動取過的標題)
CHAPTERS = [
    ("ch00", "ch00-你的問題一次回答.md", "sc-microbe-dna", 0, []),
    ("ch01", "ch01-總覽與基因註解.md", "sc-microbe-dna", 1,
     ["第 1 章　從一段 DNA 到「這隻菌能做什麼」：系統總覽與基因註解入門"]),
    ("ch02", "ch02-代謝模型與FBA.md", "sc-microbe-model", 2, []),
    ("ch03", "ch03-動態模型與dFBA.md", "sc-microbe-model", 3, []),
    ("ch04", "ch04-分階段參數與指標.md", "sc-microbe-opt", 4, []),
    ("ch05", "ch05-實驗設計與AI最適化.md", "sc-microbe-opt", 5, []),
    ("ch06", "ch06-你收集什麼與AI做什麼.md", "sc-microbe-build", 6, []),
    ("ch07", "ch07-視覺化模擬介面.md", "sc-microbe-build", 7, []),
    ("ch08", "ch08-國內外做法與行動計畫.md", "sc-microbe-build", 8, []),
]


def fetch_all(base_url, token):
    """讀出 Folio 伺服器上所有未刪除的紀錄，回傳 {key: data}。"""
    out, since = {}, 0
    while True:
        resp = requests.get(base_url.rstrip("/") + "/api/changes", params={"since": since},
                            headers={"Authorization": f"Bearer {encode_token(token)}", "X-Folio-Device": DEVICE},
                            timeout=60)
        resp.raise_for_status()
        body = resp.json()
        for r in body["records"]:
            if r["deleted"]:
                out.pop(r["key"], None)
            else:
                out[r["key"]] = r["data"]
        since = body["seq"]
        if not body["more"]:
            return out


def plan(existing):
    """決定章節要放的筆記本，回傳 (筆記本 id, 第一個分區 id)。"""
    nbs = [d["id"] for k, d in existing.items()
           if k.startswith("nb:") and d and d.get("name") == NB["name"] and d["id"] != NB["id"]]
    if len(nbs) > 1:
        raise SystemExit(f"Folio 裡有 {len(nbs)} 本「{NB['name']}」，不知道要放哪一本：{nbs}")
    return (nbs[0] if nbs else NB["id"]), SC["id"]


def build(now_ms, existing=None):
    existing = existing or {}
    nb_id, _ = plan(existing)
    bumped = 0  # 需要改動的既有紀錄用目前時間當 rev，伺服器才會接受

    def rev_for(key, changed):
        nonlocal bumped
        if key in existing and changed:
            bumped += 1
            return make_rev(now_ms, 100 + bumped)
        return CREATE_ONLY_REV

    recs = []
    if nb_id == NB["id"]:
        recs.append({"key": f"nb:{NB['id']}", "rev": CREATE_ONLY_REV, "deleted": 0,
                     "data": {**NB, "order": 200, "createdAt": now_ms, "updatedAt": now_ms}})
    first = existing.get(f"sc:{SECTIONS[0][0]}") or {}
    base_order = first.get("order", 1)
    for n, (sid, name, color, old_names) in enumerate(SECTIONS):
        key = f"sc:{sid}"
        cur = existing.get(key) or {}
        want_name = name if (not cur or cur.get("name") in old_names + [name]) else cur["name"]
        data = {"id": sid, "color": color, "order": base_order + n, "createdAt": now_ms,
                **cur, "name": want_name, "notebookId": nb_id, "updatedAt": now_ms}
        changed = cur.get("notebookId") != nb_id or cur.get("name") != want_name
        recs.append({"key": key, "rev": rev_for(key, changed), "deleted": 0, "data": data})
    for i, (slug, fname, sid, order, old_titles) in enumerate(CHAPTERS):
        md = (HERE / fname).read_text(encoding="utf-8")
        title = md.splitlines()[0].lstrip("# ").strip()
        pid, iid = f"pg-microbe-{slug}", f"it-microbe-{slug}"
        key = f"pg:{pid}"
        cur = existing.get(key) or {}
        want_title = title if (not cur or cur.get("title") in old_titles + [title]) else cur["title"]
        data = {"id": pid, "background": "blank", "order": order, "createdAt": now_ms,
                **cur, "title": want_title, "sectionId": sid, "updatedAt": now_ms}
        changed = cur.get("sectionId") != sid or cur.get("title") != want_title
        recs.append({"key": key, "rev": rev_for(key, changed), "deleted": 0, "data": data})
        recs.append({"key": f"it:{pid}:{iid}", "rev": make_rev(now_ms, i), "deleted": 0,
                     "data": {"id": iid, "type": "text", "x": 64, "y": 156, "w": 880,
                              "html": md_to_html(md)}})
    return recs


if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        print(json.dumps(build(int(time.time() * 1000)), ensure_ascii=False, indent=1)[:3000])
        sys.exit()
    url, token = os.environ.get("FOLIO_URL") or DEFAULT_URL, os.environ["FOLIO_SYNC_TOKEN"]
    existing = fetch_all(url, token)
    nb_id, sc_id = plan(existing)
    print(f"放進筆記本 {nb_id}，分區 {[s[0] for s in SECTIONS]}")
    print(publish(url, token, build(int(time.time() * 1000), existing)))
    if nb_id != NB["id"] and f"nb:{NB['id']}" in existing:
        left = [k for k, d in existing.items() if k.startswith("sc:") and d and d.get("notebookId") == NB["id"]
                and k != f"sc:{SC['id']}"]
        if left:
            print(f"多出來的筆記本 {NB['id']} 裡還有分區 {left}，沒有刪除")
        else:
            # 自動建的同名筆記本已經空了：標記刪除
            gone = {"key": f"nb:{NB['id']}", "rev": make_rev(int(time.time() * 1000), 999), "deleted": 1, "data": None}
            print(f"刪除空的筆記本 {NB['id']}：", publish(url, token, [gone]))
