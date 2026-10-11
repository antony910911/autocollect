"""用 experiments.py 的實際計算結果（results.json）畫教材的圖。執行：python make_figures.py"""

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
HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "figures"
R = json.loads((HERE / "results.json").read_text("utf-8"))
for f in ("WenQuanYi Zen Hei", "Noto Sans CJK TC", "PingFang TC", "Microsoft JhengHei"):
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = [f, "DejaVu Sans"]
        break
plt.rcParams.update({"axes.unicode_minus": False, "mathtext.fontset": "dejavusans", "font.size": 12,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True,
                     "grid.color": "#e3e6ec", "grid.linewidth": 0.8, "axes.edgecolor": "#8a93a3",
                     "axes.titleweight": "bold", "axes.titlesize": 14, "savefig.dpi": 200})
BLUE, ORANGE, RED, GREEN, PURPLE, GREY, BROWN, INK, TEAL = ("#2f6fb3", "#d9821e", "#c23b3b", "#2f9e6e", "#7b4bb3",
                                                            "#8a93a3", "#8a6d3b", "#1d2330", "#1b8a8f")
NOTE = "#5b6475"
GEM_NOTE = "計算結果：COBRApy＋大腸桿菌核心代謝模型（E. coli core, Orth et al., 2010），程式在 lessons/dna-to-culture/code/。"
DFBA_NOTE = ("計算結果：dFBA（E. coli core＋吸收動力學＋溫度/pH 經驗模型）。動力學與溫度、pH 參數為示範用的假設值，"
             "不代表任何實際菌株。")
PHASE_COL = {"遲滯期": GREY, "好氧指數生長": GREEN, "缺氧・溢流代謝": ORANGE, "回頭吃乙酸": PURPLE, "厭氧發酵": BLUE,
             "停滯期": "#c9ced8"}


def save(fig, name, note=GEM_NOTE):
    if note:
        fig.text(0.01, -0.02, note, fontsize=9.5, color=NOTE)
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("寫入", name)


def shade_phases(ax, t, phases, label=True):
    start = 0
    for i in range(1, len(phases) + 1):
        if i == len(phases) or phases[i] != phases[start]:
            ax.axvspan(t[start], t[min(i, len(t) - 1)], color=PHASE_COL[phases[start]], alpha=0.13, lw=0)
            start = i


# ───────── 第 4 章 ─────────
def fig_o2_scan():
    d = R["fba"]["o2_scan"]
    o2 = np.array(d["o2"])
    rows = d["rows"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.8))
    a1.plot(o2, [r["mu"] for r in rows], color=GREEN, lw=2.5)
    a1.set_xlabel("氧氣吸收上限（mmol O$_2$ / gDW / h）")
    a1.set_ylabel("最大生長率 μ（1/h）")
    a1.set_title("氧氣越多，長越快——直到碳源變成限制")
    a1.axvline(21.8, color=GREY, ls=":")
    a1.text(22.2, 0.3, "超過約 21.8\n氧氣不再是限制", fontsize=10, color=NOTE)
    for key, lab, col in (("ac", "乙酸", ORANGE), ("etoh", "乙醇", BLUE), ("for", "甲酸", PURPLE),
                          ("co2", "CO$_2$", GREY)):
        a2.plot(o2, [r[key] for r in rows], label=lab, lw=2.2, color=col)
    a2.axhline(0, color="#8a93a3", lw=0.8)
    a2.set_xlabel("氧氣吸收上限（mmol O$_2$ / gDW / h）")
    a2.set_ylabel("分泌速率（mmol / gDW / h）\n負值＝吸收")
    a2.set_title("同一株菌，供氧不同，走不同的代謝路徑")
    a2.set_ylim(-2, 28)
    a2.legend(frameon=False, ncol=4, loc="upper center")
    a2.text(0.5, 19.3, "厭氧：混合酸發酵", fontsize=10, color=BLUE)
    a2.text(9.5, 14.5, "缺氧：溢流代謝（乙酸）", fontsize=10, color=ORANGE)
    a2.text(16.5, 8.5, "好氧：完全氧化\n成 CO$_2$", fontsize=10, color=NOTE)
    fig.suptitle("圖 4-1　改變一個參數（供氧），看生長與產物怎麼變（葡萄糖吸收固定 10 mmol/gDW/h）",
                 fontsize=14, weight="bold", y=1.03)
    save(fig, "fd4-1-oxygen-scan")


def fig_phase_plane():
    d = R["fba"]["phase_plane"]
    g, o, mu = np.array(d["glc"]), np.array(d["o2"]), np.array(d["mu"])
    fig, ax = plt.subplots(figsize=(9.5, 6.5))
    cs = ax.contourf(o, g, mu, levels=20, cmap="viridis")
    ax.contour(o, g, mu, levels=[0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4], colors="white", linewidths=0.8, alpha=0.7)
    cb = fig.colorbar(cs, ax=ax)
    cb.set_label("最大生長率 μ（1/h）")
    # 最適線：每個葡萄糖吸收量下，再多氧也沒用的那一點
    line = []
    for i, gi in enumerate(g):
        if mu[i, -1] <= 0:
            continue
        j = int(np.argmax(mu[i] >= mu[i, -1] - 1e-3))
        line.append((o[j], gi))
    lx, ly = zip(*line)
    ax.plot(lx, ly, color="white", lw=2.5, ls="--")
    ax.text(26, 9, "最適線\n左上：氧氣不夠（加氧有用）\n右下：碳源不夠（加糖有用）", color="white", fontsize=11)
    ax.scatter([10], [10], color=ORANGE, s=90, zorder=5, edgecolor="white")
    ax.annotate("搖瓶常見情況\n（氧氣受限）", (10, 10), xytext=(3, 15), color="white", fontsize=11,
                arrowprops=dict(color="white", arrowstyle="->"))
    ax.set_xlabel("氧氣吸收上限（mmol / gDW / h）")
    ax.set_ylabel("葡萄糖吸收上限（mmol / gDW / h）")
    ax.set_title("圖 4-2　表型相平面：兩個參數一起變時，哪一個才是瓶頸？")
    ax.grid(False)
    save(fig, "fd4-2-phase-plane")


def fig_carbon():
    d = R["fba"]["carbon"]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    names = [x["name"] for x in d]
    ax.barh(names[::-1], [x["mu"] for x in d][::-1], color=[GREEN if x["mu"] > 0.8 else BLUE for x in d][::-1])
    for i, x in enumerate(d[::-1]):
        ax.text(x["mu"] + 0.01, i, f"{x['mu']:.2f}", va="center", fontsize=10)
    ax.set_xlabel("預測最大生長率 μ（1/h）；每種碳源都給每小時 60 mmol 碳、氧氣充足")
    ax.set_title("圖 4-3　換碳源：模型可以先幫你篩選，再進實驗室驗證")
    ax.set_xlim(0, 1.0)
    save(fig, "fd4-3-carbon-sources")


def fig_knockouts():
    genes = R["fba"]["knockouts"]["genes"]
    pick = ["ptsI", "pgi", "tpiA", "gapA", "ppc", "gltA", "icd", "nuoA", "atpA", "cydA", "pflB", "adhE", "ldhA",
            "pta", "sucA", "zwf"]
    rows = [g for p in pick for g in genes if g["name"] == p]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    y = np.arange(len(rows))
    ax.barh(y - 0.2, [r["aerobic"] for r in rows], height=0.38, color=ORANGE, label="好氧")
    ax.barh(y + 0.2, [r["anaerobic"] for r in rows], height=0.38, color=BLUE, label="厭氧")
    ax.set_yticks(y, [r["name"] for r in rows], fontstyle="italic")
    ax.invert_yaxis()
    ax.set_xlabel("剔除這個基因後的生長率（相對野生型）")
    ax.set_xlim(0, 1.15)
    ax.axvline(1, color=GREY, ls=":")
    ax.legend(frameon=False, loc="lower right")
    k = R["fba"]["knockouts"]
    ax.set_title(f"圖 4-4　基因剔除模擬：同一個基因，在不同條件下重要性不同（{k['n_genes']} 個基因全部算過）")
    notes = {"nuoA": "呼吸鏈：好氧時很重要，厭氧時用不到", "ppc": "厭氧時必需（補充草醯乙酸）",
             "pgi": "厭氧時必需（模型中無替代路徑）", "adhE": "核心模型中可被替代"}
    for i, r in enumerate(rows):
        if r["aerobic"] < 0.01 and r["anaerobic"] < 0.01:
            ax.text(0.01, i, "✕ 好氧、厭氧都不能生長（必需基因）", va="center", fontsize=10, color=RED, weight="bold")
        elif r["anaerobic"] < 0.01:
            ax.text(0.01, i + 0.2, "✕ 厭氧時不能生長", va="center", fontsize=9.5, color=BLUE, weight="bold")
        if r["name"] in notes:
            ax.text(1.02, i, notes[r["name"]], va="center", fontsize=9.5, color=NOTE)
    save(fig, "fd4-4-knockouts")


# ───────── 第 5 章 ─────────
def fig_batch():
    b = R["dfba"]["batch"]
    t = np.array(b["t"])
    fig, axes = plt.subplots(2, 1, figsize=(12, 8.5), sharex=True, gridspec_kw={"height_ratios": [1.15, 1]})
    a = axes[0]
    shade_phases(a, t, b["phase"])
    a.plot(t, b["G"], color=BROWN, lw=2.3, label="葡萄糖（mM）")
    a.plot(t, b["A"], color=ORANGE, lw=2.3, label="乙酸（mM）")
    a.set_ylabel("濃度（mM）")
    a2 = a.twinx()
    a2.plot(t, b["X"], color=GREEN, lw=3, label="菌量（gDW/L）")
    a2.set_ylabel("菌量（gDW/L）", color=GREEN)
    a2.grid(False)
    a2.spines["right"].set_visible(True)
    h1, l1 = a.get_legend_handles_labels()
    h2, l2 = a2.get_legend_handles_labels()
    a.legend(h1 + h2, l1 + l2, frameon=False, loc="center right")
    a.set_title("批次培養：糖、乙酸、菌量")
    for sp in R["dfba"]["spans"]:
        if sp["end"] - sp["start"] > 0.6:
            a.text((sp["start"] + min(sp["end"], 14)) / 2, a.get_ylim()[1] * 0.93, sp["phase"], ha="center",
                   fontsize=10.5, color=INK, weight="bold")
    a.set_xlim(0, 14)
    c = axes[1]
    shade_phases(c, t, b["phase"])
    c.plot(t, b["mu"], color=GREEN, lw=2.3, label="比生長速率 μ（1/h）")
    our = np.array(b["our"])
    cer = np.array(b["cer"])
    c2 = c.twinx()
    c2.plot(t, our, color=BLUE, lw=2.2, label="耗氧速率 OUR（mmol/L/h）")
    c2.axhline(30, color=BLUE, ls=":", lw=1.3)
    c2.text(0.2, 31, "供氧能力上限 30", color=BLUE, fontsize=10)
    rq = np.where(our > 0.5, cer / np.maximum(our, 1e-9), np.nan)
    c2.plot(t, rq * 10, color=PURPLE, lw=1.8, ls="--", label="呼吸商 RQ ×10")
    c2.set_ylabel("OUR（mmol/L/h）；RQ×10")
    c2.grid(False)
    c2.spines["right"].set_visible(True)
    c.set_ylabel("μ（1/h）")
    c.set_xlabel("培養時間（h）")
    h1, l1 = c.get_legend_handles_labels()
    h2, l2 = c2.get_legend_handles_labels()
    c.legend(h1 + h2, l1 + l2, frameon=False, loc="center right", fontsize=10)
    c.set_title("可以線上量的指標：耗氧、呼吸商；它們的轉折點標出階段的切換")
    fig.suptitle("圖 5-1　dFBA 模擬的批次培養：同一瓶菌，經過五個代謝階段", fontsize=15, weight="bold", y=1.0)
    fig.tight_layout()
    save(fig, "fd5-1-batch", DFBA_NOTE)


def fig_gompertz():
    g = R["dfba"]["gompertz"]
    t = np.array(g["t"])
    tt = np.linspace(0, t.max(), 300)
    A, mu, lam = g["A"], g["mu"], g["lam"]
    fit = A * np.exp(-np.exp(mu * np.e / A * (lam - tt) + 1))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(t, g["y"], color=INK, s=28, label="每小時量一次（加上量測誤差）", zorder=3)
    ax.plot(tt, fit, color=RED, lw=2.3, label=f"修正 Gompertz 擬合：μ$_m$ = {mu:.2f}/h，λ = {lam:.1f} h")
    sel = (t >= 2) & (t <= 6)
    k = g["mu_loglinear"]
    b0 = np.mean(np.array(g["y"])[sel] - k * t[sel])
    ax.plot(t[sel], b0 + k * t[sel], color=BLUE, lw=3, alpha=0.8, label=f"只取指數期做直線迴歸：μ = {k:.2f}/h")
    ax.set_xlabel("時間（h）")
    ax.set_ylabel("ln(N / N$_0$)")
    ax.set_title(f"圖 5-4　從生長曲線讀出參數（模型真實的最大 μ = {g['mu_model_max']:.2f}/h）")
    ax.legend(frameon=False, loc="lower right")
    ax.set_xlim(0, 16)
    save(fig, "fd5-2-growth-fit", DFBA_NOTE)


def fig_otr():
    d = R["dfba"]["otr_curves"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.6))
    cols = {"10": RED, "30": ORANGE, "100": GREEN}
    for k, v in d.items():
        a1.plot(v["t"], v["X"], color=cols[k], lw=2.3, label=f"供氧 {k} mmol/L/h")
        a2.plot(v["t"], v["A"], color=cols[k], lw=2.3, label=f"供氧 {k}")
    a1.set_title("菌量")
    a1.set_ylabel("gDW/L")
    a2.set_title("乙酸（溢流代謝的副產物）")
    a2.set_ylabel("mM")
    for a in (a1, a2):
        a.set_xlabel("時間（h）")
        a.set_xlim(0, 16)
    a1.legend(frameon=False)
    fig.suptitle("圖 5-3　同一株菌、同一個培養基，只改供氧能力（搖瓶裝液量、轉速、通氣量）", fontsize=14,
                 weight="bold", y=1.03)
    save(fig, "fd5-3-oxygen-supply", DFBA_NOTE)


# ───────── 第 6 章 ─────────
def fig_strategies():
    c = R["two_stage"]["curves"]
    sw = R["two_stage"]["curves_sw"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for a, (name, v) in zip(axes, c.items()):
        t = np.array(v["t"])
        shade_phases(a, t, v["phase"])
        a.plot(t, v["G"], color=BROWN, lw=2.2, label="葡萄糖")
        a.plot(t, v["E"], color=BLUE, lw=2.8, label="乙醇（目標產物）")
        a.plot(t, v["A"], color=ORANGE, lw=1.8, ls="--", label="乙酸")
        a3 = a.twinx()
        a3.plot(t, v["X"], color=GREEN, lw=2.2, label="菌量")
        a3.set_ylim(0, 10)
        a3.grid(False)
        if a is axes[-1]:
            a3.set_ylabel("菌量（gDW/L）", color=GREEN)
            a3.spines["right"].set_visible(True)
        else:
            a3.set_yticks([])
        a.set_title(f"{name}\n收穫時乙醇 {v['E'][-1]:.0f} mM（{v['E'][-1] * 46.07 / 1000:.1f} g/L）")
        a.set_xlabel("時間（h）")
        if 0 < sw[name] < 100:
            a.axvline(sw[name], color=INK, lw=1.5)
            a.text(sw[name] + 0.2, 190, f"第 {sw[name]:g} h\n停止通氣", fontsize=10)
    axes[0].set_ylabel("濃度（mM）")
    h1, l1 = axes[0].get_legend_handles_labels()
    axes[1].legend(h1 + [plt.Line2D([], [], color=GREEN, lw=2.2)], l1 + ["菌量（右軸）"], frameon=False,
                   loc="center", fontsize=10.5)
    fig.suptitle("圖 6-1　三種策略比較：起始葡萄糖 200 mM、第 12 小時收穫", fontsize=15, weight="bold", y=1.06)
    save(fig, "fd6-1-strategies", DFBA_NOTE)


def fig_switch_scan():
    rows = R["two_stage"]["scan"]
    rule = {r["t_end"]: r for r in R["two_stage"]["rule"]}
    fig, ax = plt.subplots(figsize=(11, 5.5))
    cols = {10.0: RED, 12.0: ORANGE, 16.0: GREEN, 24.0: BLUE}
    for te, col in cols.items():
        xs = [r for r in rows if r["t_end"] == te]
        ax.plot([r["t_sw"] for r in xs], [r["E_end"] for r in xs], color=col, lw=2.4, label=f"第 {te:g} h 收穫")
        b = R["two_stage"]["best"][str(te)]
        ax.scatter([b["t_sw"]], [b["E_end"]], color=col, s=70, zorder=4, edgecolor="white")
        if te in rule and rule[te]["rule_t_sw"] is not None:
            ax.axvline(rule[te]["rule_t_sw"], color=col, ls=":", lw=1.5)
    ax.text(0.15, 128, "虛線＝用簡單規則（下方說明）\n算出的切換時間；圓點＝真正最佳", fontsize=10.5, color=NOTE)
    ax.set_xlabel("停止通氣（切換成厭氧）的時間（h）")
    ax.set_ylabel("收穫時乙醇（mM）")
    ax.set_xlim(0, 12)
    ax.legend(frameon=False, loc="upper right")
    ax.set_title("圖 6-2　最佳切換時間取決於「你打算什麼時候收穫」")
    save(fig, "fd6-2-switch-scan", DFBA_NOTE)


def fig_sensitivity():
    s = R["two_stage"]["sensitivity"]
    rows = s["rows"]
    fig, ax = plt.subplots(figsize=(11, 5.2))
    y = np.arange(len(rows))
    ax.barh(y - 0.2, [r["stage1"] for r in rows], height=0.38, color=GREEN, label="只在第一階段（長菌）改")
    ax.barh(y + 0.2, [r["stage2"] for r in rows], height=0.38, color=BLUE, label="只在第二階段（產乙醇）改")
    ax.set_yticks(y, [r["label"] for r in rows])
    ax.invert_yaxis()
    ax.axvline(0, color=INK, lw=1)
    for i, r in enumerate(rows):
        for v, dy in ((r["stage1"], -0.2), (r["stage2"], 0.2)):
            if abs(v) > 0.5:
                ax.text(v - 1 if v < 0 else v + 1, i + dy, f"{v:+.0f}", va="center", ha="right" if v < 0 else "left",
                        fontsize=9.5)
            elif v == 0 and dy == -0.2 and r["stage2"] == 0:
                pass
    ax.set_xlabel(f"收穫時乙醇的變化（mM）；基準 = {s['ref']:.0f} mM（第 {s['t_sw']:g} h 切換）")
    ax.legend(frameon=False, loc="lower left")
    ax.set_title("圖 6-3　分階段敏感度：每個階段「該顧好」的參數不一樣")
    ax.set_xlim(-75, 15)
    save(fig, "fd6-3-stage-sensitivity", DFBA_NOTE)


# ───────── 第 7 章 ─────────
def fig_env():
    e = R["env"]
    cp = e["cardinal_params"]
    fig = plt.figure(figsize=(15, 9))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.8, 1.2], hspace=0.38, wspace=0.22)
    a = fig.add_subplot(gs[0, 0])
    T = np.arange(0, 50.01, 0.5)
    a.plot(T, e["cardinal"]["T"], color=RED, lw=2.5)
    for k in ("Tmin", "Topt", "Tmax"):
        a.axvline(cp[k], color=GREY, ls=":")
        a.text(cp[k], 1.04, f"{k[1:]} {cp[k]:g}", ha="center", fontsize=10)
    a.set_xlabel("溫度（°C）")
    a.set_ylabel("相對最大生長率")
    a.set_title("溫度基點模型（CTMI）", pad=18)
    a.set_ylim(0, 1.1)
    b = fig.add_subplot(gs[0, 1])
    ph = np.arange(3, 10.01, 0.05)
    b.plot(ph, e["cardinal"]["pH"], color=PURPLE, lw=2.5)
    for k in ("pHmin", "pHopt", "pHmax"):
        b.axvline(cp[k], color=GREY, ls=":")
        b.text(cp[k], 1.04, f"{k[2:]} {cp[k]:g}", ha="center", fontsize=10)
    b.set_xlabel("pH")
    b.set_title("pH 基點模型（CPMI）", pad=18)
    b.set_ylim(0, 1.1)
    for i, (key, title, cmap) in enumerate((("X_end", "全程好氧：第 12 h 菌量（gDW/L）", "Greens"),
                                            ("E_end", "兩階段（第 5.75 h 切換）：第 12 h 乙醇（mM）", "Blues"))):
        c = fig.add_subplot(gs[1, i])
        Z = np.array(e[key])
        im = c.contourf(e["pH"], e["T"], Z, levels=16, cmap=cmap)
        fig.colorbar(im, ax=c)
        k = np.unravel_index(Z.argmax(), Z.shape)
        c.scatter([e["pH"][k[1]]], [e["T"][k[0]]], marker="*", s=260, color=RED, edgecolor="white", zorder=5)
        c.annotate(f"最佳 {e['T'][k[0]]:g} °C、pH {e['pH'][k[1]]:g}\n= {Z.max():.1f}", (e["pH"][k[1]], e["T"][k[0]]),
                   xytext=(e["pH"][k[1]] + 0.4, e["T"][k[0]] - 8), fontsize=10.5,
                   arrowprops=dict(arrowstyle="->", color=INK))
        c.set_xlabel("pH")
        c.set_ylabel("溫度（°C）")
        c.set_title(title)
        c.grid(False)
    fig.suptitle("圖 7-1　溫度與 pH：GEM 算不出來，要靠經驗模型（上）；接上 dFBA 後可以看組合效果（下）",
                 fontsize=15, weight="bold", y=0.98)
    save(fig, "fd7-1-temperature-ph", DFBA_NOTE + " 基點值是假設的示範值。")


# ───────── 第 8 章 ─────────
def fig_bo():
    o = R["optimize"]
    opt = o["optimum"]["y"]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    cols = {"一次改一個因子": GREY, "隨機": ORANGE, "貝氏最適化": BLUE}
    n = o["budget"]
    x = np.arange(1, n + 1)
    for name, c in o["curves"].items():
        ax.plot(x, c["median"], color=cols[name], lw=2.6, label=name)
        ax.fill_between(x, c["q25"], c["q75"], color=cols[name], alpha=0.15)
    ax.axhline(opt, color=RED, ls="--")
    ax.text(1.2, opt + 3, f"真正的最佳值 {opt:.0f} mM（用大量模擬找出）", color=RED, fontsize=10.5)
    ax.axvline(12, color=INK, ls=":", lw=1)
    ax.text(12.3, 15, "做到第 12 個實驗時", fontsize=10.5)
    ax.set_xlabel("已做的實驗數")
    ax.set_ylabel("目前找到的最好條件，實際能產多少乙醇（mM）")
    ax.set_ylim(0, opt * 1.12)
    ax.legend(frameon=False, loc="lower right")
    ax.set_title(f"圖 8-1　同樣的實驗預算，誰先找到好條件？（4 個參數、{o['n_seeds']} 次重複的中位數與四分位）")
    save(fig, "fd8-1-optimizers", DFBA_NOTE + " 每次「實驗」含 5% 量測誤差。")


def fig_interaction():
    inter = R["optimize"]["interaction"]
    fig, ax = plt.subplots(figsize=(11, 5.2))
    cols = [RED, ORANGE, GREEN, TEAL, BLUE]
    for c, d in zip(cols, inter):
        xs, ys = zip(*d["curve"])
        ax.plot(xs, ys, color=c, lw=2.3, label=f"供氧 {d['otr']} mmol/L/h")
        ax.scatter([d["best_t_sw"]], [d["E"]], color=c, s=60, zorder=4, edgecolor="white")
    ax.set_xlabel("停止通氣的時間（h）")
    ax.set_ylabel("第 12 h 乙醇（mM）")
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("圖 8-2　交互作用：供氧越差，最佳切換時間越晚——一次只調一個參數會錯過")
    ax.set_xlim(0, 12)
    save(fig, "fd8-2-interaction", DFBA_NOTE)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for fn in (fig_o2_scan, fig_phase_plane, fig_carbon, fig_knockouts, fig_batch, fig_gompertz, fig_otr,
               fig_strategies, fig_switch_scan, fig_sensitivity, fig_env, fig_bo, fig_interaction):
        fn()
