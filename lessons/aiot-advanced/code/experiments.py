"""用模擬沼氣廠的資料，實際跑一遍教材裡的五個建模練習，輸出數字（results.json）供教材引用。

1. 產氣預測：簡單基準 vs 線性迴歸 vs 樹模型；依時間切分 vs 隨機切分
2. VFA 軟感測：用線上訊號推估 VFA；實驗室採樣頻率的影響
3. 數位孿生：AM2 模型＋擴展卡爾曼濾波（EKF）估計槽內 VFA
4. 異常預警：各種警報方法誰最早發現酸化；pH 電極漂移偵測
5. 進料建議：用模型試算未來，限制 VFA 與 pH 後建議進料量

執行：python experiments.py（約 1 分鐘）
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold

import plant
from am2 import Inputs, Params, ph, rates, step

HERE = Path(__file__).resolve().parent
TRAIN_END = 330          # 第 0–329 天訓練，第 330 天之後測試
VFA_ALARM = 1000         # mg/L，教學用警戒值
VFA_DANGER = 1500        # mg/L，視為「已經出事」的門檻


def mae(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    return float(np.mean(np.abs(a[m] - b[m])))


def ffill(a):
    a = a.copy()
    for i in range(1, len(a)):
        if np.isnan(a[i]):
            a[i] = a[i - 1]
    return a


# ───────────────────────── 1. 產氣預測 ─────────────────────────
def forecast_features(daily):
    ch4 = ffill(daily["ch4_m3"])
    load = daily["cod_load_kg"]
    n = len(ch4)
    rows, y, days = [], [], []
    for t in range(7, n - 1):
        rows.append([ch4[t], ch4[t - 1], ch4[t - 2], np.mean(ch4[t - 6:t + 1]), load[t + 1], load[t], load[t - 1],
                     load[t - 2], ffill(daily["ph"])[t], ffill(daily["ch4_pct"])[t], (t + 1) % 7 == 6])
        y.append(ch4[t + 1])
        days.append(t + 1)
    return np.array(rows, float), np.array(y), np.array(days)


FEATURE_NAMES = ["今天產氣", "昨天產氣", "前天產氣", "7 日平均產氣", "明天計畫 COD 負荷", "今天 COD 負荷", "昨天 COD 負荷",
                 "前天 COD 負荷", "今天 pH", "今天 CH₄%", "明天是週日"]


def exp_forecast(daily):
    X, y, days = forecast_features(daily)
    tr, te = days < TRAIN_END, days >= TRAIN_END
    models = {
        "簡單基準（明天＝今天）": None,
        "線性迴歸": Ridge(alpha=1.0),
        "隨機森林": RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=0),
        "梯度提升樹": HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0),
    }
    models["梯度提升樹（排除事件日訓練）"] = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
    event = (days >= 150) & (days < 162)
    preds, scores = {}, {}
    for name, m in models.items():
        if m is None:
            p = X[:, 0]
        else:
            fit = tr & ~event if "排除" in name else tr
            m.fit(X[fit], y[fit])
            p = m.predict(X)
        preds[name] = p
        normal = te & ~((days >= 380) & (days < 392))
        scores[name] = {"test_mae": mae(p[te], y[te]), "test_mae_normal_days": mae(p[normal], y[normal]),
                        "test_mape_normal_days": float(np.mean(np.abs(p[normal] - y[normal]) / y[normal]) * 100)}
    # 依時間切分 vs 隨機打散（錯誤示範）：隨機打散會讓模型「看過未來」，誤差被低估
    split = {}
    for name, make in [("隨機森林", lambda: RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=0)),
                       ("梯度提升樹", lambda: HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05,
                                                                       random_state=0))]:
        errs = []
        for a, b in KFold(5, shuffle=True, random_state=0).split(X):
            errs.append(mae(make().fit(X[a], y[a]).predict(X[b]), y[b]))
        split[name] = {"隨機打散 MAE": float(np.mean(errs)), "依時間切分 MAE": scores[name]["test_mae"]}
    lin = Ridge(alpha=1.0).fit(X[tr], y[tr])
    coef = dict(zip(FEATURE_NAMES, (lin.coef_ * X[tr].std(axis=0)).round(1).tolist()))
    return dict(days=days, y=y, preds=preds, scores=scores, split=split, linear_std_coef=coef)


# ───────────────────────── 2. VFA 軟感測 ─────────────────────────
def soft_features(hourly, daily):
    """每小時的特徵：過去 24 小時的平均與變化，都是線上量得到的。"""
    n = len(hourly["t"])
    ch4 = ffill(hourly["ch4_flow"])
    bg = ffill(hourly["biogas"])
    pct = ffill(hourly["ch4_pct"])
    phm = ffill(hourly["ph"])
    feed = hourly["feed_m3"]
    cs = lambda a: np.concatenate([[0], np.cumsum(a)])  # noqa: E731
    w = 24

    def roll(a, k=w):
        """過去 k 小時的移動平均（只用過去資料，不偷看未來）。"""
        c = cs(a)
        i = np.arange(n)
        j = np.maximum(0, i - k + 1)
        return (c[i + 1] - c[j]) / (i + 1 - j)

    pct24, ph24, ch424, bg24, feed24 = roll(pct), roll(phm), roll(ch4), roll(bg), roll(feed)
    pct_ref = roll(pct, 24 * 7)
    feats = np.column_stack([pct24, ph24, pct24 - pct_ref, ch424 / np.maximum(feed24, 1e-6), bg24 - ch424, feed24,
                             roll(feed, 72)])
    return feats


SOFT_NAMES = ["24h CH₄%", "24h pH", "CH₄% 比 7 日平均的變化", "每 m³ 進料產甲烷", "CO₂ 流量", "24h 進料量", "72h 進料量"]


def exp_soft_sensor(hourly, lab, feats):
    vfa_true_h = hourly["vfa_true"]
    test_h = np.arange(TRAIN_END * 24, len(vfa_true_h))
    out = {}
    curves = {}
    for label, keep in [("每週 1 次", lambda d: d % 7 == 0), ("每週 2 次", lambda d: d % 7 in (0, 3)),
                        ("每天 1 次（理想）", None)]:
        if keep is None:
            days = np.arange(TRAIN_END)
            idx = days * 24 + 9
            y = vfa_true_h[idx] * (1 + np.random.default_rng(1).normal(0, 0.05, len(idx)))
        else:
            sel = [i for i, d in enumerate(lab["day"]) if d < TRAIN_END and keep(d)]
            days = lab["day"][sel]
            idx = days * 24 + 9
            y = lab["vfa"][sel]
        for mname, model in [("線性迴歸", Ridge(alpha=1.0)),
                             ("梯度提升樹", HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05,
                                                                       min_samples_leaf=5, random_state=0))]:
            model.fit(feats[idx], np.log(y))
            pred = np.exp(model.predict(feats))
            ev = (test_h >= 380 * 24) & (test_h < 390 * 24)
            out[f"{label}｜{mname}"] = {"n_labels": int(len(idx)),
                                        "test_mae_normal": mae(pred[test_h[~ev]], vfa_true_h[test_h[~ev]]),
                                        "event_peak_pred": float(np.max(pred[test_h[ev]])),
                                        "event_peak_true": float(np.max(vfa_true_h[test_h[ev]]))}
            curves[f"{label}｜{mname}"] = pred
    return out, curves


# ───────────────────────── 3. EKF 數位孿生 ─────────────────────────
def exp_ekf(sim, hourly, lab, known_feed=False):
    """known_feed=True：假設每批進料都快篩 COD 與 VFA；False：只有每週兩次的進料 COD，VFA 用猜的。"""
    p_nom = Params()  # 用「教科書參數」，和真實廠不同 → 模型本身有誤差
    dt = 1 / 24
    n = len(hourly["t"])
    D = np.repeat(sim["D"], 24)
    # 進料 COD 只有實驗室每週兩次的數據，其他天沿用最近一次
    cod = np.full(plant.DAYS, np.nan)
    cod[lab["day"]] = lab["cod_in"]
    cod = np.repeat(ffill(np.where(np.arange(plant.DAYS) == 0, 25.0, cod)), 24)
    s2in_guess = 10.0
    cod_true, s2in_true = np.repeat(sim["S1in"], 24), np.repeat(sim["S2in"], 24)
    x = np.array([0.5, 0.4, 1.0, 3.0, 100.0, 80.0])
    P = np.diag([0.05, 0.05, 1.0, 25.0, 25.0, 25.0])
    Q = np.diag([1e-4, 1e-4, 0.05, 25.0, 0.5, 0.5])  # 對 VFA 給較大的不確定性，讓它跟得上變化
    R = np.diag([2.0 ** 2, 2.0 ** 2, 0.01 ** 2])
    qm_meas = ffill(hourly["ch4_flow"]) * 24 / (plant.V * plant.NM3_PER_MOL)
    qc_meas = ffill(hourly["biogas"] - hourly["ch4_flow"]) * 24 / (plant.V * plant.NM3_PER_MOL)
    ph_meas = ffill(hourly["ph"])
    est = np.zeros(n)
    openloop = np.zeros(n)
    xo = x.copy()

    def h(xx):
        _, _, qM, qC = rates(xx, p_nom)
        return np.array([qM, qC, ph(xx, p_nom)])

    for k in range(n):
        u = Inputs(D[k], cod_true[k], s2in_true[k], 100, 80) if known_feed else Inputs(D[k], cod[k], s2in_guess, 100, 80)
        xo = step(xo, u, p_nom, dt, 1)
        openloop[k] = xo[3]
        # 預測
        f0 = step(x, u, p_nom, dt, 1)
        F = np.zeros((6, 6))
        for j in range(6):
            e = np.zeros(6)
            e[j] = max(1e-4, 1e-3 * abs(x[j]))
            F[:, j] = (step(x + e, u, p_nom, dt, 1) - f0) / e[j]
        x, P = f0, F @ P @ F.T + Q
        # 修正（每小時用流量與 pH）
        z = np.array([qm_meas[k], qc_meas[k], ph_meas[k]])
        h0 = h(x)
        H = np.zeros((3, 6))
        for j in range(6):
            e = np.zeros(6)
            e[j] = max(1e-4, 1e-3 * abs(x[j]))
            H[:, j] = (h(x + e) - h0) / e[j]
        S = H @ P @ H.T + R
        K = P @ H.T @ np.linalg.inv(S)
        x = np.maximum(x + K @ (z - h0), 1e-6)
        P = (np.eye(6) - K @ H) @ P
        est[k] = x[3]
    vfa_est = est * plant.VFA_MG_PER_MMOL
    vfa_ol = openloop * plant.VFA_MG_PER_MMOL
    te = np.arange(TRAIN_END * 24, n)
    return dict(vfa_ekf=vfa_est, vfa_openloop=vfa_ol,
                mae_ekf=mae(vfa_est[te], hourly["vfa_true"][te]), mae_openloop=mae(vfa_ol[te], hourly["vfa_true"][te]))


# ───────────────────────── 4. 預警與感測器漂移 ─────────────────────────
def first_cross(series, thr, start, end, above=True):
    seg = series[start:end]
    hit = np.where(seg > thr if above else seg < thr)[0]
    return int(start + hit[0]) if len(hit) else None


def count_false(series, thr, ranges, above=True):
    """測試期中，在「沒有事件」的時段出現幾次警報（以天計）。"""
    days = set()
    for a, b in ranges:
        seg = series[a:b]
        for i in np.where(seg > thr if above else seg < thr)[0]:
            days.add((a + i) // 24)
    return len(days)


def exp_warning(hourly, lab, soft_lin, soft_gbm, ekf_vfa, ekf_known):
    n = len(hourly["t"])
    ev0 = 380 * 24
    start, end = ev0 - 24 * 5, ev0 + 24 * 10
    true_danger = first_cross(hourly["vfa_true"], VFA_DANGER, start, end)
    pct = ffill(hourly["ch4_pct"])
    pct_med = np.array([np.median(pct[max(0, i - 168):i + 1]) for i in range(n)])  # 只用過去 7 天
    ph_f = ffill(hourly["ph"])
    c = np.concatenate([[0], np.cumsum(ph_f)])
    i = np.arange(n)
    ph24 = (c[i + 1] - c[np.maximum(0, i - 5)]) / (i + 1 - np.maximum(0, i - 5))  # 過去 6 小時平均，不用未來資料
    quiet = [(TRAIN_END * 24, ev0 - 24), (ev0 + 24 * 15, n)]
    methods = {
        "pH < 7.0": (ph24, 7.0, False),
        "CH₄% 比 7 日中位數低 5 點": (pct - pct_med, -5.0, False),
        "軟感測（線性）VFA > 1000": (soft_lin, VFA_ALARM, True),
        "軟感測（梯度提升樹）VFA > 1000": (soft_gbm, VFA_ALARM, True),
        "EKF 估計 VFA > 1000（進料每週兩次 COD）": (ekf_vfa, VFA_ALARM, True),
        "EKF 估計 VFA > 1000（每批進料快篩）": (ekf_known, VFA_ALARM, True),
    }
    res = {}
    for name, (s, thr, above) in methods.items():
        hit = first_cross(s, thr, start, end, above)
        res[name] = {"alarm_hour": hit, "lead_hours": None if hit is None else true_danger - hit,
                     "false_alarm_days": count_false(s, thr, quiet, above)}
    # 實驗室：下一次採樣才會知道
    lab_hours = [d * 24 + 9 for d in lab["day"] if d * 24 + 9 >= start]
    lab_hit = next((h for h, v in zip([d * 24 + 9 for d in lab["day"]], lab["vfa"]) if h >= start and v > VFA_ALARM),
                   None)
    res["實驗室 VFA（每週兩次）"] = {"alarm_hour": lab_hit, "lead_hours": None if lab_hit is None else true_danger - lab_hit,
                                "false_alarm_days": 0}
    return dict(true_danger_hour=true_danger, methods=res, lab_hours=lab_hours)


def exp_drift(hourly, feats):
    """用其他訊號預測 pH；量測值和預測值的差慢慢變大 → 懷疑電極漂移。"""
    others = feats[:, [0, 2, 3, 4, 5]]
    phm = ffill(hourly["ph"])
    train = np.arange(24 * 30, 24 * 200)
    model = Ridge(alpha=1.0).fit(others[train], phm[train])
    resid = phm - model.predict(others)
    resid_d = np.nanmean(resid.reshape(plant.DAYS, 24), axis=1)
    mu, sd = resid_d[30:200].mean(), resid_d[30:200].std()
    # CUSUM（往下累積）
    k, hthr = 0.5 * sd, 5 * sd
    s, alarm = 0.0, None
    cusum = np.zeros(plant.DAYS)
    for d in range(200, plant.DAYS):
        s = min(0.0, s + (resid_d[d] - mu) + k)
        cusum[d] = s
        if alarm is None and s < -hthr:
            alarm = d
    return dict(resid_daily=resid_d, cusum=cusum, alarm_day=alarm, drift_start=220, threshold=-hthr)


# ───────────────────────── 5. 進料建議（模型預測控制的簡化版） ─────────────────────────
def recommend(x, plan_d, plan_s1, plan_s2, p_model, horizon=5, vfa_max=VFA_ALARM, ph_min=7.0):
    """在候選進料量中，挑出未來 horizon 天內 VFA 與 pH 都不越線、且產甲烷最多的。"""
    best = (None, -1.0)
    for D in np.linspace(0.06, plan_d, 15):
        xx, ok, ch4 = x.copy(), True, 0.0
        for day in range(horizon):
            u = Inputs(D if day < 2 else min(D, 0.12), plan_s1, plan_s2, 100, 80)
            for _ in range(24):
                xx = step(xx, u, p_model, 1 / 24, 1)
                _, _, qM, _ = rates(xx, p_model)
                ch4 += qM
                if xx[3] * plant.VFA_MG_PER_MMOL > vfa_max or ph(xx, p_model) < ph_min:
                    ok = False
        if ok and ch4 > best[1]:
            best = (D, ch4)
    return best[0] if best[0] is not None else 0.06


def exp_recommend(sim):
    p_true = plant.TRUE_PARAMS
    p_model = replace(Params(), mu2max=0.5, KI2=150.0, alpha=0.8)  # 模型參數經校正但仍有誤差
    D, S1, S2 = sim["D"].copy(), sim["S1in"], sim["S2in"]
    d0, d1 = 370, 400
    x = sim["states"][d0 * 24 - 1].copy()
    actual_vfa = sim["states"][d0 * 24:d1 * 24, 3] * plant.VFA_MG_PER_MMOL
    actual_ph = sim["out"][d0 * 24:d1 * 24, 2]
    actual_ch4 = sim["out"][d0 * 24:d1 * 24, 0]
    rec_D, cf_vfa, cf_ph, cf_ch4 = [], [], [], []
    for day in range(d0, d1):
        r = recommend(x, D[day], S1[day], S2[day], p_model)
        use = min(D[day], r)
        rec_D.append(use)
        u = Inputs(use, S1[day], S2[day], 100, 80)
        for _ in range(24):
            x = step(x, u, p_true, 1 / 24, 1)
            _, _, qM, _ = rates(x, p_true)
            cf_vfa.append(x[3] * plant.VFA_MG_PER_MMOL)
            cf_ph.append(ph(x, p_true))
            cf_ch4.append(qM)
    to_m3 = plant.V * plant.NM3_PER_MOL / 24
    return dict(days=list(range(d0, d1)), actual_D=D[d0:d1].tolist(), rec_D=rec_D,
                actual_vfa=actual_vfa, cf_vfa=np.array(cf_vfa), actual_ph=actual_ph, cf_ph=np.array(cf_ph),
                actual_ch4_total=float(np.sum(actual_ch4) * to_m3), cf_ch4_total=float(np.sum(cf_ch4) * to_m3),
                actual_vfa_max=float(actual_vfa.max()), cf_vfa_max=float(np.max(cf_vfa)),
                actual_ph_min=float(actual_ph.min()), cf_ph_min=float(np.min(cf_ph)),
                feed_actual_m3=float(np.sum(D[d0:d1]) * plant.V), feed_cf_m3=float(np.sum(rec_D) * plant.V))


def run_all():
    sim, hourly, lab, daily = plant.build()
    fc = exp_forecast(daily)
    feats = soft_features(hourly, daily)
    soft_scores, soft_curves = exp_soft_sensor(hourly, lab, feats)
    ekf = exp_ekf(sim, hourly, lab)
    ekf_known = exp_ekf(sim, hourly, lab, known_feed=True)
    warn = exp_warning(hourly, lab, soft_curves["每週 2 次｜線性迴歸"], soft_curves["每週 2 次｜梯度提升樹"], ekf["vfa_ekf"],
                       ekf_known["vfa_ekf"])
    drift = exp_drift(hourly, feats)
    rec = exp_recommend(sim)
    return dict(sim=sim, hourly=hourly, lab=lab, daily=daily, fc=fc, soft_scores=soft_scores, soft_curves=soft_curves,
                ekf=ekf, ekf_known=ekf_known, warn=warn, drift=drift, rec=rec)


def summary(r):
    def rnd(v):
        return round(v, 3) if isinstance(v, float) else v
    return {
        "forecast": {k: {kk: rnd(vv) for kk, vv in v.items()} for k, v in r["fc"]["scores"].items()},
        "forecast_split": {k: {kk: rnd(vv) for kk, vv in v.items()} for k, v in r["fc"]["split"].items()},
        "forecast_linear_std_coef": r["fc"]["linear_std_coef"],
        "soft_sensor": {k: {kk: rnd(vv) for kk, vv in v.items()} for k, v in r["soft_scores"].items()},
        "ekf": {"EKF（進料每週兩次 COD）MAE": rnd(r["ekf"]["mae_ekf"]),
                "EKF（每批進料快篩）MAE": rnd(r["ekf_known"]["mae_ekf"]),
                "只跑模型、不用量測修正 MAE": rnd(r["ekf"]["mae_openloop"])},
        "warning": {"真實 VFA 超過 1500 的時間（小時）": r["warn"]["true_danger_hour"], **r["warn"]["methods"]},
        "drift": {"漂移開始": 220, "CUSUM 警報日": r["drift"]["alarm_day"]},
        "recommend": {k: rnd(r["rec"][k]) for k in ("actual_ch4_total", "cf_ch4_total", "actual_vfa_max", "cf_vfa_max",
                                                     "actual_ph_min", "cf_ph_min", "feed_actual_m3", "feed_cf_m3")},
    }


if __name__ == "__main__":
    import time
    t0 = time.time()
    r = run_all()
    s = summary(r)
    (HERE / "results.json").write_text(json.dumps(s, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), "utf-8")
    print((HERE / "results.json").read_text("utf-8"))
    print(f"{time.time() - t0:.0f}s")
