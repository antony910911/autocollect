"""基改菌株：把「插進去的基因」變成模型裡的反應，看它改變了什麼。

兩件事：
  1 add_reaction()：示範怎麼把一個異源反應（別的生物的酵素）加進代謝模型
  2 envelope()：生產包絡線——在每一個生長速率下，產物「最多」和「最少」能有多少

生產包絡線的下限是關鍵：
  下限 = 0  代表細胞可以「只長菌、不產物」，產量完全看它高興（靠控制條件去逼它）
  下限 > 0  代表細胞「不產物就不能長」，這叫成長耦合（growth coupling），最穩定

這裡用大腸桿菌核心模型示範方法。換成你的菌（例如酵母菌 Yeast8），
把 load() 換成讀你的 SBML 檔，反應 id 換成你的模型用的名稱即可。

執行：python engineered.py → engineered.json
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import cobra  # noqa: E402
from cobra import Reaction  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "engineered.json"
BIOMASS = "Biomass_Ecoli_core"
GLC_UPTAKE = 10.0


def load():
    """換成你的菌：cobra.io.read_sbml_model('yeast-GEM.xml')"""
    return cobra.io.load_model("textbook")


def add_heterologous(model, rid: str, name: str, stoich: dict, gene: str = ""):
    """把一個異源反應加進模型。stoich 用代謝物 id：{'pyr_c': -1, 'acald_c': 1, 'co2_c': 1}"""
    r = Reaction(rid, name=name, lower_bound=0.0, upper_bound=1000.0)
    model.add_reactions([r])
    r.add_metabolites({model.metabolites.get_by_id(k): v for k, v in stoich.items()})
    if gene:
        r.gene_reaction_rule = gene
    return r


def envelope(model, product: str, n: int = 21, anaerobic: bool = True) -> dict:
    """生產包絡線：掃描生長速率，各求產物的最大與最小值。"""
    with model:
        if anaerobic:
            model.reactions.EX_o2_e.lower_bound = 0
        model.reactions.EX_glc__D_e.lower_bound = -GLC_UPTAKE
        mu_max = model.slim_optimize()
        if mu_max is None or mu_max < 1e-6:
            return {"mu_max": 0.0, "rows": []}
        rows = []
        for i in range(n):
            mu = mu_max * i / (n - 1)
            with model:
                model.reactions.get_by_id(BIOMASS).lower_bound = mu * 0.999
                model.objective = product
                model.objective_direction = "max"
                hi = model.slim_optimize()
                model.objective_direction = "min"
                lo = model.slim_optimize()
            rows.append({"mu": mu, "lo": float(lo or 0.0), "hi": float(hi or 0.0),
                         "yield_lo": float(lo or 0.0) / GLC_UPTAKE, "yield_hi": float(hi or 0.0) / GLC_UPTAKE})
        return {"mu_max": float(mu_max), "rows": rows}


STRAINS = [
    ("野生型", [], "什麼都沒改"),
    ("ΔpflB", ["PFL"], "剔除丙酮酸甲酸解離酶，堵住甲酸那條路"),
    ("ΔpflB ΔldhA", ["PFL", "LDH_D"], "再堵住乳酸"),
    ("ΔpflB ΔldhA Δpta", ["PFL", "LDH_D", "PTAr"], "再堵住乙酸"),
]


def main():
    base = load()
    # 示範：加入一個異源反應（Zymomonas mobilis 的丙酮酸脫羧酶，pdc）
    with_pdc = base.copy()
    add_heterologous(with_pdc, "PDC_het", "pyruvate decarboxylase（異源，來自 Z. mobilis）",
                     {"pyr_c": -1, "acald_c": 1, "co2_c": 1}, gene="pdc_Zm")
    res = {"model": {"reactions": len(base.reactions), "genes": len(base.genes)},
           "glc_uptake": GLC_UPTAKE, "strains": [], "pdc_effect": {}}

    # 加了異源反應，最大生長與最大產量有沒有變？
    for label, m in (("野生型", base), ("加入異源 pdc", with_pdc)):
        e = envelope(m, "EX_etoh_e")
        res["pdc_effect"][label] = {"mu_max": e["mu_max"], "etoh_at_mu_max": e["rows"][-1]["hi"],
                                    "etoh_max": max(r["hi"] for r in e["rows"])}

    for label, kos, why in STRAINS:
        m = base.copy()
        for r in kos:
            m.reactions.get_by_id(r).knock_out()
        e = envelope(m, "EX_etoh_e")
        if not e["rows"]:
            res["strains"].append({"label": label, "kos": kos, "why": why, "feasible": False})
            continue
        at_max = e["rows"][-1]
        half = e["rows"][len(e["rows"]) // 2]
        res["strains"].append({
            "label": label, "kos": kos, "why": why, "feasible": True, "mu_max": e["mu_max"],
            "at_mu_max": at_max, "at_half": half, "rows": e["rows"],
            "growth_coupled": half["lo"] > 0.01,
        })
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), "utf-8")

    print(f"模型：{res['model']['reactions']} 個反應、{res['model']['genes']} 個基因；葡萄糖吸收固定 {GLC_UPTAKE}\n")
    print("加入異源反應的影響（厭氧）：")
    for k, v in res["pdc_effect"].items():
        print(f"  {k:<14} μmax {v['mu_max']:.4f}　最大生長時乙醇 {v['etoh_at_mu_max']:.2f}"
              f"　理論最大乙醇 {v['etoh_max']:.2f} mmol/gDW/h")
    print("\n剔除競爭路徑（厭氧，乙醇 mmol/gDW/h）：")
    print(f"  {'菌株':<20}{'μmax':>8}{'最大生長時':>14}{'半速生長時（最少–最多）':>26}{'成長耦合':>10}")
    for s in res["strains"]:
        if not s["feasible"]:
            print(f"  {s['label']:<20} 不能厭氧生長")
            continue
        print(f"  {s['label']:<20}{s['mu_max']:>8.4f}{s['at_mu_max']['lo']:>8.2f}–{s['at_mu_max']['hi']:<5.2f}"
              f"{s['at_half']['lo']:>14.2f}–{s['at_half']['hi']:<5.2f}"
              f"{'是' if s['growth_coupled'] else '否':>10}")
    print("\n寫入", OUT)


if __name__ == "__main__":
    main()
