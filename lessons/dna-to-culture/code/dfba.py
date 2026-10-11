"""動態通量平衡分析（dFBA）：把代謝模型放進批次培養的時間軸。

做法（Mahadevan et al., 2002 的「靜態最佳化法」）：每一小段時間
  1. 依目前培養液裡的濃度，算出細胞最多能吸收多少基質（Michaelis–Menten 動力學）；
  2. 用 FBA 算出這段時間的生長率與分泌物；
  3. 更新菌量與濃度，進到下一段時間。

GEM 本身不知道溫度和 pH，這裡用經驗模型補上（第 7 章）：
  溫度用 Rosso 等人 (1993) 的 CTMI，pH 用 Rosso 等人 (1995) 的 CPMI，兩者相乘當作「吸收能力的折扣」。
遲滯期用 Baranyi 與 Roberts (1994) 的調適函數。

兩種計算模式：
  mode="lp"    每一步都真的解一次線性規劃（慢、最準）；
  mode="table" 事先在網格上解好，查表內插（快 100 倍以上；互動模擬器用的就是這張表）。
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TABLE_FILE = HERE / "tables.json"

# 查表的網格（mmol/gDW/h）
GLC_GRID = np.arange(0, 10.01, 0.5)
AC_GRID = np.arange(0, 6.01, 0.5)
O2_GRID = np.arange(0, 20.01, 0.5)
FIELDS = ["mu", "glc", "o2", "ac", "etoh", "for", "lac", "succ", "co2"]


@dataclass
class Params:
    T: float = 37.0            # 溫度 °C
    pH: float = 7.0
    G0: float = 60.0           # 起始葡萄糖 mM（60 mM ≈ 10.8 g/L）
    X0: float = 0.05           # 接種量 gDW/L（約 OD600 0.13）
    otr: float = 30.0          # 最大供氧能力 mmol O2/L/h（搖瓶約 5–30，發酵槽可到 100 以上）
    t_sw: float = 1e9          # 第幾小時切換成厭氧（停止通氣）；1e9 = 不切換
    t_end: float = 24.0
    lag: float = 1.0           # 遲滯期（小時），反映接種前的狀態
    dt: float = 0.05
    # 吸收動力學（Varma & Palsson, 1994 的量級；換菌要用實驗重新估計）
    vmax_glc: float = 10.0
    km_glc: float = 0.015
    vmax_ac: float = 4.0
    km_ac: float = 0.5
    vmax_o2: float = 15.0      # 細胞呼吸鏈最多能用多少氧
    # 溫度、pH 的基點值（示範用的假設值；自己的菌要用實驗估計，見第 7 章）
    Tmin: float = 5.0
    Topt: float = 39.0
    Tmax: float = 47.0
    pHmin: float = 4.0
    pHopt: float = 7.0
    pHmax: float = 9.5
    stage2: dict = field(default_factory=dict)   # 切換後要改的參數，例如 {"T": 33}


def ctmi(T, Tmin, Topt, Tmax):
    """Rosso 等人 (1993) 的溫度基點模型，回傳 0–1。"""
    if T <= Tmin or T >= Tmax:
        return 0.0
    num = (T - Tmax) * (T - Tmin) ** 2
    den = (Topt - Tmin) * ((Topt - Tmin) * (T - Topt) - (Topt - Tmax) * (Topt + Tmin - 2 * T))
    return max(0.0, num / den)


def cpmi(pH, pHmin, pHopt, pHmax):
    """Rosso 等人 (1995) 的 pH 基點模型，回傳 0–1。"""
    if pH <= pHmin or pH >= pHmax:
        return 0.0
    num = (pH - pHmin) * (pH - pHmax)
    return max(0.0, num / (num - (pH - pHopt) ** 2))


def baranyi_alpha(t, lag, nu=1.0):
    """遲滯期調適函數：0（剛接種、還沒準備好）→ 1（完全適應）。"""
    if lag <= 0:
        return 1.0
    q0 = 1.0 / (math.exp(lag * nu) - 1.0)
    q = q0 * math.exp(nu * t)
    return q / (1.0 + q)


# ── 查表 ──
_TABLES = None


def build_tables(path: Path = TABLE_FILE) -> dict:
    """在網格上解 pFBA，存成 JSON（約 900 + 500 次線性規劃，30 秒內）。"""
    import gem
    tables = {"glc_grid": GLC_GRID.tolist(), "ac_grid": AC_GRID.tolist(), "o2_grid": O2_GRID.tolist(),
              "fields": FIELDS, "map_rxns": gem.MAP_RXNS}
    for phase, grid, key in (("glucose", GLC_GRID, "glc"), ("acetate", AC_GRID, "ac")):
        vals = {f: [] for f in FIELDS}
        maps = []
        for s in grid:
            rows = {f: [] for f in FIELDS}
            mrow = []
            for o in O2_GRID:
                kw = {"glc": float(s), "o2": float(o), "ac": 0.0} if key == "glc" else \
                     {"glc": 0.0, "o2": float(o), "ac": float(s)}
                r = gem.solve(**kw)
                for f in FIELDS:
                    rows[f].append(round(r[f], 4) if r else 0.0)
                mrow.append([round(r["map"][x], 3) if r else 0.0 for x in gem.MAP_RXNS])
            for f in FIELDS:
                vals[f].append(rows[f])
            maps.append(mrow)
        tables[phase] = vals
        tables[phase + "_map"] = maps
    path.write_text(json.dumps(tables, separators=(",", ":")), "utf-8")
    return tables


def tables() -> dict:
    global _TABLES
    if _TABLES is None:
        if not TABLE_FILE.exists():
            build_tables()
        t = json.loads(TABLE_FILE.read_text("utf-8"))
        for ph in ("glucose", "acetate"):
            t[ph] = {f: np.array(v) for f, v in t[ph].items()}
            t[ph + "_map"] = np.array(t[ph + "_map"])
        _TABLES = t
    return _TABLES


def _bilinear(grid_a, grid_b, arr, a, b):
    a = min(max(a, grid_a[0]), grid_a[-1])
    b = min(max(b, grid_b[0]), grid_b[-1])
    i = min(int((a - grid_a[0]) / (grid_a[1] - grid_a[0])), len(grid_a) - 2)
    j = min(int((b - grid_b[0]) / (grid_b[1] - grid_b[0])), len(grid_b) - 2)
    u = (a - grid_a[i]) / (grid_a[1] - grid_a[0])
    v = (b - grid_b[j]) / (grid_b[1] - grid_b[0])
    return ((1 - u) * (1 - v) * arr[i, j] + u * (1 - v) * arr[i + 1, j]
            + (1 - u) * v * arr[i, j + 1] + u * v * arr[i + 1, j + 1])


def lookup(phase: str, s: float, o2: float, with_map: bool = False) -> dict | None:
    t = tables()
    ga = np.array(t["glc_grid"] if phase == "glucose" else t["ac_grid"])
    go = np.array(t["o2_grid"])
    out = {f: float(_bilinear(ga, go, t[phase][f], s, o2)) for f in FIELDS}
    if out["mu"] <= 1e-6:
        return None
    if with_map:
        out["map"] = dict(zip(t["map_rxns"], _bilinear(ga, go, t[phase + "_map"], s, o2).tolist()))
    return out


def flux(phase: str, s: float, o2: float, mode: str) -> dict | None:
    if mode == "table":
        return lookup(phase, s, o2)
    import gem
    return gem.solve(glc=s, o2=o2) if phase == "glucose" else gem.solve(glc=0.0, o2=o2, ac=s)


# ── 模擬 ──
def simulate(p: Params, mode: str = "table") -> dict:
    n = int(round(p.t_end / p.dt)) + 1
    keys = ["t", "X", "G", "A", "E", "F", "S", "L", "mu", "q_o2", "our", "cer", "o2_lim", "env"]
    out = {k: np.zeros(n) for k in keys}
    out["phase"] = []
    X, G, A, E, F, S, L = p.X0, p.G0, 0.0, 0.0, 0.0, 0.0, 0.0
    env1 = ctmi(p.T, p.Tmin, p.Topt, p.Tmax) * cpmi(p.pH, p.pHmin, p.pHopt, p.pHmax)
    q = {**asdict(p), **p.stage2}
    env2 = ctmi(q["T"], p.Tmin, p.Topt, p.Tmax) * cpmi(q["pH"], p.pHmin, p.pHopt, p.pHmax)
    for k in range(n):
        t = k * p.dt
        alpha = baranyi_alpha(t, p.lag)
        aerobic = t < p.t_sw
        f_env = (env1 if aerobic else env2) * alpha
        otr = p.otr if aerobic else q["otr"] if "otr" in p.stage2 else 0.0
        o2_cap = min(p.vmax_o2, otr / max(X, 1e-9))
        if G > 1e-6:
            phase = "glucose"
            s = f_env * p.vmax_glc * G / (p.km_glc + G)
            s = min(s, G / (X * p.dt))           # 不能吃掉比現有還多的糖
        elif A > 1e-6:
            phase = "acetate"
            s = f_env * p.vmax_ac * A / (p.km_ac + A)
            s = min(s, A / (X * p.dt))
        else:
            phase, s = "none", 0.0
        r = flux(phase, s, o2_cap, mode) if phase != "none" and s > 1e-9 else None
        if r is None:
            r = {f: 0.0 for f in FIELDS}
        mu = r["mu"]
        q_o2 = -r["o2"]
        o2_lim = otr > 0 and o2_cap < p.vmax_o2 - 1e-6 and q_o2 >= o2_cap - 1e-3 and mu > 0
        # 判斷目前處在哪個階段（給圖和模擬器標示用）
        if alpha < 0.5 and mu > 0:
            label = "遲滯期"
        elif mu <= 1e-4:
            label = "停滯期"
        elif phase == "acetate":
            label = "回頭吃乙酸"
        elif otr <= 0:
            label = "厭氧發酵"
        elif o2_lim:
            label = "缺氧・溢流代謝"
        else:
            label = "好氧指數生長"
        for key, val in zip(keys, [t, X, G, A, E, F, S, L, mu, q_o2, q_o2 * X, r["co2"] * X, float(o2_lim), f_env]):
            out[key][k] = val
        out["phase"].append(label)
        # 更新（歐拉法）
        dX = mu * X * p.dt
        G = max(0.0, G + r["glc"] * X * p.dt)
        A = max(0.0, A + r["ac"] * X * p.dt)
        E += max(0.0, r["etoh"]) * X * p.dt
        F += max(0.0, r["for"]) * X * p.dt
        S += max(0.0, r["succ"]) * X * p.dt
        L += max(0.0, r["lac"]) * X * p.dt
        X += dX
    out["params"] = asdict(p)
    return out


def summary(sim: dict) -> dict:
    """批次結束時的常用指標。"""
    t, X, E = sim["t"], sim["X"], sim["E"]
    p = sim["params"]
    used = p["G0"] - sim["G"][-1]
    return {"X_end": float(X[-1]), "X_max": float(X.max()), "E_end": float(E[-1]),
            "E_gL": float(E[-1] * 46.07 / 1000), "A_max": float(sim["A"].max()),
            "glc_left": float(sim["G"][-1]), "Y_E_G": float(E[-1] / used) if used > 0 else 0.0,
            "prod_E": float(E[-1] / t[-1]),
            "t_glc_out": float(t[np.argmax(sim["G"] <= 1e-6)]) if (sim["G"] <= 1e-6).any() else None}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE))
    build_tables()
    print("寫入", TABLE_FILE)
