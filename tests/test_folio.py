import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from autocollect import folio, topics

BIO = topics.BUILTIN["bioenergy"]["folio"]

REPORT = """# 生質能國內外新知週報 2026-W41

> 資料期間：2026-10-03 ～ 2026-10-10

## 一、本週重點摘要
- **SAF** 產能擴張 <快訊> [S1, S2]
  - 子項目 [S3]

## 五、技術成熟度與商業化訊號
| 技術路徑 | 階段 | 來源 |
|---|---|---|
| HEFA | 商轉 | [S1] |

## 參考來源（本週報告引用）
- **[S1]** [Plant opens](https://e.com/a?x=1&y=2) — Src，2026-10-08（新聞）

## 附錄：本週收集的全部資料
<details><summary>新聞</summary>
- 不應出現在 Folio 的一長串資料
</details>
"""

ALLOWED = {"b", "i", "u", "s", "br", "div", "p", "span", "ul", "ol", "li"}


def test_html_uses_only_tags_folio_keeps():
    out = folio.md_to_html(folio.report_body(REPORT))
    tags = {t.lower() for t in re.findall(r"</?([a-zA-Z]+)", out)}
    assert tags <= ALLOWED
    assert out.count("<ul>") == out.count("</ul>")
    assert "<b>SAF</b> 產能擴張 &lt;快訊&gt; [S1, S2]" in out
    assert "<li>子項目 [S3]</li>" in out
    assert "技術路徑：HEFA｜階段：商轉｜來源：[S1]" in out
    assert "Plant opens（https://e.com/a?x=1&amp;y=2）" in out
    assert "不應出現" not in out and "附錄" not in out


def test_rev_format_matches_folio_make_rev():
    # 與 js/syncmodel.js 的 makeRev(ms, counter, device) 一致
    assert folio.make_rev(1760000000000, 0) == "00mgj6k3cw.0000.autocollect"  # node 實測值
    assert folio.CREATE_ONLY_REV < folio.make_rev(2)


def test_records_shape_and_newest_week_first():
    recs = folio.build_records("2026-W41", REPORT, BIO, now_ms=1760000000000)
    keys = [r["key"] for r in recs]
    assert keys == ["nb:nb_autocollect_bio", "sc:sc_autocollect_weekly", "pg:pg_autocollect_2026W41",
                    "it:pg_autocollect_2026W41:t_autocollect_2026W41"]
    page, item = recs[2]["data"], recs[3]["data"]
    assert page["title"] == "生質能國內外新知週報 2026-W41" and page["sectionId"] == "sc_autocollect_weekly"
    assert item["type"] == "text" and all(isinstance(item[k], int) for k in ("x", "y", "w"))
    assert folio.week_order("2026-W42") < folio.week_order("2026-W41") < folio.week_order("2025-W52")


@pytest.fixture
def fake_folio():
    """模擬 Folio 伺服器的 push 規則：rev 比現有大的才收。"""
    store, auth = {}, []

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            auth.append(self.headers.get("Authorization"))
            body = json.loads(self.rfile.read(int(self.headers["content-length"])))
            accepted = 0
            for r in body["records"]:
                cur = store.get(r["key"])
                if cur and cur["rev"] >= r["rev"]:
                    continue
                store[r["key"]] = r
                accepted += 1
            data = json.dumps({"accepted": accepted, "seq": len(store)}).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}", store, auth
    srv.shutdown()


def test_publish_creates_once_and_updates_content(fake_folio):
    url, store, auth = fake_folio
    assert folio.publish(url, "我的 密碼!", folio.build_records("2026-W41", REPORT, BIO, 1000))["accepted"] == 4
    assert auth[0] == "Bearer " + folio.encode_token("我的 密碼!")

    # 使用者在 Folio 把筆記本改名（rev 較新）
    store["nb:nb_autocollect_bio"] = {**store["nb:nb_autocollect_bio"], "rev": folio.make_rev(5000),
                                      "data": {"name": "改過的名字"}}
    res = folio.publish(url, "x", folio.build_records("2026-W41", REPORT.replace("產能", "需求"), BIO, 9000))
    assert res["accepted"] == 1  # 只有內容更新
    assert store["nb:nb_autocollect_bio"]["data"]["name"] == "改過的名字"
    assert "需求" in store["it:pg_autocollect_2026W41:t_autocollect_2026W41"]["data"]["html"]
