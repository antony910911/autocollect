"""第 13 章創新思路的評估圖（本教材主觀評估，不是量測結果）。執行：python lessons/dna-to-culture/figures/src/charts.py"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
OUT = Path(__file__).resolve().parent.parent
for f in ("WenQuanYi Zen Hei", "Noto Sans CJK TC", "PingFang TC", "Microsoft JhengHei"):
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = [f, "DejaVu Sans"]
        break
plt.rcParams.update({"axes.unicode_minus": False, "font.size": 12, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True, "grid.color": "#e3e6ec",
                     "axes.edgecolor": "#8a93a3", "axes.titleweight": "bold", "axes.titlesize": 14,
                     "savefig.dpi": 200})
C = {"實驗策略": "#2f6fb3", "模型": "#7b4bb3", "培養基": "#d9821e", "平台": "#2f9e6e"}

IDEAS = [
    ("1 模型當先驗的貝氏最適化", 2.6, 4.4, "實驗策略", (12, -6)),
    ("2 指標觸發的自動切換", 2.0, 4.1, "實驗策略", (12, -6)),
    ("3 培養的數位孿生", 3.6, 4.2, "模型", (12, -6)),
    ("4 模型決定取樣時間", 1.8, 3.6, "實驗策略", (12, -6)),
    ("5 基因體預測基點值當起點", 2.2, 3.3, "模型", (12, -6)),
    ("6 最低成本培養基（在地副產物）", 2.5, 4.0, "培養基", (12, -20)),
    ("7 共培養設計", 4.3, 3.9, "模型", (-60, 16)),
    ("8 溫度相依的酵素限制模型", 4.5, 3.5, "模型", (-200, -16)),
    ("9 實驗室知識庫＋AI 助理", 1.6, 3.9, "平台", (12, 6)),
]

fig, ax = plt.subplots(figsize=(12, 7))
ax.axvspan(1, 2.8, ymin=(3.8 - 3.0) / 2.0, ymax=1, color="#2f9e6e", alpha=0.07)
ax.text(1.06, 4.9, "先做這區：價值高、難度中低", color="#2f9e6e", fontsize=12, weight="bold")
for name, x, y, cat, off in IDEAS:
    ax.scatter([x], [y], s=380, color=C[cat], alpha=0.85, edgecolor="white", linewidth=1.5, zorder=3)
    ax.annotate(name, (x, y), xytext=off, textcoords="offset points", fontsize=10.5)
for cat, col in C.items():
    ax.scatter([], [], s=150, color=col, label=cat)
ax.legend(frameon=False, loc="lower left", title="類型")
ax.set_xlim(1, 5)
ax.set_ylim(3.0, 5)
ax.set_xlabel("實施難度（設備、資料、跨領域人才）→")
ax.set_ylabel("預期價值（省實驗、提高產量、可發表性）→")
ax.set_title("圖 13-1　創新思路的價值與難度（本教材主觀評估）")
fig.text(0.01, -0.03, "相對位置依第 4–9 章模擬實驗的發現與文獻推論，用來排序；實際要依你的菌株、設備與團隊重新評估。", fontsize=10,
         color="#5b6475")
fig.savefig(OUT / "fig13-1-ideas.png", bbox_inches="tight", facecolor="white")
print("寫入 fig13-1-ideas")
