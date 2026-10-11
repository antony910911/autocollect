"""AIoT 教材的數據圖。標示「示意」的是模擬數據；案例定位與創新評估是本教材的判斷，不是量測結果。
執行：python lessons/aiot/figures/src/charts.py
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
OUT = Path(__file__).resolve().parent.parent
for f in ("WenQuanYi Zen Hei", "Noto Sans CJK TC", "PingFang TC", "Microsoft JhengHei"):
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = [f, "DejaVu Sans"]
        break
plt.rcParams.update({"axes.unicode_minus": False, "mathtext.fontset": "dejavusans", "font.size": 13,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True,
                     "grid.color": "#e3e6ec", "grid.linewidth": 0.8, "axes.edgecolor": "#8a93a3",
                     "axes.titleweight": "bold", "axes.titlesize": 15, "savefig.dpi": 200})
SENSE, NET, DATA, AI, ACT, HUMAN, RISK, INK = ("#2f6fb3", "#6b7280", "#7b4bb3", "#d9821e", "#2f9e6e", "#8a6d3b",
                                               "#c23b3b", "#1d2330")
NOTE = "#5b6475"


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("寫入", name)


def sig(t, t0, k):
    return 1 / (1 + np.exp(-(t - t0) / k))


def fig2_2_early_warning():
    t = np.linspace(0, 30, 600)
    rng = np.random.default_rng(1)
    vfa = 600 + 3400 * sig(t, 15, 1.6) + rng.normal(0, 40, t.size)
    fostac = 0.25 + 0.45 * sig(t, 15.5, 1.6)
    ph = 7.4 - 0.9 * sig(t, 21, 1.2) + rng.normal(0, 0.015, t.size)
    gas = 100 - 55 * sig(t, 22, 1.4) + rng.normal(0, 1.2, t.size)
    fig, axes = plt.subplots(4, 1, figsize=(11, 8.4), sharex=True)
    series = [(vfa, "VFA（mg/L）", RISK), (fostac, "FOS/TAC", AI), (ph, "pH", SENSE), (gas, "產氣量（%）", ACT)]
    for ax, (y, lab, col) in zip(axes, series):
        ax.plot(t, y, color=col, lw=2.2)
        ax.set_ylabel(lab, rotation=0, ha="right", va="center", labelpad=10)
        ax.axvspan(10, 12, color=NET, alpha=0.12)
    axes[0].text(10.2, 3600, "進料過量開始", fontsize=11, color=NET)
    axes[0].annotate("① 酸先累積", (14.5, 2200), xytext=(3, 2600), fontsize=12, color=RISK,
                     arrowprops=dict(arrowstyle="->", color=RISK))
    axes[1].axhline(0.4, color=AI, ls="--", lw=1)
    axes[1].text(0.3, 0.42, "常見警戒參考 0.4（依廠而異）", fontsize=10, color=AI)
    axes[2].annotate("② pH 很晚才掉（鹼度緩衝）", (20.5, 7.1), xytext=(3, 6.75), fontsize=12, color=SENSE,
                     arrowprops=dict(arrowstyle="->", color=SENSE))
    axes[3].annotate("③ 產氣下降時\n往往已經來不及", (22, 72), xytext=(25, 88), fontsize=12, color=ACT,
                     arrowprops=dict(arrowstyle="->", color=ACT))
    axes[3].set_xlabel("天數")
    fig.suptitle("圖 2-2　消化槽酸化時，各指標反應的先後（示意數據）", fontsize=15, weight="bold")
    fig.text(0.01, -0.02, "示意：真實時間尺度依負荷與緩衝能力而定。重點是 VFA 與 FOS/TAC 領先 pH 與產氣，而它們通常只能每天或每週離線量測。"
             "\n依 Drosg (2013)、Jimenez et al. (2015) 對監測指標的說明繪製。", fontsize=10, color=NOTE)
    save(fig, "fig2-2-early-warning")


def fig4_1_cases():
    cases = [
        # (名稱, 類別列, 等級, 說明)
        ("屏東中央畜牧場\n沼氣發電", 0, 1.3, -48),
        ("小型養豬場智慧沼氣\n雲端監控（研究）", 0, 2.0, 18),
        ("宜蘭養豬場 IoT＋\n豬隻影像 AI（臺大）", 0, 2.6, -48),
        ("台中外埔\n廚餘厭氧發電", 1, 1.6, 18),
        ("中國 4 座乾式廚餘槽\nML 預測＋VFA/ALK 軟感測", 1, 3.35, 18),
        ("德國彈性沼氣發電（依電價排程，\n多為規則與最佳化，不一定用 AI）", 1, 2.75, -48),
        ("桃園水資中心\n雲端統合平台", 2, 2.1, -48),
        ("竹東水資中心\n智慧水務（工研院）", 2, 3.6, 18),
        ("臺南永康水資中心\n5G AIoT 數位雙生", 2, 3.9, -48),
        ("Veolia Hubgrade\n（線上數位雙生）", 2, 4.25, 18),
    ]
    rows = ["養豬場", "沼氣廠／生質能中心", "污水處理廠"]
    cols = [HUMAN, ACT, SENSE]
    fig, ax = plt.subplots(figsize=(13, 6.6))
    for name, r, lv, dy in cases:
        ax.scatter([lv], [r], s=260, color=cols[r], zorder=3, edgecolor="white", linewidth=1.5)
        ax.annotate(name, (lv, r), xytext=(0, dy), textcoords="offset points",
                    ha="center", fontsize=10.5, color=INK)
    ax.axvline(3, color=RISK, ls="--", lw=1.4)
    ax.text(3.03, 2.62, "← IoT｜AIoT →", color=RISK, fontsize=12)
    ax.set_yticks(range(3), rows)
    ax.set_xticks([0, 1, 2, 3, 4, 5], ["L0\n人工", "L1\n自動化", "L2\n連網可視化", "L3\n分析預測", "L4\n建議與閉迴路",
                                       "L5\n自主運轉"])
    ax.set_xlim(0.6, 5.1)
    ax.set_ylim(-0.6, 2.8)
    ax.grid(axis="y", visible=False)
    ax.set_title("圖 4-1　國內外案例大約落在哪一級（本教材依公開資料判斷）")
    fig.text(0.01, -0.04, "位置是依各案例公開描述的功能推估，不是官方評等；同一場站不同單元的成熟度可能不同。"
             "\n廠商宣稱的效益多半未經第三方驗證。來源見第 4 章各案例。", fontsize=10, color=NOTE)
    save(fig, "fig4-1-case-map")


def fig5_2_soft_sensor():
    rng = np.random.default_rng(4)
    t = np.linspace(0, 60, 1200)
    true = 900 + 500 * np.sin(t / 7) + 1400 * np.exp(-((t - 40) / 3.5) ** 2)
    soft = true + rng.normal(0, 90, t.size)
    soft = np.convolve(soft, np.ones(25) / 25, mode="same")
    lab_t = np.arange(2, 60, 7.0)
    lab = np.interp(lab_t, t, true) + rng.normal(0, 60, lab_t.size)
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(t, true, color=NET, lw=1.2, alpha=0.6, label="槽內真實 VFA（實際上看不到）")
    ax.plot(t, soft, color=AI, lw=2.2, label="軟感測估計（每 10 分鐘更新）")
    ax.plot(lab_t, lab, "o", color=RISK, ms=9, label="實驗室分析（每週一次）")
    ax.annotate("每週採樣剛好錯過\n這次酸累積", (40, 2300), xytext=(46, 2500), fontsize=12, color=RISK,
                arrowprops=dict(arrowstyle="->", color=RISK))
    ax.set_xlabel("天數")
    ax.set_ylabel("VFA（mg/L）")
    ax.set_ylim(0, 3000)
    ax.legend(frameon=False, loc="upper left", fontsize=11)
    ax.set_title("圖 5-2　軟感測的價值：用連續訊號補上稀疏的實驗室數據（示意數據）")
    fig.text(0.01, -0.06, "軟感測（soft sensor）用 pH、產氣量、氣體組成、進料等便宜的線上訊號推估難量的指標；"
             "仍需定期用實驗室數據校正。", fontsize=10, color=NOTE)
    save(fig, "fig5-2-soft-sensor")


def fig8_1_ideas():
    ideas = [
        ("A 微生物早期預警\n（qPCR／定序＋ML）", 3.6, 4.0, DATA),
        ("B 原料快篩＋\n進料配方最佳化", 2.8, 4.3, AI),
        ("C ADM1 數位孿生\n＋資料同化", 3.9, 4.4, DATA),
        ("D 依電價調度的\n彈性沼氣發電", 2.6, 3.9, ACT),
        ("E 甲烷逸散監測\n＋碳權 MRV", 2.3, 3.6, RISK),
        ("F LLM 操作助理\n（SOP＋唯讀數據）", 1.6, 3.25, AI),
        ("G 聲音／影像偵測\n起泡與攪拌異常", 2.45, 2.95, SENSE),
        ("H 養豬場聯盟\n聯邦學習", 3.7, 3.2, HUMAN),
        ("I 沼液施灌\n追溯與氨揮發估算", 2.0, 2.7, ACT),
    ]
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.axvspan(1, 3, ymin=(3.5 - 2) / 3, ymax=1, color=ACT, alpha=0.07)
    ax.text(1.1, 4.82, "先做這區：價值高、難度中低", color=ACT, fontsize=12, weight="bold")
    for name, x, y, c in ideas:
        ax.scatter([x], [y], s=420, color=c, alpha=0.85, edgecolor="white", linewidth=1.5, zorder=3)
        ax.annotate(name, (x, y), xytext=(14, -8), textcoords="offset points", fontsize=10.5)
    ax.set_xlim(1, 5)
    ax.set_ylim(2, 5)
    ax.set_xlabel("實施難度（資料、設備、跨領域整合）→")
    ax.set_ylabel("預期價值（穩定度、收益、減碳）→")
    ax.set_title("圖 8-1　創新思路的價值與難度（本教材主觀評估）")
    fig.text(0.01, -0.03, "評分為本教材依文獻與案例推論的相對位置，用來幫助排序，不是量化結果。實際排序要依你的場站條件重新評估。",
             fontsize=10, color=NOTE)
    save(fig, "fig8-1-ideas")


if __name__ == "__main__":
    for fn in (fig2_2_early_warning, fig4_1_cases, fig5_2_soft_sensor, fig8_1_ideas):
        fn()
