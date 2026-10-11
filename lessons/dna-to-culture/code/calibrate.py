"""把實驗數據餵回模型：讀 CSV → 檢查 → 算衍生量 → 校正參數 → 驗證 → 存檔。

執行：python calibrate.py（約 1–2 分鐘），結果寫到 calibration.json

五個步驟，對應教材第 11 章：
  1 load_data      讀兩張表，做格式與單位檢查
  2 check          資料品質檢查：缺漏、異常、單調性、物質收支
  3 derive         每批算出 μmax、遲滯期、產率、比耗糖速率（不需要模型就能算）
  4 fit            用訓練批次校正模型參數（最小平方）
  5 validate       用沒參與校正的批次驗證；再做參數敏感度（哪些參數真的被數據決定）

重點：**驗證批次不能參與校正**。否則「模型很準」只是因為它背過答案。
"""

from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

import dfba

HERE = Path(__file__).resolve().parent
DATA = HERE / "example-data"
OUT = HERE / "calibration.json"
OD_TO_GDW = 0.35
MW_GLC, MW_ETOH, MW_AC = 180.16, 46.07, 60.05

# 要校正的參數：名稱、起始值（＝教材預設值）、下限、上限、中文說明
FIT_PARAMS = [
    ("vmax_glc", 10.0, 4.0, 16.0, "最大吃糖速率（mmol/gDW/h）"),
    ("km_glc", 0.015, 0.001, 1.0, "吃糖的半飽和常數 Km（mM）"),
    ("vmax_o2", 15.0, 6.0, 25.0, "最大耗氧能力（mmol/gDW/h）"),
    ("otr_factor", 1.0, 0.4, 1.3, "實際供氧 ÷ 設定供氧"),
    ("Topt", 39.0, 32.0, 44.0, "最適溫度（°C）"),
    ("lag_log", 1.0, 0.0, 4.0, "對數期種菌的遲滯期（h）"),
    ("lag_overnight", 1.0, 0.0, 6.0, "隔夜種菌的遲滯期（h）"),
]
TRAIN = ["B01", "B03", "B05", "B06"]
TEST = ["B02", "B04"]
# 量測誤差（用來當權重；要換成你自己量到的重現性）
SIGMA = {"od600": 0.05, "glucose_g_L": 0.04, "ethanol_g_L": 0.04, "acetate_g_L": 0.04}
FLOOR = {"od600": 0.02, "glucose_g_L": 0.3, "ethanol_g_L": 0.1, "acetate_g_L": 0.1}


# ───────── 1 讀資料 ─────────
def load_data(folder: Path = DATA) -> tuple[dict, dict]:
    def num(v):
        v = (v or "").strip()
        if v == "":
            return None
        try:
            return float(v)
        except ValueError:
            return v

    batches = {}
    for r in csv.DictReader((folder / "batches.csv").open(encoding="utf-8")):
        batches[r["batch_id"]] = {k: num(v) if k not in ("batch_id", "date", "strain", "seed_state", "medium",
                                                         "vessel", "switch_action", "note") else v
                                  for k, v in r.items()}
    samples = {b: [] for b in batches}
    for r in csv.DictReader((folder / "samples.csv").open(encoding="utf-8")):
        samples[r["batch_id"]].append({k: num(v) if k not in ("batch_id", "note") else v for k, v in r.items()})
    for b in samples:
        samples[b].sort(key=lambda x: x["time_h"])
    return batches, samples


# ───────── 2 品質檢查 ─────────
def check(batches: dict, samples: dict) -> list[dict]:
    """回報資料問題。每一項都是真實數據常見的狀況。"""
    issues = []
    need_b = ["temperature_C", "pH", "otr_setting_mmol_L_h", "inoc_od600", "glucose_g_L", "harvest_h"]
    for bid, b in batches.items():
        for k in need_b:
            if b.get(k) is None:
                issues.append({"batch": bid, "level": "阻擋", "item": k, "msg": "條件表缺少必要欄位，無法用於校正"})
        rows = samples[bid]
        if not rows:
            issues.append({"batch": bid, "level": "阻擋", "item": "samples", "msg": "沒有任何取樣紀錄"})
            continue
        # 缺漏
        n_missing = sum(1 for r in rows if r["od600"] is None)
        if n_missing:
            issues.append({"batch": bid, "level": "注意", "item": "od600",
                           "msg": f"{n_missing} 個時間點沒有 OD（會自動略過，但指數期缺點會影響 μmax）"})
        # 起始值對不對得上
        od0 = next((r["od600"] for r in rows if r["time_h"] == 0 and r["od600"] is not None), None)
        if od0 and b["inoc_od600"] and abs(od0 - b["inoc_od600"]) / b["inoc_od600"] > 0.3:
            issues.append({"batch": bid, "level": "注意", "item": "inoc_od600",
                           "msg": f"條件表寫起始 OD {b['inoc_od600']}，但第 0 小時量到 {od0}"})
        # 糖要單調下降（允許量測誤差）
        g = [(r["time_h"], r["glucose_g_L"]) for r in rows if r["glucose_g_L"] is not None]
        for (t1, g1), (t2, g2) in zip(g, g[1:]):
            if g2 > g1 + max(0.1 * g1, 1.0):
                issues.append({"batch": bid, "level": "注意", "item": "glucose",
                               "msg": f"第 {t1:.0f}→{t2:.0f} h 糖從 {g1:.1f} 升到 {g2:.1f} g/L（量測誤差或稀釋錯誤）"})
        # 碳收支：吃掉的糖，有沒有大致對得上菌＋產物
        if g and len(g) > 1:
            used = g[0][1] - g[-1][1]
            odf = max((r["od600"] for r in rows if r["od600"] is not None), default=0)
            e = max((r["ethanol_g_L"] or 0) for r in rows)
            a = max((r["acetate_g_L"] or 0) for r in rows)
            if used > 1:
                recov = (odf * OD_TO_GDW * 0.47 + e * 0.52 + a * 0.40) / (used * 0.40)
                if recov > 1.15 or recov < 0.35:
                    issues.append({"batch": bid, "level": "注意", "item": "carbon",
                                   "msg": f"碳回收率約 {recov:.0%}（其餘多為 CO₂；低於 35% 或高於 115% 要查）"})
        # 事件註記
        for r in rows:
            if r.get("note"):
                issues.append({"batch": bid, "level": "註記", "item": f"t={r['time_h']:.0f}h", "msg": r["note"]})
    return issues


# ───────── 3 衍生量（不需要模型） ─────────
def derive(batches: dict, samples: dict) -> dict:
    """每批算出 μmax、遲滯期、產率。這些數字本身就很有用，也是校正的檢查點。"""
    out = {}
    for bid, b in batches.items():
        rows = [r for r in samples[bid] if r["od600"] is not None and r["od600"] > 0]
        t = np.array([r["time_h"] for r in rows])
        y = np.log(np.array([r["od600"] for r in rows]))
        # μmax：在所有「連續 4 點」的視窗中，取斜率最大者（＝指數期）
        best = {"mu": -1}
        for i in range(len(t) - 3):
            w = slice(i, i + 4)
            k, c = np.polyfit(t[w], y[w], 1)
            r2 = 1 - np.sum((y[w] - (k * t[w] + c)) ** 2) / max(1e-12, np.sum((y[w] - y[w].mean()) ** 2))
            if k > best["mu"] and r2 > 0.95:
                best = {"mu": float(k), "r2": float(r2), "t0": float(t[i]), "t1": float(t[i + 3]), "c": float(c)}
        # 遲滯期：指數期的切線外推回到起始 OD 的時間
        lag = None
        if best["mu"] > 0:
            lag = float((y[0] - best["c"]) / best["mu"] - t[0])
        g = [(r["time_h"], r["glucose_g_L"]) for r in rows if r["glucose_g_L"] is not None]
        used = (g[0][1] - g[-1][1]) if len(g) > 1 else 0.0
        x_gain = (rows[-1]["od600"] - rows[0]["od600"]) * OD_TO_GDW
        e_end = max((r["ethanol_g_L"] or 0) for r in rows)
        out[bid] = {
            "mu_max": round(best["mu"], 4) if best["mu"] > 0 else None,
            "mu_window": [best.get("t0"), best.get("t1")], "mu_r2": round(best.get("r2", 0), 4),
            "lag_h": round(max(0.0, lag), 2) if lag is not None else None,
            "glc_used_g_L": round(used, 2),
            "Yxs_gdw_per_g": round(x_gain / used, 3) if used > 0.5 else None,
            "Yps_g_per_g": round(e_end / used, 3) if used > 0.5 else None,
            "od_end": rows[-1]["od600"], "etoh_end_g_L": e_end,
            "T": b["temperature_C"], "pH": b["pH"], "otr_set": b["otr_setting_mmol_L_h"],
            "seed_state": b["seed_state"],
        }
    return out


# ───────── 4 校正 ─────────
def make_params(b: dict, theta: dict) -> dfba.Params:
    lag = theta["lag_overnight"] if b["seed_state"] != "對數期" else theta["lag_log"]
    t_sw = b.get("switch_h")
    return dfba.Params(
        T=b["temperature_C"], pH=b["pH"], otr=b["otr_setting_mmol_L_h"] * theta["otr_factor"],
        X0=b["inoc_od600"] * OD_TO_GDW, G0=b["glucose_g_L"] / MW_GLC * 1000,
        t_end=b["harvest_h"], lag=lag, t_sw=t_sw if t_sw else 1e9,
        vmax_glc=theta["vmax_glc"], km_glc=theta["km_glc"], vmax_o2=theta["vmax_o2"], Topt=theta["Topt"])


def predict(b: dict, theta: dict, times: list[float]) -> dict:
    sim = dfba.simulate(make_params(b, theta))
    t = np.array(sim["t"])
    idx = [int(np.argmin(np.abs(t - x))) for x in times]
    return {"od600": [sim["X"][i] / OD_TO_GDW for i in idx],
            "glucose_g_L": [sim["G"][i] * MW_GLC / 1000 for i in idx],
            "ethanol_g_L": [sim["E"][i] * MW_ETOH / 1000 for i in idx],
            "acetate_g_L": [sim["A"][i] * MW_AC / 1000 for i in idx]}


def residuals(theta: dict, batches: dict, samples: dict, ids: list[str]) -> np.ndarray:
    res = []
    for bid in ids:
        rows = samples[bid]
        times = [r["time_h"] for r in rows]
        pred = predict(batches[bid], theta, times)
        for key in ("od600", "glucose_g_L", "ethanol_g_L", "acetate_g_L"):
            for r, p in zip(rows, pred[key]):
                obs = r[key]
                if obs is None:
                    continue
                scale = max(SIGMA[key] * max(obs, FLOOR[key]), FLOOR[key] * SIGMA[key] * 5)
                res.append((p - obs) / scale)
    return np.array(res)


def fit(batches: dict, samples: dict, ids: list[str]) -> dict:
    names = [p[0] for p in FIT_PARAMS]
    x0 = np.array([p[1] for p in FIT_PARAMS], float)
    lo = np.array([p[2] for p in FIT_PARAMS], float)
    hi = np.array([p[3] for p in FIT_PARAMS], float)

    def fun(x):
        return residuals(dict(zip(names, x)), batches, samples, ids)

    r = least_squares(fun, x0, bounds=(lo, hi), x_scale=np.maximum(np.abs(x0), 0.05), diff_step=0.03,
                      max_nfev=400, verbose=0)
    return {"theta": dict(zip(names, [float(v) for v in r.x])), "cost": float(r.cost), "nfev": int(r.nfev)}


# ───────── 5 驗證與敏感度 ─────────
def rmse_rel(batches: dict, samples: dict, theta: dict, ids: list[str]) -> dict:
    out = {}
    for key in ("od600", "glucose_g_L", "ethanol_g_L", "acetate_g_L"):
        errs = []
        for bid in ids:
            rows = samples[bid]
            pred = predict(batches[bid], theta, [r["time_h"] for r in rows])
            for r, p in zip(rows, pred[key]):
                if r[key] is None or r[key] < FLOOR[key]:
                    continue
                errs.append((p - r[key]) / r[key])
        out[key] = round(float(np.sqrt(np.mean(np.square(errs)))) * 100, 1) if errs else None
    return out


def sensitivity(theta: dict, batches: dict, samples: dict, ids: list[str]) -> list[dict]:
    """把每個參數單獨拉離最佳值，看擬合變差多少。變差越少 = 數據越無法決定這個參數。"""
    base = float(np.sum(residuals(theta, batches, samples, ids) ** 2))
    out = []
    for name, _, lo, hi, label in FIT_PARAMS:
        v = theta[name]
        curve = []
        for f in (0.7, 0.85, 1.0, 1.15, 1.3):
            x = min(max(v * f, lo), hi)
            c = float(np.sum(residuals({**theta, name: x}, batches, samples, ids) ** 2))
            curve.append({"value": x, "sse_ratio": c / base})
        worst = max(c["sse_ratio"] for c in curve)
        out.append({"name": name, "label": label, "value": v, "curve": curve, "worst_ratio": worst,
                    "identifiable": worst > 1.5})
    return sorted(out, key=lambda d: -d["worst_ratio"])


def main():
    batches, samples = load_data()
    issues = check(batches, samples)
    print("── 資料檢查 ──")
    for i in issues:
        print(f"  [{i['level']}] {i['batch']} {i['item']}：{i['msg']}")
    der = derive(batches, samples)
    print("\n── 每批的衍生量 ──")
    print(f"  {'批次':<5}{'T':>5}{'供氧':>6}{'μmax':>8}{'遲滯':>7}{'Yxs':>7}{'Yps':>7}")
    for bid, d in der.items():
        print(f"  {bid:<5}{d['T']:>5.0f}{d['otr_set']:>6.0f}{d['mu_max'] or 0:>8.3f}{d['lag_h'] or 0:>7.2f}"
              f"{d['Yxs_gdw_per_g'] or 0:>7.3f}{d['Yps_g_per_g'] or 0:>7.3f}")

    default = {p[0]: p[1] for p in FIT_PARAMS}
    print(f"\n── 校正（訓練批次 {', '.join(TRAIN)}）──")
    res = fit(batches, samples, TRAIN)
    theta = res["theta"]
    print(f"  least_squares 收斂，呼叫模型 {res['nfev']} 次")
    print(f"  {'參數':<16}{'校正前':>9}{'校正後':>9}{'真實值':>9}")
    truth = {**labdata_truth()}
    for name, d0, *_ , label in FIT_PARAMS:
        tv = truth.get(name)
        print(f"  {name:<16}{d0:>9.3f}{theta[name]:>9.3f}{(f'{tv:.3f}' if tv is not None else '—'):>9}")

    print("\n── 驗證（沒有參與校正的批次）──")
    before_tr, after_tr = rmse_rel(batches, samples, default, TRAIN), rmse_rel(batches, samples, theta, TRAIN)
    before_te, after_te = rmse_rel(batches, samples, default, TEST), rmse_rel(batches, samples, theta, TEST)
    print(f"  {'':<14}{'訓練前':>8}{'訓練後':>8}{'驗證前':>8}{'驗證後':>8}")
    for k in before_tr:
        print(f"  {k:<14}{before_tr[k] or 0:>7.1f}%{after_tr[k] or 0:>7.1f}%{before_te[k] or 0:>7.1f}%"
              f"{after_te[k] or 0:>7.1f}%")

    per_batch = {bid: {"before": rmse_rel(batches, samples, default, [bid]),
                       "after": rmse_rel(batches, samples, theta, [bid]),
                       "role": "訓練" if bid in TRAIN else "驗證"} for bid in batches}
    print("\n── 每批的誤差（校正前 → 校正後，OD／乙醇）──")
    for bid, d in per_batch.items():
        print(f"  {bid} {d['role']}　OD {d['before']['od600'] or 0:>6.1f}% → {d['after']['od600'] or 0:>5.1f}%"
              f"　乙醇 {d['before']['ethanol_g_L'] or 0:>6.1f}% → {d['after']['ethanol_g_L'] or 0:>5.1f}%")

    sens = sensitivity(theta, batches, samples, TRAIN)
    print("\n── 哪些參數真的被數據決定？──")
    for s in sens:
        mark = "可辨識" if s["identifiable"] else "數據不足"
        print(f"  {s['label']:<26}{s['value']:>8.3f}　擬合劣化 ×{s['worst_ratio']:.1f}　{mark}")

    OUT.write_text(json.dumps({
        "issues": issues, "derived": der, "default": default, "theta": theta, "truth": truth,
        "train": TRAIN, "test": TEST, "nfev": res["nfev"],
        "rmse": {"train_before": before_tr, "train_after": after_tr,
                 "test_before": before_te, "test_after": after_te},
        "sensitivity": sens, "per_batch": per_batch,
        "curves": {bid: curve_for(batches, samples, bid, default, theta) for bid in batches},
    }, ensure_ascii=False, indent=1), "utf-8")
    print("\n寫入", OUT)


def curve_for(batches, samples, bid, default, theta):
    rows = samples[bid]
    tt = list(np.arange(0, batches[bid]["harvest_h"] + 1e-9, 0.25))
    return {"obs": {"t": [r["time_h"] for r in rows],
                    **{k: [r[k] for r in rows] for k in ("od600", "glucose_g_L", "ethanol_g_L", "acetate_g_L")}},
            "t": [round(float(x), 2) for x in tt],
            "before": {k: [round(v, 4) for v in vs] for k, vs in predict(batches[bid], default, tt).items()},
            "after": {k: [round(v, 4) for v in vs] for k, vs in predict(batches[bid], theta, tt).items()},
            "T": batches[bid]["temperature_C"], "otr": batches[bid]["otr_setting_mmol_L_h"],
            "switch_h": batches[bid].get("switch_h")}


def labdata_truth() -> dict:
    """示範資料的真實參數（真實實驗當然不知道，這裡只用來評分）。"""
    import labdata
    return {**labdata.TRUE_PARAMS, "otr_factor": labdata.OTR_FACTOR,
            "lag_log": labdata.LAG["對數期"], "lag_overnight": labdata.LAG["隔夜培養"]}


if __name__ == "__main__":
    main()
