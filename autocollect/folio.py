"""把週報寫進 Folio 筆記本（https://github.com/antony910911/folio）。

Folio 的同步 API 把資料拆成一筆筆紀錄（nb: 筆記本、sc: 分區、pg: 頁面、it: 頁面上的項目），
每筆有版本號 rev，伺服器只收 rev 比現有大的。這裡的做法：
- 筆記本、分區、頁面用固定 id 和「最舊」的 rev：不存在時建立；已存在時伺服器會忽略，
  所以你在 Folio 裡改名、換顏色、移動頁面都不會被覆蓋。
- 報告內容是頁面上的一個文字框，用目前時間當 rev：重跑時會更新內容。
  你在頁面上另外加的手寫或文字框是別筆紀錄，不受影響。
"""

from __future__ import annotations

import base64
import html
import re
import time

import requests

DEFAULT_URL = "https://folio.antony910912.workers.dev"
DEVICE = "autocollect"
NOTEBOOK_ID = "nb_autocollect_bio"
SECTION_ID = "sc_autocollect_weekly"
# 最舊的版本號：只在紀錄不存在時才會被伺服器接受
CREATE_ONLY_REV = f"{'1'.rjust(10, '0')}.0000.{DEVICE}"


def make_rev(ms: int, counter: int = 0) -> str:
    """與 Folio 的 makeRev 相同格式：<毫秒 36 進位>.<計數 36 進位>.<裝置>"""
    return f"{_b36(ms).rjust(10, '0')}.{_b36(counter).rjust(4, '0')}.{DEVICE}"


def _b36(n: int) -> str:
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    while True:
        n, r = divmod(n, 36)
        out = digits[r] + out
        if n == 0:
            return out


def encode_token(token: str) -> str:
    raw = base64.urlsafe_b64encode(token.strip().encode("utf-8")).decode().rstrip("=")
    return "b64." + raw


_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")


def inline(text: str) -> str:
    """Markdown 行內格式轉成 Folio 文字框允許的 HTML（只有 b/i/u/s/br/ul/ol/li/p/div/span）。"""
    links = []

    def keep_link(m):
        links.append(f"{m.group(1)}（{m.group(2)}）")
        return f"\x00{len(links) - 1}\x00"

    text = _LINK.sub(keep_link, text)
    text = html.escape(text, quote=False)
    text = _BOLD.sub(r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: html.escape(links[int(m.group(1))], quote=False), text)


def md_to_html(md: str) -> str:
    out: list[str] = []
    list_depths: list[int] = []
    table_header: list[str] | None = None

    def close_lists(to_depth=-1):
        while list_depths and list_depths[-1] > to_depth:
            list_depths.pop()
            out.append("</ul>")

    for raw in md.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        bullet = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            if table_header is None:
                table_header = cells
                continue
            close_lists()
            pairs = [f"{h}：{c}" for h, c in zip(table_header, cells) if c]
            out.append("<ul><li>" + inline("｜".join(pairs)) + "</li></ul>")
            continue
        table_header = None
        if bullet:
            depth = len(bullet.group(1).replace("\t", "  ")) // 2
            if not list_depths or depth > list_depths[-1]:
                out.append("<ul>")
                list_depths.append(depth)
            else:
                close_lists(depth)
                if not list_depths:
                    out.append("<ul>")
                    list_depths.append(depth)
            out.append(f"<li>{inline(bullet.group(2))}</li>")
            continue
        close_lists()
        if not stripped:
            continue
        if stripped.startswith("<details") or stripped.startswith("</details"):
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level, title = len(heading.group(1)), inline(heading.group(2))
            if out:
                out.append("<br>")
            out.append(f"<div><b><u>{title}</u></b></div>" if level <= 2 else f"<div><b>{title}</b></div>")
            continue
        if stripped.startswith(">"):
            out.append(f"<div><i>{inline(stripped.lstrip('> '))}</i></div>")
            continue
        out.append(f"<div>{inline(stripped)}</div>")
    close_lists()
    return "".join(out)


def report_body(report_md: str) -> str:
    """Folio 頁面放分析、統計、參考來源與品質檢查；全部資料的附錄太長，留在 GitHub。"""
    return report_md.split("\n## 附錄")[0]


def week_order(week: str) -> int:
    year, w = week.split("-W")
    return -(int(year) * 100 + int(w))  # 越新的週越前面


def build_records(week: str, report_md: str, now_ms: int | None = None) -> list[dict]:
    now_ms = now_ms or int(time.time() * 1000)
    page_id = f"pg_autocollect_{week.replace('-', '')}"
    title = report_md.splitlines()[0].lstrip("# ").strip() if report_md.strip() else f"生質能週報 {week}"
    notebook = {"id": NOTEBOOK_ID, "name": "生質能週報", "order": 100, "createdAt": now_ms, "updatedAt": now_ms}
    section = {"id": SECTION_ID, "notebookId": NOTEBOOK_ID, "name": "每週週報", "color": "#2f9e6e",
               "order": 1, "createdAt": now_ms, "updatedAt": now_ms}
    page = {"id": page_id, "sectionId": SECTION_ID, "title": title, "background": "blank",
            "order": week_order(week), "createdAt": now_ms, "updatedAt": now_ms}
    item = {"id": f"t_autocollect_{week.replace('-', '')}", "type": "text", "x": 64, "y": 156, "w": 880,
            "html": md_to_html(report_body(report_md))}
    return [
        {"key": f"nb:{NOTEBOOK_ID}", "rev": CREATE_ONLY_REV, "deleted": 0, "data": notebook},
        {"key": f"sc:{SECTION_ID}", "rev": CREATE_ONLY_REV, "deleted": 0, "data": section},
        {"key": f"pg:{page_id}", "rev": CREATE_ONLY_REV, "deleted": 0, "data": page},
        {"key": f"it:{page_id}:{item['id']}", "rev": make_rev(now_ms), "deleted": 0, "data": item},
    ]


def publish(base_url: str, token: str, records: list[dict]) -> dict:
    resp = requests.post(
        base_url.rstrip("/") + "/api/changes",
        json={"records": records},
        headers={"Authorization": f"Bearer {encode_token(token)}", "X-Folio-Device": DEVICE},
        timeout=60,
    )
    if resp.status_code == 401:
        raise RuntimeError("Folio 同步密碼不對（401）")
    if resp.status_code == 503:
        raise RuntimeError("Folio 伺服器尚未設定 SYNC_TOKEN（503）")
    resp.raise_for_status()
    return resp.json()
