"""產生示範用的「實驗數據」，格式就是教材第 11 章建議的兩張表。

為什麼要產生假數據？因為要示範「把實驗數據餵回模型」的完整流程，需要一組
「真實參數和模型預設值不一樣」的數據——真實實驗就是這樣：你一開始用的參數
一定不等於這株菌的真實參數。

這裡的「真菌株」參數故意和 dfba.Params 的預設值不同（見 TRUE_PARAMS），
校正程式（calibrate.py）事先並不知道這些值，要從數據把它們找回來。

產生的檔案（code/example-data/）：
  batches.csv  每批一列：條件（溫度、pH、轉速換算的供氧、接種量、起始糖、切換時間）
  samples.csv  每次取樣一列：時間、OD600、葡萄糖、乙醇、乙酸

量測誤差依一般實驗室的水準設定：
  OD600  相對誤差 5% ＋ 絕對誤差 0.01；超過 0.8 要稀釋，稀釋本身再帶 3% 誤差
  HPLC   相對誤差 4%，低於偵測極限（0.2 mM）記為 0
"""

from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

import numpy as np

import dfba

OUT = Path(__file__).resolve().parent / "example-data"
OD_TO_GDW = 0.35
MW_GLC, MW_ETOH, MW_AC = 180.16, 46.07, 60.05

# ── 這株菌的「真實」參數（校正程式不知道，要從數據找回來）──
TRUE_PARAMS = dict(
    vmax_glc=8.5,     # 預設值是 10.0
    km_glc=0.05,      # 預設值是 0.015
    vmax_o2=13.0,     # 預設值是 15.0
    Topt=37.5,        # 預設值是 39.0
    Tmin=6.0,
    Tmax=45.0,
    pHopt=6.8,        # 預設值是 7.0
)
OTR_FACTOR = 0.85     # 實際供氧只有設定值的 85%（搖床、瓶塞、裝液量造成）

# ── 六批實驗：故意涵蓋不同溫度與供氧，這樣參數才有機會被辨識出來 ──
BATCHES = [
    # 編號, 溫度, pH, 設定供氧, 起始OD, 起始糖(g/L), 切換時間(h), 培養時間, 種菌狀態
    ("B01", 37.0, 7.0, 30.0, 0.14, 36.0, None, 12.0, "對數期"),
    ("B02", 37.0, 7.0, 30.0, 0.14, 36.0, 5.75, 12.0, "對數期"),
    ("B03", 30.0, 7.0, 30.0, 0.14, 36.0, 5.75, 14.0, "對數期"),
    ("B04", 42.0, 7.0, 30.0, 0.14, 36.0, 5.75, 12.0, "對數期"),
    ("B05", 37.0, 7.0, 10.0, 0.14, 36.0, None, 14.0, "對數期"),
    ("B06", 37.0, 6.2, 30.0, 0.07, 36.0, 5.75, 14.0, "隔夜培養"),
]
LAG = {"對數期": 1.0, "隔夜培養": 2.2}


def true_sim(row) -> dict:
    bid, T, pH, otr_set, od0, glc_gL, t_sw, t_end, seed = row
    p = dfba.Params(
        T=T, pH=pH, otr=otr_set * OTR_FACTOR, X0=od0 * OD_TO_GDW,
        G0=glc_gL / MW_GLC * 1000, t_end=t_end, lag=LAG[seed],
        t_sw=t_sw if t_sw is not None else 1e9, **TRUE_PARAMS)
    return dfba.simulate(p)


def measure_od(x_gdw: float, rng) -> float | str:
    od_true = x_gdw / OD_TO_GDW
    if od_true > 0.8:  # 要稀釋，稀釋倍率本身有誤差
        od = od_true * float(rng.normal(1, 0.03)) * float(rng.normal(1, 0.05))
    else:
        od = od_true * float(rng.normal(1, 0.05)) + float(rng.normal(0, 0.01))
    return round(max(0.0, od), 3)


def measure_hplc(mM: float, rng, lod: float = 0.2) -> float:
    if mM < lod:
        return 0.0
    return round(max(0.0, mM * float(rng.normal(1, 0.04))), 2)


def main(seed: int = 11):
    rng = np.random.default_rng(seed)
    OUT.mkdir(exist_ok=True)
    with (OUT / "batches.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["batch_id", "date", "strain", "seed_state", "medium", "glucose_g_L", "volume_mL",
                    "vessel", "temperature_C", "pH", "rpm", "otr_setting_mmol_L_h", "inoc_od600",
                    "switch_h", "switch_action", "harvest_h", "note"])
        for row in BATCHES:
            bid, T, pH, otr, od0, glc, t_sw, t_end, seed_state = row
            w.writerow([bid, f"2026-11-{int(bid[1:]) + 2:02d}", "WT", seed_state, "M9", glc, 50,
                        "250 mL 搖瓶", T, pH, 200, otr, od0,
                        "" if t_sw is None else t_sw, "" if t_sw is None else "停止通氣", t_end,
                        "" if seed_state == "對數期" else "種菌為隔夜培養，遲滯期偏長"])

    rows = []
    for row in BATCHES:
        bid, *_ , t_end, _ = row
        sim = true_sim(row)
        t = np.array(sim["t"])
        for h in np.arange(0, t_end + 1e-9, 1.0):   # OD 每小時
            k = int(np.argmin(np.abs(t - h)))
            hplc = abs(h % 2) < 1e-6                 # HPLC 每 2 小時
            rows.append({
                "batch_id": bid, "time_h": round(float(h), 2),
                "od600": measure_od(sim["X"][k], rng),
                "glucose_g_L": round(measure_hplc(sim["G"][k], rng) * MW_GLC / 1000, 3) if hplc else "",
                "ethanol_g_L": round(measure_hplc(sim["E"][k], rng) * MW_ETOH / 1000, 3) if hplc else "",
                "acetate_g_L": round(measure_hplc(sim["A"][k], rng) * MW_AC / 1000, 3) if hplc else "",
                "note": "",
            })
    # 故意留兩個真實資料常見的問題，讓第 11 章示範怎麼檢查
    rows[14]["od600"] = ""                       # 漏記一點
    rows[14]["note"] = "未取樣"
    for r in rows:
        if r["batch_id"] == "B04" and r["time_h"] == 6.0:
            r["note"] = "搖床門被打開約 10 分鐘"
    with (OUT / "samples.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("寫入", OUT / "batches.csv", "與", OUT / "samples.csv")
    print(f"共 {len(BATCHES)} 批、{len(rows)} 筆取樣")


if __name__ == "__main__":
    main()
