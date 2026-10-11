"""把 lessons/ 底下的教材（Markdown＋圖）寫進 Folio，一章一頁，文字框和圖片由上往下交錯排列。

做法和週報（folio.py）相同：筆記本、分區、頁面只在第一次建立；頁面上的文字框與圖片每次重新排版。
圖片以內容雜湊當 id 上傳到 Folio 的圖片儲存區，內容沒變就不會重傳。
你在 Folio 頁面上自己加的手寫、文字框是別筆紀錄，不受影響。
"""

from __future__ import annotations

import hashlib
import re
import struct
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from . import folio

NOTEBOOK_ID = "nb_autocollect_ammonia"
NOTEBOOK_NAME = "氨氮降解教材"
SECTION_ID = "sc_autocollect_ammonia_basics"
SECTION_NAME = "基礎教材"
PAGE_X, PAGE_W = 64, 880
TOP_Y = 156
GAP = 28
# 每次重新發布時，多送幾筆刪除紀錄，清掉上一版比較長時留下的項目
SPARE_TOMBSTONES = 16

_IMAGE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$")
_REL_LINK = re.compile(r"\[([^\]]+)\]\((?!https?://)[^)]+\)")
_ITALIC = re.compile(r"(?<![\w*<])\*([^*\s<][^*<]*?)\*(?![\w*])")


@dataclass
class Text:
    md: str


@dataclass
class Image:
    path: Path
    alt: str


def png_size(data: bytes) -> tuple[int, int]:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("只支援 PNG 圖片")
    return struct.unpack(">II", data[16:24])


def parse(md: str, base: Path) -> tuple[str, list]:
    """拆成標題與依序排列的文字段、圖片。"""
    lines = md.splitlines()
    title = ""
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        lines = lines[1:]
    blocks: list = []
    buf: list[str] = []

    def flush():
        text = "\n".join(buf).strip()
        if text:
            blocks.append(Text(text))
        buf.clear()

    for line in lines:
        m = _IMAGE.match(line.strip())
        if m:
            flush()
            blocks.append(Image(base / m.group(2), m.group(1)))
        else:
            buf.append(line)
    flush()
    return title, blocks


def to_html(md: str) -> str:
    md = _REL_LINK.sub(r"\1", md)  # 教材內部的相對連結在 Folio 點不到，只留文字
    return _ITALIC.sub(r"<i>\1</i>", folio.md_to_html(md))


def estimate_height(html: str, width: int = PAGE_W) -> int:
    """估計 Folio 文字框的高度（字級 16px、行高 1.6）。故意估高一點，寧可留白也不要重疊。"""
    line_h = 16 * 1.6
    height = 0.0
    for kind, body in _blocks(html):
        avail = width - 12 - (23 if kind == "li" else 0)
        text = re.sub(r"<[^>]+>", "", body)
        text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        lines = max(1, -(-int(_text_width(text) * 1.06) // avail)) if text else 1
        height += lines * line_h
    return int(height * 1.06 + line_h + 12)  # 多留一行：換行位置與裝置字型會有差異


def _blocks(html: str) -> list[tuple[str, str]]:
    out = []
    for m in re.finditer(r"<(div|li)>(.*?)</\1>|<br>", html):
        if m.group(0) == "<br>":
            out.append(("div", ""))
        else:
            out.append((m.group(1), m.group(2)))
    return out


def _text_width(s: str) -> int:
    w = 0.0
    for ch in s:
        o = ord(ch)
        if o >= 0x2E80 or 0xFF00 <= o <= 0xFFEF:
            w += 16  # 中文、全形標點
        elif ch in "mwMW@%":
            w += 13
        elif ch.isupper() or ch.isdigit():
            w += 10.5
        else:
            w += 8.5
    return int(w)


def asset_id(data: bytes) -> str:
    return "as_lesson_" + hashlib.sha256(data).hexdigest()[:32]


def build_chapter(chapter_no: int, md_path: Path, now_ms: int, rev_counter: list[int]) -> tuple[list[dict], dict]:
    """回傳（紀錄, 需要上傳的圖片 {asset_id: bytes}）。"""
    title, blocks = parse(md_path.read_text("utf-8"), md_path.parent)
    title = title or md_path.stem
    page_id = f"pg_autocollect_amm_{chapter_no:02d}"
    tag = page_id.removeprefix("pg_autocollect_")

    def rev():
        rev_counter[0] += 1
        return folio.make_rev(now_ms, rev_counter[0])

    page = {"id": page_id, "sectionId": SECTION_ID, "title": title, "background": "blank",
            "order": chapter_no, "createdAt": now_ms, "updatedAt": now_ms}
    records = [{"key": f"pg:{page_id}", "rev": folio.CREATE_ONLY_REV, "deleted": 0, "data": page}]
    uploads: dict[str, bytes] = {}
    y = TOP_Y
    for i, block in enumerate(blocks):
        item_id = f"x_{tag}_{i:03d}"
        if isinstance(block, Text):
            html = to_html(block.md)
            item = {"id": item_id, "type": "text", "x": PAGE_X, "y": y, "w": PAGE_W, "html": html}
            y += estimate_height(html) + GAP
        else:
            data = block.path.read_bytes()
            pw, ph = png_size(data)
            aid = asset_id(data)
            uploads[aid] = data
            records.append({"key": f"as:{aid}", "rev": folio.CREATE_ONLY_REV, "deleted": 0,
                            "data": {"id": aid, "w": pw, "h": ph, "type": "image/png", "size": len(data)}})
            h = round(PAGE_W * ph / pw)
            item = {"id": item_id, "type": "image", "x": PAGE_X, "y": y, "w": PAGE_W, "h": h, "asset": aid}
            y += h + GAP
        records.append({"key": f"it:{page_id}:{item_id}", "rev": rev(), "deleted": 0, "data": item})
    for j in range(len(blocks), len(blocks) + SPARE_TOMBSTONES):
        records.append({"key": f"it:{page_id}:x_{tag}_{j:03d}", "rev": rev(), "deleted": 1, "data": None})
    return records, uploads


def chapter_files(lesson_dir: Path) -> list[Path]:
    """README 當第 0 頁（導讀），其餘依檔名排序。"""
    files = sorted(p for p in lesson_dir.glob("[0-9][0-9]-*.md"))
    readme = lesson_dir / "README.md"
    return ([readme] if readme.exists() else []) + files


def build_all(lesson_dir: Path, now_ms: int | None = None) -> tuple[list[dict], dict]:
    now_ms = now_ms or int(time.time() * 1000)
    notebook = {"id": NOTEBOOK_ID, "name": NOTEBOOK_NAME, "order": 110, "createdAt": now_ms, "updatedAt": now_ms}
    section = {"id": SECTION_ID, "notebookId": NOTEBOOK_ID, "name": SECTION_NAME, "color": "#2f6fb3",
               "order": 1, "createdAt": now_ms, "updatedAt": now_ms}
    records = [
        {"key": f"nb:{NOTEBOOK_ID}", "rev": folio.CREATE_ONLY_REV, "deleted": 0, "data": notebook},
        {"key": f"sc:{SECTION_ID}", "rev": folio.CREATE_ONLY_REV, "deleted": 0, "data": section},
    ]
    uploads: dict[str, bytes] = {}
    counter = [0]
    for path in chapter_files(lesson_dir):
        m = re.match(r"(\d+)-", path.name)
        no = int(m.group(1)) if m else 0
        recs, ups = build_chapter(no, path, now_ms, counter)
        if path.name == "README.md":
            recs[0]["data"]["title"] = "導讀：" + recs[0]["data"]["title"]
        records += recs
        uploads.update(ups)
    return records, uploads


def upload_assets(base_url: str, token: str, uploads: dict[str, bytes]) -> int:
    """先問伺服器缺哪些，只上傳缺的。回傳上傳張數。"""
    if not uploads:
        return 0
    headers = {"Authorization": f"Bearer {folio.encode_token(token)}", "X-Folio-Device": folio.DEVICE}
    base = base_url.rstrip("/") + "/api/assets"
    resp = requests.post(base + "/check", json={"ids": list(uploads)}, headers=headers, timeout=60)
    resp.raise_for_status()
    missing = resp.json().get("missing", [])
    for aid in missing:
        r = requests.put(f"{base}/{aid}", data=uploads[aid], headers={**headers, "Content-Type": "image/png"},
                         timeout=120)
        r.raise_for_status()
    return len(missing)


def publish(base_url: str, token: str, lesson_dir: Path) -> dict:
    records, uploads = build_all(lesson_dir)
    sent = upload_assets(base_url, token, uploads)  # 圖片先上傳，頁面出現時才不會是空白
    result = folio.publish(base_url, token, records)
    result["images_uploaded"] = sent
    result["pages"] = sum(1 for r in records if r["key"].startswith("pg:"))
    return result
