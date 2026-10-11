"""模型價格與快取的實際成本圖。執行：python lessons/using-claude/figures/src/charts.py"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_tools"))
from mplstyle import apply as _apply_house_style  # noqa: E402
_apply_house_style()   # 先裝好 Noto Sans TC 並設定共同樣式；下面的 rcParams 可再覆蓋
OUT = Path(__file__).resolve().parent.parent
CODE = OUT.parent / "code"
for f in ("Noto Sans TC", "WenQuanYi Zen Hei", "Noto Sans CJK TC",
          "PingFang TC", "Microsoft JhengHei"):
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = [f, "DejaVu Sans"]
        break
plt.rcParams.update({"axes.unicode_minus": False, "mathtext.fontset": "dejavusans",
                     "font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "axes.axisbelow": True, "grid.color": "#e3e6ec",
                     "axes.edgecolor": "#8a93a3", "axes.titleweight": "bold",
                     "axes.titlesize": 14, "savefig.dpi": 200})
NOTE = "#5b6475"


def fig_cost():
    d = json.loads((CODE / "models.json").read_text("utf-8"))
    ms, ex = d["models"], d["example"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.6, 4.8))

    x = np.arange(len(ms))
    w = 0.38
    a1.bar(x - w / 2, [m["in_usd_per_mtok"] for m in ms], w, label="輸入", color="#2f6fb3")
    a1.bar(x + w / 2, [m["out_usd_per_mtok"] for m in ms], w, label="輸出", color="#d47c18")
    for i, m in enumerate(ms):
        a1.text(i - w / 2, m["in_usd_per_mtok"] + 0.6, f'{m["in_usd_per_mtok"]:g}',
                ha="center", fontsize=10.5)
        a1.text(i + w / 2, m["out_usd_per_mtok"] + 0.6, f'{m["out_usd_per_mtok"]:g}',
                ha="center", fontsize=10.5, weight="bold")
    a1.set_xticks(x, [m["name"] for m in ms], fontsize=11)
    a1.set_ylabel("美元／每百萬 token")
    a1.set_ylim(0, 58)
    a1.legend(frameon=False, fontsize=11)
    a1.set_title(f'牌價（{d["as_of"]}）：輸出比輸入貴 5 倍')

    nc = [m["example_no_cache_usd"] for m in ms]
    ca = [m["example_cached_usd"] for m in ms]
    a2.bar(x - w / 2, nc, w, label="沒開快取", color="#c23b3b")
    a2.bar(x + w / 2, ca, w, label="開了快取", color="#2f9e6e")
    for i, (n, c) in enumerate(zip(nc, ca)):
        a2.text(i - w / 2, n + 0.15, f"${n:.2f}", ha="center", fontsize=10.5)
        a2.text(i + w / 2, c + 0.15, f"${c:.2f}", ha="center", fontsize=10.5, weight="bold")
    a2.set_xticks(x, [m["name"] for m in ms], fontsize=11)
    a2.set_ylabel("美元")
    a2.set_ylim(0, max(nc) * 1.25)
    a2.legend(frameon=False, fontsize=11)
    a2.set_title(f'一份 {ex["doc_tokens"]:,} token 的文件問 {ex["questions"]} 次\n'
                 f'開快取省 {ms[0]["cache_saving_pct"]:.0f}%')

    fig.suptitle("圖 9-2　花多少錢：模型價格，以及快取能省下多少",
                 fontsize=15, weight="bold", y=1.0)
    fig.tight_layout()
    fig.text(0.01, -0.04,
             "牌價為 Anthropic 第一方 API，會變動；計算程式在 lessons/using-claude/code/models.py。"
             "快取情境假設文件不變、每次只換問題。", fontsize=9.5, color=NOTE)
    fig.savefig(OUT / "fd9-2-cost.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("寫入 fd9-2-cost")


fig_cost()


def fig_tokens():
    """使用者自己的設計系統：實際色票與驗算過的對比度。"""
    d = json.loads((CODE / "contrast.json").read_text("utf-8"))
    sw, pairs = d["swatches"], d["pairs"]
    fig = plt.figure(figsize=(13.4, 6.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1])
    a1, a2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])

    # 左：色票（每個 token 一列，淺／深兩塊）
    a1.set_xlim(0, 10)
    a1.set_ylim(0, len(sw) + 1.1)
    for i, s in enumerate(sw):
        y = len(sw) - i - 1
        for j, th in enumerate(("light", "dark")):
            if s[th]:
                a1.add_patch(plt.Rectangle((4.3 + j * 1.25, y + 0.14), 1.15, 0.72,
                                           facecolor=s[th], edgecolor="#8a93a3", lw=0.7))
        a1.text(4.2, y + 0.5, s["name"], ha="right", va="center", fontsize=11)
        a1.text(7.0, y + 0.5, (s["light"] or "").lower(), ha="left", va="center",
                fontsize=9.5, color="#5b6475", family="monospace")
    a1.text(4.87, len(sw) + 0.3, "淺色", ha="center", fontsize=11, weight="bold")
    a1.text(6.12, len(sw) + 0.3, "深色", ha="center", fontsize=11, weight="bold")
    a1.axis("off")
    c = d["counts"]
    a1.set_title(f'{c["colors"]} 個顏色 token，每個都有深淺兩種值與用途說明', fontsize=13)

    # 右：對比度
    labels = [f'{r["fg"]} / {r["bg"]}' for r in pairs]
    lt = [r["by_theme"]["light"]["ratio"] for r in pairs]
    dk = [r["by_theme"]["dark"]["ratio"] for r in pairs]
    y = np.arange(len(pairs))
    h = 0.38
    a2.barh(y + h / 2, lt, h, label="淺色", color="#2f6fb3")
    a2.barh(y - h / 2, dk, h, label="深色", color="#7b4bb3")
    a2.axvline(4.5, color="#c23b3b", lw=1.8, ls="--")
    a2.axvline(3.0, color="#d47c18", lw=1.5, ls=":")
    a2.text(4.7, -0.5, "4.5:1 一般文字", fontsize=10, color="#c23b3b", va="center")
    a2.text(2.85, -0.5, "3:1 非文字", fontsize=10, color="#d47c18", ha="right", va="center")
    a2.set_yticks(y, labels, fontsize=9.5)
    a2.set_ylim(len(pairs) - 0.4, -1.0)
    a2.set_xlabel("對比度（越高越清楚）")
    a2.set_xlim(0, 20)
    a2.legend(frameon=False, fontsize=10.5, loc="lower right")
    a2.set_title(f'{len(pairs)} 組配對，深淺兩個模式**全部通過**'.replace("**", ""), fontsize=13)

    fig.suptitle("圖 11-2　一個設計系統實際長什麼樣：你自己的 Beamup",
                 fontsize=15, weight="bold", y=1.0)
    fig.tight_layout()
    fig.text(0.01, -0.03,
             f'資料來自使用者自己的 Beamup 設計系統（{d["source"]["snapshot"]} 快照，'
             f'建自 {d["source"]["built_from"]}）；對比度由 lessons/using-claude/code/contrast.py '
             f'依 WCAG 2.x 公式重新算過，不是照抄系統裡寫的數字。',
             fontsize=9.5, color=NOTE)
    fig.savefig(OUT / "fd11-2-tokens.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("寫入 fd11-2-tokens")


fig_tokens()
