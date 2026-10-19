"""BMB171 PHB 的數據圖。執行：python lessons/bmb171-phb/figures/src/charts.py

數字全部來自 code/checks.json（由 code/checks.py 產生）。
"""

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

_apply_house_style()
OUT = Path(__file__).resolve().parent.parent
CODE = OUT.parent / "code"
for f in ("Noto Sans TC", "WenQuanYi Zen Hei", "Noto Sans CJK TC",
          "PingFang TC", "Microsoft JhengHei"):
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = [f, "DejaVu Sans"]
        break
plt.rcParams.update({"axes.unicode_minus": False, "mathtext.fontset": "dejavusans",
                     "font.size": 13, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "axes.axisbelow": True, "grid.color": "#e3e6ec",
                     "axes.edgecolor": "#8a93a3", "axes.titleweight": "bold",
                     "axes.titlesize": 15, "savefig.dpi": 200})

INK, MUTED = "#1d2330", "#5b6475"
BLUE, ORANGE, RED, GREEN, PURPLE, TEAL = ("#2f6fb3", "#d47c18", "#c23b3b",
                                          "#2f9e6e", "#7b4bb3", "#1b8a8f")
D = json.loads((CODE / "checks.json").read_text("utf-8"))


def fig_tradeoff():
    """左：產率與氧需求隨生長上升怎麼變。右：每多讓 5% 生長，PHB 掉多少。"""
    rows = D["tradeoff"]
    x = np.array([r["growth_fraction"] for r in rows]) * 100
    y = np.array([r["phb_yield_g_g"] for r in rows])
    o2 = np.array([r["o2_uptake_reported"] for r in rows])
    ceiling = D["ceiling"]["mass_yield_g_g"]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.0, 5.0),
                                 gridspec_kw={"width_ratios": [1.15, 1]})

    a1.plot(x, y, "-o", color=TEAL, lw=2.6, ms=7, label="PHB 產率", zorder=4)
    a1.axvspan(10, 25, color=GREEN, alpha=0.11, zorder=0)
    a1.axvline(60, color=RED, ls="--", lw=1.8, zorder=1)
    a1.set_xlabel("生長速率（佔最大生長速率 μmax 的百分比）")
    a1.set_ylabel("PHB 產率（g PHB / g 葡萄糖）", color=TEAL)
    a1.tick_params(axis="y", labelcolor=TEAL)
    a1.set_ylim(-0.03, ceiling * 1.18)
    a1.set_xlim(-4, 104)
    a1.set_title("讓菌長得越快，PHB 產率掉越多")

    a1b = a1.twinx()
    a1b.plot(x, o2, "-s", color=ORANGE, lw=2.0, ms=6, alpha=0.9, label="氧需求")
    a1b.set_ylabel("氧攝取（mmol/gDW/h）", color=ORANGE)
    a1b.tick_params(axis="y", labelcolor=ORANGE)
    a1b.grid(False)
    a1b.spines["top"].set_visible(False)
    a1b.set_ylim(0, 56)

    a1.axhline(ceiling, color=MUTED, ls=":", lw=1.4, zorder=1)
    a1.text(44, ceiling + 0.013, f"化學計量上限 {ceiling:.3f}", fontsize=11.5,
            color=MUTED, va="bottom", ha="left")
    a1.annotate("甜蜜區 10–25% μmax\n保住 86–94% 上限", xy=(18, 0.527),
                xytext=(31, 0.295), fontsize=12, color=GREEN, weight="bold",
                ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.6))
    a1.text(61.5, 0.055, "60% 之後\n掉得快 3 倍", fontsize=12, color=RED,
            weight="bold", ha="left", va="bottom")
    h1, l1 = a1.get_legend_handles_labels()
    h2, l2 = a1b.get_legend_handles_labels()
    a1.legend(h1 + h2, l1 + l2, loc="upper right", frameon=False, fontsize=12)

    sl = D["phb_slope_per_5pct"]
    labels = [f"{s['from']:.0%}→{s['to']:.0%}" for s in sl]
    vals = [s["per_5pct"] for s in sl]
    cols = [RED if v > 0.7 else (ORANGE if v > 0.45 else TEAL) for v in vals]
    bars = a2.bar(range(len(vals)), vals, color=cols, width=0.68)
    for b, v in zip(bars, vals):
        a2.text(b.get_x() + b.get_width() / 2, v + 0.03, f"{v:.2f}",
                ha="center", va="bottom", fontsize=11.5, color=INK, weight="bold")
    a2.set_xticks(range(len(labels)))
    a2.set_xticklabels(labels, fontsize=10.5, rotation=38, ha="right")
    a2.set_ylabel("每多讓 5% μmax，PHB 通量掉多少\n（mmol/gDW/h）")
    a2.set_ylim(0, 1.22)
    a2.set_title("轉折點在 60%，不是 55%")
    a2.text(0.03, 0.93, "0–55% 每一格都剛好掉 0.36（線性）",
            transform=a2.transAxes, fontsize=11.5, color=TEAL, weight="bold")

    fig.tight_layout()
    return fig


def fig_carbon():
    """0.5973 g/g 比課本路徑高 1.25 倍——這個差距要講清楚。"""
    c = D["ceiling"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.0, 4.6),
                                 gridspec_kw={"width_ratios": [1, 1.1]})

    names = ["課本路徑\n（走 PDH，丟 2 個 CO₂）", "這個模型算出來的\n化學計量上限"]
    vals = [c["textbook_mass_yield_g_g"], c["mass_yield_g_g"]]
    bars = a1.barh(names, vals, color=[MUTED, PURPLE], height=0.38)
    for b, v, m in zip(bars, vals, [c["textbook_mol_per_mol"], c["mol_per_mol_glucose"]]):
        a1.text(v + 0.012, b.get_y() + b.get_height() / 2,
                f"{v:.4f} g/g\n（{m:g} mol/mol）", va="center", fontsize=12,
                color=INK, weight="bold")
    a1.set_xlim(0, 0.84)
    a1.set_xlabel("PHB 產率上限（g PHB / g 葡萄糖）")
    a1.set_title(f"模型的上限是課本的 {c['ratio_to_textbook']:g} 倍")
    a1.grid(axis="y", visible=False)
    a1.tick_params(axis="y", labelsize=12)

    # 碳帳：一分子葡萄糖的 6 個碳去哪裡
    width = 0.58
    xs = [0, 1]
    into = [c["textbook_carbon_recovery"] * 6, c["carbon_recovery"] * 6]
    lost = [6 - v for v in into]
    a2.bar(xs, into, width, color=TEAL, label="變成 PHB 的碳")
    a2.bar(xs, lost, width, bottom=into, color="#d9dde5", label="變成 CO₂ 的碳")
    for xi, v in zip(xs, into):
        a2.text(xi, v / 2, f"{v:.1f} 個碳\n{v / 6:.1%}", ha="center", va="center",
                fontsize=12.5, color="white", weight="bold")
        a2.text(xi, v + (6 - v) / 2, f"{6 - v:.1f} 個碳", ha="center", va="center",
                fontsize=12, color=MUTED, weight="bold")
    a2.set_xticks(xs)
    a2.set_xticklabels(["課本路徑", "這個模型"], fontsize=12.5)
    a2.set_ylabel("一分子葡萄糖的 6 個碳")
    a2.set_ylim(0, 7.2)
    a2.set_title("模型保住了 5 個碳——它沒走丟 CO₂ 的那條路")
    a2.legend(loc="upper center", ncol=2, frameon=False, fontsize=12)
    a2.grid(axis="x", visible=False)

    fig.tight_layout()
    return fig


def fig_nitrogen():
    """氮需求和生長完全線性；代謝 C/N 是結果，不是你能直接旋的鈕。"""
    rows = [r for r in D["tradeoff"] if r["metabolic_c_n"]]
    x = np.array([r["growth_fraction"] for r in rows]) * 100
    n = np.array([r["nh4_required"] for r in rows])
    cn = np.array([r["metabolic_c_n"] for r in rows])

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.0, 4.6))

    a1.plot(x, n, "-o", color=BLUE, lw=2.6, ms=7)
    k = D["basis"]["nh4_per_mu"]
    a1.set_xlabel("生長速率（佔 μmax 的百分比）")
    a1.set_ylabel("需要的氨氮 q(NH₄)\n（mmol/gDW/h）", color=BLUE)
    a1.tick_params(axis="y", labelcolor=BLUE)
    a1.set_title("氮需求完全跟著生長走")
    a1.text(0.04, 0.88, f"q(NH₄) = {k} × μ\n一條直線，沒有例外",
            transform=a1.transAxes, fontsize=12.5, color=BLUE, weight="bold")
    a1.text(0.04, 0.70, "→ 氮沒有直接參與 PHB 合成",
            transform=a1.transAxes, fontsize=12, color=MUTED)

    a2.plot(x, cn, "-o", color=ORANGE, lw=2.6, ms=7)
    a2.axvspan(10, 25, color=GREEN, alpha=0.13)
    a2.set_xlabel("生長速率（佔 μmax 的百分比）")
    a2.set_ylabel("代謝 C/N（mol 碳 / mol 氮）")
    a2.set_ylim(0, 140)
    a2.set_title("代謝 C/N 是算出來的結果，不是培養基配方")
    a2.text(30, 88, "甜蜜區對應\n代謝 C/N 約 50–126", fontsize=12.5,
            color=GREEN, weight="bold", va="center")
    a2.annotate("", xy=(11, 125.6), xytext=(28, 96),
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.6))

    fig.tight_layout()
    return fig


FIGS = {"fig3-1-tradeoff": fig_tradeoff, "fig1-2-carbon": fig_carbon,
        "fig3-2-nitrogen": fig_nitrogen}

if __name__ == "__main__":
    want = sys.argv[1:] or list(FIGS)
    OUT.mkdir(parents=True, exist_ok=True)
    for name in want:
        if name not in FIGS:
            continue
        fig = FIGS[name]()
        fig.savefig(OUT / f"{name}.png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print("寫入", name)
