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
class Part:
    """一門教材要發佈到的一個 Folio 分區。

    一門教材可以拆成多個分區（例如前半是通用流程、後半是某一株菌的案例）。
    每個分區有自己的頁面 id 前綴與檔名樣式，所以章號各自從 1 開始。
    """

    section_id: str
    section_name: str
    page_prefix: str
    glob: str = "[0-9][0-9]-*.md"
    intro: str | None = "README.md"      # 這個分區的導讀，當第 0 頁
    color: str = "#2f6fb3"
    order: int = 1

    def chapters(self, lesson_dir: Path) -> list[Path]:
        """導讀當第 0 頁，其餘依檔名排序，章號依序從 1 給。"""
        files = sorted(lesson_dir.glob(self.glob))
        intro = lesson_dir / self.intro if self.intro else None
        return ([intro] if intro and intro.exists() else []) + files


@dataclass
class Course:
    """一門教材：放在哪本筆記本、拆成哪幾個分區。設定寫在教材資料夾的 course.yaml。"""

    dir: Path
    notebook_id: str
    notebook_name: str
    parts: list[Part]
    find_notebook_by_name: bool = False  # True：Folio 裡已有同名筆記本就放進去，沒有才建立
    notebook_order: int = 110

    # 舊的單分區介面，保留給既有呼叫端
    @property
    def section_id(self) -> str:
        return self.parts[0].section_id

    @property
    def section_name(self) -> str:
        return self.parts[0].section_name

    @property
    def page_prefix(self) -> str:
        return self.parts[0].page_prefix

    @property
    def section_color(self) -> str:
        return self.parts[0].color

    @property
    def section_order(self) -> int:
        return self.parts[0].order

    @classmethod
    def load(cls, lesson_dir: Path) -> "Course":
        cfg = yaml.safe_load((lesson_dir / "course.yaml").read_text("utf-8"))
        nb = cfg["notebook"]
        if "sections" in cfg:                       # 多分區
            parts = [Part(section_id=s["id"], section_name=s["name"], page_prefix=s["page_prefix"],
                          glob=s.get("glob", "[0-9][0-9]-*.md"), intro=s.get("intro"),
                          color=s.get("color", "#2f6fb3"), order=int(s.get("order", i + 1)))
                     for i, s in enumerate(cfg["sections"])]
        else:                                       # 單分區（原本的寫法）
            sc = cfg["section"]
            parts = [Part(section_id=sc["id"], section_name=sc["name"], page_prefix=cfg["page_prefix"],
                          color=sc.get("color", "#2f6fb3"), order=int(sc.get("order", 1)))]
        return cls(dir=lesson_dir, notebook_id=nb["id"], notebook_name=nb["name"], parts=parts,
                   find_notebook_by_name=bool(nb.get("find_by_name", False)),
                   notebook_order=int(nb.get("order", 110)))


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


def chapter_label(chapter_no: int, total: int, part_name: str) -> str:
    """頁面最上面那一行「第幾章」。

    一門教材可以拆成多個分區，每個分區的章號都從 1 開始，所以光寫「第 3 章」
    還是會搞混；分區名稱一起寫上去才知道是哪一套的第 3 章。
    """
    if chapter_no == 0:
        return f"**導讀**　{part_name}（共 {total} 章）"
    return f"**第 {chapter_no} 章**（共 {total} 章）　{part_name}"


def build_chapter(course: Course, section_id: str, chapter_no: int, md_path: Path, now_ms: int,
                  rev_counter: list[int], page_prefix: str | None = None,
                  part_name: str = "", total: int = 0) -> tuple[list[dict], dict]:
    """回傳（紀錄, 需要上傳的圖片 {asset_id: bytes}）。"""
    title, blocks = parse(md_path.read_text("utf-8"), md_path.parent)
    title = title or md_path.stem
    if part_name and total:
        blocks.insert(0, Text(chapter_label(chapter_no, total, part_name)))
    tag = f"{page_prefix or course.page_prefix}_{chapter_no:02d}"
    page_id = f"pg_autocollect_{tag}"

    def rev():
        rev_counter[0] += 1
        return folio.make_rev(now_ms, rev_counter[0])

    page = {"id": page_id, "sectionId": section_id, "title": title, "background": "blank",
            "order": chapter_no, "createdAt": now_ms, "updatedAt": now_ms}

    # 頁面用「會更新」的 rev，不是 CREATE_ONLY：章節重新排序之後，
    # 標題與順序要以 repo 為準，不然內容會跑到錯的位置上。
    records = [{"key": f"pg:{page_id}", "rev": rev(), "deleted": 0, "data": page}]
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


def resolve_targets(course: Course, existing: list[dict] | None,
                    part: "Part | None" = None) -> tuple[str, str, bool, bool]:
    """決定實際要用的（筆記本 id, 分區 id, 要不要建筆記本, 要不要建分區）。

    existing 是從 Folio 拉下來的全部紀錄；None 表示不查（離線預覽）。
    part 不給就用第一個分區（保留舊的單分區呼叫方式）。
    """
    part = part or course.parts[0]
    live = [r for r in (existing or []) if not r.get("deleted") and isinstance(r.get("data"), dict)]
    nb_id, create_nb = course.notebook_id, True
    if any(r["key"] == f"nb:{course.notebook_id}" for r in live):
        create_nb = False
    elif course.find_notebook_by_name:
        named = [r["data"] for r in live if r["key"].startswith("nb:") and _same(r["data"].get("name", ""),
                                                                                 course.notebook_name)]
        if named:
            nb_id, create_nb = named[0]["id"], False
    sc_id, create_sc = part.section_id, True
    if any(r["key"] == f"sc:{part.section_id}" for r in live):
        create_sc = False
    else:
        named = [r["data"] for r in live if r["key"].startswith("sc:") and r["data"].get("notebookId") == nb_id
                 and _same(r["data"].get("name", ""), part.section_name)]
        if named:
            sc_id, create_sc = named[0]["id"], False
    return nb_id, sc_id, create_nb, create_sc


def prune_pages(prefix: str, keep: set[str], existing: list[dict] | None,
                rev) -> list[dict]:
    """把同一個前綴下、這次沒有產生的頁面標記成刪除。

    章節搬到別的分區之後，舊分區會留下孤兒頁。Folio 的同步只會新增與更新，
    不會自己清掉，所以要主動送刪除紀錄——頁面本身，還有它底下的項目。
    """
    live = [r for r in (existing or []) if not r.get("deleted") and isinstance(r.get("data"), dict)]
    out = []
    head = f"pg_autocollect_{prefix}_"
    stale = {r["data"]["id"] for r in live
             if r["key"].startswith("pg:") and r["data"].get("id", "").startswith(head)
             and r["data"]["id"] not in keep}
    for pid in sorted(stale):
        for r in live:
            if r["key"].startswith(f"it:{pid}:"):
                out.append({"key": r["key"], "rev": rev(), "deleted": 1, "data": None})
        out.append({"key": f"pg:{pid}", "rev": rev(), "deleted": 1, "data": None})
    return out


def build_course(course: Course, existing: list[dict] | None = None, now_ms: int | None = None,
                 counter: list[int] | None = None) -> tuple[list[dict], dict]:
    now_ms = now_ms or int(time.time() * 1000)
    counter = counter if counter is not None else [0]

    def rev():
        counter[0] += 1
        return folio.make_rev(now_ms, counter[0])

    records: list[dict] = []
    uploads: dict[str, bytes] = {}
    made_nb = False
    for part in course.parts:
        nb_id, sc_id, create_nb, create_sc = resolve_targets(course, existing, part)
        if create_nb and not made_nb:
            records.append({"key": f"nb:{nb_id}", "rev": folio.CREATE_ONLY_REV, "deleted": 0,
                            "data": {"id": nb_id, "name": course.notebook_name,
                                     "order": course.notebook_order,
                                     "createdAt": now_ms, "updatedAt": now_ms}})
            made_nb = True
        if create_sc:
            records.append({"key": f"sc:{sc_id}", "rev": folio.CREATE_ONLY_REV, "deleted": 0,
                            "data": {"id": sc_id, "notebookId": nb_id, "name": part.section_name,
                                     "color": part.color, "order": part.order,
                                     "createdAt": now_ms, "updatedAt": now_ms}})
        paths = list(part.chapters(course.dir))
        total = sum(1 for p in paths if not (part.intro and p.name == part.intro))
        keep, n = set(), 0
        for path in paths:
            if part.intro and path.name == part.intro:
                no = 0                    # 導讀固定是第 0 頁
            else:
                n += 1                    # 其餘依順序從 1 開始，和檔名裡的數字無關
                no = n
            recs, ups = build_chapter(course, sc_id, no, path, now_ms, counter, part.page_prefix,
                                      part.section_name, total)
            if no == 0:
                recs[0]["data"]["title"] = "導讀：" + recs[0]["data"]["title"]
            keep.add(recs[0]["data"]["id"])
            records += recs
            uploads.update(ups)
        records += prune_pages(part.page_prefix, keep, existing, rev)
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
