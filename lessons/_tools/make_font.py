"""把 Noto Sans TC 裁成「這個 repo 實際用得到的字」，給圖使用。

為什麼要自己裁：完整的 Noto Sans TC 有 106 個子集、每個字重 3.3 MB，太大不適合進版本庫。
這支程式掃過 lessons/ 底下所有 .md 與 .py，收集真的出現過的字元，只保留那些字，
檔案會小一到兩個數量級。

前置（只有要重做字型時才需要，而且要有網路）：
    npm install @fontsource/noto-sans-tc@5.2.5

執行：
    python lessons/_tools/make_font.py [node_modules 的路徑]

產出 lessons/_tools/fonts/NotoSansTC-{Regular,Bold}.subset.ttf，
svgkit 與 matplotlib 都讀這兩個檔。字型授權 SIL OFL 1.1（見 fonts/OFL.txt）。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "fonts"
WEIGHTS = {"Regular": "400", "Bold": "700"}
# 教材之外一定要有的：ASCII、常用標點、數學與箭頭、圈號
EXTRA = (" !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`"
         "abcdefghijklmnopqrstuvwxyz{|}~"
         "　，。、；：？！…—～（）「」『』〈〉《》【】％＋－×÷＝≈≥≤→←↑↓↔⟶"
         "①②③④⑤⑥⑦⑧⑨⑩⑪⑫★☆✓✗⚠·•∕‰°±µΩαβγΔ")


def charset() -> set[str]:
    chars = set(EXTRA)
    for pat in ("**/*.md", "**/*.py", "**/*.json", "**/*.yaml"):
        for p in (ROOT / "lessons").glob(pat):
            try:
                chars |= set(p.read_text("utf-8"))
            except (UnicodeDecodeError, OSError):
                pass
    return {c for c in chars if c.isprintable() and c != " "} | {" "}


def build(node_modules: Path, chars: set[str]) -> None:
    from fontTools.merge import Merger
    from fontTools.subset import Subsetter
    from fontTools.ttLib import TTFont

    src = node_modules / "@fontsource/noto-sans-tc/files"
    if not src.is_dir():
        sys.exit(f"找不到 {src}——先跑 npm install @fontsource/noto-sans-tc@5.2.5")
    OUT.mkdir(parents=True, exist_ok=True)
    want = {ord(c) for c in chars}

    for name, w in WEIGHTS.items():
        files = sorted(src.glob(f"*-{w}-normal.woff2"))
        keep, covered = [], set()
        for f in files:                      # 只留「有我們要的字」的子集
            font = TTFont(f)
            have = want & set(font.getBestCmap())
            if have:
                tmp = OUT / f"_tmp-{f.stem}.ttf"
                font.flavor = None
                font.save(tmp)
                keep.append(tmp)
                covered |= have
        if not keep:
            sys.exit("沒有任何子集涵蓋到需要的字")
        merged = Merger().merge([str(p) for p in keep]) if len(keep) > 1 else TTFont(keep[0])
        ss = Subsetter()
        ss.populate(unicodes=sorted(covered))
        ss.subset(merged)
        _rename(merged, name, int(w))        # 合併後名稱會沿用第一個子集，要改正
        dst = OUT / f"NotoSansTC-{name}.subset.ttf"
        merged.save(dst)
        for p in keep:
            p.unlink()
        missing = len(want - covered)
        print(f"{dst.name}：用了 {len(keep)} 個子集、{len(covered):,} 個字，"
              f"{dst.stat().st_size / 1024:.0f} KB（{missing} 個字元字型裡沒有）")



def _rename(font, style: str, weight: int) -> None:
    """把合併後的名稱表改成正確的家族名與字重，否則 fontconfig 會抓到子集的舊名字。"""
    family, full = "Noto Sans TC", f"Noto Sans TC {style}" if style != "Regular" else "Noto Sans TC"
    ps = f"NotoSansTC-{style}"
    values = {1: family, 2: style, 3: f"{ps};subset", 4: full, 6: ps,
              16: family, 17: style}
    name = font["name"]
    name.names = [r for r in name.names if r.nameID not in values]
    for nid, val in values.items():
        name.setName(val, nid, 3, 1, 0x409)
        name.setName(val, nid, 1, 0, 0)
    font["OS/2"].usWeightClass = weight
    font["OS/2"].fsSelection = (font["OS/2"].fsSelection & ~0b1100000) | (
        0b0100000 if weight >= 700 else 0b1000000)
    font["head"].macStyle = 1 if weight >= 700 else 0


if __name__ == "__main__":
    nm = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("node_modules")
    cs = charset()
    print(f"教材用到 {len(cs):,} 個不同字元")
    build(nm, cs)
