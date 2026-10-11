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
SC = {"id": "sc-microbe-dna", "name": "微生物DNA功能分析", "color": "#2f7fbf"}
CHAPTERS = [("ch01", "ch01-總覽與基因註解.md", 1)]


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
    """決定章節要放的筆記本與分區，回傳 (筆記本 id, 分區 id)。"""
    nbs = [d["id"] for k, d in existing.items()
           if k.startswith("nb:") and d and d.get("name") == NB["name"] and d["id"] != NB["id"]]
    if len(nbs) > 1:
        raise SystemExit(f"Folio 裡有 {len(nbs)} 本「{NB['name']}」，不知道要放哪一本：{nbs}")
    nb_id = nbs[0] if nbs else NB["id"]
    scs = [d["id"] for k, d in existing.items()
           if k.startswith("sc:") and d and d.get("notebookId") == nb_id and d.get("name") == SC["name"]]
    return nb_id, (SC["id"] if SC["id"] in scs or not scs else scs[0])


def build(now_ms, existing=None):
    existing = existing or {}
    nb_id, sc_id = plan(existing)
    moved = 0  # 需要搬家的紀錄用目前時間當 rev，伺服器才會接受

    def rev_for(key, field, want):
        nonlocal moved
        cur = existing.get(key)
        if cur and cur.get(field) != want:
            moved += 1
            return make_rev(now_ms, 100 + moved)
        return CREATE_ONLY_REV

    recs = []
    if nb_id == NB["id"]:
        recs.append({"key": f"nb:{NB['id']}", "rev": CREATE_ONLY_REV, "deleted": 0,
                     "data": {**NB, "order": 200, "createdAt": now_ms, "updatedAt": now_ms}})
    if sc_id == SC["id"]:
        key = f"sc:{SC['id']}"
        data = {**SC, "order": 1, "createdAt": now_ms, **existing.get(key, {}), "notebookId": nb_id, "updatedAt": now_ms}
        recs.append({"key": key, "rev": rev_for(key, "notebookId", nb_id), "deleted": 0, "data": data})
    for i, (slug, fname, order) in enumerate(CHAPTERS):
        md = (HERE / fname).read_text(encoding="utf-8")
        title = md.splitlines()[0].lstrip("# ").strip()
        pid, iid = f"pg-microbe-{slug}", f"it-microbe-{slug}"
        key = f"pg:{pid}"
        data = {"id": pid, "title": title, "background": "blank", "order": order, "createdAt": now_ms,
                **existing.get(key, {}), "sectionId": sc_id, "updatedAt": now_ms}
        recs.append({"key": key, "rev": rev_for(key, "sectionId", sc_id), "deleted": 0, "data": data})
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
    print(f"放進筆記本 {nb_id}，分區 {sc_id}")
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
