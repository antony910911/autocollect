"""畫教材示意圖用的小工具：用 Python 產生 SVG，再用 Chromium 轉成 PNG。"""

from __future__ import annotations

import html
import os
from pathlib import Path

FONT = ("'Noto Sans TC','WenQuanYi Zen Hei','Noto Sans CJK TC',"
        "'PingFang TC','Microsoft JhengHei',sans-serif")
FONT_DIR = Path(__file__).resolve().parent / "fonts"

# Folio 把圖一律縮到 880 px 寬（autocollect/lessons.py 的 PAGE_W）。
# 所以畫布越寬，字在頁面上就越小：畫布 1480 px 的 14.5 px 字，顯示出來只有 8.5 px。
# 新圖一律畫在 FIG_W，內文不小於 17 px——這樣縮完還有 15 px，看得清楚。
FIG_W = 1000
PAGE_W = 880


def on_page(size: float, canvas_w: int) -> float:
    """這個字級在 Folio 頁面上實際會顯示成幾 px。"""
    return size * PAGE_W / canvas_w


def ensure_fonts() -> bool:
    """把 repo 裡的 Noto Sans TC 裝進使用者字型目錄，讓 Chromium 與 matplotlib 都看得到。

    做過一次就會跳過。字型檔是用 make_font.py 裁過的子集，授權見 fonts/OFL.txt。
    回傳 True 代表字型可用。
    """
    import shutil
    import subprocess
    srcs = sorted(FONT_DIR.glob("NotoSansTC-*.subset.ttf"))
    if not srcs:
        return False
    dst_dir = Path.home() / ".local/share/fonts"
    dst_dir.mkdir(parents=True, exist_ok=True)
    changed = False
    for s in srcs:
        d = dst_dir / s.name
        if not d.exists() or d.stat().st_size != s.stat().st_size:
            shutil.copy(s, d)
            changed = True
    if changed:
        subprocess.run(["fc-cache", "-f", str(dst_dir)], capture_output=True)
    return True


INK = "#1d2330"
MUTED = "#5b6475"
# 色票、字級、間距都集中在 tokens.py（見第 11 章：設計決定要有名字、放一個地方）
from tokens import C, ICON, RADIUS, SPACE, STROKE, TYPE, USAGE  # noqa: E402,F401


def tint(hex_color: str, k: float = 0.86) -> str:
    """把顏色往白色混合，當作方塊底色。"""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(v + (255 - v) * k) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


class Svg:
    def __init__(self, w: int, h: int, title: str = ""):
        self.w, self.h = w, h
        self.parts: list[str] = []
        self.markers: set[str] = set()
        if title:
            self.text(24, 40, title, size=24, weight=700)

    # ── 基本元素 ──
    def text(self, x, y, s, size=16, color=INK, anchor="start", weight=400, italic=False):
        lines = str(s).split("\n")
        lh = size * 1.3
        y0 = y - (len(lines) - 1) * lh / 2 if anchor == "middle-v" else y
        anchor = "middle" if anchor == "middle-v" else anchor
        style = "font-style:italic;" if italic else ""
        for i, line in enumerate(lines):
            self.parts.append(
                f'<text x="{x}" y="{y0 + i * lh:.1f}" font-size="{size}" fill="{color}" text-anchor="{anchor}" '
                f'font-weight="{weight}" style="{style}">{_rich(line)}</text>')

    def box(self, x, y, w, h, label="", color=C["grey"], size=17, fill=None, sub="", sub_size=13, r=10,
            weight=700, dash=False, label_color=None):
        fill = fill or tint(color)
        d = ' stroke-dasharray="6 5"' if dash else ""
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" '
                          f'stroke="{color}" stroke-width="2"{d}/>')
        lines = label.split("\n") if label else []
        sublines = sub.split("\n") if sub else []
        total = len(lines) * size * 1.25 + len(sublines) * sub_size * 1.3 + (6 if lines and sublines else 0)
        cy = y + h / 2 - total / 2
        for line in lines:
            cy += size * 1.25
            self.parts.append(f'<text x="{x + w / 2}" y="{cy - size * 0.28:.1f}" font-size="{size}" '
                              f'fill="{label_color or INK}" text-anchor="middle" font-weight="{weight}">{_rich(line)}</text>')
        if lines and sublines:
            cy += 6
        for line in sublines:
            cy += sub_size * 1.3
            self.parts.append(f'<text x="{x + w / 2}" y="{cy - sub_size * 0.3:.1f}" font-size="{sub_size}" '
                              f'fill="{MUTED}" text-anchor="middle">{_rich(line)}</text>')

    def pill(self, x, y, s, color, size=13, pad=8):
        w = _text_w(s, size) + pad * 2
        self.parts.append(f'<rect x="{x - w / 2:.1f}" y="{y - size}" width="{w:.1f}" height="{size * 1.6:.1f}" rx="{size * 0.8:.1f}" '
                          f'fill="#ffffff" stroke="{color}" stroke-width="1.5"/>')
        self.parts.append(f'<text x="{x}" y="{y + size * 0.15:.1f}" font-size="{size}" fill="{color}" '
                          f'text-anchor="middle" font-weight="700">{_rich(s)}</text>')

    def arrow(self, pts, color=INK, width=2.5, label="", label_at=0.5, label_dx=0, label_dy=-8, size=14,
              dash=False, curve=False, both=False, label_color=None, label_anchor="middle"):
        mid = self._marker(color)
        d = ' stroke-dasharray="7 5"' if dash else ""
        if curve and len(pts) == 3:
            (x1, y1), (cx, cy), (x2, y2) = pts
            path = f"M{x1},{y1} Q{cx},{cy} {x2},{y2}"
        else:
            path = "M" + " L".join(f"{x},{y}" for x, y in pts)
        start = f' marker-start="url(#{mid}s)"' if both else ""
        self.parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{width}"{d} '
                          f'marker-end="url(#{mid})"{start}/>')
        if label:
            if curve and len(pts) == 3:
                t = label_at
                (x1, y1), (cx, cy), (x2, y2) = pts
                lx = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t ** 2 * x2
                ly = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t ** 2 * y2
            else:
                (x1, y1), (x2, y2) = pts[0], pts[-1]
                lx, ly = x1 + (x2 - x1) * label_at, y1 + (y2 - y1) * label_at
            self.text(lx + label_dx, ly + label_dy, label, size=size, color=label_color or color,
                      anchor=label_anchor, weight=700)

    def line(self, x1, y1, x2, y2, color=MUTED, width=1.5, dash=False):
        d = ' stroke-dasharray="5 5"' if dash else ""
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{d}/>')


    # ── 流程圖的標準形狀 ──
    def stadium(self, x, y, w, h, label, color=INK, size=19, fill=None, weight=700):
        """圓角膠囊＝流程的起點／終點。"""
        fill = fill or tint(color, 0.9)
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" '
                          f'fill="{fill}" stroke="{color}" stroke-width="2.5"/>')
        self._center(x, y, w, h, label, size, color, weight)

    def diamond(self, cx, cy, w, h, label, color=INK, size=18, fill=None):
        """菱形＝判斷。label 用 \n 換行；分支標籤自己畫在旁邊。"""
        fill = fill or tint(color, 0.9)
        self.parts.append(f'<path d="M{cx},{cy - h / 2} L{cx + w / 2},{cy} L{cx},{cy + h / 2} '
                          f'L{cx - w / 2},{cy} Z" fill="{fill}" stroke="{color}" '
                          f'stroke-width="2.5" stroke-linejoin="round"/>')
        self._center(cx - w / 2, cy - h / 2, w, h, label, size, color, 700)

    def para(self, x, y, w, h, label, color=INK, size=18, fill=None, skew=22):
        """平行四邊形＝資料（輸入／輸出）。"""
        fill = fill or tint(color, 0.9)
        self.parts.append(f'<path d="M{x + skew},{y} L{x + w},{y} L{x + w - skew},{y + h} '
                          f'L{x},{y + h} Z" fill="{fill}" stroke="{color}" stroke-width="2.5" '
                          f'stroke-linejoin="round"/>')
        self._center(x, y, w, h, label, size, color, 700)

    def _center(self, x, y, w, h, label, size, color, weight):
        lines = str(label).split("\n")
        y0 = y + h / 2 - (len(lines) - 1) * size * 0.65 + size * 0.34
        for i, ln in enumerate(lines):
            self.text(x + w / 2, y0 + i * size * 1.3, ln, size=size, color=color,
                      anchor="middle", weight=weight)

    # ── 圖示與元件 ──
    def icon(self, name, x, y, size=22, color=None, width=2.0):
        """畫一個 Lucide 線條圖示，(x, y) 是左上角。顏色跟 stroke 走。"""
        from icons import ICONS
        body = ICONS.get(name)
        if body is None:
            raise KeyError(f"icons.py 裡沒有 {name!r}——拼錯了，或要用 make_icons 補進去。"
                           f"現有的看 ICONS.keys()")
        k = size / 24
        self.parts.append(
            f'<g transform="translate({x},{y}) scale({k:.4f})" fill="none" '
            f'stroke="{color or INK}" stroke-width="{width}" stroke-linecap="round" '
            f'stroke-linejoin="round">{body}</g>')
        return True

    def card(self, x, y, w, items, title="", sub="", color=None, icon=None,
             foot="", size=15, pad=24, lh=26, title_size=19, fill=None, min_h=0):
        """一張會自己算高度的卡片：圖示＋標題＋小字＋分隔線＋條列＋底註。

        回傳實際高度，所以下一塊可以接著排——**不用再手算座標**，
        這是以前每張圖都要重畫兩三次的主因。
        """
        color = color or C["grey"]
        inner = w - pad * 2
        head = 0
        if title:
            head = 30 if not sub else 56
        lines = []
        for it in items:
            lines.extend(wrap(it, size, inner - (0 if not it.startswith("・") else 0)))
        body_h = len(lines) * lh
        foot_lines = wrap(foot, size - 1, inner) if foot else []
        h = max(min_h, pad + head + (18 if title else 0) + body_h
                + (len(foot_lines) * (lh - 2) + 14 if foot else 0) + pad - 8)
        self.box(x, y, w, h, "", color=color, fill=fill if fill is not None else tint(color, 0.95))
        cy = y + pad + 20
        tx = x + pad
        if icon and title:
            self.icon(icon, tx, cy - 17, 22, color, 2.1)
            tx += 32
        if title:
            self.text(tx, cy, title, size=title_size, weight=700, color=color)
            if sub:
                self.text(x + pad, cy + 24, sub, size=13.5, color=MUTED)
            ly = y + pad + head
            self.line(x + pad, ly, x + w - pad, ly, color=color)
            cy = ly + 30
        else:
            cy = y + pad + 18
        for ln in lines:
            self.text(x + pad, cy, ln, size=size)
            cy += lh
        if foot_lines:
            cy += 12
            for ln in foot_lines:
                self.text(x + pad, cy, ln, size=size - 1, weight=700, color=color)
                cy += lh - 2
        return h

    def chip(self, x, y, s, color, size=13, icon=None):
        """小標籤。回傳寬度，方便一個接一個排。"""
        iw = 17 if icon else 0
        w = _text_w(s, size) + 22 + iw
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{size * 1.85:.1f}" '
                          f'rx="{size * 0.92:.1f}" fill="{tint(color, 0.88)}" stroke="{color}" '
                          f'stroke-width="1.4"/>')
        if icon:
            self.icon(icon, x + 9, y + size * 0.45, size * 0.95, color, 2.2)
        self.text(x + 11 + iw, y + size * 1.28, s, size=size, color=color, weight=700)
        return w + 8

    def raw(self, s: str):
        self.parts.append(s)

    def _marker(self, color):
        mid = "m" + color.lstrip("#")
        if mid not in self.markers:
            self.markers.add(mid)
            self.parts.insert(0, (
                f'<defs><marker id="{mid}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" '
                f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>'
                f'<marker id="{mid}s" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" '
                f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker></defs>'))
        return mid

    def svg(self) -> str:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">'
                f'<rect width="100%" height="100%" fill="#ffffff"/>' + "".join(self.parts) + "</svg>")


def _rich(s: str) -> str:
    """支援 **粗體**、*斜體*、上下標 NH4^+^／N_2_；`\\_` `\\^` 印出字面；其餘照字面跳脫。"""
    out, i = [], 0
    s = html.escape(s, quote=False)
    while i < len(s):
        if s.startswith("**", i):          # **粗體**：行內加粗，而不是印出星號
            j = s.find("**", i + 2)
            if j > i:
                out.append(f'<tspan font-weight="700">{_rich(s[i + 2:j])}</tspan>')
                i = j + 2
                continue
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] in "^_\\":
            out.append(s[i + 1])   # \_ \^ \\ ：印出字面，不當上下標
            i += 2
            continue
        if ch == "*":                      # *斜體*：學名用
            j = s.find("*", i + 1)
            if j > i:
                out.append(f'<tspan font-style="italic">{_rich(s[i + 1:j])}</tspan>')
                i = j + 1
                continue
        if ch in "^_":
            j = s.find(ch, i + 1)
            if j > i:
                shift = "-0.45em" if ch == "^" else "0.3em"
                back = "0.45em" if ch == "^" else "-0.3em"
                out.append(f'<tspan dy="{shift}" font-size="70%">{s[i + 1:j]}</tspan><tspan dy="{back}">​</tspan>')
                i = j + 1
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def _text_w(s: str, size: float) -> float:
    plain = s.replace("^", "").replace("_", "")
    return sum(size if ord(ch) > 0x2E80 else size * 0.58 for ch in plain)



_NO_LINE_START = set("，。、；：？！）」』〉》】%,.:;?!)]}…～")


def wrap(txt: str, size: float, maxw: float) -> list[str]:
    """依實際寬度斷行；ASCII 單字不切開，行首不留標點。"""
    import re as _re
    tokens = _re.findall(r"[A-Za-z0-9²³·\.\-–—/%‰+×=（）()]+|\s+|.", str(txt))
    lines, cur = [], ""
    for tok in tokens:
        if tok.isspace() and not cur:
            continue
        # 標點不能掉到行首：寧可讓這一行超出一點點，也不要「，」開頭
        if _text_w(cur + tok, size) > maxw and cur and tok not in _NO_LINE_START:
            lines.append(cur.rstrip())
            cur = "" if tok.isspace() else tok
        else:
            cur += tok
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def render(svgs: dict[str, Svg], out_dir: Path, scale: float = 2.0) -> None:
    """把 SVG 存檔並轉成 PNG（白底、2 倍解析度）。"""
    from playwright.sync_api import sync_playwright

    ensure_fonts()

    exe = os.environ.get("CHROMIUM", "/opt/pw-browsers/chromium")
    out_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe if Path(exe).exists() else None)
        for name, s in svgs.items():
            page = browser.new_page(viewport={"width": s.w, "height": s.h}, device_scale_factor=scale)
            page.set_content(f"<html><body style='margin:0'>{s.svg()}</body></html>")
            page.screenshot(path=str(out_dir / f"{name}.png"), clip={"x": 0, "y": 0, "width": s.w, "height": s.h})
            page.close()
            print("寫入", name)
        browser.close()
