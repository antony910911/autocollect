"""酵母菌版的起手式：載入 Yeast8／Yeast9，檢查、設定培養基、加入基改路徑、跑 FBA。

**這支程式要在你自己的電腦上跑**，因為它需要先下載酵母菌模型（本教材的執行環境沒有對外網路）。

準備：
  pip install cobra
  從 https://github.com/SysBioChalmers/yeast-GEM 下載 model/yeast-GEM.xml
  （Yeast8／Yeast9 共識模型，Lu et al. 2019；論文見第 3 章參考文獻）

用法：
  python yeast.py yeast-GEM.xml                 # 檢查模型、列出培養基與關鍵反應
  python yeast.py yeast-GEM.xml --anaerobic     # 厭氧條件
  python yeast.py yeast-GEM.xml --ko YGR087C    # 模擬剔除某個基因（這裡是 PDC6）

如果你的菌不是 S. cerevisiae：
  Komagataella phaffii（舊稱 Pichia pastoris）、Yarrowia lipolytica、Kluyveromyces 等
  都有各自發表的模型，可到 BioModels 或作者的 GitHub 找；找不到時，
  用 RAVEN 以 Yeast8 當模板、依同源性建草稿（第 3 章）。
"""

from __future__ import annotations

import sys
import warnings

warnings.filterwarnings("ignore")

# Yeast8 常用的反應 id（不同版本可能略有不同，程式會自動略過找不到的）
KEY_RXNS = {
    "r_2111": "生長（biomass pseudo-reaction）",
    "r_1714": "葡萄糖交換",
    "r_1992": "氧氣交換",
    "r_1761": "乙醇交換",
    "r_1672": "二氧化碳交換",
    "r_2033": "丙酮酸",
    "r_1654": "氨（氮源）",
}
# 厭氧培養一定要補的成分（酵母菌沒有氧就無法自行合成麥角固醇與不飽和脂肪酸）
ANAEROBIC_SUPPLEMENT = {"r_1757": "麥角固醇（ergosterol）", "r_2106": "zymosterol",
                        "r_1915": "油酸（oleate）", "r_2189": "棕櫚油酸"}


def describe(model):
    print(f"模型：{len(model.reactions)} 反應、{len(model.metabolites)} 代謝物、{len(model.genes)} 基因")
    comp = {}
    for met in model.metabolites:
        comp[met.compartment] = comp.get(met.compartment, 0) + 1
    print("區隔（細菌模型通常只有 1–2 個，酵母菌有十幾個）：")
    for c, n in sorted(comp.items(), key=lambda kv: -kv[1]):
        print(f"  {c:<8}{n:>6} 個代謝物")
    print("\n關鍵反應：")
    for rid, label in KEY_RXNS.items():
        if rid in model.reactions:
            r = model.reactions.get_by_id(rid)
            print(f"  {rid:<8}{label:<28}界限 [{r.lower_bound:>8.2f}, {r.upper_bound:>8.2f}]")


def medium_report(model):
    print("\n目前培養基（吸收上限 > 0 的交換反應）：")
    for rid, v in sorted(model.medium.items(), key=lambda kv: -kv[1])[:20]:
        name = model.reactions.get_by_id(rid).name
        print(f"  {rid:<10}{name[:46]:<48}{v:>8.2f}")


def set_anaerobic(model):
    """酵母菌的厭氧培養：關掉氧氣，並補上麥角固醇與不飽和脂肪酸。"""
    if "r_1992" in model.reactions:
        model.reactions.r_1992.lower_bound = 0.0
    added = []
    for rid, label in ANAEROBIC_SUPPLEMENT.items():
        if rid in model.reactions:
            model.reactions.get_by_id(rid).lower_bound = -1000.0
            added.append(label)
    if added:
        print("已補上厭氧必需成分：" + "、".join(added))
    else:
        print("注意：找不到麥角固醇／脂肪酸的交換反應，請依你的模型版本調整 ANAEROBIC_SUPPLEMENT")


def main():
    import cobra
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    path = sys.argv[1]
    model = cobra.io.read_sbml_model(path)
    describe(model)
    medium_report(model)

    if "--anaerobic" in sys.argv:
        print("\n── 設定為厭氧 ──")
        set_anaerobic(model)
    if "--ko" in sys.argv:
        gid = sys.argv[sys.argv.index("--ko") + 1]
        if gid in model.genes:
            model.genes.get_by_id(gid).knock_out()
            print(f"\n已剔除基因 {gid}（{model.genes.get_by_id(gid).name}）")
        else:
            print(f"\n找不到基因 {gid}")

    sol = model.optimize()
    print(f"\n預測生長率 μ = {sol.objective_value:.4f} /h")
    if sol.objective_value and sol.objective_value > 1e-6:
        print("主要分泌物（> 0.1 mmol/gDW/h）：")
        for r in model.exchanges:
            v = sol.fluxes[r.id]
            if v > 0.1:
                print(f"  {r.id:<10}{r.name[:44]:<46}{v:>9.3f}")
    else:
        print("模型長不起來。常見原因：培養基缺成分、厭氧沒補固醇與脂肪酸、剔除了必需基因。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
