"""把最適化找到的參數，換算成實驗室真的做得出來的操作建議。

輸入：一組培養參數（溫度、pH、供氧能力、接種量、切換時間…）
輸出：
  1. 配製與接種：培養基體積、裝液量、種菌要接多少
  2. 供氧換算：需要多少 kLa，哪一種容器做得到
  3. 取樣時程：依模型預測的階段轉折點安排，不是固定每小時
  4. 切換判準：用 OD 門檻（而不是時鐘）觸發，並附「這批長得慢怎麼辦」的對照表
  5. 期望軌跡與容許範圍：用蒙地卡羅算出 p10–p90，當作「這批正不正常」的判斷依據
  6. 異常處置：偏離容許範圍時怎麼辦

所有數字都由 dfba.py 的模型算出來；換成你的菌時，改 dfba.Params 與下面的換算常數即可。
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dfba  # noqa: E402

# ── 實驗室換算常數（換菌、換儀器都要重新量）──
OD_TO_GDW = 0.35        # 1 單位 OD600 約等於多少 gDW/L（大腸桿菌常見範圍 0.3–0.4，要自己做檢量線）
O2_SAT = 0.20           # 37 °C、1 atm 下水中飽和溶氧約 0.20 mmol/L
MW_GLC = 180.16         # 葡萄糖分子量
MW_ETOH = 46.07

# 常見容器的 kLa 量級（1/h）。來源見教材第 10 章參考文獻，實際值一定要自己量。
VESSELS = [
    ("試管／深孔盤（靜置或慢速）", 5, 20),
    ("搖瓶，裝液 40%、150 rpm", 20, 60),
    ("搖瓶，裝液 20%、200 rpm", 60, 120),
    ("搖瓶，裝液 10%、250 rpm 或加擋板", 120, 250),
    ("攪拌式發酵槽（通氣＋攪拌）", 200, 1000),
]


def od(x_gdw: float) -> float:
    """菌量（gDW/L）換成 OD600。"""
    return x_gdw / OD_TO_GDW


def required_kla(otr: float) -> float:
    """要達到這個供氧能力（mmol O2/L/h），需要多少 kLa（1/h）。

    OTR = kLa × (C* − C_L)；假設溶氧控制在接近 0（最嚴苛），C* − C_L ≈ C*。
    """
    return otr / O2_SAT


def vessel_options(otr: float) -> list[dict]:
    kla = required_kla(otr)
    out = []
    for name, lo, hi in VESSELS:
        fit = "可以" if lo <= kla <= hi else ("不足" if hi < kla else "綽綽有餘")
        out.append({"vessel": name, "kla_lo": lo, "kla_hi": hi, "fit": fit})
    return out


def inoculum(p: dfba.Params, work_volume_mL: float, seed_od: float) -> dict:
    """算出要接多少種菌。"""
    target_od = od(p.X0)
    seed_mL = work_volume_mL * target_od / seed_od
    return {"target_od": target_od, "seed_od": seed_od, "seed_mL": seed_mL,
            "ratio": seed_mL / work_volume_mL * 100, "work_volume_mL": work_volume_mL}


def medium(p: dfba.Params) -> dict:
    return {"glc_mM": p.G0, "glc_gL": p.G0 * MW_GLC / 1000}


def trajectory(p: dfba.Params) -> dict:
    """期望軌跡：每小時的 OD、糖、產物與階段。"""
    sim = dfba.simulate(p)
    step = max(1, int(round(1.0 / p.dt)))
    idx = list(range(0, len(sim["t"]), step))
    if idx[-1] != len(sim["t"]) - 1:
        idx.append(len(sim["t"]) - 1)
    return {"t": [sim["t"][i] for i in idx], "od": [od(sim["X"][i]) for i in idx],
            "glc": [sim["G"][i] for i in idx], "etoh": [sim["E"][i] for i in idx],
            "ac": [sim["A"][i] for i in idx], "phase": [sim["phase"][i] for i in idx]}


def band(p: dfba.Params, n: int = 400, seed: int = 0) -> dict:
    """容許範圍：把實驗一定會有的變異丟進模型，算出 p10–p90。

    變異來源與幅度（依一般實驗室的重現性設定，自己的實驗室要用實測的批間變異取代）：
      接種量 ±20%、遲滯期 ±0.5 h、最大吸收速率 ±10%、供氧能力 ±20%、溫度 ±0.5 °C
    """
    rng = np.random.default_rng(seed)
    runs = []
    for _ in range(n):
        q = replace(p,
                    X0=p.X0 * float(rng.uniform(0.8, 1.2)),
                    lag=max(0.0, p.lag + float(rng.uniform(-0.5, 0.5))),
                    vmax_glc=p.vmax_glc * float(rng.uniform(0.9, 1.1)),
                    otr=p.otr * float(rng.uniform(0.8, 1.2)),
                    T=p.T + float(rng.uniform(-0.5, 0.5)))
        runs.append(dfba.simulate(q))
    t = runs[0]["t"]
    step = max(1, int(round(1.0 / p.dt)))
    idx = list(range(0, len(t), step))
    if idx[-1] != len(t) - 1:
        idx.append(len(t) - 1)
    out = {"t": [t[i] for i in idx]}
    for key, conv in (("X", od), ("G", lambda v: v), ("E", lambda v: v), ("A", lambda v: v)):
        arr = np.array([[conv(r[key][i]) for i in idx] for r in runs])
        out[key] = {"p10": np.percentile(arr, 10, axis=0).tolist(),
                    "p50": np.percentile(arr, 50, axis=0).tolist(),
                    "p90": np.percentile(arr, 90, axis=0).tolist()}
    finals = np.array([r["E"][-1] for r in runs])
    out["E_end"] = {"p10": float(np.percentile(finals, 10)), "p50": float(np.percentile(finals, 50)),
                    "p90": float(np.percentile(finals, 90))}
    out["n"] = n
    return out


def sampling_plan(p: dfba.Params) -> list[dict]:
    """依模型預測的階段轉折點安排取樣，而不是固定每小時取。"""
    sim = dfba.simulate(p)
    spans, cur, start = [], sim["phase"][0], 0.0
    for t, ph in zip(sim["t"], sim["phase"]):
        if ph != cur:
            spans.append((cur, start, float(t)))
            cur, start = ph, float(t)
    spans.append((cur, start, float(sim["t"][-1])))
    plan = []
    for phase, a, b in spans:
        if b - a < 0.3:
            continue
        dense = phase in ("好氧指數生長", "缺氧・溢流代謝") or (p.t_sw < 1e8 and a <= p.t_sw <= b)
        every = 1.0 if dense else 2.0
        times = list(np.arange(a, b + 1e-9, every))
        plan.append({"phase": phase, "start": a, "end": b, "every_h": every,
                     "times": [round(float(x), 2) for x in times],
                     "measure": "OD＋HPLC" if dense else "OD（HPLC 每 2 小時一次）"})
    return plan


def switch_rule(p: dfba.Params, check_h: float, obs_scale=(0.6, 0.8, 1.0, 1.25, 1.5)) -> dict:
    """「這批長得比預期慢（或快）怎麼辦」：在 check_h 看 OD，查表決定新的切換時間。

    做法：把接種量乘上不同倍率模擬出「長得慢／長得快」的批次，
    對每一種批次重新掃描最佳切換時間，得到「觀察到的 OD → 建議切換時間」對照表。
    """
    base = dfba.simulate(p)
    k = min(len(base["t"]) - 1, int(round(check_h / p.dt)))
    rows = []
    for s in obs_scale:
        q = replace(p, X0=p.X0 * s)
        sim = dfba.simulate(q)
        obs_od = od(sim["X"][k])
        best_t, best_y = None, -1.0
        for t_sw in np.arange(0.0, p.t_end + 1e-9, 0.25):
            y = dfba.summary(dfba.simulate(replace(q, t_sw=float(t_sw))))["E_end"]
            if y > best_y:
                best_t, best_y = float(t_sw), y
        # 照原訂時間切換會損失多少
        y_fixed = dfba.summary(dfba.simulate(replace(q, t_sw=p.t_sw)))["E_end"]
        rows.append({"scale": s, "od_at_check": obs_od, "best_t_sw": best_t, "E_best": best_y,
                     "E_if_fixed": y_fixed, "loss": best_y - y_fixed})
    return {"check_h": check_h, "base_od": od(base["X"][k]), "rows": rows}


def switch_trigger(p: dfba.Params) -> dict:
    """切換當下的 OD 與剩餘糖，當作觸發條件。"""
    sim = dfba.simulate(p)
    k = min(len(sim["t"]) - 1, int(round(p.t_sw / p.dt)))
    return {"t_sw": p.t_sw, "od": od(sim["X"][k]), "glc_mM": sim["G"][k],
            "glc_gL": sim["G"][k] * MW_GLC / 1000, "our": sim["our"][k]}


def harvest(p: dfba.Params) -> dict:
    s = dfba.summary(dfba.simulate(p))
    return {"t_end": p.t_end, "etoh_mM": s["E_end"], "etoh_gL": s["E_end"] * MW_ETOH / 1000,
            "od": od(s["X_end"]), "glc_left_mM": s["glc_left"], "ac_mM": s["A_max"],
            "yield_mol": s["Y_E_G"]}


def build(p: dfba.Params, work_volume_mL: float = 100.0, seed_od: float = 2.0, check_h: float = 4.0,
          n_band: int = 400) -> dict:
    """產生完整的操作建議。"""
    return {"params": {k: getattr(p, k) for k in ("T", "pH", "otr", "X0", "lag", "G0", "t_sw", "t_end")},
            "medium": medium(p), "inoculum": inoculum(p, work_volume_mL, seed_od),
            "kla": required_kla(p.otr), "vessels": vessel_options(p.otr),
            "trajectory": trajectory(p), "band": band(p, n_band), "sampling": sampling_plan(p),
            "switch": switch_trigger(p), "switch_rule": switch_rule(p, check_h), "harvest": harvest(p),
            "od_to_gdw": OD_TO_GDW}


def to_text(pr: dict) -> str:
    """把建議印成一張可以貼在實驗桌上的操作單。"""
    p, inoc, sw, hv = pr["params"], pr["inoculum"], pr["switch"], pr["harvest"]
    L = []
    L.append("═" * 68)
    L.append("  培養操作單（由模型產生，第一次執行請當作起點並記錄實際值）")
    L.append("═" * 68)
    L.append(f"目標：第 {p['t_end']:.0f} 小時收穫，乙醇約 {hv['etoh_gL']:.1f} g/L（{hv['etoh_mM']:.0f} mM）")
    L.append("")
    L.append("【1】培養基與容器")
    L.append(f"  葡萄糖 {pr['medium']['glc_gL']:.1f} g/L（{pr['medium']['glc_mM']:.0f} mM），工作體積 {inoc['work_volume_mL']:.0f} mL")
    L.append(f"  溫度 {p['T']:.1f} °C，pH 控制在 {p['pH']:.1f}")
    L.append(f"  供氧需求：OTR {p['otr']:.0f} mmol O₂/L/h → 需要 kLa 約 {pr['kla']:.0f} 1/h")
    for v in pr["vessels"]:
        if v["fit"] == "可以":
            L.append(f"    建議容器：{v['vessel']}（kLa 約 {v['kla_lo']}–{v['kla_hi']} 1/h）")
    L.append("")
    L.append("【2】接種")
    L.append(f"  種菌 OD600 {inoc['seed_od']:.1f}（對數期），取 {inoc['seed_mL']:.1f} mL")
    L.append(f"  → 起始 OD600 {inoc['target_od']:.2f}（接種比例 {inoc['ratio']:.1f}%）")
    L.append("")
    L.append("【3】取樣時程")
    for s in pr["sampling"]:
        L.append(f"  {s['start']:.1f}–{s['end']:.1f} h　{s['phase']}：每 {s['every_h']:.0f} 小時，{s['measure']}")
    L.append("")
    L.append("【4】切換（第二階段）")
    L.append(f"  預計第 {sw['t_sw']:.2f} 小時，但以 OD600 達到 {sw['od']:.1f} 為準")
    L.append(f"  （此時預計剩糖 {sw['glc_gL']:.1f} g/L）→ 停止通氣，密封或通氮氣")
    r = pr["switch_rule"]
    L.append(f"  第 {r['check_h']:.0f} 小時查核（預期 OD600 {r['base_od']:.2f}）：")
    for row in r["rows"]:
        L.append(f"    OD {row['od_at_check']:.2f} → 建議第 {row['best_t_sw']:.2f} h 切換"
                 f"（照原訂時間會少 {row['loss']:.0f} mM）")
    L.append("")
    L.append("【5】收穫")
    L.append(f"  第 {hv['t_end']:.0f} 小時；預期 OD600 {hv['od']:.1f}、乙醇 {hv['etoh_gL']:.1f} g/L、"
             f"剩糖 {hv['glc_left_mM']:.0f} mM")
    L.append("")
    L.append("【6】容許範圍（超出就要查原因）")
    b = pr["band"]
    for i, t in enumerate(b["t"]):
        if abs(t - round(t)) > 1e-6 or int(t) % 2:
            continue
        L.append(f"  第 {t:4.0f} h　OD600 {b['X']['p10'][i]:5.2f}–{b['X']['p90'][i]:5.2f}"
                 f"　乙醇 {b['E']['p10'][i]:5.0f}–{b['E']['p90'][i]:5.0f} mM")
    L.append("═" * 68)
    return "\n".join(L)


# 第 11 章用的異常處置表（依模型行為與第 4–8 章的發現整理）
TROUBLESHOOT = [
    ("OD 低於容許範圍下緣", "種菌狀態差、遲滯期過長、接種量不足、溫度偏低",
     "延後切換（查【4】的對照表）；下一批改用對數期種菌、提高接種量"),
    ("OD 正常但乙酸比預期高", "供氧不足（溢流代謝）", "提高轉速或降低裝液量；或降溫減慢吃糖速度"),
    ("溶氧一直是 0、耗氧貼在上限", "供氧已達極限", "換成 kLa 更高的容器；或改分批補糖，讓吃糖速度降下來"),
    ("切換後產物上升很慢", "厭氧不完全、溫度或 pH 偏離、菌量不足", "確認密封與通氮；確認 pH 控制；查核 OD 是否達門檻"),
    ("糖提早吃完", "起始糖不足或菌量超出預期", "提前收穫或補糖；下一批提高起始糖"),
    ("收穫時糖還剩很多", "切換太早、菌量不足、抑制", "依對照表延後切換；檢查產物或乙酸是否已到抑制濃度"),
    ("批次之間差異大", "種菌狀態、裝液量、轉速沒有固定", "固定並記錄所有條件；每批都做同樣的種菌流程"),
]


def main():
    import json
    # 用第 8 章最適化找到的條件
    res = json.loads((HERE / "results.json").read_text("utf-8"))
    best = res["optimize"]["optimum"]["x"]
    p = dfba.Params(G0=200.0, t_end=12.0, T=round(best["T"], 1), pH=round(best["pH"], 1),
                    otr=round(best["otr"]), t_sw=round(best["t_sw"] * 4) / 4)
    pr = build(p)
    (HERE / "protocol.json").write_text(json.dumps(pr, ensure_ascii=False, indent=1), "utf-8")
    print(to_text(pr))
    print("\n寫入", HERE / "protocol.json")


if __name__ == "__main__":
    main()
