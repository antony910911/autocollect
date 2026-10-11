"""教材 matplotlib 圖的共同設定：字型、配色、座標軸樣式。

集中在這裡的理由和第 11 章講的一樣——**設計決定要有一個名字、放一個地方**。
以前每個畫圖程式各自寫一份 rcParams，改一個顏色要翻三個檔案。

用法：
    import sys; sys.path.insert(0, "<repo>/lessons/_tools")
    from mplstyle import C, apply
    apply()
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# 教材的色票（和 svgkit 的 C 一致；語意命名，不要在圖裡直接寫色碼）
C = {
    "blue": "#2f6fb3", "orange": "#d9821e", "red": "#c23b3b", "green": "#2f9e6e",
    "purple": "#7b4bb3", "grey": "#6b7280", "brown": "#8a6d3b", "teal": "#1b8a8f",
    "ink": "#1d2330", "muted": "#5b6475", "grid": "#e3e6ec", "axis": "#8a93a3",
}
# 分類資料的預設順序：相鄰兩色在明度與色相都分得開（灰階印出來也分得出）
CYCLE = [C["blue"], C["orange"], C["teal"], C["purple"], C["green"], C["red"], C["brown"]]


def _install_fonts() -> bool:
    try:
        from svgkit import ensure_fonts
    except ImportError:
        return False
    if not ensure_fonts():
        return False
    if not any(f.name == "Noto Sans TC" for f in font_manager.fontManager.ttflist):
        for p in Path(matplotlib.get_cachedir()).glob("fontlist-*.json"):
            p.unlink(missing_ok=True)
        font_manager._load_fontmanager(try_read_cache=False)
    return any(f.name == "Noto Sans TC" for f in font_manager.fontManager.ttflist)


def apply() -> None:
    _install_fonts()
    fams = [f for f in ("Noto Sans TC", "WenQuanYi Zen Hei", "Noto Sans CJK TC")
            if any(x.name == f for x in font_manager.fontManager.ttflist)]
    plt.rcParams.update({
        "font.family": fams + ["DejaVu Sans"],
        "axes.unicode_minus": False, "mathtext.fontset": "dejavusans",
        "font.size": 12.5,
        "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlepad": 12,
        "axes.labelsize": 12.5, "axes.labelcolor": C["ink"],
        "text.color": C["ink"],
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": C["axis"], "axes.linewidth": 1.1,
        "axes.grid": True, "axes.axisbelow": True,
        "grid.color": C["grid"], "grid.linewidth": 0.9,
        "xtick.color": C["muted"], "ytick.color": C["muted"],
        "xtick.labelsize": 11.5, "ytick.labelsize": 11.5,
        "xtick.major.size": 0, "ytick.major.size": 0,
        "legend.frameon": False, "legend.fontsize": 11.5,
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "savefig.dpi": 200,
        "axes.prop_cycle": plt.cycler(color=CYCLE),
    })
