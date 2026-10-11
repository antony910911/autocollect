"""畫教材示意圖用的小工具：用 Python 產生 SVG，再用 Chromium 轉成 PNG。"""

from __future__ import annotations

import html
import os
from pathlib import Path

FONT = "'WenQuanYi Zen Hei','Noto Sans CJK TC','PingFang TC','Microsoft JhengHei',sans-serif"
INK = "#1d2330"
MUTED = "#5b6475"
# 氮的各種形態固定用同一組顏色，章節之間看得出對應
C = {
    "nh4": "#2f6fb3",   # 氨氮
    "no2": "#d9821e",   # 亞硝酸鹽
    "no3": "#c23b3b",   # 硝酸鹽
    "n2": "#2f9e6e",    # 氮氣
    "org": "#8a6d3b",   # 有機氮
    "amx": "#7b4bb3",   # 厭氧氨氧化
    "gas": "#6b7280",   # 其他氣體
    "grey": "#8a93a3",
}


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
    """支援上下標：NH4^+^、NO3^-^、N_2_；其餘照字面跳脫。"""
    out, i = [], 0
    s = html.escape(s, quote=False)
    while i < len(s):
        ch = s[i]
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


def render(svgs: dict[str, Svg], out_dir: Path, scale: float = 2.0) -> None:
    """把 SVG 存檔並轉成 PNG（白底、2 倍解析度）。"""
    from playwright.sync_api import sync_playwright

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
