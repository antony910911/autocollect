"""把「每平方公尺每天幾克氮」算成「要多大一塊地」，以及硝化槽＋植體槽的設計計算。

這支程式回答四個問題：
 1. 文獻上各種水生植物技術的單位面積去除速率有多少？（整理成同一個單位 g N/m²/d）
 2. 我的廢水要多大面積？（三個情境：沼液、養殖循環水、生活污水二級放流）
 3. 收割植體真正帶走多少氮，佔總去除的幾成？（生物量產率 × 植體含氮率）
 4. 硝化槽＋植體槽：投餵量 → 氨氮產生量 → 需氧量 → 鹼度消耗 → 植栽面積。

化學計量是自己算的（寫在 STOICH），文獻數字標了 conf（abstract／secondary），
單位換算全部在這裡做，章節只引用輸出的 JSON。

執行：python lessons/aquatic-plants/code/sizing.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

# ── 化學計量（自己算的，不是查的）──────────────────────────────
# 完全硝化：NH4+ + 2 O2 → NO3- + 2 H+ + H2O
#   需氧量 = 2 × 32 / 14.007 = 4.57 g O2 / g N
#   產生 2 mol H+，每 mol H+ 消耗 1/2 mol CaCO3（當量 50 g/eq）
#   鹼度消耗 = 2 × 50 / 14.007 = 7.14 g CaCO3 / g N
M_N, M_O2, EQ_CACO3 = 14.007, 32.0, 50.0
STOICH = dict(
    o2_per_n=round(2 * M_O2 / M_N, 3),
    alk_caco3_per_n=round(2 * EQ_CACO3 / M_N, 3),
    note=("自己依 NH4+ + 2O2 → NO3- + 2H+ + H2O 算的。"
          "教科書常見的 4.3 g O2/g N 是扣掉菌體合成所用的氮之後的值，比純化學計量略低。"),
    o2_per_n_textbook=4.3, o2_textbook_ref="r_osu_nutrient",
)

# 蛋白質 → 氮：慣用係數 6.25（蛋白質含氮 16%）
PROTEIN_N = 6.25

# ── 1. 單位面積去除速率（文獻）────────────────────────────────
# unit 一律換算成 g N/m²/d；kind 說明那是「總氮去除」還是「氨氮去除」還是「植物吸收」
RATES = [
    dict(key="duckweed_full", zh="浮萍塘（實場，豬糞廢水）", rate=4.4, kind="TKN 去除",
         conf="abstract", ref="r_duckweed_full", note="文獻自稱是已報導中最高的之一"),
    dict(key="duckweed_pilot", zh="浮萍塘（中試，豬糞液稀釋）", rate=1.2, kind="總氮去除",
         conf="abstract", ref="r_duckweed_pilot"),
    dict(key="hyacinth_opt", zh="布袋蓮（最適條件、無機氮源）", rate=2.161, kind="植物吸收",
         conf="abstract", ref="r_reddy_tucker", note="同一篇的範圍是 0.533–2.161"),
    dict(key="hyacinth_digestate", zh="布袋蓮（沼液為氮源）", rate=0.602, kind="植物吸收",
         conf="abstract", ref="r_reddy_tucker", note="同一篇：沼液組只有 0.124–0.602"),
    dict(key="myrio_cw", zh="粉綠狐尾藻濕地（中試，養豬廢水）", rate=0.9, kind="氨氮去除",
         conf="abstract", ref="r_myrio_cw", note="原文 9 kg N/ha/d，600 天平均去除率 98.3%"),
    dict(key="cw_hssf", zh="水平流人工濕地（HF）", rate=1.13, kind="總氮去除",
         conf="secondary", ref="r_vymazal_hybrid", note="1.13 ± 2.01，標準差比平均大"),
    dict(key="cw_vf", zh="垂直流人工濕地（VF）", rate=1.85, kind="總氮去除",
         conf="secondary", ref="r_vymazal_hybrid", note="1.85 ± 3.66"),
    dict(key="cw_hybrid", zh="混合式濕地（含表面流段）", rate=4.24, kind="總氮去除",
         conf="secondary", ref="r_vymazal_hybrid", note="4.24 ± 5.12"),
    dict(key="ftw_mean", zh="浮島（16 個系統的平均）", rate=0.64, kind="總氮去除",
         conf="secondary", ref="r_ftw_review", note="範圍 0.0015–2.8"),
    dict(key="ftw_field", zh="浮島（實場滯洪池／處理塘）", rate=0.3, kind="總氮去除",
         conf="abstract", ref="r_ftw_lagoon", note="原文 0.06–0.57，這裡取中點"),
    dict(key="tw_xinhai", zh="新海二期表面流濕地（台灣）", rate=1.0, kind="氨氮去除",
         conf="secondary", ref="r_tw_thesis"),
    dict(key="tw_daniaopi", zh="打鳥埤濕地（台灣）", rate=1.3, kind="氨氮去除",
         conf="secondary", ref="r_tw_thesis"),
]

# ── 2. 情境 ───────────────────────────────────────────────────
SCENARIOS = [
    dict(key="digestate", zh="養豬場沼液（厭氧消化後）", q_m3d=30.0, tan=800.0,
         target=0.8, note="濃度高，一定要先稀釋或先硝化"),
    dict(key="ras", zh="室內養殖循環水排放", q_m3d=100.0, tan=3.0,
         target=0.8, note="濃度低、水量大"),
    dict(key="sewage", zh="生活污水二級放流", q_m3d=1000.0, tan=20.0,
         target=0.8, note="人工濕地最常見的對象"),
]

# ── 3. 收割：生物量產率 × 含氮率 ──────────────────────────────
HARVEST = [
    dict(key="duckweed_pilot", zh="浮萍（中試，豬糞液）", dw=5.5, protein_pct=None, n_pct=5.6,
         total_removal=1.2, conf="abstract", ref="r_duckweed_pilot",
         note="含氮率由實場那篇的 35% 粗蛋白換算（35/6.25）"),
    dict(key="duckweed_full", zh="浮萍（實場，豬糞廢水）", dw=18.6, protein_pct=35.0, n_pct=None,
         total_removal=4.4, conf="abstract", ref="r_duckweed_full",
         note="68 t DW/ha/yr 換成每日每平方公尺"),
    dict(key="lemna_gibba_urban", zh="浮萍（都市污水，Lemna gibba）", dw=30.0, protein_pct=None,
         n_pct=5.6, total_removal=None, conf="abstract", ref="r_lemna_urban",
         note="原文 23.87–36.17 g DW/m²/d，這裡取中點；蛋白產率 1.19–1.95 g/m²/d"),
    dict(key="hyacinth_opt", zh="布袋蓮（最適條件）", dw=53.0, protein_pct=None, n_pct=None,
         total_removal=2.161, conf="abstract", ref="r_reddy_tucker",
         note="這一組反過來算含氮率（見 implied_n_pct）"),
]

# 人工濕地的收割移除（年值）與總去除（年值）
CW_HARVEST = dict(harvest_g_m2_yr=(100.0, 200.0), total_g_m2_yr=(250.0, 630.0),
                  conf="secondary", ref="r_vymazal2007")

# ── 4. 硝化槽＋植體槽 ─────────────────────────────────────────
# PTAN = F × PC × 0.092（Ebeling, Timmons & Bisogni 2006）
# 0.092 = 0.16（蛋白含氮）× 0.80（氮被吃進去的比例）× 0.80 × 0.90
TAN_COEF = 0.092
COUPLING = dict(
    feed_ratio_design=80.0,          # g 飼料/m²/d（浮筏式的設計值）
    feed_ratio_range=(60.0, 100.0),
    feed_ratio_uvi=57.0,             # UVI 商業規模實測
    nft_factor=(0.25, 0.75),         # 薄膜水耕只有浮筏的 25–75%
    protein_pct=32.0,
    conf="secondary", ref="r_osu_smallscale",
)


def build() -> dict:
    out: dict = {"stoichiometry": STOICH, "protein_to_n": PROTEIN_N}

    out["areal_rates"] = sorted(RATES, key=lambda r: -r["rate"])

    # 情境 → 面積
    scen = []
    for s in SCENARIOS:
        load = s["q_m3d"] * s["tan"] / 1000.0           # kg N/d
        removed = load * s["target"]
        rows = []
        for r in RATES:
            area = removed * 1000.0 / r["rate"]          # m²
            rows.append(dict(tech=r["zh"], key=r["key"], rate=r["rate"],
                             area_m2=round(area), area_ha=round(area / 1e4, 3)))
        scen.append(dict(**s, load_kgN_d=round(load, 2), removed_kgN_d=round(removed, 2),
                         areas=rows))
    out["scenarios"] = scen

    # 稀釋需求：沼液要稀釋到多少倍，才讓總氨氮降到植物的操作上限
    dig = SCENARIOS[0]
    out["dilution"] = [
        dict(limit_tan=lim, label=lab,
             fold=round(dig["tan"] / lim, 1),
             extra_water_m3d=round(dig["q_m3d"] * (dig["tan"] / lim - 1), 1))
        for lim, lab in ((60.0, "浮萍操作上限 60 mg N/L"),
                         (200.0, "美人蕉／香蒲自我修復門檻 200 mg N/L"),
                         (364.0, "粉綠狐尾藻可存活 364 mg N/L"))
    ]

    # 收割佔比
    harv = []
    for h in HARVEST:
        n_pct = h["n_pct"]
        if n_pct is None and h["protein_pct"] is not None:
            n_pct = h["protein_pct"] / PROTEIN_N
        row = dict(**h, n_pct_used=round(n_pct, 2) if n_pct else None)
        if n_pct is not None:
            n_rate = h["dw"] * n_pct / 100.0
            row["harvest_n_g_m2_d"] = round(n_rate, 3)
            if h["total_removal"]:
                row["share_pct"] = round(n_rate / h["total_removal"] * 100, 1)
        if h["total_removal"] and n_pct is None:
            # 含氮率沒查到，就反過來用「吸收速率 ÷ 生物量產率」推回去
            row["implied_n_pct"] = round(h["total_removal"] / h["dw"] * 100, 2)
            row["harvest_n_g_m2_d"] = h["total_removal"]
        harv.append(row)
    out["harvest"] = harv
    out["cw_harvest"] = dict(
        **CW_HARVEST,
        share_pct_range=(round(CW_HARVEST["harvest_g_m2_yr"][0] / CW_HARVEST["total_g_m2_yr"][1] * 100, 1),
                         round(CW_HARVEST["harvest_g_m2_yr"][1] / CW_HARVEST["total_g_m2_yr"][0] * 100, 1)),
        harvest_g_m2_d=(round(CW_HARVEST["harvest_g_m2_yr"][0] / 365, 3),
                        round(CW_HARVEST["harvest_g_m2_yr"][1] / 365, 3)),
        # 低配低、高配高的「同一座濕地」配對，比極端配對有意義
        share_pct_paired=(round(CW_HARVEST["harvest_g_m2_yr"][0] / CW_HARVEST["total_g_m2_yr"][0] * 100, 1),
                          round(CW_HARVEST["harvest_g_m2_yr"][1] / CW_HARVEST["total_g_m2_yr"][1] * 100, 1)))

    # 耦合設計
    c = dict(COUPLING)
    pc = c["protein_pct"] / 100.0
    rows = []
    for feed in (c["feed_ratio_uvi"], *c["feed_ratio_range"], c["feed_ratio_design"]):
        tan = feed * pc * TAN_COEF                      # g TAN-N/m²/d
        rows.append(dict(
            feed_g_m2_d=feed,
            n_in_feed=round(feed * pc / PROTEIN_N, 3),
            tan_g_m2_d=round(tan, 3),
            tan_pct_of_feed_n=round(tan / (feed * pc / PROTEIN_N) * 100, 1),
            o2_g_m2_d=round(tan * STOICH["o2_per_n"], 2),
            alk_g_caco3_m2_d=round(tan * STOICH["alk_caco3_per_n"], 2),
        ))
    c["per_m2"] = rows
    c["tan_coef"] = TAN_COEF

    # 一個 10 噸魚缸的例子：魚量 → 飼料 → 植栽面積 → 鹼度補充
    fish_kg, feed_pct = 300.0, 1.5         # 300 kg 魚、每天餵體重的 1.5%
    feed_kg_d = fish_kg * feed_pct / 100.0
    tan_kg_d = feed_kg_d * pc * TAN_COEF
    c["example"] = dict(
        fish_kg=fish_kg, feed_pct_bw=feed_pct, feed_kg_d=round(feed_kg_d, 2),
        tan_g_d=round(tan_kg_d * 1000, 1),
        o2_g_d=round(tan_kg_d * 1000 * STOICH["o2_per_n"], 1),
        alk_g_caco3_d=round(tan_kg_d * 1000 * STOICH["alk_caco3_per_n"], 1),
        caco3_g_d=round(tan_kg_d * 1000 * STOICH["alk_caco3_per_n"], 1),
        plant_area_m2=round(feed_kg_d * 1000 / c["feed_ratio_design"], 1),
        plant_area_m2_range=(round(feed_kg_d * 1000 / c["feed_ratio_range"][1], 1),
                             round(feed_kg_d * 1000 / c["feed_ratio_range"][0], 1)),
        note="投餵率、蛋白含量都是假設值，換成自己的數字再算一次。",
    )
    # 交叉檢查：魚菜共生的經驗法則換算成氮負荷，和濕地文獻的去除速率是不是同一個數量級？
    wetland = [r["rate"] for r in RATES if r["key"].startswith(("cw_", "duckweed", "myrio"))]
    c["cross_check"] = dict(
        n_load_at_feed_60_100=(rows[1]["tan_g_m2_d"], rows[2]["tan_g_m2_d"]),
        wetland_rate_range=(min(wetland), max(wetland)),
        comment=("兩套互相獨立的文獻：魚菜共生的投餵率經驗法則（60–100 g 飼料/m²/d）換算成"
                 "氨氮負荷是 %.1f–%.1f g N/m²/d，和濕地／浮萍塘實測的去除速率 %.1f–%.1f g N/m²/d "
                 "落在同一個區間。這是推論，不是哪一篇文獻的結論。"
                 % (rows[1]["tan_g_m2_d"], rows[2]["tan_g_m2_d"], min(wetland), max(wetland))),
        kind="inference",
    )
    out["coupling"] = c

    # 收割的植體拿去厭氧消化：能回收多少甲烷
    # 甲烷產率取文獻的 BMP 範圍（conf=abstract），能量用甲烷低熱值 35.8 MJ/m³
    ch4 = dict(
        water_hyacinth_untreated=143.0, water_hyacinth_pretreated=193.0,
        water_hyacinth_continuous=332.0, duckweed_codigest=193.0,
        unit="mL CH4 / g VS", conf="abstract", ref="r_bmp_wh",
        ch4_lhv_mj_m3=35.8,
    )
    # 以實場浮萍塘的產率算：18.6 g DW/m²/d，假設 VS 佔乾重 85%
    vs_frac = 0.85
    ch4["example"] = dict(
        dw_g_m2_d=18.6, vs_frac=vs_frac,
        ch4_L_m2_d=round(18.6 * vs_frac * ch4["duckweed_codigest"] / 1000, 2),
        energy_kj_m2_d=round(18.6 * vs_frac * ch4["duckweed_codigest"] / 1e6 * 35.8 * 1000, 1),
        note="VS 佔乾重 85% 是假設值（沒查到浮萍的實測 VS/TS）。",
    )
    out["biogas"] = ch4
    return out


if __name__ == "__main__":
    d = build()
    (OUT / "sizing.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
    print("化學計量：", d["stoichiometry"]["o2_per_n"], "g O2/g N；",
          d["stoichiometry"]["alk_caco3_per_n"], "g CaCO3/g N")
    for s in d["scenarios"]:
        print(f'\n{s["zh"]}：{s["q_m3d"]} m³/d × {s["tan"]} mg N/L = {s["load_kgN_d"]} kg N/d')
        for a in s["areas"][:4]:
            print(f'   {a["tech"]:<30} {a["rate"]:>5} g/m²/d → {a["area_m2"]:>8} m²（{a["area_ha"]} ha）')
    print("\n稀釋：", d["dilution"])
    print("\n收割佔比：")
    for h in d["harvest"]:
        print("  ", h["zh"], h["harvest_n_g_m2_d"], "g N/m²/d", h.get("share_pct"), "%",
              h.get("implied_n_pct", ""))
    print("  人工濕地：", d["cw_harvest"]["share_pct_range"], "%")
    print("\n耦合：")
    for r in d["coupling"]["per_m2"]:
        print("  ", r)
    print("  例子：", d["coupling"]["example"])
    print("\n沼氣：", d["biogas"]["example"])
