"""教材第 4–8 章的計算實驗。執行：python experiments.py（約 1–2 分鐘），結果寫到 results.json。

1 FBA：氧氣、碳源、生長限制因子、基因剔除、中心代謝流量
2 dFBA：批次生長曲線、階段與指標、生長曲線擬合
3 兩階段：好氧長菌 → 厭氧產乙醇，切換時間掃描、各階段敏感度
4 環境參數：溫度 × pH
5 少做實驗：一次改一個因子、隨機、貝氏最適化的比較
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dfba  # noqa: E402
import gem  # noqa: E402

OUT = HERE / "results.json"
# 兩階段實驗的共同設定：200 mM 葡萄糖（36 g/L），第 12 小時收穫
TWO = dfba.Params(G0=200.0, t_end=12.0)
# 參數搜尋範圍（第 8 章）
BOUNDS = {"T": (25.0, 45.0), "pH": (5.0, 9.0), "otr": (2.0, 40.0), "t_sw": (0.0, 12.0)}
NOISE = 0.05  # 實驗量測的相對誤差


# ─────────────── 1 FBA ───────────────
def exp_fba() -> dict:
    res = {"model": gem.info()}
    o2s = np.arange(0, 25.01, 0.5)
    scan = []
    for o in o2s:
        r = gem.solve(glc=10, o2=float(o))
        scan.append({k: r[k] for k in ("mu", "o2", "ac", "etoh", "for", "succ", "lac", "co2")})
    res["o2_scan"] = {"o2": o2s.tolist(), "rows": scan}

    carb = []
    for name, (rid, nc) in gem.CARBON_SOURCES.items():
        up = 60.0 / nc  # 每種碳源都給「每小時 60 mmol 碳」，公平比較
        r = gem.solve(glc=0, o2=1000, other={rid: up}, parsimonious=False)
        mu = r["mu"] if r else 0.0
        carb.append({"name": name, "uptake": up, "mu": mu, "yield_per_c": mu / 60.0 * 1000})  # mgDW / mmol C
    res["carbon"] = sorted(carb, key=lambda d: -d["mu"])

    # 表型相平面：葡萄糖 × 氧氣 的最大生長率
    gg = np.arange(0, 20.01, 0.5)
    oo = np.arange(0, 40.01, 1.0)
    grid = []
    for g in gg:
        row = []
        for o in oo:
            r = gem.solve(glc=float(g), o2=float(o), parsimonious=False)
            row.append(r["mu"] if r else 0.0)
        grid.append(row)
    res["phase_plane"] = {"glc": gg.tolist(), "o2": oo.tolist(), "mu": grid}
    # 生長率對各基質的敏感度（影子價格）在三種情境
    res["shadow"] = {name: gem.shadow_prices(**kw) for name, kw in
                     {"氧氣充足": dict(glc=10, o2=1000), "氧氣受限": dict(glc=10, o2=8), "糖受限": dict(glc=3, o2=1000)}.items()}

    aer, ana = gem.gene_deletions(1000), gem.gene_deletions(0)
    ana_map = {d["gene"]: d["rel"] for d in ana}
    genes = [{"gene": d["gene"], "name": d["name"], "aerobic": d["rel"], "anaerobic": ana_map[d["gene"]]} for d in aer]
    res["knockouts"] = {"genes": genes,
                        "essential_aerobic": [g["name"] for g in genes if g["aerobic"] < 0.01],
                        "essential_anaerobic": [g["name"] for g in genes if g["anaerobic"] < 0.01],
                        "n_genes": len(genes)}
    res["maps"] = {"好氧": gem.solve(glc=10, o2=1000)["map"], "缺氧": gem.solve(glc=10, o2=5)["map"],
                   "厭氧": gem.solve(glc=10, o2=0)["map"]}
    res["maps_exchange"] = {k: {x: gem.solve(glc=10, o2=o)[x] for x in ("mu", "ac", "etoh", "for", "co2", "o2")}
                            for k, o in {"好氧": 1000, "缺氧": 5, "厭氧": 0}.items()}
    return res


# ─────────────── 2 dFBA ───────────────
def _ts(sim, keys=("t", "X", "G", "A", "E", "F", "mu", "q_o2", "our", "cer", "o2_lim"), every=2):
    return {k: np.round(sim[k][::every], 4).tolist() for k in keys} | {"phase": sim["phase"][::every]}


def gompertz(t, A, mu, lam):
    """Zwietering 等人 (1990) 修正的 Gompertz 模型；y = ln(N/N0)。"""
    return A * np.exp(-np.exp(mu * math.e / A * (lam - t) + 1))


def exp_dfba() -> dict:
    from scipy.optimize import curve_fit
    base = dfba.Params(lag=1.5)
    lp = dfba.simulate(base, mode="lp")
    tb = dfba.simulate(base, mode="table")
    res = {"batch": _ts(lp), "summary": dfba.summary(lp),
           "lp_vs_table": {"max_dX": float(np.abs(lp["X"] - tb["X"]).max()),
                           "max_dA": float(np.abs(lp["A"] - tb["A"]).max()),
                           "max_dG": float(np.abs(lp["G"] - tb["G"]).max())}}
    # 各階段的起訖時間
    spans, cur, start = [], lp["phase"][0], 0.0
    for t, ph in zip(lp["t"], lp["phase"]):
        if ph != cur:
            spans.append({"phase": cur, "start": start, "end": float(t)})
            cur, start = ph, float(t)
    spans.append({"phase": cur, "start": start, "end": float(lp["t"][-1])})
    res["spans"] = spans
    # 用「每小時量一次 OD」的假資料擬合 Gompertz，看能不能找回生長參數
    rng = np.random.default_rng(7)
    idx = np.arange(0, len(lp["t"]), 20)
    t_obs = lp["t"][idx]
    y_true = np.log(lp["X"][idx] / lp["X"][0])
    y_obs = y_true + rng.normal(0, 0.06, len(idx))
    popt, _ = curve_fit(gompertz, t_obs, y_obs, p0=[4, 0.6, 1.0])
    mu_obs = np.gradient(np.log(lp["X"]), lp["t"])
    # 另一種做法：只取指數期（ln OD 近似直線的那段）做線性迴歸
    sel = (t_obs >= 2) & (t_obs <= 6)
    slope = float(np.polyfit(t_obs[sel], y_obs[sel], 1)[0])
    res["gompertz"] = {"t": t_obs.tolist(), "y": y_obs.tolist(), "A": popt[0], "mu": popt[1], "lam": popt[2],
                       "mu_model_max": float(mu_obs.max()), "mu_loglinear": slope}
    # 供氧能力不同時的生長曲線
    res["otr_curves"] = {str(o): _ts(dfba.simulate(replace(base, otr=o)), keys=("t", "X", "A"), every=4)
                         for o in (10, 30, 100)}
    return res


# ─────────────── 3 兩階段 ───────────────
def exp_two_stage() -> dict:
    res = {"setup": {"G0": TWO.G0, "t_end": TWO.t_end}}
    strategies = {"全程好氧": 1e9, "全程厭氧": 0.0}
    sw = np.arange(0, 12.01, 0.25)
    rows = []
    for tend in (10.0, 12.0, 16.0, 24.0):
        for s in sw:
            if s > tend:
                continue
            sm = dfba.summary(dfba.simulate(replace(TWO, t_sw=float(s), t_end=tend)))
            rows.append({"t_end": tend, "t_sw": float(s), **sm})
    res["scan"] = rows
    best = {}
    for tend in (10.0, 12.0, 16.0, 24.0):
        r = max((x for x in rows if x["t_end"] == tend), key=lambda x: x["E_end"])
        best[str(tend)] = r
    res["best"] = best
    strategies["兩階段（最佳切換）"] = best["12.0"]["t_sw"]
    res["curves"] = {name: _ts(dfba.simulate(replace(TWO, t_sw=s))) for name, s in strategies.items()}
    res["curves_sw"] = strategies
    # 切換規則：「現有菌量在剩下時間內，用厭氧吃糖速率能不能吃完剩下的糖」
    rule = []
    for tend in (10.0, 12.0, 16.0):
        sim = dfba.simulate(replace(TWO, t_end=tend))
        q_ana = 10.0  # 厭氧時每克菌每小時最多吃 10 mmol 糖（模型設定）
        hit = None
        for t, X, G in zip(sim["t"], sim["X"], sim["G"]):
            # 厭氧期間菌量還會長（μ≈0.21/h），用平均菌量估計
            remain = tend - t
            if remain <= 0:
                break
            mu_a = 0.21
            x_avg = X * (math.exp(mu_a * remain) - 1) / (mu_a * remain)
            if x_avg * q_ana * remain >= G:
                hit = float(t)
                break
        rule.append({"t_end": tend, "rule_t_sw": hit, "best_t_sw": best[str(tend)]["t_sw"]})
    res["rule"] = rule
    # 各階段的敏感度：只在第一或第二階段改一個參數，收穫時乙醇變多少
    t_sw = best["12.0"]["t_sw"]
    ref = dfba.summary(dfba.simulate(replace(TWO, t_sw=t_sw)))["E_end"]
    pert = {"溫度 −4 °C": ("T", -4.0), "pH −1": ("pH", -1.0)}
    sens = []
    for label, (k, d) in pert.items():
        p1 = replace(TWO, t_sw=t_sw, stage2={k: getattr(TWO, k)}, **{k: getattr(TWO, k) + d})
        p2 = replace(TWO, t_sw=t_sw, stage2={k: getattr(TWO, k) + d})
        sens.append({"label": label, "stage1": dfba.summary(dfba.simulate(p1))["E_end"] - ref,
                     "stage2": dfba.summary(dfba.simulate(p2))["E_end"] - ref})
    sens.append({"label": "供氧 −30%", "stage1": dfba.summary(dfba.simulate(replace(TWO, t_sw=t_sw, otr=TWO.otr * 0.7)))["E_end"] - ref,
                 "stage2": 0.0})
    sens.append({"label": "第二階段微量通氣\n(2 mmol/L/h)", "stage1": 0.0,
                 "stage2": dfba.summary(dfba.simulate(replace(TWO, t_sw=t_sw, stage2={"otr": 2.0})))["E_end"] - ref})
    sens.append({"label": "接種量 −50%", "stage1": dfba.summary(dfba.simulate(replace(TWO, t_sw=t_sw, X0=TWO.X0 * 0.5)))["E_end"] - ref,
                 "stage2": 0.0})
    sens.append({"label": "切換提早 1 h", "stage1": dfba.summary(dfba.simulate(replace(TWO, t_sw=t_sw - 1)))["E_end"] - ref,
                 "stage2": 0.0})
    sens.append({"label": "切換延後 1 h", "stage1": dfba.summary(dfba.simulate(replace(TWO, t_sw=t_sw + 1)))["E_end"] - ref,
                 "stage2": 0.0})
    res["sensitivity"] = {"ref": ref, "t_sw": t_sw, "rows": sens}
    return res


# ─────────────── 4 溫度 × pH ───────────────
def exp_env() -> dict:
    Ts = np.arange(20, 47.01, 1.0)
    pHs = np.arange(4.5, 9.51, 0.25)
    xg, eg = [], []
    for T in Ts:
        rx, re_ = [], []
        for ph in pHs:
            rx.append(dfba.summary(dfba.simulate(replace(TWO, T=float(T), pH=float(ph), t_end=12.0)))["X_end"])
            re_.append(dfba.summary(dfba.simulate(replace(TWO, T=float(T), pH=float(ph), t_sw=5.75)))["E_end"])
        xg.append(rx)
        eg.append(re_)
    p = dfba.Params()
    curves = {"T": [dfba.ctmi(t, p.Tmin, p.Topt, p.Tmax) for t in np.arange(0, 50.01, 0.5)],
              "pH": [dfba.cpmi(x, p.pHmin, p.pHopt, p.pHmax) for x in np.arange(3, 10.01, 0.05)]}
    return {"T": Ts.tolist(), "pH": pHs.tolist(), "X_end": xg, "E_end": eg, "cardinal": curves,
            "cardinal_params": {k: getattr(p, k) for k in ("Tmin", "Topt", "Tmax", "pHmin", "pHopt", "pHmax")}}


# ─────────────── 5 少做實驗 ───────────────
def objective(x: dict, rng=None) -> float:
    """一次「實驗」：用給定條件培養 12 小時，量乙醇（mM）。rng 不為 None 時加上 5% 量測誤差。"""
    p = replace(TWO, T=x["T"], pH=x["pH"], otr=x["otr"], t_sw=x["t_sw"])
    y = dfba.summary(dfba.simulate(p))["E_end"]
    if rng is not None:
        y *= float(np.exp(rng.normal(0, NOISE)))
    return y


def _to_x(u):
    return {k: lo + float(v) * (hi - lo) for v, (k, (lo, hi)) in zip(u, BOUNDS.items())}


def true_optimum() -> dict:
    from scipy.optimize import differential_evolution
    r = differential_evolution(lambda u: -objective(_to_x(u)), [(0, 1)] * 4, seed=1, maxiter=60, popsize=12,
                               tol=1e-6, polish=False)
    return {"x": _to_x(r.x), "y": -r.fun}


def run_ofat(rng, budget):
    """一次改一個因子：從一個起始條件出發，依序掃描每個因子，固定在最好的值再換下一個。

    起始條件隨機抽（代表「對這株菌沒有先驗知識」）；如果起點本來就接近最佳，這個方法會表現得很好。
    """
    x = _to_x(rng.random(4))
    hist = []
    per = budget // 4
    for k, (lo, hi) in BOUNDS.items():
        best_v, best_y = x[k], -1
        for v in np.linspace(lo, hi, per):
            xx = dict(x, **{k: float(v)})
            y = objective(xx, rng)
            hist.append((xx, y))
            if y > best_y:
                best_v, best_y = float(v), y
        x[k] = best_v
    return hist


def run_random(rng, budget):
    return [(x, objective(x, rng)) for x in (_to_x(rng.random(4)) for _ in range(budget))]


def run_bo(rng, budget, n_init=6):
    """貝氏最適化：高斯過程代理模型＋期望改善（EI）。"""
    from scipy.stats import norm
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
    from scipy.stats import qmc
    U = qmc.LatinHypercube(d=4, seed=rng).random(n_init).tolist()
    Y = [objective(_to_x(u), rng) for u in U]
    while len(Y) < budget:
        gp = GaussianProcessRegressor(ConstantKernel(1.0) * Matern(length_scale=[0.3] * 4, nu=2.5,
                                                                   length_scale_bounds=(0.03, 3))
                                      + WhiteKernel(1e-2, (1e-5, 1)), normalize_y=True,
                                      random_state=int(rng.integers(1e9)))
        gp.fit(np.array(U), np.array(Y))
        cand = rng.random((4000, 4))
        mu, sd = gp.predict(cand, return_std=True)
        best = max(Y)
        z = (mu - best) / np.maximum(sd, 1e-9)
        ei = (mu - best) * norm.cdf(z) + sd * norm.pdf(z)
        u = cand[int(np.argmax(ei))].tolist()
        U.append(u)
        Y.append(objective(_to_x(u), rng))
    return [(_to_x(u), y) for u, y in zip(U, Y)]


def exp_optimize(n_seeds: int = 20, budget: int = 28) -> dict:
    opt = true_optimum()
    curves = {}
    finals = {}
    example = {}
    for name, fn in {"一次改一個因子": run_ofat, "隨機": run_random, "貝氏最適化": run_bo}.items():
        allc, fin = [], []
        for seed in range(n_seeds):
            rng = np.random.default_rng(seed)
            hist = fn(rng, budget)
            # 每一輪「目前認為最好的條件」的真實表現（不含量測誤差）
            best_true, cur, cy = [], None, -1
            for x, y in hist:
                if y > cy:
                    cur, cy = x, y
                best_true.append(objective(cur))
            allc.append(best_true)
            fin.append(best_true[-1])
            if seed == 0:
                example[name] = [{"x": x, "y": y} for x, y in hist]
        a = np.array(allc)
        curves[name] = {"median": np.median(a, 0).tolist(), "q25": np.percentile(a, 25, 0).tolist(),
                        "q75": np.percentile(a, 75, 0).tolist()}
        finals[name] = {"median": float(np.median(fin)), "min": float(np.min(fin)), "max": float(np.max(fin)),
                        "pct_of_opt": float(np.median(fin) / opt["y"] * 100)}
    # 交互作用：最佳切換時間隨供氧能力改變
    inter = []
    for otr in (3, 5, 10, 20, 40):
        ys = [(s, objective({"T": 37.0, "pH": 7.0, "otr": float(otr), "t_sw": float(s)})) for s in np.arange(0, 12.01, 0.25)]
        s, y = max(ys, key=lambda v: v[1])
        inter.append({"otr": otr, "best_t_sw": s, "E": y, "curve": ys})
    return {"optimum": opt, "budget": budget, "n_seeds": n_seeds, "curves": curves, "finals": finals,
            "example": example, "interaction": inter, "bounds": BOUNDS}


def main():
    import time
    t0 = time.time()
    res = {}
    for name, fn in (("fba", exp_fba), ("dfba", exp_dfba), ("two_stage", exp_two_stage), ("env", exp_env),
                     ("optimize", exp_optimize)):
        res[name] = fn()
        print(f"{name} 完成（{time.time() - t0:.0f} 秒）")
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1,
                              default=lambda o: float(o) if isinstance(o, np.floating) else o), "utf-8")
    print("寫入", OUT)


if __name__ == "__main__":
    main()
