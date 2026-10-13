"""第 14 章創新思路的評估圖（本教材主觀評估，不是量測結果）。執行：python lessons/dna-to-culture/figures/src/charts.py"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_tools"))
from mplstyle import apply as _apply_house_style  # noqa: E402
_apply_house_style()   # 先裝好 Noto Sans TC 並設定共同樣式；下面的 rcParams 可再覆蓋
OUT = Path(__file__).resolve().parent.parent
for f in ("Noto Sans TC", "WenQuanYi Zen Hei", "Noto Sans CJK TC",
          "PingFang TC", "Microsoft JhengHei"):
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = [f, "DejaVu Sans"]
        break
plt.rcParams.update({"axes.unicode_minus": False, "font.size": 12, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True, "grid.color": "#e3e6ec",
                     "axes.edgecolor": "#8a93a3", "axes.titleweight": "bold", "axes.titlesize": 14,
                     "savefig.dpi": 200})
C = {"實驗策略": "#2f6fb3", "模型": "#7b4bb3", "培養基": "#d47c18", "平台": "#2f9e6e"}

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
ax.set_title("圖 14-1　創新思路的價值與難度（本教材主觀評估）")
fig.text(0.01, -0.03, "相對位置依第 4–9 章模擬實驗的發現與文獻推論，用來排序；實際要依你的菌株、設備與團隊重新評估。", fontsize=10,
         color="#5b6475")
fig.savefig(OUT / "fig14-1-ideas.png", bbox_inches="tight", facecolor="white")
print("寫入 fig14-1-ideas")


# ───────── 第 16 章：基改菌株的生產包絡線（真實計算） ─────────
def fig_envelope():
    import json
    import numpy as np
    E = json.loads((OUT.parent / "code" / "engineered.json").read_text("utf-8"))
    BLUE, PURPLE, GREEN, GREY, RED, INK = "#2f6fb3", "#7b4bb3", "#2f9e6e", "#8a93a3", "#c23b3b", "#1d2330"
    NOTE = "#5b6475"
    CN = ("計算結果：COBRApy＋大腸桿菌核心模型（E. coli core）。這裡示範的是「把基改變成反應、再看生產包絡線」的方法；"
          "換成酵母菌模型（Yeast8）步驟完全相同。程式在 lessons/dna-to-culture/code/engineered.py。")
    strains = [s for s in E["strains"] if s.get("feasible")]
    cols = [GREY, BLUE, PURPLE, GREEN]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.5, 5.4), gridspec_kw={"width_ratios": [1.25, 1]})
    for s, c in zip(strains, cols):
        mu = [r["mu"] for r in s["rows"]]
        lo = [r["yield_lo"] for r in s["rows"]]
        hi = [r["yield_hi"] for r in s["rows"]]
        a1.fill_between(mu, lo, hi, color=c, alpha=0.16)
        a1.plot(mu, hi, color=c, lw=2.2)
        a1.plot(mu, lo, color=c, lw=2.6, ls="--")
        a1.scatter([s["mu_max"]], [s["at_mu_max"]["yield_hi"]], color=c, s=75, zorder=5, edgecolor="white")
        a1.plot([], [], color=c, lw=2.4, label=s["label"])
    a1.set_xlabel("生長速率 μ（1/h）")
    a1.set_ylabel("乙醇產率（mol / mol 葡萄糖）")
    a1.set_title("生產包絡線：實線＝最多能產，虛線＝最少會產")
    a1.legend(frameon=False, loc="lower left", fontsize=10.5)
    a1.set_ylim(0, 2.15)
    a1.axhline(2.0, color=INK, ls=":", lw=1.2)
    a1.text(0.004, 2.03, "理論上限 2.0 mol/mol", fontsize=10, color=NOTE)
    a1.annotate("野生型在半速生長時\n可以完全不產乙醇", (strains[0]["at_half"]["mu"], 0.02),
                xytext=(0.055, 0.55), fontsize=10.5, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED))
    labels = [s["label"] for s in strains]
    mins = [s["at_half"]["yield_lo"] for s in strains]
    a2.bar(range(len(strains)), mins, color=[GREEN if m > 0.01 else RED for m in mins])
    for i, m in enumerate(mins):
        a2.text(i, m + 0.025, f"{m:.2f}" if m > 0.005 else "0（不耦合）", ha="center", fontsize=10.5,
                weight="bold" if m > 0.005 else "normal", color=INK if m > 0.005 else RED)
    a2.set_xticks(range(len(strains)), [l.replace(" ", "\n") for l in labels], fontsize=10)
    a2.set_ylabel("半速生長時「最少」的乙醇產率\n（mol/mol）")
    a2.set_title("成長耦合：細胞不產乙醇就長不了")
    a2.set_ylim(0, max(mins) * 1.35 + 0.05)
    fig.suptitle("圖 2-3　基改菌株的評估：把剔除的基因放進模型，看產物能不能「被迫」生成",
                 fontsize=15, weight="bold", y=1.0)
    fig.tight_layout()
    fig.text(0.01, -0.03, CN, fontsize=9.5, color=NOTE)
    fig.savefig(OUT / "fdr2-3-envelope.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("寫入 fd16-3-envelope")


fig_envelope()
