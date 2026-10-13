"""核對並延伸「A13_4 ＋ AFS」這個模型，產出第 21 章引用的所有數字。

模型檔不在這個 repo 裡（2 MB，而且是使用者自己跑出來的）。執行時指定路徑：

    python rhto_afs.py <A13_4_AFS_draft_v2.json> -o rhto_afs.json

這支程式做兩件事：

**一、核對別人給的結果。** 不是重述它的說法，是自己再算一次：
反應有沒有配平、關掉碳源會不會還有產物（漏洞）、生產包絡線的六個點、
以及「碳產率有沒有超過教科書的 MVA 上限」。

**二、補上原本沒算的。** 葡萄糖吸收速率的敏感度（預設 1.0 太低）、
FPP 的競爭者是誰、調降 ERG9 的效果、C/N 掃描、拷貝數在 FBA 裡有沒有用。

輸出的 JSON 每一欄都標了它是「核對」還是「新算」。
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import cobra  # noqa: E402

BM, GLC, NH4, O2 = "r_2111", "r_1714", "r_1654", "r_1992"
AFS_RXN, AFS_EX = "AFS_alpha_farnesene", "EX_alpha_farnesene"
ERG9 = "r_1012"                       # 鯊烯合成酶，搶 FPP 的主要競爭者
GGPP = "r_0373"                       # farnesyltranstransferase，往類胡蘿蔔素
PK = "t_0081"                         # 磷酸酮醇酶：不掉 CO2 的捷徑
PDH = "r_0961"                        # 丙酮酸脫氫酶：每次掉一個 CO2
MW_FARNESENE, MW_GLC = 204.36, 180.16  # C15H24、C6H12O6
# 教科書的 MVA 路線：4.5 葡萄糖 → 1 farnesene（第 17.8 節自己算過）
TEXTBOOK_C_YIELD = 15 / (4.5 * 6)


def envelope(model, n_points=11) -> dict:
    """生產包絡線：每個生長下限下，產物最多與最少能有多少。"""
    mu = model.slim_optimize()
    glc = abs(model.reactions.get_by_id(GLC).lower_bound)
    rows = []
    for i in range(n_points):
        f = i / (n_points - 1)
        with model:
            model.reactions.get_by_id(BM).lower_bound = mu * f
            model.objective = AFS_EX
            model.objective_direction = "max"
            hi = model.slim_optimize() or 0.0
            model.objective_direction = "min"
            lo = model.slim_optimize() or 0.0
        hi = 0.0 if abs(hi) < 1e-9 else hi
        lo = 0.0 if abs(lo) < 1e-9 else lo
        rows.append({"growth_fraction": round(f, 3), "mu": round(mu * f, 6),
                     "afs_min": round(float(lo), 6), "afs_max": round(float(hi), 6),
                     "carbon_yield": round(hi * 15 / (glc * 6), 4),
                     "g_per_g": round(hi * MW_FARNESENE / (glc * MW_GLC), 4)})
    return {"mu_max": round(float(mu), 8), "glucose_uptake": glc, "rows": rows}


def check(model) -> dict:
    """核對：配平、漏洞、關掉 AFS 之後產物是不是 0。"""
    out = {}
    r = model.reactions.get_by_id(AFS_RXN)
    out["afs_reaction"] = r.reaction
    out["afs_mass_balanced"] = not r.check_mass_balance()
    out["afs_gpr_copies"] = len([g for g in r.genes if g.id.startswith("AFS_copy")])
    with model:
        r.upper_bound = 0
        model.objective = AFS_EX
        out["afs_off_product"] = round(float(model.slim_optimize() or 0.0), 9)
    with model:                                     # 漏洞檢查
        for x in model.reactions:
            if "maintenance" in (x.name or "").lower():
                x.lower_bound = 0
        closed = 0
        for x in model.exchanges:
            met = next(iter(x.metabolites))
            if (met.elements or {}).get("C") and x.lower_bound < 0:
                x.lower_bound = 0
                closed += 1
        model.objective = AFS_EX
        out["no_carbon_product"] = round(float(model.slim_optimize() or 0.0), 9)
        out["carbon_inputs_closed"] = closed
    return out


def carbon_route(model) -> dict:
    """碳走哪一條路到乙醯輔酶A：省碳的磷酸酮醇酶，還是會掉 CO2 的丙酮酸脫氫酶。"""
    with model:
        model.objective = AFS_EX
        sol = cobra.flux_analysis.pfba(model)
    get = lambda rid: round(float(sol.fluxes[rid]), 4) if rid in model.reactions else None  # noqa: E731
    return {"phosphoketolase": get(PK), "pyruvate_dehydrogenase": get(PDH),
            "co2_out": get("r_1672"), "afs": get(AFS_EX),
            "note": "磷酸酮醇酶不掉 CO2，所以模型的碳產率會高過教科書的 MVA 路線"}


def glucose_scan(model, levels) -> list:
    """葡萄糖吸收上限的敏感度。模型預設 1.0，實際培養通常 5–15。"""
    rows = []
    for g in levels:
        with model:
            model.reactions.get_by_id(GLC).lower_bound = -g
            mu = model.slim_optimize() or 0.0
            with model:
                model.objective = AFS_EX
                top = model.slim_optimize() or 0.0
            with model:
                model.reactions.get_by_id(BM).lower_bound = mu * 0.5
                model.objective = AFS_EX
                half = model.slim_optimize() or 0.0
        rows.append({"glucose_uptake": g, "mu_max": round(float(mu), 5),
                     "doubling_h": round(0.693 / mu, 2) if mu > 1e-9 else None,
                     "afs_max": round(float(top), 5),
                     "afs_at_half_growth": round(float(half), 5),
                     "carbon_yield_max": round(top * 15 / (g * 6), 4)})
    return rows


def cn_scan(model, cns, glucose=10.0) -> list:
    """C/N 掃描。氮吸收 ＝ 6 × 葡萄糖吸收 ÷ (C/N)（第 20.5 節）。"""
    rows = []
    for cn in cns:
        n_up = 6.0 * glucose / cn
        with model:
            model.reactions.get_by_id(GLC).lower_bound = -glucose
            model.reactions.get_by_id(NH4).lower_bound = -n_up
            mu = model.slim_optimize() or 0.0
            with model:
                model.reactions.get_by_id(BM).lower_bound = mu * 0.5
                model.objective = AFS_EX
                half = model.slim_optimize() or 0.0
        rows.append({"c_n_molar": cn, "n_uptake": round(n_up, 4),
                     "mu_max": round(float(mu), 5),
                     "afs_at_half_growth": round(float(half), 5)})
    return rows


def erg9_scan(model, fracs, glucose=10.0) -> dict:
    """調降 ERG9（鯊烯合成酶）：它和 AFS 搶同一桶 FPP。

    **要按「它實際跑多快」去壓，不是按上限去壓。** 模型給的上限是 1000，
    而實際通量只有零點幾——把上限設成 1000 的 10% ＝ 100，根本沒碰到它，
    結果會是「調降完全沒效果」，而那是假的。第一版就是這樣錯的。
    """
    rows = []
    with model:
        model.reactions.get_by_id(GLC).lower_bound = -glucose
        mu_full = model.slim_optimize() or 0.0
        sol = model.optimize()
        base_flux = float(sol.fluxes[ERG9])        # 最大生長時 ERG9 實際跑多快
        for f in fracs:
            with model:
                model.reactions.get_by_id(ERG9).upper_bound = base_flux * f
                mu = model.slim_optimize() or 0.0
                hi = float("nan")
                if mu and mu > 1e-9:
                    with model:
                        model.reactions.get_by_id(BM).lower_bound = mu * 0.5
                        model.objective = AFS_EX
                        hi = model.slim_optimize() or 0.0
            # 再做一次公平比較：把生長固定在同一個絕對值，才分得出
            # 「真的搶到 FPP」和「只是因為長得慢所以碳有剩」
            fixed = float("nan")
            with model:
                model.reactions.get_by_id(ERG9).upper_bound = base_flux * f
                model.reactions.get_by_id(BM).lower_bound = mu_full * 0.1
                model.objective = AFS_EX
                v = model.slim_optimize()
                fixed = v if v is not None else float("nan")
            rows.append({"erg9_fraction": f, "erg9_upper_bound": round(base_flux * f, 6),
                         "mu_max": round(float(mu), 5),
                         "afs_at_half_own_growth": None if hi != hi else round(float(hi), 5),
                         "afs_at_fixed_growth": None if fixed != fixed else round(float(fixed), 5)})
    return {"reaction": ERG9, "mu_full": round(float(mu_full), 5),
            "erg9_flux_at_max_growth": round(base_flux, 6),
            "fixed_growth_floor": round(mu_full * 0.1, 5),
            "note": "afs_at_half_own_growth 的生長下限是各自 μmax 的一半（會互相不可比）；"
                    "afs_at_fixed_growth 把生長固定在同一個絕對值，才是公平比較",
            "rows": rows}


def fpp_users(model) -> list:
    """誰在用 FPP——這就是第 17 章那張「搶原料」的表，現在有模型裡的真 id。"""
    fpp = model.metabolites.get_by_id("s_0190")
    out = []
    for r in sorted(fpp.reactions, key=lambda x: x.id):
        out.append({"id": r.id, "name": r.name,
                    "consumes": r.metabolites[fpp] < 0,
                    "genes": sorted(g.id for g in r.genes),
                    "reaction": r.reaction[:120]})
    return out


def copy_number(model, glucose=10.0) -> dict:
    """拷貝數在 FBA 裡有沒有用。OR 規則只管有沒有，不管幾份。"""
    copies = sorted(g.id for g in model.genes if g.id.startswith("AFS_copy"))
    out = {"n_copies": len(copies)}
    with model:
        model.reactions.get_by_id(GLC).lower_bound = -glucose
        model.objective = AFS_EX
        out["all_present"] = round(float(model.slim_optimize() or 0.0), 5)
        with model:
            for cid in copies[:-1]:
                model.genes.get_by_id(cid).knock_out()
            out["only_one_left"] = round(float(model.slim_optimize() or 0.0), 5)
        with model:
            for cid in copies:
                model.genes.get_by_id(cid).knock_out()
            out["all_knocked_out"] = round(float(model.slim_optimize() or 0.0), 5)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model", type=Path, help="A13_4_AFS_draft_v2.json")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    m = cobra.io.load_json_model(str(a.model))
    res = {
        "model": {"reactions": len(m.reactions), "metabolites": len(m.metabolites),
                  "genes": len(m.genes), "objective": [r.id for r in m.reactions
                                                       if r.objective_coefficient]},
        "verify": check(m),
        "envelope_default": envelope(m),
        "textbook_carbon_yield": round(TEXTBOOK_C_YIELD, 4),
        "carbon_route": carbon_route(m),
        "glucose_scan": glucose_scan(m, [1, 2, 5, 10, 15]),
        "cn_scan": cn_scan(m, [10, 20, 40, 80, 120]),
        "erg9_scan": erg9_scan(m, [1.0, 0.5, 0.25, 0.1, 0.0]),
        "fpp_users": fpp_users(m),
        "copy_number": copy_number(m),
    }
    print(f"反應 {res['model']['reactions']}、代謝物 {res['model']['metabolites']}、"
          f"基因 {res['model']['genes']}")
    v = res["verify"]
    print(f"\n核對：AFS 配平 {'✓' if v['afs_mass_balanced'] else '✗'}　"
          f"關掉 AFS 產物 {v['afs_off_product']}　"
          f"無碳源產物 {v['no_carbon_product']}（都應該是 0）")
    e = res["envelope_default"]
    print(f"\n生產包絡線（葡萄糖 {e['glucose_uptake']}）：μmax {e['mu_max']}")
    print(f"{'生長下限':>8}{'產物上限':>12}{'碳產率':>9}")
    for r in e["rows"][::2]:
        print(f"{r['growth_fraction']*100:>7.0f}%{r['afs_max']:>12.5f}{r['carbon_yield']*100:>8.1f}%")
    print(f"\n教科書 MVA 上限 {TEXTBOOK_C_YIELD*100:.1f}%　"
          f"模型最高 {max(r['carbon_yield'] for r in e['rows'])*100:.1f}%")
    c = res["carbon_route"]
    print(f"原因：磷酸酮醇酶通量 {c['phosphoketolase']} vs 丙酮酸脫氫酶 {c['pyruvate_dehydrogenase']}")
    print(f"\n葡萄糖吸收的敏感度：")
    for r in res["glucose_scan"]:
        print(f"  {r['glucose_uptake']:>3} → μ {r['mu_max']:.4f}（倍增 {r['doubling_h']} h）"
              f"、產物上限 {r['afs_max']:.4f}")
    k = res["copy_number"]
    print(f"\n拷貝數：全部在 {k['all_present']}、只剩 1 份 {k['only_one_left']}、"
          f"全剔除 {k['all_knocked_out']}")
    if a.out:
        a.out.write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
        print(f"\n寫入 {a.out}")


if __name__ == "__main__":
    main()
