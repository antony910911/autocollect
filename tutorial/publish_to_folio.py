"""把 tutorial/ 的章節寫進 Folio「Claude圖解教材」筆記本（沿用 autocollect/folio.py 的格式）。

用法（在 autocollect 儲存庫根目錄，環境變數 FOLIO_SYNC_TOKEN 已設定）：
    python tutorial/publish_to_folio.py
筆記本、分區、頁面只在不存在時建立；章節內容文字框每次執行會更新。
"""
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, os.getcwd())
from autocollect.folio import CREATE_ONLY_REV, DEFAULT_URL, make_rev, md_to_html, publish

HERE = Path(__file__).parent
NB = {"id": "nb-claude-tutorial", "name": "Claude圖解教材"}
SC = {"id": "sc-microbe-dna", "name": "微生物DNA功能分析", "color": "#2f7fbf"}
CHAPTERS = [("ch01", "ch01-總覽與基因註解.md", 1)]


def build(now_ms):
    recs = [
        {"key": f"nb:{NB['id']}", "rev": CREATE_ONLY_REV, "deleted": 0,
         "data": {**NB, "order": 200, "createdAt": now_ms, "updatedAt": now_ms}},
        {"key": f"sc:{SC['id']}", "rev": CREATE_ONLY_REV, "deleted": 0,
         "data": {**SC, "notebookId": NB["id"], "order": 1, "createdAt": now_ms, "updatedAt": now_ms}},
    ]
    for i, (slug, fname, order) in enumerate(CHAPTERS):
        md = (HERE / fname).read_text(encoding="utf-8")
        title = md.splitlines()[0].lstrip("# ").strip()
        pid, iid = f"pg-microbe-{slug}", f"it-microbe-{slug}"
        recs.append({"key": f"pg:{pid}", "rev": CREATE_ONLY_REV, "deleted": 0,
                     "data": {"id": pid, "sectionId": SC["id"], "title": title, "background": "blank",
                              "order": order, "createdAt": now_ms, "updatedAt": now_ms}})
        recs.append({"key": f"it:{pid}:{iid}", "rev": make_rev(now_ms, i), "deleted": 0,
                     "data": {"id": iid, "type": "text", "x": 64, "y": 156, "w": 880,
                              "html": md_to_html(md)}})
    return recs


if __name__ == "__main__":
    records = build(int(time.time() * 1000))
    if "--dry-run" in sys.argv:
        print(json.dumps(records, ensure_ascii=False, indent=1)[:3000])
    else:
        print(publish(os.environ.get("FOLIO_URL") or DEFAULT_URL, os.environ["FOLIO_SYNC_TOKEN"], records))
