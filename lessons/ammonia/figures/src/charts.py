"""教材的數據圖。公式來源寫在各函式說明；標示「示意」的圖是模擬數據，只用來說明判讀方式。
執行：python lessons/ammonia/figures/src/charts.py
"""

from __future__ import annotations

from pathlib import Path

import logging

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
OUT = Path(__file__).resolve().parent.parent
for f in ("WenQuanYi Zen Hei", "Noto Sans CJK TC", "PingFang TC", "Microsoft JhengHei"):
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = [f, "DejaVu Sans"]  # DejaVu 補上標 ⁺⁻ 等符號
        break
plt.rcParams.update({"axes.unicode_minus": False, "mathtext.fontset": "dejavusans", "font.size": 13, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True, "grid.color": "#e3e6ec", "grid.linewidth": 0.8,
                     "axes.edgecolor": "#8a93a3", "axes.titleweight": "bold", "axes.titlesize": 15,
                     "figure.dpi": 100, "savefig.dpi": 200})
NH4, NO2, NO3, N2, ORG, AMX, GREY, INK = ("#2f6fb3", "#d9821e", "#c23b3b", "#2f9e6e", "#8a6d3b", "#7b4bb3",
                                          "#8a93a3", "#1d2330")


def pka(t_c):
    """Emerson et al. (1975)：pKa = 0.09018 + 2729.92 / T（K）"""
    return 0.09018 + 2729.92 / (t_c + 273.15)


def nh3_fraction(ph, t_c):
    return 1 / (1 + 10 ** (pka(t_c) - ph))


def free_ammonia(tan, ph, t_c):
    """Anthonisen et al. (1976)：FA（mg NH3/L）= 17/14 × TAN × 10^pH / (exp(6334/(273+T)) + 10^pH)"""
    return 17 / 14 * tan * 10 ** ph / (np.exp(6334 / (273 + t_c)) + 10 ** ph)


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("寫入", name)


def fig1_2_fraction():
    ph = np.linspace(6, 12, 400)
    fig, ax = plt.subplots(figsize=(10, 5.6))
    temps = [(10, "#9fc3e6"), (20, "#5f9bd3"), (25, NH4), (30, "#1d4f86"), (35, "#0f2e52")]
    for t, c in temps:
        ax.plot(ph, nh3_fraction(ph, t) * 100, color=c, lw=2.6 if t == 25 else 1.6,
                label=f"{t} °C（pKa {pka(t):.2f}）")
    for p in (7, 8, 9):
        v = nh3_fraction(p, 25) * 100
        ax.plot([p], [v], "o", color=NO3, zorder=5)
        ax.annotate(f"pH {p}：{v:.1f}%", (p, v), xytext=(p + 0.35 if p == 9 else p - 0.95, v - 14 if p == 9 else v + 12), fontsize=12, color=NO3,
                    arrowprops=dict(arrowstyle="-", color=NO3, lw=1))
    ax.axhline(50, color=GREY, ls="--", lw=1)
    ax.text(6.05, 52, "50%：pH = pKa（25 °C 約 9.25）", color=GREY, fontsize=11)
    ax.axvspan(6.5, 8.5, color="#2f9e6e", alpha=0.07)
    ax.text(7.5, 92, "生物處理常見 pH 範圍\n多數是 NH₄⁺", ha="center", fontsize=11, color=N2)
    ax.axvspan(10.5, 12, color=GREY, alpha=0.08)
    ax.text(11.25, 30, "氣提操作範圍\n多數是 NH₃", ha="center", fontsize=11, color=INK)
    ax.set_xlabel("pH")
    ax.set_ylabel("NH₃ 佔總氨氮的比例（%）")
    ax.set_xlim(6, 12)
    ax.set_ylim(0, 100)
    ax.set_title("圖 1-2　游離氨（NH₃）比例隨 pH 與溫度變化")
    ax.legend(loc="upper left", fontsize=10.5, frameon=False, bbox_to_anchor=(0, 0.86))
    fig.text(0.01, -0.02, "依 Emerson et al. (1975) 公式計算（淡水、低離子強度）。海水或高鹽廢水的 pKa 會略高，NH₃ 比例略低。",
             fontsize=10, color="#5b6475")
    save(fig, "fig1-2-nh3-fraction")


def fig1_3_anthonisen():
    ph = np.linspace(6.5, 9.5, 300)
    t = 20
    fig, ax = plt.subplots(figsize=(10, 6))

    def tan_for(fa):
        return fa * 14 / 17 * (np.exp(6334 / (273 + t)) + 10 ** ph) / 10 ** ph

    lo, hi = 1, 3000
    b01, b1, b10, b150 = (np.clip(tan_for(v), lo, hi) for v in (0.1, 1.0, 10, 150))
    ax.fill_between(ph, lo, b01, color=N2, alpha=0.18, label="FA < 0.1：硝化可完整進行")
    ax.fill_between(ph, b01, b1, color=NO2, alpha=0.28, label="FA 0.1–1：NOB 開始受抑制 → NO₂⁻ 累積")
    ax.fill_between(ph, b1, b10, color=NO2, alpha=0.12, label="FA 1–10：NOB 受抑制，AOB 仍可作用")
    ax.fill_between(ph, b10, b150, color=NO3, alpha=0.18, label="FA 10–150：AOB 也開始受抑制")
    ax.fill_between(ph, b150, hi, color=NO3, alpha=0.36, label="FA > 150：硝化幾乎停止")
    for v, b in ((0.1, b01), (1, b1), (10, b10), (150, b150)):
        ax.plot(ph, b, color=INK, lw=0.8)
        i = int(np.argmin(np.abs(b - 4 * v ** 0.5 * 10)))  # 找線條落在圖內的位置放標籤
        i = min(max(i, 10), len(ph) - 60)
        ax.text(ph[i], b[i] * 1.15, f"FA = {v:g} mg/L", fontsize=10, color=INK, rotation=-24)
    ax.plot([7.5, 8.5], [50, 50], "s", color=NH4)
    fa75, fa85 = free_ammonia(50, 7.5, t), free_ammonia(50, 8.5, t)
    ax.annotate(f"同樣 50 mg N/L：\npH 7.5 → FA ≈ {fa75:.1f} mg/L\npH 8.5 → FA ≈ {fa85:.0f} mg/L\npH 升 1，FA 約增 10 倍", (8.5, 50),
                xytext=(8.6, 4), fontsize=11, color=NH4, arrowprops=dict(arrowstyle="->", color=NH4))
    ax.set_yscale("log")
    ax.set_ylim(lo, hi)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlim(6.5, 9.5)
    ax.set_xlabel("pH")
    ax.set_ylabel("總氨氮 TAN（mg N/L，對數座標）")
    ax.set_title("圖 1-3　游離氨（FA）抑制硝化的區域（20 °C）")
    ax.legend(loc="upper left", fontsize=10, frameon=False, bbox_to_anchor=(1.01, 1.0))
    fig.text(0.01, -0.03, "邊界依 Anthonisen et al. (1976) 的 FA 公式與抑制範圍計算；文獻報告的抑制門檻差異大，請視為「趨勢」而非精確切線。",
             fontsize=10, color="#5b6475")
    save(fig, "fig1-3-free-ammonia-zones")


def fig2_1_resources():
    routes = ["傳統硝化＋脫硝\n（NH₄⁺→NO₃⁻→N₂）", "短程硝化＋脫硝\n（NH₄⁺→NO₂⁻→N₂）", "部分亞硝化＋Anammox\n（PN/A）"]
    o2 = [4.57, 3.43, 1.94]
    cod = [2.86, 1.71, 0]
    x = np.arange(3)
    fig, ax = plt.subplots(figsize=(10, 5.4))
    b1 = ax.bar(x - 0.2, o2, 0.38, color=NH4, label="需氧量（g O₂ / g N）")
    b2 = ax.bar(x + 0.2, cod, 0.38, color=ORG, label="有機碳需求（g COD / g N）")
    for bars in (b1, b2):
        for b in bars:
            h = b.get_height()
            if h == 0:
                continue
            ax.text(b.get_x() + b.get_width() / 2, h + 0.08, f"{h:.2f}", ha="center", fontsize=12)
    ax.text(1 - 0.2, 4.0, "−25%", ha="center", color=NH4, fontsize=12, weight="bold")
    ax.text(1 + 0.2, 2.25, "−40%", ha="center", color=ORG, fontsize=12, weight="bold")
    ax.text(2 - 0.2, 2.5, "約 −58%", ha="center", color=NH4, fontsize=12, weight="bold")
    ax.text(2 + 0.2, 0.25, "不需要", ha="center", color=ORG, fontsize=12, weight="bold")
    ax.set_xticks(x, routes)
    ax.set_ylim(0, 5.4)
    ax.set_ylabel("每去除 1 g 氮")
    ax.set_title("圖 2-1　三種脫氮路線的理論需氧量與碳源需求")
    ax.legend(frameon=False, loc="upper right")
    fig.text(0.01, -0.06, "化學計量理論值，未計入菌體合成（實務上碳源常需 4–6 g COD/g N）。PN/A 以約 57% 氨氮氧化為亞硝酸鹽估算。\n"
             "依 Metcalf & Eddy (2014)、Rittmann & McCarty (2020)、Strous et al. (1998) 計算。", fontsize=10, color="#5b6475")
    save(fig, "fig2-1-resources")


def fig3_3_calibration():
    rng = np.random.default_rng(3)
    conc = np.array([0, 0.1, 0.2, 0.5, 1.0, 1.5, 2.0])
    absb = 0.012 + 0.415 * conc + rng.normal(0, 0.006, conc.size)
    k, b = np.polyfit(conc, absb, 1)
    r2 = np.corrcoef(conc, absb)[0, 1] ** 2
    fig, ax = plt.subplots(figsize=(9, 5.4))
    ax.plot(conc, absb, "o", color=NH4, ms=8, label="標準溶液")
    xx = np.linspace(0, 2.1, 50)
    ax.plot(xx, k * xx + b, color=NH4, lw=1.6, label=f"y = {k:.3f}x + {b:.3f}　R² = {r2:.4f}")
    sample_abs = 0.37
    sx = (sample_abs - b) / k
    ax.plot([0, sx, sx], [sample_abs, sample_abs, 0], ls="--", color=NO3, lw=1.2)
    ax.plot([sx], [sample_abs], "D", color=NO3, ms=8, label="樣品（稀釋 50 倍後測）")
    ax.annotate(f"讀值 {sx:.2f} mg N/L\n× 稀釋倍數 50\n= 原水 {sx * 50:.0f} mg N/L", (sx, sample_abs), xytext=(1.25, 0.18),
                fontsize=12, color=NO3, arrowprops=dict(arrowstyle="->", color=NO3))
    ax.axhspan(0.9, 1.0, color=GREY, alpha=0.12)
    ax.text(0.05, 0.92, "吸光值過高 → 稀釋後再測，不要外插", fontsize=11, color="#5b6475")
    ax.set_xlabel("氨氮濃度（mg N/L）")
    ax.set_ylabel("吸光值（640 nm）")
    ax.set_xlim(0, 2.2)
    ax.set_ylim(0, 1.0)
    ax.set_title("圖 3-3　靛酚比色法標準曲線怎麼用（示意數據）")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, 0.9))
    save(fig, "fig3-3-calibration")


def fig5_2_batch():
    t = np.linspace(0, 10, 300)
    k1, k2 = 0.55, 0.9
    a = 50 * np.exp(-k1 * t)
    nit = 50 * k1 / (k2 - k1) * (np.exp(-k1 * t) - np.exp(-k2 * t))
    nat = 50 - a - nit
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), sharey=True)
    ax = axes[0]
    ax.plot(t, a, color=NH4, lw=2.4, label="NH₄⁺-N")
    ax.plot(t, nit, color=NO2, lw=2.4, label="NO₂⁻-N")
    ax.plot(t, nat, color=NO3, lw=2.4, label="NO₃⁻-N")
    ax.plot(t, a + nit + nat, color=INK, lw=1.4, ls="--", label="三者合計（≈ 溶解性 TN）")
    ax.set_title("(a) 好氧硝化：氨氮下降，但總氮沒變", fontsize=13)
    ax.set_xlabel("時間（h）")
    ax.set_ylabel("濃度（mg N/L）")
    ax.legend(frameon=False, fontsize=11)
    ax = axes[1]
    a2 = 50 * np.exp(-0.45 * t)
    no3b = 6 * (1 - np.exp(-0.6 * t)) * np.exp(-0.15 * t)
    tn = a2 + no3b
    ax.plot(t, a2, color=NH4, lw=2.4, label="NH₄⁺-N")
    ax.plot(t, no3b, color=NO3, lw=2.4, label="NO₂⁻ + NO₃⁻-N")
    ax.plot(t, tn, color=INK, lw=1.4, ls="--", label="溶解性 TN")
    ax.fill_between(t, tn, 50, color=N2, alpha=0.15)
    ax.text(5.3, 30, "TN 減少的部分＝\n變成氣體（N₂/N₂O）\n或進入菌體\n→ 要再區分", fontsize=11, color=N2)
    ax.set_title("(b) 有脫氮（或同化）：總氮也下降", fontsize=13)
    ax.set_xlabel("時間（h）")
    ax.legend(frameon=False, fontsize=11, loc="upper right")
    fig.suptitle("圖 5-2　批次試驗要同時量多種氮（示意數據）", fontsize=15, weight="bold")
    fig.text(0.01, -0.03, "比速率 = 斜率 ÷ 生物量，例如 mg NH₄⁺-N /(g VSS·h)。用線性段（通常前 30–60% 的下降）計算，並做無接種、滅菌對照扣除氣提與吸附。",
             fontsize=10, color="#5b6475")
    save(fig, "fig5-2-batch-test")


def fig5_3_our():
    seg = [(0, 5, 6, "內源呼吸"), (5, 12, 26, "＋NH₄Cl\n總耗氧"), (12, 19, 21, "＋NaClO₃\n抑制 NOB"), (19, 26, 6, "＋ATU\n抑制 AOB")]
    fig, ax = plt.subplots(figsize=(11, 5))
    for s, e, v, lab in seg:
        ax.plot([s, e], [v, v], color=INK, lw=3)
        ax.text((s + e) / 2, v + 1.2, lab, ha="center", fontsize=11)
    ax.annotate("", (12.5, 21), (12.5, 26), arrowprops=dict(arrowstyle="<->", color=NO2, lw=2))
    ax.text(13, 23.2, "NOB 耗氧\n= 5", color=NO2, fontsize=12, weight="bold")
    ax.annotate("", (19.5, 6), (19.5, 21), arrowprops=dict(arrowstyle="<->", color=NH4, lw=2))
    ax.text(20, 13, "AOB 耗氧 = 15", color=NH4, fontsize=12, weight="bold")
    ax.set_xlim(0, 26)
    ax.set_ylim(0, 32)
    ax.set_xticks([])
    ax.set_xlabel("依序加入藥劑（時間 →）")
    ax.set_ylabel("耗氧速率 OUR（mg O₂/L·h）")
    ax.set_title("圖 5-3　用抑制劑拆開 AOB 與 NOB 的耗氧速率（示意）")
    fig.text(0.01, -0.04, "AOB:NOB 耗氧比理論上約 3.43 : 1.14 ≈ 3 : 1。氯酸鈉抑制 NOB、ATU 抑制 AOB；方法概念見 Ginestet et al. (1998)（該研究以 azide 抑制 NOB）。\n"
             "實際藥劑濃度與接觸時間請依原文與預試驗決定。", fontsize=10, color="#5b6475")
    save(fig, "fig5-3-our-inhibitors")


def fig6_2_qpcr():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    ax = axes[0]
    cyc = np.linspace(0, 40, 400)
    logs = [7, 6, 5, 4, 3, 2]
    cmap = plt.get_cmap("Blues")
    cqs = []
    for i, lg in enumerate(logs):
        cq = 38.0 - 3.32 * lg
        cqs.append(cq)
        f = 1 / (1 + np.exp(-(cyc - cq - 2.2) / 1.25)) * 10
        ax.semilogy(cyc, f + 0.02, color=cmap(0.95 - i * 0.11), lw=2, label=f"10{'⁰¹²³⁴⁵⁶⁷⁸⁹'[lg]} copies")
    ax.axhline(0.35, color=NO3, ls="--", lw=1.2)
    ax.text(1, 0.42, "閾值（threshold）", color=NO3, fontsize=11)
    ax.plot([0, 40], [0.025, 0.025], color=GREY, lw=1.5, ls=":")
    ax.text(30, 0.03, "NTC：沒有訊號", color=GREY, fontsize=10)
    ax.set_xlabel("循環數（cycle）")
    ax.set_ylabel("螢光（ΔRn，對數座標）")
    ax.set_title("(a) 擴增曲線：起始量多 → 越早超過閾值", fontsize=13)
    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    ax.set_ylim(0.01, 30)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax = axes[1]
    rng = np.random.default_rng(7)
    x = np.repeat(logs, 3)
    y = 38.0 - 3.32 * x + rng.normal(0, 0.12, x.size)
    k, b = np.polyfit(x, y, 1)
    r2 = np.corrcoef(x, y)[0, 1] ** 2
    eff = (10 ** (-1 / k) - 1) * 100
    ax.plot(x, y, "o", color=NH4, ms=7)
    xx = np.linspace(1.5, 7.5, 20)
    ax.plot(xx, k * xx + b, color=NH4)
    ax.text(4.75, 32.5, f"斜率 = {k:.2f}\nR² = {r2:.3f}\n效率 E = 10^(−1/斜率) − 1\n　　= {eff:.0f}%", fontsize=12, va="top")
    scq = 24.1
    sx = (scq - b) / k
    ax.plot([sx], [scq], "D", color=NO3, ms=9)
    ax.annotate(f"樣品 Cq {scq} → 10 的 {sx:.2f} 次方\n≈ {10 ** sx:,.0f} copies/反應", (sx, scq), xytext=(2.0, 15.5), fontsize=11.5,
                color=NO3, arrowprops=dict(arrowstyle="->", color=NO3))
    ax.set_xlabel("log₁₀（起始拷貝數 / 反應）")
    ax.set_ylabel("Cq")
    ax.set_title("(b) 標準曲線：用 Cq 回推拷貝數", fontsize=13)
    fig.suptitle("圖 6-2　qPCR 怎麼讀（示意數據）", fontsize=15, weight="bold")
    fig.text(0.01, -0.03, "理想斜率 −3.32 代表每循環剛好加倍（效率 100%）；可接受範圍約 −3.6 到 −3.1（效率 90–110%）。依 Bustin et al. (2009)。",
             fontsize=10, color="#5b6475")
    save(fig, "fig6-2-qpcr-curves")


def fig6_3_melt():
    t = np.linspace(65, 95, 400)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
    good = 2.2 * np.exp(-((t - 85.5) / 0.9) ** 2)
    bad = 1.6 * np.exp(-((t - 85.5) / 0.9) ** 2) + 0.9 * np.exp(-((t - 76) / 1.4) ** 2)
    axes[0].plot(t, good, color=N2, lw=2.4)
    axes[0].set_title("(a) 單一峰：產物專一 ✓", fontsize=13, color=N2)
    axes[1].plot(t, bad, color=NO3, lw=2.4)
    axes[1].set_title("(b) 多一個低溫峰：引子二聚體或非專一產物 ✗", fontsize=13, color=NO3)
    axes[1].annotate("引子二聚體\n（常出現在低濃度與 NTC）", (76, 0.9), xytext=(66, 1.6), fontsize=11, color=NO3,
                     arrowprops=dict(arrowstyle="->", color=NO3))
    for ax in axes:
        ax.set_xlabel("溫度（°C）")
    axes[0].set_ylabel("−dF/dT")
    fig.suptitle("圖 6-3　SYBR Green 熔解曲線判讀（示意）", fontsize=15, weight="bold")
    save(fig, "fig6-3-melt-curve")


def fig9_2_balance():
    labels = ["進流", "出流\n只有硝化", "出流\n硝化＋脫硝"]
    data = {
        "有機氮": ([10, 2, 2], ORG),
        "NH₄⁺-N": ([50, 2, 3], NH4),
        "NO₂⁻-N": ([0, 1, 0.5], NO2),
        "NO₃⁻-N": ([0, 50, 9.5], NO3),
        "進入污泥（排泥）": ([0, 5, 6], GREY),
        "變成氣體 N₂（＋少量 N₂O）": ([0, 0, 39], N2),
    }
    fig, ax = plt.subplots(figsize=(10, 5.6))
    bottom = np.zeros(3)
    for name, (vals, col) in data.items():
        ax.bar(labels, vals, bottom=bottom, color=col, width=0.55, label=name,
               alpha=0.55 if "氣體" in name or "污泥" in name else 1, edgecolor="white")
        for i, v in enumerate(vals):
            if v >= 4:
                ax.text(i, bottom[i] + v / 2, f"{v:g}", ha="center", va="center", color="white", fontsize=12,
                        weight="bold")
        bottom += vals
    ax.set_ylabel("氮（mg N/L 當量）")
    ax.set_ylim(0, 70)
    ax.text(1, 63, "氨氮去除率 96%\n但 TN 幾乎沒少", ha="center", fontsize=11, color=NO3)
    ax.text(2, 63, "氨氮去除率 94%\nTN 去除約 75%", ha="center", fontsize=11, color=N2)
    ax.set_title("圖 9-2　氮質量平衡：「氨氮去除率」≠「脫氮率」（示意數據）")
    ax.legend(frameon=False, fontsize=10, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    save(fig, "fig9-2-mass-balance")


if __name__ == "__main__":
    for fn in (fig1_2_fraction, fig1_3_anthonisen, fig2_1_resources, fig3_3_calibration, fig5_2_batch, fig5_3_our,
               fig6_2_qpcr, fig6_3_melt, fig9_2_balance):
        fn()
