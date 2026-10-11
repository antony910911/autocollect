"""AM2 兩步驟厭氧消化模型（Bernard et al., 2001）的教學版實作。

狀態（每公升）：
  X1 酸化菌 [g/L]、X2 產甲烷菌 [g/L]、S1 有機物 COD [g/L]、S2 揮發性脂肪酸 VFA [mmol/L]、
  Z 總鹼度 [mmol/L]、C 總無機碳 [mmol/L]
輸入：稀釋率 D [1/d]（＝進料流量 ÷ 槽體積）、進料濃度 S1in、S2in、Zin、Cin
輸出：甲烷產率 qM、CO₂ 產率 qC [mmol/L/d]、pH

參數取 AM2 文獻常用值；不同研究識別出的參數差異很大，這裡只用來產生「像真的」教學資料，
不能直接代表任何實廠。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np


@dataclass(frozen=True)
class Params:
    mu1max: float = 1.2    # 酸化菌最大比生長速率 [1/d]
    KS1: float = 7.1       # [g COD/L]
    mu2max: float = 0.74   # 產甲烷菌最大比生長速率 [1/d]
    KS2: float = 9.28      # [mmol/L]
    KI2: float = 256.0     # VFA 抑制常數 [mmol/L]
    alpha: float = 0.5     # 菌體留在槽內的程度（0＝完全留住，1＝隨出流流失）
    k1: float = 42.14
    k2: float = 116.5
    k3: float = 268.0
    k4: float = 50.6
    k5: float = 343.6
    k6: float = 453.0
    kLa: float = 19.8      # 氣液質傳 [1/d]
    KH: float = 16.0       # 亨利常數 [mmol/L/atm]
    PT: float = 1.0        # 總壓 [atm]
    Kb: float = 6.5e-7     # 碳酸氫根解離常數 [mol/L]


@dataclass
class Inputs:
    D: float
    S1in: float
    S2in: float = 5.0
    Zin: float = 50.0
    Cin: float = 40.0


def rates(x: np.ndarray, p: Params):
    X1, X2, S1, S2, Z, C = np.maximum(x, 1e-9)
    mu1 = p.mu1max * S1 / (p.KS1 + S1)
    mu2 = p.mu2max * S2 / (p.KS2 + S2 + S2 * S2 / p.KI2)
    qM = p.k6 * mu2 * X2
    phi = C + S2 - Z + p.KH * p.PT + p.k6 / p.kLa * mu2 * X2
    disc = max(phi * phi - 4 * p.KH * p.PT * (C + S2 - Z), 0.0)
    Pc = (phi - np.sqrt(disc)) / (2 * p.KH)
    qC = p.kLa * (C + S2 - Z - p.KH * Pc)
    return mu1, mu2, qM, qC


def deriv(x: np.ndarray, u: Inputs, p: Params) -> np.ndarray:
    X1, X2, S1, S2, Z, C = x
    mu1, mu2, qM, qC = rates(x, p)
    return np.array([
        (mu1 - p.alpha * u.D) * X1,
        (mu2 - p.alpha * u.D) * X2,
        u.D * (u.S1in - S1) - p.k1 * mu1 * X1,
        u.D * (u.S2in - S2) + p.k2 * mu1 * X1 - p.k3 * mu2 * X2,
        u.D * (u.Zin - Z),
        u.D * (u.Cin - C) - qC + p.k4 * mu1 * X1 + p.k5 * mu2 * X2,
    ])


def step(x: np.ndarray, u: Inputs, p: Params, dt: float, substeps: int = 4) -> np.ndarray:
    """RK4 積分 dt 天。"""
    h = dt / substeps
    for _ in range(substeps):
        k1 = deriv(x, u, p)
        k2 = deriv(x + h / 2 * k1, u, p)
        k3 = deriv(x + h / 2 * k2, u, p)
        k4 = deriv(x + h * k3, u, p)
        x = np.maximum(x + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4), 1e-9)
    return x


def ph(x: np.ndarray, p: Params) -> float:
    _, _, _, S2, Z, C = x
    B = max(Z - S2, 0.03 * Z)         # 碳酸氫根（鹼度扣掉 VFA；設下限避免數值失真）
    co2 = max(C - B, 1e-6)            # 溶解 CO₂
    return float(-np.log10(p.Kb * co2 / B))


X0 = np.array([0.5, 0.9, 1.0, 8.0, 50.0, 45.0])
