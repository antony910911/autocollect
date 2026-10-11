"""第 10 章創新思路的評估圖（本教材主觀評估，不是量測結果）。執行：python lessons/aiot-advanced/figures/src/charts.py"""

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
C = {"資料": "#2f6fb3", "模型": "#7b4bb3", "決策": "#d9821e", "現場": "#2f9e6e"}

IDEAS = [
    ("1 主動學習排實驗室採樣", 1.6, 4.3, "資料", (12, -6)),
    ("2 模擬資料預訓練＋實廠微調", 3.0, 3.9, "模型", (12, -6)),
    ("3 機理＋機器學習殘差修正", 3.3, 4.2, "模型", (12, 6)),
    ("4 狀態與參數一起估計", 3.8, 4.0, "模型", (-20, 16)),
    ("5 考慮不確定性的進料建議", 3.6, 4.5, "決策", (12, -6)),
    ("6 感測器交叉檢查網", 1.9, 3.9, "資料", (12, -6)),
    ("7 從操作員回饋學習警報", 2.0, 3.5, "決策", (12, -6)),
    ("8 進料影像辨識", 3.4, 3.4, "現場", (12, -6)),
    ("9 數位孿生情境演練", 2.6, 3.1, "現場", (12, -6)),
    ("10 儀表投資的資訊價值分析", 2.4, 4.1, "決策", (12, 6)),
]

fig, ax = plt.subplots(figsize=(12, 7))
ax.axvspan(1, 2.75, ymin=(3.75 - 2.5) / 2.5, ymax=1, color="#2f9e6e", alpha=0.07)
ax.text(1.06, 4.9, "先做這區：價值高、難度中低", color="#2f9e6e", fontsize=12, weight="bold")
for name, x, y, cat, off in IDEAS:
    ax.scatter([x], [y], s=380, color=C[cat], alpha=0.85, edgecolor="white", linewidth=1.5, zorder=3)
    ax.annotate(name, (x, y), xytext=off, textcoords="offset points", fontsize=10.5)
for cat, col in C.items():
    ax.scatter([], [], s=150, color=col, label=f"{cat}面")
ax.legend(frameon=False, loc="lower right", title="類型")
ax.set_xlim(1, 5)
ax.set_ylim(2.5, 5)
ax.set_xlabel("實施難度（資料、設備、跨領域人才）→")
ax.set_ylabel("預期價值（穩定度、產氣、決策品質）→")
ax.set_title("圖 10-1　進階建模創新思路的價值與難度（本教材主觀評估）")
fig.text(0.01, -0.03, "相對位置依第 3–8 章模擬實驗的發現與文獻推論，用來排序；實際要依你的場站條件重新評估。", fontsize=10, color="#5b6475")
fig.savefig(OUT / "fig10-1-ideas.png", bbox_inches="tight", facecolor="white")
print("寫入 fig10-1-ideas")
