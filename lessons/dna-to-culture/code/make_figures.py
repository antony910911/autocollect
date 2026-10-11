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
PR = json.loads((HERE / "protocol.json").read_text("utf-8")) if (HERE / "protocol.json").exists() else None
CAL = json.loads((HERE / "calibration.json").read_text("utf-8")) if (HERE / "calibration.json").exists() else None
for f in ("WenQuanYi Zen Hei", "Noto Sans CJK TC", "PingFang TC", "Microsoft JhengHei"):
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = [f, "DejaVu Sans"]
        break
plt.rcParams.update({"axes.unicode_minus": False, "mathtext.fontset": "dejavusans", "font.size": 12,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True,
                     "grid.color": "#e3e6ec", "grid.linewidth": 0.8, "axes.edgecolor": "#8a93a3",
                     "axes.titleweight": "bold", "axes.titlesize": 14, "savefig.dpi": 200})
ETOH_C = "#2f6fb3"
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


# ───────── 第 10 章：操作建議 ─────────
def fig_protocol():
    b, tr, sp = PR["band"], PR["trajectory"], PR["sampling"]
    sw, hv = PR["switch"], PR["harvest"]
    t = np.array(b["t"])
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 8.4), sharex=True,
                                 gridspec_kw={"height_ratios": [1, 1], "hspace": 0.18})
    # 上：OD 的期望軌跡與容許範圍
    a1.fill_between(t, b["X"]["p10"], b["X"]["p90"], color=GREEN, alpha=0.18,
                    label="容許範圍（p10–p90，400 次模擬）")
    a1.plot(t, b["X"]["p50"], color=GREEN, lw=2.8, label="期望值（中位數）")
    for s_ in sp:
        for x in s_["times"]:
            a1.plot([x], [np.interp(x, t, b["X"]["p50"])], marker="v", color=INK, ms=6, zorder=5)
    a1.plot([], [], marker="v", color=INK, ls="none", label="取樣點")
    a1.axvline(sw["t_sw"], color=BLUE, lw=1.8)
    a1.axhline(sw["od"], color=BLUE, ls=":", lw=1.5)
    a1.text(sw["t_sw"] + 0.12, sw["od"] * 1.5, f"切換門檻\nOD600 {sw['od']:.1f}\n（約第 {sw['t_sw']:.2f} h）",
            color=BLUE, fontsize=11, weight="bold")
    a1.set_yscale("log")
    a1.set_yticks([0.1, 0.2, 0.5, 1, 2, 5, 10, 20])
    a1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    a1.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    a1.set_ylabel("OD600（對數軸）")
    a1.set_title("期望軌跡與容許範圍：量到的值掉出綠色區間，就要查原因")
    a1.legend(frameon=False, loc="lower right", fontsize=10.5)
    # 下：產物與糖
    a2.fill_between(t, b["E"]["p10"], b["E"]["p90"], color=ETOH_C, alpha=0.18)
    a2.plot(t, b["E"]["p50"], color=ETOH_C, lw=2.8, label="乙醇（目標產物）")
    a2.fill_between(t, b["G"]["p10"], b["G"]["p90"], color=BROWN, alpha=0.15)
    a2.plot(t, b["G"]["p50"], color=BROWN, lw=2.4, label="葡萄糖")
    a2.plot(t, b["A"]["p50"], color=ORANGE, lw=2.0, ls="--", label="乙酸（副產物）")
    a2.axvline(sw["t_sw"], color=BLUE, lw=1.8)
    a2.scatter([hv["t_end"]], [hv["etoh_mM"]], color=ETOH_C, s=90, zorder=5, edgecolor="white")
    a2.annotate(f"收穫：乙醇 {hv['etoh_gL']:.1f} g/L", (hv["t_end"], hv["etoh_mM"]),
                xytext=(-150, 18), textcoords="offset points", fontsize=11, color=ETOH_C, weight="bold")
    a2.set_ylabel("濃度（mM）")
    a2.set_xlabel("培養時間（h）")
    a2.set_title("糖與產物：收穫時的預期值與容許範圍")
    a2.legend(frameon=False, loc="upper left", fontsize=10.5)
    a2.set_xlim(0, hv["t_end"])
    # 階段色帶
    for ax in (a1, a2):
        for s_ in sp:
            ax.axvspan(s_["start"], s_["end"], color=PHASE_COL.get(s_["phase"], GREY), alpha=0.08, lw=0)
    for s_ in sp:
        if s_["end"] - s_["start"] > 1.0:
            a1.text((s_["start"] + s_["end"]) / 2, a1.get_ylim()[1] * 0.75, s_["phase"],
                    ha="center", fontsize=10.5, color=INK, weight="bold")
    fig.suptitle("圖 10-1　操作單的核心：期望軌跡、取樣點、切換門檻與容許範圍", fontsize=15, weight="bold", y=0.97)
    save(fig, "fd10-1-protocol", DFBA_NOTE + " 容許範圍來自接種量、遲滯期、吸收速率、供氧與溫度的變異。")


def fig_switch_rule():
    r = PR["switch_rule"]
    rows = r["rows"]
    xs = [x["od_at_check"] for x in rows]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.8))
    a1.plot(xs, [x["best_t_sw"] for x in rows], marker="o", color=BLUE, lw=2.5, ms=9)
    a1.axvline(r["base_od"], color=GREY, ls=":")
    a1.text(r["base_od"] - 0.03, max(x["best_t_sw"] for x in rows) - 0.1,
            f"照計畫長的話是 OD {r['base_od']:.2f} ", fontsize=10.5, color=NOTE, ha="right")
    for x in rows:
        a1.annotate(f"{x['best_t_sw']:.2f} h", (x["od_at_check"], x["best_t_sw"]),
                    xytext=(6, 6), textcoords="offset points", fontsize=10)
    a1.set_xlabel(f"第 {r['check_h']:.0f} 小時實際量到的 OD600")
    a1.set_ylabel("建議的切換時間（h）")
    a1.set_title("長得慢就晚一點切換")
    a2.bar([f"{x['od_at_check']:.2f}" for x in rows], [x["loss"] for x in rows],
           color=[GREEN if x["loss"] < 10 else ORANGE if x["loss"] < 40 else RED for x in rows])
    for i, x in enumerate(rows):
        a2.text(i, x["loss"] + 1.2, f"{x['loss']:.0f}", ha="center", fontsize=10.5)
    a2.set_xlabel(f"第 {r['check_h']:.0f} 小時實際量到的 OD600")
    a2.set_ylabel("照原訂時間切換會少掉的乙醇（mM）")
    a2.set_title("不調整的代價：長得慢時最嚴重")
    fig.suptitle("圖 10-2　中途查核與調整：看一次 OD，就能決定要不要改切換時間", fontsize=14, weight="bold", y=1.03)
    save(fig, "fd10-2-switch-rule", DFBA_NOTE)


# ───────── 第 11 章：把數據餵回模型 ─────────
LAB_NOTE = ("示範資料：用一組「和教材預設值不同」的參數模擬出來的六批實驗，加上一般實驗室水準的量測誤差。"
            "程式在 lessons/dna-to-culture/code/（labdata.py 產生、calibrate.py 校正）。")


def fig_derive():
    der, curves = CAL["derived"], CAL["curves"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5))
    # 左：一批的 OD 與 μmax、遲滯期怎麼讀出來
    bid = "B01"
    obs = curves[bid]["obs"]
    d = der[bid]
    t = np.array([x for x, y in zip(obs["t"], obs["od600"]) if y])
    y = np.array([y for y in obs["od600"] if y])
    a1.scatter(t, y, color=INK, s=42, zorder=4, label="量到的 OD600")
    w0, w1 = d["mu_window"]
    sel = (t >= w0) & (t <= w1)
    k, c = np.polyfit(t[sel], np.log(y[sel]), 1)
    tt = np.linspace(0, w1 + 1.5, 50)
    a1.plot(tt, np.exp(k * tt + c), color=RED, lw=2.2,
            label=f"指數期直線迴歸：μmax = {k:.3f}/h")
    a1.axvspan(w0, w1, color=GREEN, alpha=0.12)
    a1.text((w0 + w1) / 2, y.max() * 0.95, "自動挑出的\n指數期視窗", ha="center", va="top", fontsize=10.5,
            color=GREEN, weight="bold")
    a1.axhline(y[0], color=GREY, ls=":")
    a1.axvline(d["lag_h"], color=BLUE, ls="--", lw=1.8)
    a1.annotate(f"遲滯期 {d['lag_h']:.2f} h\n（切線外推回起始 OD）", (d["lag_h"], y[0]),
                xytext=(18, -34), textcoords="offset points", fontsize=10.5, color=BLUE,
                arrowprops=dict(arrowstyle="->", color=BLUE))
    a1.set_yscale("log")
    a1.set_yticks([0.1, 0.3, 1, 3, 10, 30])
    a1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    a1.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    a1.set_xlabel("時間（h）")
    a1.set_ylabel("OD600（對數軸）")
    a1.set_title(f"從一批的原始 OD 讀出生長參數（{bid}）")
    a1.legend(loc="lower right", fontsize=10, framealpha=0.95, facecolor="white", edgecolor="none")
    # 右：六批的 μmax 對溫度
    Ts = sorted({v["T"] for v in der.values()})
    bump = {}
    for bid2, v in sorted(der.items(), key=lambda kv: (kv[1]["T"], -kv[1]["mu_max"])):
        col = GREEN if v["otr_set"] >= 20 else ORANGE
        i = bump.get(v["T"], 0)
        bump[v["T"]] = i + 1
        a2.scatter([v["T"]], [v["mu_max"]], color=col, s=120, zorder=4, edgecolor="white")
        a2.annotate(bid2, (v["T"], v["mu_max"]), xytext=(11, 12 - i * 13), textcoords="offset points",
                    fontsize=10, arrowprops=dict(arrowstyle="-", color=GREY, lw=0.8, shrinkA=2, shrinkB=2))
    a2.scatter([], [], color=GREEN, s=100, label="供氧 30")
    a2.scatter([], [], color=ORANGE, s=100, label="供氧 10")
    a2.set_xlabel("培養溫度（°C）")
    a2.set_ylabel("實測 μmax（1/h）")
    a2.set_title("六批彙整：溫度確實有影響，但只有三個溫度")
    a2.legend(frameon=False, loc="lower right")
    a2.set_ylim(0, 0.78)
    a2.text(30, 0.13, "只有 30、37、42 三個溫度，\n擬合溫度曲線剛好夠用；\n要更準就要再加溫度點。",
            fontsize=10.5, color=NOTE)
    fig.suptitle("圖 11-1　第一步：不必用模型，先從原始數據算出衍生量", fontsize=15, weight="bold", y=1.02)
    save(fig, "fd11-1-derive", LAB_NOTE)


def fig_calibrate():
    curves, pb = CAL["curves"], CAL["per_batch"]
    show = ["B01", "B06", "B02", "B04"]
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 8.6))
    for ax, bid in zip(axes.ravel(), show):
        c, role = curves[bid], pb[bid]["role"]
        t, obs = np.array(c["t"]), c["obs"]
        ot = np.array(obs["t"])
        ax.plot(t, c["before"]["od600"], color=GREY, lw=1.8, ls="--", label="校正前（預設參數）")
        ax.plot(t, c["after"]["od600"], color=GREEN, lw=2.6, label="校正後")
        m = [i for i, v in enumerate(obs["od600"]) if v]
        ax.scatter(ot[m], [obs["od600"][i] for i in m], color=INK, s=34, zorder=5, label="實測 OD600")
        a2 = ax.twinx()
        a2.plot(t, c["before"]["ethanol_g_L"], color=GREY, lw=1.4, ls=":")
        a2.plot(t, c["after"]["ethanol_g_L"], color=ETOH_C, lw=2.2)
        m2 = [i for i, v in enumerate(obs["ethanol_g_L"]) if v]
        a2.scatter(ot[m2], [obs["ethanol_g_L"][i] for i in m2], color=ETOH_C, s=30, marker="s", zorder=5)
        a2.set_ylabel("乙醇（g/L）", color=ETOH_C, fontsize=10)
        a2.grid(False)
        a2.spines["right"].set_visible(True)
        if c["switch_h"]:
            ax.axvline(c["switch_h"], color=INK, lw=1.2)
        col = GREEN if role == "訓練" else PURPLE
        ax.set_title(f"{bid}（{role}）　{c['T']:.0f} °C、供氧 {c['otr']:.0f}　"
                     f"OD 誤差 {pb[bid]['before']['od600']:.0f}% → {pb[bid]['after']['od600']:.0f}%",
                     color=col, fontsize=12.5)
        ax.set_xlabel("時間（h）")
        ax.set_ylabel("OD600")
        if bid == show[0]:
            h1, l1 = ax.get_legend_handles_labels()
            ax.legend(h1 + [plt.Line2D([], [], color=ETOH_C, lw=2.2, marker="s", ls="-")],
                      l1 + ["乙醇（右軸）"], frameon=False, fontsize=9.5, loc="upper left")
    fig.suptitle("圖 11-2　校正前後：上排是參與校正的批次，下排是沒參與的驗證批次", fontsize=15, weight="bold", y=0.985)
    fig.tight_layout()
    save(fig, "fd11-2-calibration", LAB_NOTE + " B04 在 42 °C，超出訓練批次的溫度範圍。")


def fig_identifiability():
    sens, theta, truth = CAL["sensitivity"], CAL["theta"], CAL["truth"]
    default = CAL["default"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.5, 5.2), gridspec_kw={"width_ratios": [1.1, 1]})
    labels = [s["label"] for s in sens][::-1]
    vals = [s["worst_ratio"] for s in sens][::-1]
    cols = [GREEN if s["identifiable"] else RED for s in sens][::-1]
    a1.barh(labels, vals, color=cols)
    a1.set_xscale("log")
    a1.axvline(1.5, color=INK, ls="--", lw=1.5)
    a1.text(1.7, len(vals) - 1.4, "門檻：參數偏離 ±30% 時\n擬合至少要變差 1.5 倍", fontsize=10, color=NOTE)
    for i, v in enumerate(vals):
        a1.text(v * 1.15, i, f"×{v:,.0f}" if v >= 10 else f"×{v:.1f}", va="center", fontsize=10)
    a1.set_xlabel("把參數拉離最佳值 ±30%，擬合誤差變成幾倍（對數軸）")
    a1.set_title("哪些參數真的被數據決定？")
    a1.set_xlim(0.8, max(vals) * 4)
    # 右：參數回收
    names = [s["name"] for s in sens]
    show = [n for n in names if truth.get(n) is not None]
    x = np.arange(len(show))
    rel_d = [default[n] / truth[n] for n in show]
    rel_a = [theta[n] / truth[n] for n in show]
    a2.axhline(1, color=INK, lw=1.5)
    a2.bar(x - 0.2, rel_d, width=0.38, color=GREY, label="校正前 ÷ 真實值")
    a2.bar(x + 0.2, rel_a, width=0.38, color=GREEN, label="校正後 ÷ 真實值")
    for i, n in enumerate(show):
        if not next(s for s in sens if s["name"] == n)["identifiable"]:
            a2.text(i + 0.2, rel_a[i] + 0.3, "數據\n不足", ha="center", fontsize=9.5, color=RED, weight="bold")
    a2.set_xticks(x, [n.replace("_", "\n") for n in show], fontsize=9.5)
    a2.set_ylabel("估計值 ÷ 真實值（1.0 = 完全正確）")
    a2.set_title("參數回收：可辨識的都回到 1.0 附近")
    a2.legend(frameon=False, loc="upper left", fontsize=10)
    a2.set_ylim(0, max(max(rel_d), max(rel_a)) * 1.25)
    fig.suptitle("圖 11-3　不是每個參數都能從數據決定", fontsize=15, weight="bold", y=1.0)
    fig.tight_layout()
    save(fig, "fd11-3-identifiability", LAB_NOTE + " 真實值只有示範資料才知道；真實實驗沒有答案可以對。")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for fn in (fig_derive, fig_calibrate, fig_identifiability, fig_protocol, fig_switch_rule, fig_o2_scan, fig_phase_plane, fig_carbon, fig_knockouts, fig_batch, fig_gompertz, fig_otr,
               fig_strategies, fig_switch_scan, fig_sensitivity, fig_env, fig_bo, fig_interaction):
        fn()
