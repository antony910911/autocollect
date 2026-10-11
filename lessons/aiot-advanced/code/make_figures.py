"""用 experiments.py 的實際計算結果畫教材的圖。執行：python make_figures.py"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402

import experiments as E  # noqa: E402
import plant  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
OUT = Path(__file__).resolve().parent.parent / "figures"
for f in ("WenQuanYi Zen Hei", "Noto Sans CJK TC", "PingFang TC", "Microsoft JhengHei"):
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = [f, "DejaVu Sans"]
        break
plt.rcParams.update({"axes.unicode_minus": False, "mathtext.fontset": "dejavusans", "font.size": 12,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True,
                     "grid.color": "#e3e6ec", "grid.linewidth": 0.8, "axes.edgecolor": "#8a93a3",
                     "axes.titleweight": "bold", "axes.titlesize": 14, "savefig.dpi": 200})
BLUE, ORANGE, RED, GREEN, PURPLE, GREY, BROWN, INK = ("#2f6fb3", "#d9821e", "#c23b3b", "#2f9e6e", "#7b4bb3", "#8a93a3",
                                                      "#8a6d3b", "#1d2330")
NOTE = "#5b6475"
SIM_NOTE = "模擬資料：依 AM2 模型（Bernard et al., 2001）產生的教學用沼氣廠，不代表任何實廠。程式在 lessons/aiot-advanced/code/。"


def save(fig, name, note=SIM_NOTE):
    if note:
        fig.text(0.01, -0.015, note, fontsize=9.5, color=NOTE)
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("寫入", name)


def shade(ax, ylab=True):
    for name, (a, b) in plant.EVENTS.items():
        if name == "換原料":
            ax.axvline(a, color=BROWN, lw=1, ls=":")
            if ylab:
                ax.text(a + 2, ax.get_ylim()[1] * 0.97, name, color=BROWN, fontsize=9, va="top")
            continue
        col = GREY if "漂移" in name else RED
        ax.axvspan(a, b, color=col, alpha=0.12)
        if ylab:
            ax.text(a + 1, ax.get_ylim()[1] * 0.97, name, color=col if col == RED else NOTE, fontsize=9, va="top")


def fig_overview(r):
    d, lab = r["daily"], r["lab"]
    days = d["day"]
    fig, axes = plt.subplots(4, 1, figsize=(12, 9.5), sharex=True)
    axes[0].plot(days, d["ch4_m3"], color=GREEN, lw=1.3)
    axes[0].set_ylabel("甲烷\n(Nm³/天)")
    axes[1].plot(days, d["cod_load_kg"], color=BROWN, lw=1.1)
    axes[1].set_ylabel("進料 COD\n(kg/天)")
    axes[2].plot(days, d["ph"], color=BLUE, lw=1.2, label="pH 電極讀值")
    axes[2].plot(days, d["ph_true"], color=INK, lw=0.8, ls="--", label="真實 pH")
    axes[2].set_ylabel("pH")
    axes[2].legend(frameon=False, fontsize=9, loc="lower left")
    axes[3].plot(days, d["vfa_true"], color=GREY, lw=1, label="槽內真實 VFA（現實中看不到）")
    axes[3].plot(lab["day"], lab["vfa"], "o", color=RED, ms=3.5, label="實驗室 VFA（每週兩次）")
    axes[3].set_ylabel("VFA\n(mg/L)")
    axes[3].set_yscale("log")
    axes[3].legend(frameon=False, fontsize=9, loc="upper left")
    axes[3].set_xlabel("天數")
    for ax in axes:
        shade(ax, ylab=ax is axes[0])
        ax.axvline(E.TRAIN_END, color=PURPLE, lw=1.2)
    axes[0].text(E.TRAIN_END + 2, axes[0].get_ylim()[1] * 0.75, "← 訓練期｜測試期 →", color=PURPLE, fontsize=10)
    fig.suptitle("圖 3-1　模擬沼氣廠 480 天的資料總覽", fontsize=15, weight="bold")
    save(fig, "fa3-1-plant-overview")


def fig_forecast(r):
    fc = r["fc"]
    days, y, P = fc["days"], fc["y"], fc["preds"]
    te = days >= E.TRAIN_END
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw={"width_ratios": [2.2, 1]})
    ax = axes[0]
    ax.plot(days[te], y[te], color=INK, lw=2, label="實際")
    styles = [("簡單基準（明天＝今天）", GREY, ":"), ("隨機森林", GREEN, "-"), ("梯度提升樹", RED, "-"),
              ("梯度提升樹（排除事件日訓練）", ORANGE, "--")]
    for name, c, ls in styles:
        ax.plot(days[te], P[name][te], color=c, ls=ls, lw=1.3, label=name)
    ax.set_xlim(E.TRAIN_END, 478)
    ax.set_ylim(300, 2600)
    ax.set_xlabel("天數（測試期）")
    ax.set_ylabel("隔天甲烷產量（Nm³/天）")
    ax.legend(frameon=False, fontsize=9.5, loc="upper left", ncol=2)
    ax.set_title("(a) 預測 vs 實際")
    ax = axes[1]
    names = ["簡單基準（明天＝今天）", "線性迴歸", "隨機森林", "梯度提升樹", "梯度提升樹（排除事件日訓練）"]
    vals = [fc["scores"][n]["test_mae_normal_days"] for n in names]
    short = ["簡單基準", "線性迴歸", "隨機森林", "梯度提升樹", "梯度提升樹\n（排除事件日）"]
    cols = [GREY, BLUE, GREEN, RED, ORANGE]
    bars = ax.barh(short[::-1], vals[::-1], color=cols[::-1])
    for b, v in zip(bars, vals[::-1]):
        ax.text(v + 4, b.get_y() + b.get_height() / 2, f"{v:.0f}", va="center")
    ax.set_xlabel("正常日的平均誤差 MAE（Nm³/天）")
    ax.set_title("(b) 誤差越小越好")
    fig.suptitle("圖 4-1　產氣預測：同一份資料，不同模型的表現差很多", fontsize=15, weight="bold")
    save(fig, "fa4-1-forecast")


def fig_split(r):
    sp = r["fc"]["split"]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    names = list(sp)
    x = np.arange(len(names))
    a = [sp[n]["隨機打散 MAE"] for n in names]
    b = [sp[n]["依時間切分 MAE"] for n in names]
    b1 = ax.bar(x - 0.18, a, 0.34, color=GREY, label="隨機打散（錯誤做法）")
    b2 = ax.bar(x + 0.18, b, 0.34, color=RED, label="依時間切分（正確做法）")
    for bars in (b1, b2):
        for bb in bars:
            ax.text(bb.get_x() + bb.get_width() / 2, bb.get_height() + 4, f"{bb.get_height():.0f}", ha="center")
    ax.set_xticks(x, names)
    ax.set_ylabel("測試誤差 MAE（Nm³/天）")
    ax.legend(frameon=False)
    ax.set_title("圖 4-2　隨機打散會讓模型「偷看未來」，看起來比實際準很多")
    save(fig, "fa4-2-split")


def fig_soft(r):
    h, lab, c = r["hourly"], r["lab"], r["soft_curves"]
    t = h["t"]
    sel = (t >= 360) & (t < 400)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw={"width_ratios": [2, 1]})
    ax = axes[0]
    ax.plot(t[sel], h["vfa_true"][sel], color=INK, lw=2, label="真實 VFA")
    ax.plot(t[sel], c["每週 2 次｜線性迴歸"][sel], color=BLUE, lw=1.2, label="軟感測：線性（對數尺度）")
    ax.plot(t[sel], c["每週 2 次｜梯度提升樹"][sel], color=ORANGE, lw=1.2, label="軟感測：梯度提升樹")
    m = (lab["day"] >= 360) & (lab["day"] < 400)
    ax.plot(lab["day"][m] + 9 / 24, lab["vfa"][m], "o", color=RED, ms=7, label="實驗室（每週兩次）")
    ax.axhline(E.VFA_ALARM, color=RED, ls="--", lw=1)
    ax.text(361, E.VFA_ALARM * 1.15, "警戒 1000 mg/L", color=RED, fontsize=9)
    ax.set_yscale("log")
    ax.set_ylim(20, 30000)
    ax.set_xlabel("天數")
    ax.set_ylabel("VFA（mg/L，對數座標）")
    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    ax.set_title("(a) 大過量事件前後")
    ax = axes[1]
    s = r["soft_scores"]
    freqs = ["每週 1 次", "每週 2 次", "每天 1 次（理想）"]
    x = np.arange(3)
    lin = [s[f"{f}｜線性迴歸"]["test_mae_normal"] for f in freqs]
    gb = [s[f"{f}｜梯度提升樹"]["test_mae_normal"] for f in freqs]
    ax.bar(x - 0.18, lin, 0.34, color=BLUE, label="線性")
    ax.bar(x + 0.18, gb, 0.34, color=ORANGE, label="梯度提升樹")
    ax.set_xticks(x, ["每週 1 次\n(48 筆)", "每週 2 次\n(95 筆)", "每天 1 次\n(330 筆)"])
    ax.set_ylabel("正常日誤差 MAE（mg/L）")
    ax.legend(frameon=False)
    ax.set_title("(b) 正常日誤差：樹模型很吃資料量")
    fig.suptitle("圖 5-1　VFA 軟感測：樹模型「看不到」比訓練資料更高的值", fontsize=15, weight="bold")
    save(fig, "fa5-1-soft-sensor")


def fig_ekf(r):
    h = r["hourly"]
    t = h["t"]
    sel = (t >= 360) & (t < 400)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(t[sel], h["vfa_true"][sel], color=INK, lw=2.2, label="真實 VFA")
    ax.plot(t[sel], r["ekf"]["vfa_openloop"][sel], color=GREY, lw=1.2, ls=":", label="只跑模型（不用量測修正）")
    ax.plot(t[sel], r["ekf"]["vfa_ekf"][sel], color=PURPLE, lw=1.4, label="EKF：進料只有每週兩次 COD")
    ax.plot(t[sel], r["ekf_known"]["vfa_ekf"][sel], color=GREEN, lw=1.4, ls="--", label="EKF：每批進料快篩 COD 與 VFA")
    ax.axhline(E.VFA_ALARM, color=RED, ls="--", lw=1)
    ax.set_xlabel("天數")
    ax.set_ylabel("VFA（mg/L）")
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax.set_title("圖 6-2　數位孿生（AM2＋EKF）用每小時的產氣與 pH 修正模型，估計槽內 VFA")
    save(fig, "fa6-2-ekf")


def fig_warning(r):
    w = r["warn"]
    ev0 = 380 * 24
    rows = [(k, v["alarm_hour"]) for k, v in w["methods"].items()]
    fig, ax = plt.subplots(figsize=(12, 5.2))
    for i, (name, hr) in enumerate(rows):
        y = len(rows) - i
        if hr is None:
            ax.text(-11, y, "（這次沒有發出警報）", va="center", fontsize=10, color=NOTE)
        else:
            x = hr - ev0
            col = GREEN if hr <= w["true_danger_hour"] else RED
            ax.plot([x], [y], "D", color=col, ms=10)
            ax.text(x + 0.6, y + 0.18, f"{x:+.0f} h", fontsize=10, color=col)
        ax.text(-12.5, y, name, va="center", ha="right", fontsize=10.5)
    dz = w["true_danger_hour"] - ev0
    ax.axvline(0, color=GREY, lw=1)
    ax.text(0.3, len(rows) + 0.6, "過量進料開始", fontsize=10, color=NOTE)
    ax.axvline(dz, color=RED, lw=1.5, ls="--")
    ax.text(dz + 0.3, len(rows) + 0.6, "真實 VFA 超過 1500", fontsize=10, color=RED)
    ax.set_xlim(-12, 36)
    ax.set_ylim(0.3, len(rows) + 1)
    ax.set_yticks([])
    ax.set_xlabel("距離過量進料開始的時間（小時）")
    ax.set_title("圖 7-1　誰最早發現酸化？（綠色＝在出事前，紅色＝出事後才知道）")
    fig.subplots_adjust(left=0.33)
    save(fig, "fa7-1-warning")


def fig_drift(r):
    dr = r["drift"]
    days = np.arange(plant.DAYS)
    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    axes[0].plot(days, dr["resid_daily"], color=BLUE, lw=1.2)
    axes[0].axhline(0, color=GREY, lw=0.8)
    axes[0].set_ylabel("pH 讀值 − 預測值")
    axes[0].axvspan(220, 281, color=GREY, alpha=0.15)
    axes[0].text(222, axes[0].get_ylim()[0] * 0.9, "電極實際在漂移", color=NOTE, fontsize=10)
    axes[1].plot(days, dr["cusum"], color=PURPLE, lw=1.4)
    axes[1].axhline(dr["threshold"], color=RED, ls="--", lw=1)
    axes[1].axvline(dr["alarm_day"], color=RED, lw=1.5)
    axes[1].text(dr["alarm_day"] + 2, dr["threshold"] * 1.5, f"第 {dr['alarm_day']} 天發出警報\n（漂移開始後 {dr['alarm_day'] - 220} 天）",
                 color=RED, fontsize=10)
    axes[1].set_ylabel("CUSUM 累積偏差")
    axes[1].set_xlabel("天數")
    axes[1].set_xlim(180, 320)
    fig.suptitle("圖 7-2　用其他訊號「交叉檢查」pH 電極，提早發現感測器漂移", fontsize=15, weight="bold")
    save(fig, "fa7-2-sensor-drift")


def fig_recommend(r):
    rc = r["rec"]
    days = np.array(rc["days"])
    th = np.arange(len(rc["actual_vfa"])) / 24 + days[0]
    fig, axes = plt.subplots(3, 1, figsize=(12, 8.5), sharex=True)
    axes[0].step(days, np.array(rc["actual_D"]) * plant.V, where="post", color=RED, lw=1.8, label="實際進料（操作員）")
    axes[0].step(days, np.array(rc["rec_D"]) * plant.V, where="post", color=GREEN, lw=1.8, ls="--", label="照模型建議")
    axes[0].set_ylabel("進料量\n(m³/天)")
    axes[0].legend(frameon=False, fontsize=10, loc="upper left")
    axes[1].plot(th, rc["actual_vfa"], color=RED, lw=1.6, label="實際")
    axes[1].plot(th, rc["cf_vfa"], color=GREEN, lw=1.6, ls="--", label="照建議")
    axes[1].axhline(E.VFA_ALARM, color=GREY, ls=":", lw=1)
    axes[1].set_ylabel("VFA\n(mg/L)")
    axes[2].plot(th, rc["actual_ph"], color=RED, lw=1.6)
    axes[2].plot(th, rc["cf_ph"], color=GREEN, lw=1.6, ls="--")
    axes[2].axhline(7.0, color=GREY, ls=":", lw=1)
    axes[2].set_ylabel("pH")
    axes[2].set_xlabel("天數")
    fig.suptitle("圖 8-1　進料建議：用模型往前試算 5 天，避開 VFA 與 pH 越線（反事實模擬）", fontsize=15, weight="bold")
    save(fig, "fa8-1-recommend")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    res = E.run_all()
    for fn in (fig_overview, fig_forecast, fig_split, fig_soft, fig_ekf, fig_warning, fig_drift, fig_recommend):
        fn(res)
