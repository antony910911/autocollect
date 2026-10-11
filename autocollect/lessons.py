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
import yaml

from . import folio

PAGE_X, PAGE_W = 64, 880
TOP_Y = 156
GAP = 28
# 每次重新發布時，多送幾筆刪除紀錄，清掉上一版比較長時留下的項目
SPARE_TOMBSTONES = 16

_IMAGE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$")
_REL_LINK = re.compile(r"\[([^\]]+)\]\((?!https?://)[^)]+\)")
_ITALIC = re.compile(r"(?<![\w*<])\*([^*\s<][^*<]*?)\*(?![\w*])")


@dataclass
class Course:
    """一門教材：放在哪本筆記本、哪個分區，頁面 id 用什麼前綴。設定寫在教材資料夾的 course.yaml。"""

    dir: Path
    notebook_id: str
    notebook_name: str
    section_id: str
    section_name: str
    page_prefix: str
    find_notebook_by_name: bool = False  # True：Folio 裡已有同名筆記本就放進去，沒有才建立
    section_color: str = "#2f6fb3"
    notebook_order: int = 110
    section_order: int = 1

    @classmethod
    def load(cls, lesson_dir: Path) -> "Course":
        cfg = yaml.safe_load((lesson_dir / "course.yaml").read_text("utf-8"))
        nb, sc = cfg["notebook"], cfg["section"]
        return cls(dir=lesson_dir, notebook_id=nb["id"], notebook_name=nb["name"], section_id=sc["id"],
                   section_name=sc["name"], page_prefix=cfg["page_prefix"],
                   find_notebook_by_name=bool(nb.get("find_by_name", False)),
                   section_color=sc.get("color", "#2f6fb3"), notebook_order=int(nb.get("order", 110)),
                   section_order=int(sc.get("order", 1)))


def all_courses(root: Path) -> list[Course]:
    return [Course.load(p.parent) for p in sorted(root.glob("*/course.yaml"))]


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


def build_chapter(course: Course, section_id: str, chapter_no: int, md_path: Path, now_ms: int,
                  rev_counter: list[int]) -> tuple[list[dict], dict]:
    """回傳（紀錄, 需要上傳的圖片 {asset_id: bytes}）。"""
    title, blocks = parse(md_path.read_text("utf-8"), md_path.parent)
    title = title or md_path.stem
    tag = f"{course.page_prefix}_{chapter_no:02d}"
    page_id = f"pg_autocollect_{tag}"

    def rev():
        rev_counter[0] += 1
        return folio.make_rev(now_ms, rev_counter[0])

    page = {"id": page_id, "sectionId": section_id, "title": title, "background": "blank",
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


def _same(a: str, b: str) -> bool:
    return a.strip().casefold() == b.strip().casefold()


def resolve_targets(course: Course, existing: list[dict] | None) -> tuple[str, str, bool, bool]:
    """決定實際要用的（筆記本 id, 分區 id, 要不要建筆記本, 要不要建分區）。

    existing 是從 Folio 拉下來的全部紀錄；None 表示不查（離線預覽）。
    """
    live = [r for r in (existing or []) if not r.get("deleted") and isinstance(r.get("data"), dict)]
    nb_id, create_nb = course.notebook_id, True
    if any(r["key"] == f"nb:{course.notebook_id}" for r in live):
        create_nb = False
    elif course.find_notebook_by_name:
        named = [r["data"] for r in live if r["key"].startswith("nb:") and _same(r["data"].get("name", ""),
                                                                                 course.notebook_name)]
        if named:
            nb_id, create_nb = named[0]["id"], False
    sc_id, create_sc = course.section_id, True
    if any(r["key"] == f"sc:{course.section_id}" for r in live):
        create_sc = False
    else:
        named = [r["data"] for r in live if r["key"].startswith("sc:") and r["data"].get("notebookId") == nb_id
                 and _same(r["data"].get("name", ""), course.section_name)]
        if named:
            sc_id, create_sc = named[0]["id"], False
    return nb_id, sc_id, create_nb, create_sc


def build_course(course: Course, existing: list[dict] | None = None, now_ms: int | None = None,
                 counter: list[int] | None = None) -> tuple[list[dict], dict]:
    now_ms = now_ms or int(time.time() * 1000)
    counter = counter if counter is not None else [0]
    nb_id, sc_id, create_nb, create_sc = resolve_targets(course, existing)
    records = []
    if create_nb:
        notebook = {"id": nb_id, "name": course.notebook_name, "order": course.notebook_order,
                    "createdAt": now_ms, "updatedAt": now_ms}
        records.append({"key": f"nb:{nb_id}", "rev": folio.CREATE_ONLY_REV, "deleted": 0, "data": notebook})
    if create_sc:
        section = {"id": sc_id, "notebookId": nb_id, "name": course.section_name, "color": course.section_color,
                   "order": course.section_order, "createdAt": now_ms, "updatedAt": now_ms}
        records.append({"key": f"sc:{sc_id}", "rev": folio.CREATE_ONLY_REV, "deleted": 0, "data": section})
    uploads: dict[str, bytes] = {}
    for path in chapter_files(course.dir):
        m = re.match(r"(\d+)-", path.name)
        no = int(m.group(1)) if m else 0
        recs, ups = build_chapter(course, sc_id, no, path, now_ms, counter)
        if path.name == "README.md":
            recs[0]["data"]["title"] = "導讀：" + recs[0]["data"]["title"]
        records += recs
        uploads.update(ups)
    return records, uploads


def build_all(lesson_dir: Path, now_ms: int | None = None) -> tuple[list[dict], dict]:
    """單一教材資料夾（離線，不查 Folio）。"""
    return build_course(Course.load(lesson_dir), None, now_ms)


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {folio.encode_token(token)}", "X-Folio-Device": folio.DEVICE}


def fetch_records(base_url: str, token: str) -> list[dict]:
    """把 Folio 伺服器上的全部紀錄拉下來（分頁）。"""
    out, since = [], 0
    while True:
        r = requests.get(base_url.rstrip("/") + "/api/changes", params={"since": since}, headers=_headers(token),
                         timeout=60)
        if r.status_code == 401:
            raise RuntimeError("Folio 同步密碼不對（401）")
        r.raise_for_status()
        body = r.json()
        out += body.get("records", [])
        if not body.get("more") or body.get("seq", since) == since:
            return out
        since = body["seq"]


def describe(records: list[dict]) -> str:
    """列出筆記本與分區（給人看，用來確認放在哪裡）。"""
    live = [r for r in records if not r.get("deleted") and isinstance(r.get("data"), dict)]
    nbs = [r["data"] for r in live if r["key"].startswith("nb:")]
    scs = [r["data"] for r in live if r["key"].startswith("sc:")]
    pages = [r["data"] for r in live if r["key"].startswith("pg:")]
    lines = []
    for nb in sorted(nbs, key=lambda n: n.get("order", 0)):
        lines.append(f"筆記本「{nb.get('name')}」（{nb['id']}）")
        for sc in sorted((s for s in scs if s.get("notebookId") == nb["id"]), key=lambda s: s.get("order", 0)):
            n = sum(1 for p in pages if p.get("sectionId") == sc["id"])
            lines.append(f"  └ 分區「{sc.get('name')}」（{sc['id']}，{n} 頁）")
    return "\n".join(lines)


def upload_assets(base_url: str, token: str, uploads: dict[str, bytes]) -> int:
    """先問伺服器缺哪些，只上傳缺的。回傳上傳張數。"""
    if not uploads:
        return 0
    headers = _headers(token)
    base = base_url.rstrip("/") + "/api/assets"
    resp = requests.post(base + "/check", json={"ids": list(uploads)}, headers=headers, timeout=60)
    resp.raise_for_status()
    missing = resp.json().get("missing", [])
    for aid in missing:
        r = requests.put(f"{base}/{aid}", data=uploads[aid], headers={**headers, "Content-Type": "image/png"},
                         timeout=120)
        r.raise_for_status()
    return len(missing)


def publish(base_url: str, token: str, courses: list[Course]) -> list[dict]:
    existing = fetch_records(base_url, token)
    results = []
    counter = [0]
    for course in courses:
        records, uploads = build_course(course, existing, counter=counter)
        sent = upload_assets(base_url, token, uploads)  # 圖片先上傳，頁面出現時才不會是空白
        result = folio.publish(base_url, token, records)
        nb_id, sc_id, _, _ = resolve_targets(course, existing)
        result.update(course=course.dir.name, images_uploaded=sent, notebook_id=nb_id, section_id=sc_id,
                      pages=sum(1 for r in records if r["key"].startswith("pg:")))
        results.append(result)
    return results
