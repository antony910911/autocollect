"""數據圖。所有數值讀自 code/*.json（由 tolerance.py、sizing.py 產生），不在這裡寫死。
執行：python lessons/aquatic-plants/figures/src/charts.py [圖名 ...]
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import matplotlib
import matplotlib.ticker as mt

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
OUT = Path(__file__).resolve().parent.parent
CODE = OUT.parent / "code"
for f in ("WenQuanYi Zen Hei", "Noto Sans CJK TC", "Noto Sans TC", "PingFang TC"):
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = [f, "DejaVu Sans"]
        break
plt.rcParams.update({"axes.unicode_minus": False, "mathtext.fontset": "dejavusans",
                     "font.size": 13, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "axes.axisbelow": True, "grid.color": "#e3e6ec",
                     "grid.linewidth": 0.8, "axes.edgecolor": "#8a93a3",
                     "axes.titleweight": "bold", "axes.titlesize": 15,
                     "figure.dpi": 100, "savefig.dpi": 200})

INK, MUTED, GREY = "#1d2330", "#5b6475", "#8a93a3"
BLUE, ORANGE, TEAL, PURPLE, GREEN, RED, BROWN = ("#2f6fb3", "#d47c18", "#1b8a8f", "#7b4bb3",
                                                 "#2f9e6e", "#c23b3b", "#8a6d3b")
T = json.loads((CODE / "tolerance.json").read_text("utf-8"))
S = json.loads((CODE / "sizing.json").read_text("utf-8"))


def pka(t_c):
    return 0.09018 + 2729.92 / (t_c + 273.15)


def frac(ph, t_c=25.0):
    return 1.0 / (1.0 + 10 ** (pka(t_c) - ph))


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("寫入", name)


def plain_log(ax, which="y"):
    """對數軸用一般數字，不要 10^x（上標在中文字型下會變方框）。"""
    for axis in (ax.yaxis,) if which == "y" else (ax.xaxis,):
        axis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v:g}"))
        axis.set_minor_formatter(mt.NullFormatter())


# ── 圖 3-1　安全曲線 ────────────────────────────────────────────
def fd3_1_safe_tan():
    ph = np.linspace(6.0, 9.0, 400)
    fig, ax = plt.subplots(figsize=(10, 6.0))
    for lim, color, lab in ((0.5, GREEN, "保守操作"), (2.0, ORANGE, "開始要小心"),
                            (8.0, RED, "Lemna gibba 致死")):
        ax.plot(ph, lim / frac(ph), color=color, lw=2.6,
                label=f"游離氨 ≤ {lim:g} mg N/L（{lab}）")
    ax.set_yscale("log")
    plain_log(ax, "y")
    ax.set_ylim(3, 5000)
    ax.set_xlim(6, 9)

    pts = [(7.5, 60.0, "浮萍操作上限 60", BLUE), (7.5, 200.0, "香蒲／美人蕉門檻 200", TEAL),
           (7.5, 364.0, "粉綠狐尾藻可存活 364", PURPLE)]
    for p, v, lab, c in pts:
        ax.plot([p], [v], "o", color=c, ms=8, zorder=6)
        ax.annotate(f"{lab}", (p, v), xytext=(p + 0.08, v * 1.25), fontsize=11.5, color=c,
                    arrowprops=dict(arrowstyle="-", color=c, lw=1))
    ax.annotate("pH 每上升 1，容許的總氨氮大約掉 10 倍", xy=(8.0, 37.3), xytext=(6.55, 9.5),
                fontsize=12.5, color=INK,
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.4))
    ax.set_xlabel("pH（25 °C）")
    ax.set_ylabel("容許的總氨氮 TAN（mg N/L，對數軸）")
    ax.set_title("圖 3-1　同一個耐受門檻，在不同 pH 下是完全不同的總氨氮")
    ax.legend(loc="lower left", fontsize=11.5, frameon=True, facecolor="white",
              edgecolor="#e3e6ec")
    fig.text(0.01, -0.03, "依 Emerson et al. (1975) 的 pKa 計算（25 °C）。圖上三個點的 pH 是假設值："
             "文獻摘要沒有給 pH，實際位置可能上下移動 10 倍。", fontsize=10.5, color=MUTED)
    save(fig, "fd3-1-safe-tan")


# ── 圖 3-2　文獻沒寫 pH 就沒辦法比較 ─────────────────────────
def fd3_2_tolerance():
    """同一筆 TAN 門檻，在 pH 6.5–8.0 之間換算出來的游離氨差 20 倍以上——
    比物種之間的差異還大。所以「哪一種比較耐」這個問題，文獻多半回答不了。"""
    rows = sorted([r for r in T["thresholds"] if r["tan_mgN_L"]],
                  key=lambda r: r["tan_mgN_L"])
    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(11.4, 6.0))
    for i, r in enumerate(rows):
        lo, hi = r["tan_mgN_L"] * frac(6.5), r["tan_mgN_L"] * frac(8.0)
        mid = r["tan_mgN_L"] * frac(7.5)
        color = (PURPLE if "狐尾藻" in r["zh"] else
                 TEAL if ("香蒲" in r["zh"] or "美人蕉" in r["zh"]) else
                 BLUE if "浮萍" in r["zh"] else GREY)
        ax.plot([lo, hi], [i, i], color=color, lw=9, solid_capstyle="butt", alpha=0.35)
        ax.plot([mid], [i], "o", color=color, ms=10, zorder=5)
        ax.text(30, i, f'TAN {r["tan_mgN_L"]:g}', va="center", fontsize=11, color=color)
    ax.set_xscale("log")
    plain_log(ax, "x")
    ax.set_xlim(0.02, 120)
    ax.axvline(8.0, color=RED, ls="--", lw=1.6)
    ax.text(8.6, -0.42, "浮萍致死 8", color=RED, fontsize=11, va="center")
    ax.axvline(0.5, color=GREEN, ls="--", lw=1.6)
    ax.text(0.53, -0.42, "保守操作 0.5", color=GREEN, fontsize=11, va="center")
    ax.set_yticks(y)
    ax.set_yticklabels([f'{r["zh"]}：{r["endpoint"]}' for r in rows], fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("換算成游離氨 NH₃-N（mg N/L，對數軸）")
    ax.set_title("圖 3-2　文獻沒寫 pH，就沒辦法比較「哪一種比較耐」", pad=30)
    ax.grid(axis="y", visible=False)
    fig.text(0.01, -0.03, "每一條橫帶＝同一筆門檻在 pH 6.5（左端）到 8.0（右端）之間的換算結果，"
             "圓點是 pH 7.5。一條橫帶自己就橫跨 20 倍以上，比物種之間的差距還大，而且彼此重疊。",
             fontsize=10.5, color=MUTED)
    fig.text(0.01, -0.075, "這不是在說這些研究做得不好，是在說：要比較耐受度，就得自己在固定 pH "
             "下重做一次（第 6 章給了做法）。", fontsize=10.5, color=MUTED)
    save(fig, "fd3-2-tolerance")


# ── 圖 3-3　酸化：總氨氮高 4 倍卻活得好 ─────────────────────────
def fd3_3_acid():
    d = T["acidification"]["derived"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.0))
    names = ["未調 pH\n（pH 8.2、稀釋到 5%）", "酸化後\n（pH 6.5、稀釋到 20%）"]
    tan = [d["unamended_tan"], d["acidified_tan"]]
    nh3 = [d["unamended_nh3"], d["acidified_nh3"]]
    for ax, vals, title, ylab, color in (
            (axes[0], tan, f'總氨氮：酸化組反而高 {d["tan_ratio"]:g} 倍', "TAN（mg N/L）", BLUE),
            (axes[1], nh3, f'真正有毒的游離氨：酸化組低 {d["nh3_ratio"]:g} 倍', "NH₃-N（mg N/L）", RED)):
        bars = ax.bar(names, vals, color=[GREY, color], width=0.52)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v * 1.04, f"{v:g}", ha="center",
                    fontsize=13, fontweight="bold")
        ax.set_ylim(0, max(vals) * 1.25)
        ax.set_ylabel(ylab)
        ax.set_title(title, fontsize=14)
    axes[0].text(0.5, max(tan) * 0.5, "浮萍長不起來", ha="center", color=RED, fontsize=12.5,
                 fontweight="bold")
    axes[1].text(1.0, max(nh3) * 0.55, "浮萍正成長", ha="center", color=GREEN, fontsize=12.5,
                 fontweight="bold")
    fig.suptitle("圖 3-3　同一份沼液：pH 差 1.7，結論完全相反", fontsize=15, fontweight="bold")
    fig.text(0.01, -0.04, "實驗結果來自 Aberystwyth 的研究紀錄（期刊與年份未查證）；"
             "游離氨由我們用 20 °C 的 pKa 換算。原液 TAN 由「20% 稀釋 = 239.3 mg N/L」回推為 "
             f'{d["tan_full_strength"]:g} mg N/L。', fontsize=10.5, color=MUTED)
    fig.tight_layout()
    save(fig, "fd3-3-acid")


# ── 圖 6-1　收割只佔一小部分 ───────────────────────────────────
def fd1_1_harvest():
    rows = [h for h in S["harvest"] if h.get("share_pct")]
    cw = S["cw_harvest"]
    labels = [h["zh"] for h in rows] + ["人工濕地\n（年值，低配低）", "人工濕地\n（年值，高配高）"]
    share = [h["share_pct"] for h in rows] + list(cw["share_pct_paired"])
    fig, ax = plt.subplots(figsize=(10.4, 4.6))
    y = np.arange(len(labels))
    ax.barh(y, share, color=GREEN, height=0.6, label="收割植體帶走的氮")
    ax.barh(y, [100 - s for s in share], left=share, color="#dfe3ea", height=0.6,
            label="其他路徑（根圈硝化脫硝、沉澱、揮發）")
    for i, s in enumerate(share):
        ax.text(s / 2, i, f"{s:g}%", ha="center", va="center", fontsize=12.5,
                color="white", fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=11.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("佔總氮去除量的比例（%）")
    ax.set_title("圖 1-1　「收割才算真的移除」——但收割只佔總去除的兩三成")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=11,
              frameon=False)
    ax.grid(axis="y", visible=False)
    fig.text(0.01, -0.22, "收割量＝生物量產率 × 植體含氮率（含氮率由粗蛋白 ÷ 6.25 換算）。"
             "剩下的部分不是憑空消失，而是走根圈的硝化—脫硝；要分清楚就得做質量平衡（第 1 章）。",
             fontsize=10.5, color=MUTED)
    save(fig, "fd1-1-harvest")


# ── 圖 b2-1　單位面積去除速率 ──────────────────────────────────
def fdb2_1_rates():
    rows = S["areal_rates"]
    kind_color = {"TKN 去除": BLUE, "總氮去除": BLUE, "氨氮去除": TEAL, "植物吸收": ORANGE}
    fig, ax = plt.subplots(figsize=(11, 6.4))
    y = np.arange(len(rows))
    ax.barh(y, [r["rate"] for r in rows], height=0.62,
            color=[kind_color[r["kind"]] for r in rows])
    for i, r in enumerate(rows):
        ax.text(r["rate"] + 0.06, i, f'{r["rate"]:g}', va="center", fontsize=11.5)
    ax.set_yticks(y)
    ax.set_yticklabels([r["zh"] for r in rows], fontsize=11.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 5.2)
    ax.set_xlabel("單位面積去除速率（g N/m²/d）")
    ax.set_title("圖 2-1　各種水生植物技術的單位面積去除速率")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (BLUE, TEAL, ORANGE)]
    ax.legend(handles, ["總氮／TKN 去除", "氨氮去除", "只算植物吸收"], fontsize=11,
              loc="lower right", frameon=True, facecolor="white")
    ax.grid(axis="y", visible=False)
    cc = S["coupling"]["cross_check"]
    lo, hi = cc["n_load_at_feed_60_100"]
    ax.axvspan(lo, hi, color=PURPLE, alpha=0.10)
    ax.text((lo + hi) / 2, 0.15, "魚菜共生經驗法則\n換算的氮負荷區間（第三分區第 3 章）",
            ha="center", va="top", fontsize=10.5, color=PURPLE)
    fig.text(0.01, -0.04, "同一張圖上混了三種定義（總氮去除、氨氮去除、只算植物吸收），"
             "不能直接比大小——這正是讀文獻時最容易被誤導的地方。濕地那三筆的原始數值帶著比平均還大的"
             "標準差（例如 1.13 ± 2.01），代表實場變異極大，這裡只畫了平均。", fontsize=10.5, color=MUTED)
    save(fig, "fdb2-1-rates")


# ── 圖 b2-2　三個情境要多大面積 ────────────────────────────────
def fdb2_2_area():
    keys = ["duckweed_full", "cw_hybrid", "hyacinth_opt", "cw_vf", "duckweed_pilot",
            "cw_hssf", "myrio_cw", "ftw_mean", "hyacinth_digestate", "ftw_field"]
    fig, ax = plt.subplots(figsize=(11, 6.0))
    marks = [("digestate", "o", PURPLE), ("sewage", "s", BLUE), ("ras", "^", TEAL)]
    for s in S["scenarios"]:
        m = next(m for m in marks if m[0] == s["key"])
        areas = {a["key"]: a for a in s["areas"]}
        xs = [areas[k]["area_m2"] for k in keys]
        ax.plot(xs, np.arange(len(keys)), m[1], color=m[2], ms=9, ls="none",
                label=f'{s["zh"]}（{s["load_kgN_d"]:g} kg N/d）')
    ax.set_xscale("log")
    plain_log(ax, "x")
    ax.set_yticks(np.arange(len(keys)))
    ax.set_yticklabels([next(r["zh"] for r in S["areal_rates"] if r["key"] == k) for k in keys],
                       fontsize=11.5)
    ax.invert_yaxis()
    for v, lab in ((400, "一個籃球場"), (10000, "一公頃")):
        ax.axvline(v, color=GREY, ls=":", lw=1.4)
        ax.text(v * 1.08, -0.35, lab, color=MUTED, fontsize=11, ha="left")
    ax.set_xlabel("需要的水面／床體面積（m²，對數軸）")
    ax.set_title("圖 2-2　同樣的技術，面積需求差三個數量級", pad=26)
    ax.legend(fontsize=11, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3,
              frameon=False)
    ax.grid(axis="y", visible=False)
    fig.text(0.01, -0.17, "面積 = 要去除的氮量 ÷ 單位面積速率，去除目標都設 80%。"
             "這是「理想狀態下的下限」：沒有考慮冬季降速、死角、短流與收割停機。",
             fontsize=10.5, color=MUTED)
    save(fig, "fdb2-2-area")


# ── 圖 c3-1　投餵率 → 氨氮 → 氧氣 → 鹼度 ───────────────────────
def fdc3_1_coupling():
    rows = sorted(S["coupling"]["per_m2"], key=lambda r: r["feed_g_m2_d"])
    feed = [r["feed_g_m2_d"] for r in rows]
    fig, ax = plt.subplots(figsize=(10.6, 5.8))
    ax.plot(feed, [r["tan_g_m2_d"] for r in rows], "o-", color=BLUE, lw=2.6, ms=8,
            label="氨氮產生量（g N/m²/d）")
    ax.plot(feed, [r["o2_g_m2_d"] for r in rows], "s-", color=TEAL, lw=2.6, ms=8,
            label="硝化需氧量（g O₂/m²/d）")
    ax.plot(feed, [r["alk_g_caco3_m2_d"] for r in rows], "^-", color=ORANGE, lw=2.6, ms=8,
            label="鹼度消耗（g CaCO₃/m²/d）")
    d80 = next(r for r in rows if r["feed_g_m2_d"] == 80)
    for key, color, dy in (("tan_g_m2_d", BLUE, -20), ("o2_g_m2_d", TEAL, 12),
                           ("alk_g_caco3_m2_d", ORANGE, 12)):
        ax.annotate(f'{d80[key]:g}', (80, d80[key]), xytext=(6, dy),
                    textcoords="offset points", fontsize=12, color=color, fontweight="bold")
    ax.axvspan(60, 100, color=GREY, alpha=0.10)
    ax.text(80, 22.2, "文獻建議的投餵率區間（浮筏式 60–100），常用設計值 80", ha="center",
            fontsize=11.5, color=MUTED)
    ax.set_xlabel("投餵率（g 飼料 / m² 植栽面積 / 天）")
    ax.set_ylabel("每平方公尺植栽面積每天")
    ax.set_title("圖 3-1　投餵多少飼料，就要準備多少氧氣與鹼度", pad=30)
    ax.legend(fontsize=11.5, loc="upper left", frameon=False)
    ax.set_xlim(50, 108)
    ax.set_ylim(0, 23)
    fig.text(0.01, -0.04, "氨氮用 PTAN = 飼料 × 蛋白比例 × 0.092（Ebeling et al. 2006，飼料蛋白設 32%）；"
             "需氧量 4.57 g O₂/g N 與鹼度 7.14 g CaCO₃/g N 是我們自己依硝化反應式算的，"
             "不是查表值。", fontsize=10.5, color=MUTED)
    save(fig, "fdc3-1-coupling")


FIGS = {"fd3-1-safe-tan": fd3_1_safe_tan, "fd3-2-tolerance": fd3_2_tolerance,
        "fd3-3-acid": fd3_3_acid, "fd1-1-harvest": fd1_1_harvest,
        "fdb2-1-rates": fdb2_1_rates, "fdb2-2-area": fdb2_2_area,
        "fdc3-1-coupling": fdc3_1_coupling}

if __name__ == "__main__":
    want = sys.argv[1:] or list(FIGS)
    for k in want:
        if k in FIGS:
            FIGS[k]()
