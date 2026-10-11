"""產生教學用的「模擬沼氣廠」資料：480 天、每小時一筆線上量測、每週兩次實驗室分析。

情境（刻意安排，讓每種建模方法都有東西可學）：
- 原料濃度每天變動，並有季節起伏；週末進料較少。
- 第 150–155 天：小規模過量進料（訓練期內，讓模型看過一次異常）。
- 第 220–280 天：pH 電極慢慢漂移，第 281 天校正歸零（感測器故障偵測的題材）。
- 第 300 天起：換了一批原料，平均濃度變高（概念漂移）。
- 第 380–386 天：大規模過量進料，造成酸化（測試期，用來比較預警）。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np

from am2 import X0, Inputs, Params, ph, rates, step

V = 2000.0            # 消化槽有效體積 [m³]
NM3_PER_MOL = 0.0224  # 1 mol 氣體在標準狀態的體積 [Nm³]
VFA_MG_PER_MMOL = 60  # 以乙酸計
TRUE_PARAMS = replace(Params(), mu2max=0.42, KI2=120.0, alpha=0.8)  # 「真實」廠的參數，和教科書值不同
DAYS = 480
EVENTS = {"小過量": (150, 156), "pH 電極漂移": (220, 281), "換原料": (300, DAYS), "大過量": (380, 387)}


def schedule(rng: np.random.Generator):
    """每天的操作輸入。"""
    d = np.arange(DAYS)
    season = 1 + 0.08 * np.sin(2 * np.pi * d / 365)
    S1in = 25 * season * np.exp(rng.normal(0, 0.10, DAYS))
    S1in[300:] *= 1.15
    S2in = 10 * np.exp(rng.normal(0, 0.25, DAYS))
    D = 0.12 * np.exp(rng.normal(0, 0.06, DAYS))
    D[d % 7 == 6] *= 0.6  # 週日少進料
    D[150:156], S1in[150:156], S2in[150:156] = 0.18, 40, 120
    D[380:387], S1in[380:387], S2in[380:387] = 0.20, 45, 150
    return D, S1in, S2in


def simulate(seed: int = 7, params: Params = TRUE_PARAMS):
    rng = np.random.default_rng(seed)
    D, S1in, S2in = schedule(rng)
    x = X0.copy()
    for _ in range(24 * 200):  # 先跑到穩態
        x = step(x, Inputs(D[:30].mean(), S1in[:30].mean(), 10, 100, 80), params, 1 / 24, 1)
    hours = DAYS * 24
    states = np.zeros((hours, 6))
    out = np.zeros((hours, 3))  # qM, qC, pH
    for h in range(hours):
        day = h // 24
        u = Inputs(D[day], S1in[day], S2in[day], 100, 80)
        x = step(x, u, params, 1 / 24, 1)
        _, _, qM, qC = rates(x, params)
        states[h], out[h] = x, (qM, qC, ph(x, params))
    return dict(D=D, S1in=S1in, S2in=S2in, states=states, out=out, rng=rng)


def measurements(sim: dict):
    """把真實狀態轉成「感測器看到的樣子」：加雜訊、漂移與缺漏。"""
    rng = sim["rng"]
    qM, qC, pH = sim["out"].T
    hours = len(qM)
    t = np.arange(hours) / 24
    ch4_flow = qM * V * NM3_PER_MOL / 24 * (1 + rng.normal(0, 0.02, hours))       # Nm³/h
    biogas = (qM + qC) * V * NM3_PER_MOL / 24 * (1 + rng.normal(0, 0.02, hours))  # Nm³/h
    ch4_pct = 100 * qM / (qM + qC) + rng.normal(0, 0.4, hours)
    drift = np.where((t >= 220) & (t < 281), -0.006 * (t - 220), 0.0)             # pH 電極漂移
    ph_meas = pH + drift + rng.normal(0, 0.02, hours)
    temp = 37 + rng.normal(0, 0.15, hours)
    gaps = rng.random(hours) < 0.01                                               # 1% 資料缺漏
    for arr in (ch4_flow, biogas, ch4_pct, ph_meas, temp):
        arr[gaps] = np.nan
    S2 = sim["states"][:, 3]
    Z = sim["states"][:, 4]
    feed_m3 = np.repeat(sim["D"] * V, 24) / 24
    hourly = dict(t=t, ch4_flow=ch4_flow, biogas=biogas, ch4_pct=ch4_pct, ph=ph_meas, temp=temp, feed_m3=feed_m3,
                  vfa_true=S2 * VFA_MG_PER_MMOL, ratio_true=S2 / Z, ph_true=pH, drift=drift)
    # 實驗室：每週一、四上午 9 點採樣，VFA 有 5% 分析誤差
    lab_days = [d for d in range(DAYS) if d % 7 in (0, 3)]
    idx = np.array([d * 24 + 9 for d in lab_days])
    lab = dict(day=np.array(lab_days), vfa=S2[idx] * VFA_MG_PER_MMOL * (1 + rng.normal(0, 0.05, len(idx))),
               cod_in=sim["S1in"][lab_days] * (1 + rng.normal(0, 0.05, len(idx))))
    return hourly, lab


def daily_table(hourly: dict, sim: dict):
    """每日彙總：營運最常用的時間尺度。"""
    def dmean(a):
        return np.nanmean(a.reshape(DAYS, 24), axis=1)

    return dict(day=np.arange(DAYS), ch4_m3=dmean(hourly["ch4_flow"]) * 24, biogas_m3=dmean(hourly["biogas"]) * 24,
                ch4_pct=dmean(hourly["ch4_pct"]), ph=dmean(hourly["ph"]), feed_m3=sim["D"] * V,
                cod_load_kg=sim["D"] * V * sim["S1in"], vfa_true=dmean(hourly["vfa_true"]),
                ph_true=dmean(hourly["ph_true"]), ratio_true=dmean(hourly["ratio_true"]))


def build(seed: int = 7):
    sim = simulate(seed)
    hourly, lab = measurements(sim)
    return sim, hourly, lab, daily_table(hourly, sim)


if __name__ == "__main__":
    import time
    t0 = time.time()
    sim, hourly, lab, daily = build()
    print(f"模擬完成 {time.time() - t0:.1f}s")
    for a, b in [(140, 170), (370, 400)]:
        for d in range(a, b, 3):
            print(d, round(daily["ch4_m3"][d]), round(daily["vfa_true"][d]), round(daily["ph"][d], 2), round(daily["cod_load_kg"][d]))
    print("lab n=", len(lab["day"]))
