"""第 17 章：轉入 α-farnesene 合成酶之後，代謝上多了什麼負擔、和誰搶資源。

這支程式不做 FBA（rhto-GEM 要連網下載，這個環境做不到），它做的是**化學計量的
加總**：把 MVA 路徑與脂肪酸合成的每一步寫下來，逐步累加乙醯輔酶 A、NADPH、ATP
與碳的收支。這些數字是生化課本等級的計量，不是模擬結果，所以可以直接驗算。

輸出 farnesene_path.json，第 17 章的圖讀它。

執行：python farnesene_path.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 分子量（g/mol），只用到碳氫氧
MW = {"glucose": 180.156, "xylose": 150.130, "farnesene": 204.357,
      "stearate": 284.484, "squalene": 410.730, "ergosterol": 396.659}

# MVA 路徑：每一步的 (名稱, 乙醯輔酶A, NADPH, ATP, 釋出CO2)
# 參考任何一本生化課本的 mevalonate pathway；酵母的版本在細胞質。
MVA_STEPS = [
    ("ERG10　2 乙醯輔酶A → 乙醯乙醯輔酶A", 2, 0, 0, 0),
    ("ERG13　＋1 乙醯輔酶A → HMG-CoA", 1, 0, 0, 0),
    ("HMG1 　HMG-CoA → 甲羥戊酸（限速步驟）", 0, 2, 0, 0),
    ("ERG12　甲羥戊酸 → 5-磷酸", 0, 0, 1, 0),
    ("ERG8 　→ 5-焦磷酸", 0, 0, 1, 0),
    ("ERG19　→ IPP ＋ CO_2_", 0, 0, 1, 1),
]
C5_PER_FPP = 3        # FPP（C15）＝ DMAPP ＋ 2 IPP
ACETYL_C = 2          # 乙醯輔酶 A 帶 2 個碳
# 硬脂酸 C18：乙醯輔酶A→丙二醯輔酶A 每次 1 ATP，每延長一次 2 NADPH
STEARATE = {"acetyl_coa": 9, "nadph": 16, "atp": 8, "carbon": 18}


def per_ipp() -> dict:
    return {"acetyl_coa": sum(s[1] for s in MVA_STEPS),
            "nadph": sum(s[2] for s in MVA_STEPS),
            "atp": sum(s[3] for s in MVA_STEPS),
            "co2": sum(s[4] for s in MVA_STEPS)}


def per_farnesene() -> dict:
    ipp = per_ipp()
    d = {k: v * C5_PER_FPP for k, v in ipp.items()}
    d["carbon"] = 15
    return d


def carbon_yield(product_c: int, acetyl_coa: int, co2_in_mva: int, sugar: str) -> dict:
    """碳收支：糖 → 乙醯輔酶A（每 2 個碳丟 1 個 CO_2_）→ 產物。

    只算碳，不檢查 ATP 與 NADPH 夠不夠——所以這是**上限的上限**。
    """
    sugar_c = 6 if sugar == "glucose" else 5
    # 每個乙醯輔酶A 來自 3 個糖碳（丙酮酸 C3 脫羧成乙醯基 C2）
    substrate_c = acetyl_coa * 3
    n_sugar = substrate_c / sugar_c
    return {"sugar": sugar, "sugar_mol": round(n_sugar, 3),
            "substrate_carbon": substrate_c,
            "co2_to_acetyl_coa": acetyl_coa,
            "co2_in_mva": co2_in_mva,
            "product_carbon": product_c,
            "carbon_yield": round(product_c / substrate_c, 4)}


# 類胡蘿蔔素：C40，由 2 個 GGPP（各 C15+C5）合成 → 8 個 C5 單元
CAROTENOID = {"name": "torulene／β-胡蘿蔔素（C40）", "mw": 536.9, "c5_units": 8}


def carotenoid_as_farnesene(mg_per_gdw: float) -> float:
    """把「每克乾重幾毫克類胡蘿蔔素」換算成「最多能多拿幾毫克 α-farnesene」。

    換算的基礎是**異戊二烯單元（C5）**，不是碳或質量：
      C40 類胡蘿蔔素 = 8 個 C5；α-farnesene（C15）= 3 個 C5。
    這是**上限**——真的把類胡蘿蔔素關掉，釋出的 FPP 不會 100% 流向你的產物，
    有一部分會被麥角固醇那條路吃掉。
    """
    mol = mg_per_gdw / CAROTENOID["mw"]                   # mmol/g
    c5 = mol * CAROTENOID["c5_units"]
    return c5 / 3 * MW["farnesene"]


def main():
    ipp, fpp = per_ipp(), per_farnesene()
    gluc = carbon_yield(15, fpp["acetyl_coa"], fpp["co2"], "glucose")
    xyl = carbon_yield(15, fpp["acetyl_coa"], fpp["co2"], "xylose")
    for d, s in ((gluc, "glucose"), (xyl, "xylose")):
        d["mass_yield_g_per_g"] = round(MW["farnesene"] / (d["sugar_mol"] * MW[s]), 4)

    # 同樣用掉 9 個乙醯輔酶A 時，兩條路線各要付多少輔因子
    compare = {
        "α-farnesene（1 mol）": {**{k: fpp[k] for k in ("acetyl_coa", "nadph", "atp")},
                                "carbon": 15, "note": "倍半萜，C15"},
        "硬脂酸（1 mol）": {**STEARATE, "note": "油脂的代表性脂肪酸，C18"},
    }

    # FPP 的去向：誰來搶
    competitors = [
        {"name": "ERG9 角鯊烯合成酶", "takes": "2 FPP → 角鯊烯 → 麥角固醇",
         "essential": True,
         "note": "細胞膜必需，不能剔除，只能調降（弱啟動子或可調控啟動子）"},
        {"name": "GGPP 合成酶 → 類胡蘿蔔素", "takes": "FPP ＋ IPP → GGPP → 紅色色素",
         "essential": False,
         "note": "紅酵母之所以是紅的；會干擾 OD600 讀值，調降可同時釋出 FPP"},
        {"name": "蛋白質法呢基化", "takes": "FPP → 修飾 Ras 等蛋白",
         "essential": True, "note": "量少，但必需"},
        {"name": "脂肪酸／三酸甘油酯", "takes": "乙醯輔酶A → 丙二醯輔酶A → 油脂",
         "essential": False,
         "note": "產油酵母最大的競爭者，搶的是上游的乙醯輔酶A，不是 FPP"},
    ]

    # 類胡蘿蔔素值得不值得動：換算成 α-farnesene 的當量
    carot = [{"carotenoid_mg_per_gdw": v,
              "farnesene_equiv_mg_per_gdw": round(carotenoid_as_farnesene(v), 3)}
             for v in (0.2, 0.5, 1.0, 2.0, 3.0, 5.0)]

    out = {"per_ipp": ipp, "per_farnesene": fpp, "mva_steps": MVA_STEPS,
           "carotenoid": CAROTENOID, "carotenoid_equiv": carot,
           "yield": {"glucose": gluc, "xylose": xyl},
           "compare": compare, "competitors": competitors, "mw": MW,
           "copies_functional": 11}
    (HERE / "farnesene_path.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")

    print(f"每 1 個 IPP：{ipp['acetyl_coa']} 乙醯輔酶A、{ipp['nadph']} NADPH、"
          f"{ipp['atp']} ATP，釋出 {ipp['co2']} CO2")
    print(f"每 1 個 α-farnesene（＝1 FPP）：{fpp['acetyl_coa']} 乙醯輔酶A、"
          f"{fpp['nadph']} NADPH、{fpp['atp']} ATP，釋出 {fpp['co2']} CO2")
    print(f"同樣 9 個乙醯輔酶A：α-farnesene 要 {fpp['nadph']} NADPH，"
          f"硬脂酸要 {STEARATE['nadph']} NADPH")
    for s, d in out["yield"].items():
        print(f"碳上限（{s}）：{d['sugar_mol']} mol 糖 → 1 mol 產物，"
              f"碳產率 {d['carbon_yield']:.1%}，質量產率 {d['mass_yield_g_per_g']:.3f} g/g")
    print("\n類胡蘿蔔素換算成 α-farnesene 當量（以 C5 單元計，上限）：")
    for c in carot:
        print(f'  {c["carotenoid_mg_per_gdw"]:4.1f} mg/g 乾重 → 最多多拿 '
              f'{c["farnesene_equiv_mg_per_gdw"]:5.2f} mg/g')
    print("\n寫入 farnesene_path.json")


if __name__ == "__main__":
    main()
