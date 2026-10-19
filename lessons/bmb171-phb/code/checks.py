#!/usr/bin/env python3
"""核對 BMB171 PHB 那份筆記裡的數字。執行：python lessons/bmb171-phb/code/checks.py

這份筆記的模型是在使用者自己的電腦上跑的（CarveMe + COBRApy），這個環境沒有
BMB171 基因體、沒有 CarveMe、也沒有對外網路，所以**模型本身重跑不了**。

能做的是「內部一致性查核」：表格裡的通量、產率、佔理論上限的百分比、氮需求、
代謝 C/N 是互相綁死的，只要有一個抄錯就會對不起來。這支程式把每一欄重算一次，
再和筆記上寫的值比對，並且加算兩件筆記沒算的事：

1. 把 0.5973 g/g 和「課本路徑」的上限 0.4779 g/g 比——差 1.25 倍，代表模型用了
   不丟 CO2 的路徑。這個數字拿去跟實驗比會嚴重高估。
2. 逐段算 PHB 每掉 5% μmax 的幅度，確認轉折點到底在哪一格。

輸出 checks.json，章節與圖都引用它。
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "checks.json"

# 分子量：PHB 重複單元 C4H6O2、葡萄糖 C6H12O6
MW_PHB, MW_GLC = 86.09, 180.156
GLC_UPTAKE = 10.0          # mmol/gDW/h，筆記的固定基準
MU_MAX = 0.443536          # h^-1
N_PER_MU = 10.7682         # mmol NH4 / gDW / h 每單位 μ（biomass reaction 的 N 係數）

# 筆記上的 Growth–PHB trade-off 表（原始值，不是這裡算出來的）
# (生長佔 μmax 的比例, 筆記寫的 Growth flux 或 None, PHB flux, 產率, 佔上限, O2 攝取)
REPORTED = [
    (0.00, 0.0,     12.50, 0.597, 1.00,  3.75),
    (0.10, 0.0444,  11.78, 0.563, 0.94,  5.24),
    (0.25, 0.1109,  10.71, 0.512, 0.86,  7.47),
    (0.50, 0.2218,   8.92, 0.426, 0.71, 11.18),
    (0.55, None,     8.56, 0.409, 0.68, 11.93),
    (0.60, None,     8.00, 0.382, 0.64, 13.78),
    (0.75, 0.3327,   5.00, 0.239, 0.40, 27.22),
    (0.90, 0.3992,   2.00, 0.096, 0.16, 40.67),
    (1.00, 0.4435,   0.00, 0.000, 0.00, 49.63),
]

# 筆記上的 q(NH4) ≈ 10.7682 × μ 對照（Step 13 的內部一致性檢查）
REPORTED_N = [(0.04435, 0.4776), (0.11088, 1.1940),
              (0.22177, 2.3880), (0.33265, 3.5821)]

TOL_FLUX, TOL_YIELD, TOL_PCT = 5e-4, 1.5e-3, 1.5e-2


def mass_yield(phb_flux: float, glc: float = GLC_UPTAKE) -> float:
    """g PHB / g glucose。"""
    return phb_flux * MW_PHB / (glc * MW_GLC)


def main() -> dict:
    ceiling = mass_yield(12.50)                      # 不要求生長時的化學計量上限
    textbook = 1.0 * MW_PHB / MW_GLC                 # 走 PDH、每分子葡萄糖丟 2 個 CO2
    mol_per_glc = 12.50 / GLC_UPTAKE                 # mol PHB 重複單元 / mol glucose

    rows, mismatches = [], []
    for frac, mu_rep, phb, y_rep, pct_rep, o2 in REPORTED:
        mu = frac * MU_MAX
        y = mass_yield(phb)
        pct = y / ceiling
        n_need = N_PER_MU * mu
        cn = (GLC_UPTAKE * 6) / n_need if n_need > 1e-9 else None
        row = {"growth_fraction": frac, "growth_flux": round(mu, 6),
               "growth_flux_reported": mu_rep, "phb_flux": phb,
               "phb_yield_g_g": round(y, 4), "phb_yield_reported": y_rep,
               "pct_of_ceiling": round(pct, 4), "pct_of_ceiling_reported": pct_rep,
               "nh4_required": round(n_need, 4),
               "metabolic_c_n": round(cn, 1) if cn else None,
               "o2_uptake_reported": o2}
        rows.append(row)
        if mu_rep is not None and abs(mu - mu_rep) > TOL_FLUX:
            mismatches.append(f"{frac:.0%} Growth flux：算 {mu:.6f}、筆記 {mu_rep}")
        if abs(y - y_rep) > TOL_YIELD:
            mismatches.append(f"{frac:.0%} 產率：算 {y:.4f}、筆記 {y_rep}")
        if abs(pct - pct_rep) > TOL_PCT:
            mismatches.append(f"{frac:.0%} 佔上限：算 {pct:.3f}、筆記 {pct_rep}")

    n_rows = []
    for mu, n_rep in REPORTED_N:
        n = N_PER_MU * mu
        n_rows.append({"growth_flux": mu, "nh4_computed": round(n, 4), "nh4_reported": n_rep})
        if abs(n - n_rep) > 1e-3:
            mismatches.append(f"q(NH4) at μ={mu}：算 {n:.4f}、筆記 {n_rep}")

    # 每掉 5% μmax，PHB 掉多少 → 轉折點在哪一格
    slope = []
    for a, b in zip(REPORTED, REPORTED[1:]):
        steps = (b[0] - a[0]) / 0.05
        slope.append({"from": a[0], "to": b[0], "delta_phb": round(a[2] - b[2], 3),
                      "per_5pct": round((a[2] - b[2]) / steps, 3)})

    res = {
        "source": "使用者上傳的 BMB171_PHB_分析筆記.md（整理自一份 ChatGPT 對話）。"
                  "模型與通量不是這個 repo 算的，這裡只做內部一致性查核。",
        "basis": {"glucose_uptake": GLC_UPTAKE, "o2_uptake_cap": 60.0,
                  "mu_max": MU_MAX, "nh4_per_mu": N_PER_MU,
                  "mw_phb_repeat": MW_PHB, "mw_glucose": MW_GLC},
        "ceiling": {
            "phb_flux": 12.50,
            "mol_per_mol_glucose": round(mol_per_glc, 4),
            "mass_yield_g_g": round(ceiling, 4),
            "carbon_recovery": round(mol_per_glc * 4 / 6, 4),
            "textbook_mol_per_mol": 1.0,
            "textbook_mass_yield_g_g": round(textbook, 4),
            "textbook_carbon_recovery": round(4 / 6, 4),
            "ratio_to_textbook": round(ceiling / textbook, 3),
        },
        "tradeoff": rows,
        "nitrogen_consistency": n_rows,
        "phb_slope_per_5pct": slope,
        "mismatches": mismatches,
    }
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), "utf-8")

    print(f"{'佔μmax':>7}{'Growth':>10}{'PHB':>7}{'產率算':>9}{'筆記':>7}{'佔上限算':>10}{'筆記':>7}{'C/N':>8}")
    for r in rows:
        cn = f"{r['metabolic_c_n']:.1f}" if r["metabolic_c_n"] else "—"
        print(f"{r['growth_fraction']:>7.0%}{r['growth_flux']:>10.4f}{r['phb_flux']:>7.2f}"
              f"{r['phb_yield_g_g']:>9.4f}{r['phb_yield_reported']:>7.3f}"
              f"{r['pct_of_ceiling']:>10.3f}{r['pct_of_ceiling_reported']:>7.2f}{cn:>8}")
    c = res["ceiling"]
    print(f"\n化學計量上限 {c['mol_per_mol_glucose']} mol/mol = {c['mass_yield_g_g']} g/g"
          f"（碳回收 {c['carbon_recovery']:.1%}）")
    print(f"課本路徑上限 {c['textbook_mol_per_mol']} mol/mol = {c['textbook_mass_yield_g_g']} g/g"
          f"（碳回收 {c['textbook_carbon_recovery']:.1%}）")
    print(f"→ 模型比課本高 {c['ratio_to_textbook']} 倍")
    print("\nPHB 每掉 5% μmax 的幅度：")
    for s in slope:
        print(f"  {s['from']:.0%}→{s['to']:.0%}  每 5% 掉 {s['per_5pct']}")
    print("\n對不起來的地方：" + ("無，全部一致" if not mismatches else ""))
    for m in mismatches:
        print("  －", m)
    print("\n寫入", OUT)
    return res


if __name__ == "__main__":
    main()
