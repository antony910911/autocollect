import json
import re
import struct
import threading
import zlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from autocollect import folio, lessons

ALLOWED = {"b", "i", "u", "s", "br", "div", "p", "span", "ul", "ol", "li"}
LESSON_DIR = Path(__file__).resolve().parent.parent / "lessons" / "ammonia"


def tiny_png(w, h, seed=0):
    raw = b"".join(b"\x00" + bytes([seed % 256]) * (w * 3) for _ in range(h))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


@pytest.fixture
def lesson(tmp_path):
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "a.png").write_bytes(tiny_png(400, 200, 1))
    (tmp_path / "figures" / "b.png").write_bytes(tiny_png(300, 300, 2))
    (tmp_path / "course.yaml").write_text(
        "notebook: {id: nb_t, name: claude圖解教材, find_by_name: true}\n"
        "section: {id: sc_t, name: 測試分區}\npage_prefix: amm\n", "utf-8")
    (tmp_path / "README.md").write_text("# 導讀\n\n見 [第 1 章](01-x.md)。\n", "utf-8")
    (tmp_path / "01-x.md").write_text(
        "# 第 1 章　測試\n\n## 1.1 小節\n\n*Nitrospira* 與 **重點** [1]\n\n"
        "![圖 1](figures/a.png)\n\n| 欄 | 值 |\n|---|---|\n| pH | 7 |\n\n![圖 2](figures/b.png)\n\n## 參考文獻\n\n"
        "1. Someone (2020). Title. https://doi.org/10.1/x\n", "utf-8")
    return tmp_path


def test_parse_interleaves_text_and_images(lesson):
    title, blocks = lessons.parse((lesson / "01-x.md").read_text("utf-8"), lesson)
    assert title == "第 1 章　測試"
    kinds = [type(b).__name__ for b in blocks]
    assert kinds == ["Text", "Image", "Text", "Image", "Text"]
    assert blocks[1].path == lesson / "figures" / "a.png"


def test_html_is_folio_safe_and_keeps_italics(lesson):
    html = lessons.to_html((lesson / "01-x.md").read_text("utf-8").split("![")[0])
    tags = {t.lower() for t in re.findall(r"</?([a-zA-Z]+)", html)}
    assert tags <= ALLOWED
    assert "<i>Nitrospira</i>" in html and "<b>重點</b>" in html
    assert lessons.to_html("見 [第 1 章](01-x.md)。") == "<div>見 第 1 章。</div>"


def test_layout_stacks_without_overlap_and_cleans_old_items(lesson):
    records, uploads = lessons.build_all(lesson, now_ms=1000)
    keys = [r["key"] for r in records]
    assert keys[:2] == ["nb:nb_t", "sc:sc_t"]
    pages = [r["data"] for r in records if r["key"].startswith("pg:")]
    assert [p["title"] for p in pages] == ["導讀：導讀", "第 1 章　測試"]
    items = [r["data"] for r in records if r["key"].startswith("it:pg_autocollect_amm_01:") and not r["deleted"]]
    assert [i["type"] for i in items] == ["text", "image", "text", "image", "text"]
    for a, b in zip(items, items[1:]):
        bottom = a["y"] + (a["h"] if a["type"] == "image" else lessons.estimate_height(a["html"]))
        assert bottom < b["y"]
    img = items[1]
    assert img["w"] == lessons.PAGE_W and img["h"] == lessons.PAGE_W // 2
    assert img["asset"] in uploads and f"as:{img['asset']}" in keys
    tomb = [r for r in records if r["key"].startswith("it:pg_autocollect_amm_01:") and r["deleted"]]
    assert len(tomb) == lessons.SPARE_TOMBSTONES and tomb[0]["key"].endswith("x_amm_01_005")
    revs = [r["rev"] for r in records if r["key"].startswith("it:")]
    assert len(set(revs)) == len(revs) and all(folio.CREATE_ONLY_REV < r for r in revs)


def test_estimate_grows_with_text():
    short = lessons.estimate_height("<div>短</div>")
    long = lessons.estimate_height("<div>" + "很長的文字" * 200 + "</div>")
    # 1000 個中文字 × 16px ÷ 868px 可用寬度 ≈ 19 行，每行 25.6px
    assert short < 70 and long > 19 * 25.6


def test_real_lessons_build():
    """教材本身：每章都有標題、圖都存在且是 PNG。"""
    records, uploads = lessons.build_all(LESSON_DIR, now_ms=1000)
    titles = [r["data"]["title"] for r in records if r["key"].startswith("pg:")]
    assert len(titles) == 10 and titles[1].startswith("第 1 章")
    assert len(uploads) >= 15


@pytest.fixture
def fake_folio():
    store, assets, puts = {}, {}, []

    class H(BaseHTTPRequestHandler):
        def _send(self, obj):
            data = json.dumps(obj).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["content-length"])))
            if self.path == "/api/assets/check":
                return self._send({"missing": [i for i in body["ids"] if i not in assets]})
            accepted = 0
            for r in body["records"]:
                cur = store.get(r["key"])
                if cur and cur["rev"] >= r["rev"]:
                    continue
                store[r["key"]] = r
                accepted += 1
            self._send({"accepted": accepted})

        def do_GET(self):
            self._send({"records": list(store.values()), "seq": len(store), "more": False})

        def do_PUT(self):
            aid = self.path.rsplit("/", 1)[1]
            assets[aid] = self.rfile.read(int(self.headers["content-length"]))
            puts.append((aid, self.headers["content-type"]))
            self._send({"ok": True})

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}", store, assets, puts
    srv.shutdown()


def test_publish_uploads_images_once(lesson, fake_folio):
    url, store, assets, puts = fake_folio
    course = lessons.Course.load(lesson)
    [res] = lessons.publish(url, "pw", [course])
    assert res["images_uploaded"] == 2 and res["pages"] == 2
    assert all(ct == "image/png" for _, ct in puts)
    assert all(store[f"as:{a}"]["data"]["type"] == "image/png" for a in assets)
    [res] = lessons.publish(url, "pw", [course])
    assert res["images_uploaded"] == 0 and len(puts) == 2


def test_publish_finds_existing_notebook_by_name(lesson, fake_folio):
    url, store, assets, puts = fake_folio
    mine = {"id": "nb_user123", "name": " Claude圖解教材 ", "order": 5}
    store["nb:nb_user123"] = {"key": "nb:nb_user123", "rev": folio.make_rev(5000), "deleted": 0, "data": mine}
    [res] = lessons.publish(url, "pw", [lessons.Course.load(lesson)])
    assert res["notebook_id"] == "nb_user123" and "nb:nb_t" not in store
    assert store["sc:sc_t"]["data"]["notebookId"] == "nb_user123"
    assert store["pg:pg_autocollect_amm_01"]["data"]["sectionId"] == "sc_t"
    # 使用者已有同名分區時，也直接用它
    store.pop("sc:sc_t")
    store["sc:sc_mine"] = {"key": "sc:sc_mine", "rev": folio.make_rev(6000), "deleted": 0,
                           "data": {"id": "sc_mine", "notebookId": "nb_user123", "name": "測試分區"}}
    nb, sc, create_nb, create_sc = lessons.resolve_targets(lessons.Course.load(lesson), list(store.values()))
    assert (nb, sc, create_nb, create_sc) == ("nb_user123", "sc_mine", False, False)
    assert "筆記本「 Claude圖解教材 」" in lessons.describe(list(store.values()))


def test_check_refs_extracts_dois_with_parentheses():
    import importlib.util
    spec = importlib.util.spec_from_file_location("check_refs", LESSON_DIR.parent / "_tools" / "check_refs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.extract_doi("x. https://doi.org/10.1061/(ASCE)0733-9372(2001)127:8(673)") == \
        "10.1061/(ASCE)0733-9372(2001)127:8(673)"
    assert mod.extract_doi("（見 https://doi.org/10.1/abc）") == "10.1/abc"
    assert mod.extract_doi("https://doi.org/10.1890/1051-0761(2006)016[2091:MFMDDA]2.0.CO;2") == \
        "10.1890/1051-0761(2006)016[2091:MFMDDA]2.0.CO;2"
    assert mod.extract_doi("沒有 DOI") is None
    refs = mod.references((LESSON_DIR / "06-qpcr-design.md").read_text("utf-8"))
    assert len(refs) == 20 and all(mod.extract_doi(r) for r in refs)
