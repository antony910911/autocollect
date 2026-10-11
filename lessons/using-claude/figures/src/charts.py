"""模型價格與快取的實際成本圖。執行：python lessons/using-claude/figures/src/charts.py"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
OUT = Path(__file__).resolve().parent.parent
CODE = OUT.parent / "code"
for f in ("WenQuanYi Zen Hei", "Noto Sans CJK TC", "PingFang TC", "Microsoft JhengHei"):
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
    a1.bar(x + w / 2, [m["out_usd_per_mtok"] for m in ms], w, label="輸出", color="#d9821e")
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
