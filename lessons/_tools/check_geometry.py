"""檢查圖「裡面」的幾何：文字疊不疊、跑不跑出畫布、被不被蓋住、壓不壓在線上。

`check_layout.py` 檢查的是 Folio 頁面上「文字區塊 vs 圖片」會不會疊；
這一支檢查的是**一張圖內部**。兩個互補，推送前兩個都要跑。

為什麼需要它：這些問題不會讓程式報錯，只會讓圖變得看不懂，而且很容易漏看。
以前都靠畫完用 Read 看一次 PNG——有效，但會累、會漏。

做法是把 `Svg.svg()` 產生的字串用 XML 解析器讀回來，算出每個元素的邊界：

- A 文字跑出畫布
- B 兩段文字互相重疊
- C 文字被「畫在它後面」的不透明矩形蓋住（SVG 是後畫的蓋前畫的）
- D 文字壓在線條或箭頭上，而且底下沒有白底遮罩
- E 箭頭有斜線段（只是提醒；教材有幾張是刻意畫斜的）

文字寬度用 svgkit 的 `_text_w()` 估，和畫圖時用的是同一支函式，所以誤差一致。

用法：
  python lessons/_tools/check_geometry.py                      # 檢查所有教材
  python lessons/_tools/check_geometry.py lessons/using-claude # 只檢查一門
  python lessons/_tools/check_geometry.py --only fig17-10-independent
  python lessons/_tools/check_geometry.py --skip E             # 不看斜箭頭

有問題時以代碼 1 結束。
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[1]
sys.path.insert(0, str(TOOLS))

from svgkit import Svg, _text_w  # noqa: E402

NS = "{http://www.w3.org/2000/svg}"

# 容忍值。調這幾個數字之前先想清楚：調鬆了就抓不到真的問題。
PAD_X = 1.0      # 文字左右各縮排多少才算重疊（字距本來就有空隙）
PAD_Y = 2.0      # 上下同理
MIN_OVERLAP = 4.0   # 重疊要超過這麼多 px 才報，避免標點擦邊
EDGE_TOL = 4.0      # 出界容忍：_text_w() 把全形標點當 1em，會高估一點
BITE = 3.0          # 線要吃進文字框這麼多 px 才算「壓在線上」，擦邊不算
ASCENT, DESCENT = 0.78, 0.22        # 相對於 font-size 的上緣與下緣
WHITE = {"#ffffff", "#fff", "white"}


class Box:
    __slots__ = ("x0", "y0", "x1", "y1", "what", "i")

    def __init__(self, x0, y0, x1, y1, what, i):
        self.x0, self.y0, self.x1, self.y1, self.what, self.i = x0, y0, x1, y1, what, i

    def overlap(self, o: "Box") -> tuple[float, float]:
        return (min(self.x1, o.x1) - max(self.x0, o.x0),
                min(self.y1, o.y1) - max(self.y0, o.y0))

    def inside(self, o: "Box") -> bool:
        return self.x0 >= o.x0 - 1 and self.x1 <= o.x1 + 1 and \
            self.y0 >= o.y0 - 1 and self.y1 <= o.y1 + 1

    def __repr__(self):
        return f"({self.x0:.0f},{self.y0:.0f})–({self.x1:.0f},{self.y1:.0f})"


def _f(el, name, default=0.0) -> float:
    v = el.get(name)
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _plain(el) -> str:
    """<text> 的可見文字；上下標的 tspan 也算進去。"""
    return "".join(el.itertext()).replace("​", "")


def parse(svg_text: str):
    """回傳 (文字框, 不透明矩形, 線段)，三者都帶繪製順序 i。"""
    root = ET.fromstring(svg_text)
    texts, rects, segs = [], [], []
    for i, el in enumerate(root.iter()):
        tag = el.tag
        if tag == NS + "text":
            s = _plain(el)
            if not s.strip():
                continue
            size = _f(el, "font-size", 14)
            w = _text_w(s, size)
            x, y = _f(el, "x"), _f(el, "y")
            anchor = el.get("text-anchor", "start")
            x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
            texts.append(Box(x0 + PAD_X, y - size * ASCENT + PAD_Y,
                             x0 + w - PAD_X, y + size * DESCENT - PAD_Y, s, i))
        elif tag == NS + "rect":
            fill = (el.get("fill") or "").lower()
            if fill in ("none", "transparent") or el.get("fill-opacity") == "0":
                continue
            x, y = _f(el, "x"), _f(el, "y")
            rects.append(Box(x, y, x + _f(el, "width"), y + _f(el, "height"),
                             fill or "#000000", i))
        elif tag == NS + "line":
            segs.append((_f(el, "x1"), _f(el, "y1"), _f(el, "x2"), _f(el, "y2"), i,
                         el.get("marker-end") is not None))
        elif tag == NS + "path":
            d = el.get("d") or ""
            if "Q" in d or "C" in d or "A" in d:      # 曲線：不檢查幾何，只是不要誤報
                continue
            pts = [(float(a), float(b)) for a, b in
                   re.findall(r"[ML]\s*(-?[\d.]+),\s*(-?[\d.]+)", d)]
            arrow = el.get("marker-end") is not None
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                segs.append((x1, y1, x2, y2, i, arrow))
    return texts, rects, segs


def _seg_hits_box(seg, b: Box) -> bool:
    """線段有沒有「吃進」矩形（只處理水平／垂直段，教材的線幾乎都是）。

    擦過邊緣不算——字框本來就比墨水寬一點，貼著邊的線看起來是有留白的。
    """
    x1, y1, x2, y2 = seg[:4]
    if abs(y1 - y2) < 0.5:                      # 水平
        return (b.y0 + BITE <= y1 <= b.y1 - BITE
                and min(x1, x2) < b.x1 - BITE and max(x1, x2) > b.x0 + BITE)
    if abs(x1 - x2) < 0.5:                      # 垂直
        return (b.x0 + BITE <= x1 <= b.x1 - BITE
                and min(y1, y2) < b.y1 - BITE and max(y1, y2) > b.y0 + BITE)
    return False


def check_svg(name: str, svg_text: str, w: int, h: int, skip: set[str]) -> list[str]:
    texts, rects, segs = parse(svg_text)
    bad = []

    if "A" not in skip:
        for t in texts:
            if (t.x0 < -EDGE_TOL or t.y0 < -EDGE_TOL
                    or t.x1 > w + EDGE_TOL or t.y1 > h + EDGE_TOL):
                bad.append(f"A 文字跑出畫布（{w}×{h}）：{t} 「{t.what[:28]}」")

    if "B" not in skip:
        for i, a in enumerate(texts):
            for b in texts[i + 1:]:
                ox, oy = a.overlap(b)
                if ox > MIN_OVERLAP and oy > MIN_OVERLAP:
                    bad.append(f"B 兩段文字重疊 {ox:.0f}×{oy:.0f} px："
                               f"「{a.what[:22]}」{a} ×「{b.what[:22]}」{b}")

    if "C" not in skip:
        for t in texts:
            for r in rects:
                # 只有畫在文字之後、而且不透明的矩形才會蓋住文字
                if r.i > t.i and r.what not in ("none",):
                    ox, oy = t.overlap(r)
                    if ox > t.x1 - t.x0 - 2 and oy > t.y1 - t.y0 - 2:
                        bad.append(f"C 文字被後畫的方塊蓋住：「{t.what[:26]}」{t} ← {r.what}")
                        break

    if "D" not in skip:
        for t in texts:
            for seg in segs:
                if not _seg_hits_box(seg, t):
                    continue
                # 線 → 不透明方塊 → 文字，這是對的畫法。方塊不一定是白的：
                # chip、卡片、方塊底色都算遮罩，只要它蓋得住文字又畫在中間。
                if any(t.inside(m) and seg[4] < m.i < t.i for m in rects):
                    continue
                bad.append(f"D 文字壓在線上又沒有遮罩：「{t.what[:26]}」{t}")
                break

    note = 0
    if "E" not in skip:
        note = sum(1 for x1, y1, x2, y2, _, arrow in segs
                   if arrow and abs(x1 - x2) > 1.5 and abs(y1 - y2) > 1.5)

    out = [f"  ⚠ {name}：{m}" for m in bad]
    if note:
        out.append(f"  · {name}：{note} 條斜箭頭（只是提醒，不算問題；"
                   "放射狀與代謝流量圖本來就是斜的）")
    return out, len(bad)


def load_figs(course: Path) -> dict[str, Svg]:
    src = course / "figures/src/diagrams.py"
    if not src.exists():
        return {}
    sys.path.insert(0, str(src.parent))
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"_dg_{course.name}", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.path.pop(0)
    return {k: fn() for k, fn in mod.FIGS.items()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="*", help="要檢查的教材資料夾（預設全部）")
    ap.add_argument("--only", help="只檢查這張圖")
    ap.add_argument("--skip", default="", help="跳過哪幾項檢查，例如 --skip DE")
    a = ap.parse_args(argv)
    skip = set(a.skip.upper())

    dirs = [Path(d) for d in a.dirs] if a.dirs else sorted(
        p.parent for p in (ROOT / "lessons").glob("*/course.yaml"))
    total = 0
    for course in dirs:
        figs = load_figs(course)
        if a.only:
            figs = {k: v for k, v in figs.items() if k == a.only}
        msgs, n = [], 0
        for name, s in figs.items():
            m, k = check_svg(name, s.svg(), s.w, s.h, skip)
            msgs += m
            n += k
        total += n
        print(f"{course.name}：{len(figs)} 張圖，{n} 個問題")
        for m in msgs:
            print(m)
    if total:
        print(f"\n共 {total} 個問題——修好再推。（· 開頭的斜箭頭只是提醒，不計入）")
        return 1
    print("\n全部通過。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
