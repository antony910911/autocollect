"""基因體尺度代謝模型（GEM）的基本操作：用 COBRApy 內建的大腸桿菌核心模型示範。

E. coli core（Orth, Fleming & Palsson, 2010）有 95 個反應、72 個代謝物、137 個基因，
是 BiGG 資料庫中 iJO1366 的精簡版，安裝 COBRApy 就有，不需要連網。
換成自己的菌時，把 load() 改成讀 CarveMe 或 gapseq 產生的 SBML 檔即可（見第 3 章）。
"""

from __future__ import annotations

import warnings

import cobra
from cobra.flux_analysis import pfba

warnings.filterwarnings("ignore")
cobra.Configuration().solver = "glpk"

BIOMASS = "Biomass_Ecoli_core"
# 會分泌或吸收的代謝物（交換反應）
EXCHANGE = {"glc": "EX_glc__D_e", "o2": "EX_o2_e", "ac": "EX_ac_e", "etoh": "EX_etoh_e", "for": "EX_for_e",
            "lac": "EX_lac__D_e", "succ": "EX_succ_e", "co2": "EX_co2_e", "nh4": "EX_nh4_e", "pi": "EX_pi_e"}
# 中心碳代謝圖上要畫的反應（第 4 章流量圖與互動模擬器共用）
MAP_RXNS = ["GLCpts", "PGI", "PFK", "FBA", "GAPD", "PGK", "ENO", "PYK", "G6PDH2r", "GND", "PDH", "PFL", "CS",
            "ICDHyr", "AKGDH", "SUCOAS", "SUCDi", "FUM", "MDH", "PPC", "PTAr", "ACKr", "ACALD", "ALCD2x",
            "LDH_D", "FRD7", "CYTBD", "ATPS4r", "NADH16", "ICL", "MALS", "PPCK", "ME1", "ME2"]
CARBON_SOURCES = {  # 交換反應、每分子碳數、中文名
    "葡萄糖": ("EX_glc__D_e", 6), "果糖": ("EX_fru_e", 6), "丙酮酸": ("EX_pyr_e", 3), "乙酸": ("EX_ac_e", 2),
    "琥珀酸": ("EX_succ_e", 4), "蘋果酸": ("EX_mal__L_e", 4), "延胡索酸": ("EX_fum_e", 4),
    "α-酮戊二酸": ("EX_akg_e", 5), "麩胺酸": ("EX_glu__L_e", 5), "乳酸": ("EX_lac__D_e", 3)}

_MODEL = None


def load() -> cobra.Model:
    """載入模型（只載一次）。自己的菌：return cobra.io.read_sbml_model('my_strain.xml')"""
    global _MODEL
    if _MODEL is None:
        _MODEL = cobra.io.load_model("textbook")
    return _MODEL


def solve(glc: float = 10.0, o2: float = 1000.0, ac: float = 0.0, other: dict | None = None,
          parsimonious: bool = True) -> dict | None:
    """給定各種基質「最多能吸收多少」（mmol/gDW/h），求最大生長時的流量分布。

    回傳 None 代表不可行（例如基質不夠維持細胞的基本耗能）。
    parsimonious=True 用 pFBA：在生長最大的前提下讓總流量最小，避免同一個生長率有很多種流量解。
    """
    m = load()
    with m:
        m.reactions.EX_glc__D_e.lower_bound = -glc
        m.reactions.EX_o2_e.lower_bound = -o2
        m.reactions.EX_ac_e.lower_bound = -ac
        for rid, ub in (other or {}).items():
            m.reactions.get_by_id(rid).lower_bound = -ub
        if parsimonious:
            try:
                sol = pfba(m)
            except Exception:  # 不可行
                return None
        else:
            sol = m.optimize()
        if sol.status != "optimal":
            return None
        f = sol.fluxes
        out = {"mu": float(f[BIOMASS])}
        out.update({k: float(f[r]) for k, r in EXCHANGE.items()})
        out["map"] = {r: float(f[r]) for r in MAP_RXNS}
        return out


def shadow_prices(glc: float = 10.0, o2: float = 1000.0) -> dict:
    """每個基質多給 1 單位，生長率會增加多少（有限差分）。這就是「哪個參數正在限制生長」。"""
    base = solve(glc, o2, parsimonious=False)["mu"]
    res = {}
    for name, kw in {"葡萄糖": dict(glc=glc + 0.5, o2=o2), "氧氣": dict(glc=glc, o2=o2 + 0.5)}.items():
        res[name] = (solve(parsimonious=False, **kw)["mu"] - base) / 0.5
    return res


def gene_deletions(o2: float) -> list[dict]:
    """單一基因剔除：每個基因拿掉後，生長率剩多少（相對野生型）。"""
    from cobra.flux_analysis import single_gene_deletion
    m = load()
    with m:
        m.reactions.EX_o2_e.lower_bound = -o2
        wt = m.slim_optimize()
        df = single_gene_deletion(m)
    names = {g.id: g.name for g in m.genes}
    out = []
    for ids, g in zip(df["ids"], df["growth"]):
        gid = next(iter(ids))
        rel = 0.0 if g != g else max(0.0, float(g) / wt)  # NaN（不可行）視為不能生長
        out.append({"gene": gid, "name": names[gid], "rel": rel})
    return out


def info() -> dict:
    m = load()
    return {"reactions": len(m.reactions), "metabolites": len(m.metabolites), "genes": len(m.genes),
            "atpm": m.reactions.ATPM.lower_bound}
