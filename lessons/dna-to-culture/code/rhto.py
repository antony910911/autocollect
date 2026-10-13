"""把 rhto-GEM 真的跑起來：檢查、找 id、設培養基、加 AFS、算生產包絡線。

rhto-GEM 是紅酵母的全基因體代謝模型（Tiukova et al. 2019）。這支程式負責「拿到模型檔之後」的每一步。

**注意：rhto-GEM 建在 NP11 上，不是 IFO 0880。** 模型裡的基因是 `RHTO_#####`，
不是你的註解用的 `g_#####`，所以要談基因層次的事一定要先做 ID 對照。
建在 IFO 0880 上的是 iRhto1108（Dinh et al. 2019）。

**模型檔要自己下載**（本教材環境沒有對外網路）：

    pip install cobra
    git clone https://github.com/SysBioChalmers/rhto-GEM
    find rhto-GEM -name "*.xml"      # 找出 SBML 檔在哪——不要猜路徑，資料夾改過幾次

沒有模型檔也可以先練：**把路徑寫成 `textbook`**，程式會載入 COBRApy 內建的
大腸桿菌核心模型。指令、輸出格式、會踩的坑全部一樣，只有數字不同。
**先用它把流程走一遍，再換成 rhto-GEM，可以省掉很多來回。**

六個子指令，照這個順序用：

    python rhto.py check   rhto.xml                    # 1 模型長什麼樣、長不長得起來
    python rhto.py find    rhto.xml 葡萄糖的關鍵字      # 2 用名字找 id（最常用）
    python rhto.py medium  rhto.xml --glucose 10 --cn 40   # 3 設培養基、跑 FBA
    python rhto.py afs     rhto.xml                    # 4 加 α-farnesene 反應
    python rhto.py envelope rhto.xml                   # 5 生產包絡線
    python rhto.py scan    rhto.xml                    # 6 掃 C/N 與 ERG9 調降

**為什麼不把反應 id 寫死**：rhto-GEM 用的是 `r_####`／`s_####` 這種流水號，
不同版本會變。寫死的 id 在新版模型上會安靜地找不到，然後你會得到一個
「跑得完、但其實什麼都沒設到」的結果。所以這支程式一律**用名字去找**，
而且**把找到的 id 印出來讓你確認**。
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import cobra  # noqa: E402
from cobra import Metabolite, Reaction  # noqa: E402

HERE = Path(__file__).resolve().parent

# 要找的東西用「可能的名字」去找，不寫死 id。順序就是偏好順序。
WANT = {
    "glucose": ["D-glucose exchange", "glucose exchange", "EX_glc"],
    "ammonium": ["ammonium exchange", "ammonia exchange", "EX_nh4"],
    "oxygen": ["oxygen exchange", "EX_o2"],
    "xylose": ["D-xylose exchange", "xylose exchange"],
    "acetate": ["acetate exchange", "EX_ac"],
}
# α-farnesene 合成酶做的事：FPP → α-farnesene ＋ 焦磷酸
FPP_NAMES = ["farnesyl diphosphate", "farnesyl-PP", "trans,trans-farnesyl diphosphate", "frdp"]
PPI_NAMES = ["diphosphate", "pyrophosphate", "ppi"]
AFS_RXN, AFS_MET, AFS_EX = "AFS", "afarnesene_c", "EX_afarnesene"
# 競爭 FPP 的那條：鯊烯合成酶（ERG9）
ERG9_NAMES = ["squalene synthase", "farnesyl-diphosphate farnesyltransferase"]


# ── 載入與搜尋 ────────────────────────────────────────────────────────

def load(path: str):
    """路徑寫 `textbook` 就載入內建的大腸桿菌核心模型，用來練手。"""
    if path in ("textbook", "e_coli_core"):
        print("※ 載入內建的大腸桿菌核心模型（練手用，不是你的菌）\n")
        return cobra.io.load_model("textbook")
    p = Path(path)
    if not p.exists():
        raise SystemExit(
            f"找不到 {p}。\n"
            f"先 git clone https://github.com/SysBioChalmers/rhto-GEM，\n"
            f"再用 `find rhto-GEM -name \"*.xml\"` 把 SBML 檔的實際路徑找出來"
            f"（資料夾名稱換過幾次，不要猜）。\n"
            f"想先練手的話，路徑直接寫 textbook。")
    return cobra.io.read_sbml_model(str(p))


def search(model, words: list[str], kind: str = "both") -> dict:
    """用關鍵字找反應與代謝物。比對 id 和 name，不分大小寫。"""
    low = [w.lower() for w in words]
    hit = lambda s: any(w in s.lower() for w in low)  # noqa: E731
    out = {"reactions": [], "metabolites": []}
    if kind in ("both", "r"):
        out["reactions"] = [r for r in model.reactions if hit(r.id) or hit(r.name or "")]
    if kind in ("both", "m"):
        out["metabolites"] = [m for m in model.metabolites if hit(m.id) or hit(m.name or "")]
    return out


def first(model, names: list[str], kind: str):
    """照偏好順序找第一個命中的。找不到回 None，**不要靜靜當作沒事**。"""
    for n in names:
        got = search(model, [n], kind)["reactions" if kind == "r" else "metabolites"]
        if got:
            return sorted(got, key=lambda x: len(x.id))[0]
    return None


def exchanges(model) -> dict:
    """把常用的交換反應找出來。回傳 {用途: 反應}，找不到的那一項是 None。"""
    got = {}
    for key, names in WANT.items():
        r = None
        for n in names:
            cands = [x for x in model.exchanges
                     if n.lower() in (x.name or "").lower() or n.lower() in x.id.lower()]
            if cands:
                r = sorted(cands, key=lambda x: len(x.id))[0]
                break
        got[key] = r
    return got


def biomass(model):
    """生質反應：先看目標函數，再用名字找。"""
    obj = [r for r in model.reactions if r.objective_coefficient]
    if obj:
        return obj[0]
    cands = search(model, ["biomass", "growth"], "r")["reactions"]
    return sorted(cands, key=lambda r: len(r.metabolites), reverse=True)[0] if cands else None


# ── 子指令 ────────────────────────────────────────────────────────────

def cmd_check(model, _a) -> dict:
    print(f"模型：{len(model.reactions)} 反應、{len(model.metabolites)} 代謝物、"
          f"{len(model.genes)} 基因")
    comp = {}
    for m in model.metabolites:
        comp[m.compartment] = comp.get(m.compartment, 0) + 1
    print("\n區隔（細菌只有一兩個，酵母菌十幾個——這是確認你載對模型的第一個訊號）：")
    for c, n in sorted(comp.items(), key=lambda kv: -kv[1]):
        print(f"  {c:<10}{n:>6} 個代謝物")

    bm = biomass(model)
    print(f"\n目標函數（生質反應）：{bm.id}　{(bm.name or '')[:50]}" if bm else "\n※ 找不到生質反應")

    med = model.medium
    print(f"\n目前培養基：{len(med)} 個交換反應開著（吸收上限 > 0）")
    for rid, v in sorted(med.items(), key=lambda kv: -kv[1])[:12]:
        print(f"  {rid:<14}{(model.reactions.get_by_id(rid).name or '')[:42]:<44}{v:>8.2f}")
    if len(med) > 12:
        print(f"  …還有 {len(med) - 12} 個")

    ex = exchanges(model)
    print("\n認出來的交換反應：")
    for k, r in ex.items():
        print(f"  {k:<10}{r.id if r else '※ 沒找到——用 find 子指令自己查'}"
              f"{'　' + (r.name or '')[:40] if r else ''}")

    mu = model.slim_optimize()
    print(f"\n跑一次 FBA：生長速率 μ = {mu:.4f} /h"
          f"（倍增時間 {0.693 / mu:.1f} 小時）" if mu and mu > 1e-6 else
          f"\n跑一次 FBA：**長不起來**（μ = {mu}）——培養基缺東西，先看上面那張清單")
    return {"n_reactions": len(model.reactions), "n_metabolites": len(model.metabolites),
            "n_genes": len(model.genes), "biomass": bm.id if bm else None,
            "mu_default": float(mu or 0.0),
            "exchanges": {k: (r.id if r else None) for k, r in ex.items()}}


def cmd_find(model, a) -> dict:
    res = search(model, a.words)
    print(f"關鍵字 {'、'.join(a.words)}：反應 {len(res['reactions'])} 個、"
          f"代謝物 {len(res['metabolites'])} 個\n")
    for r in res["reactions"][:a.limit]:
        genes = ", ".join(sorted(g.id for g in r.genes))[:46]
        print(f"[反應] {r.id:<12}{(r.name or '')[:46]:<48}[{r.lower_bound:>7.1f},{r.upper_bound:>7.1f}]")
        print(f"        {r.reaction[:110]}")
        if genes:
            print(f"        基因：{genes}")
    for m in res["metabolites"][:a.limit]:
        print(f"[代謝物] {m.id:<12}{(m.name or '')[:46]:<48}{m.formula or ''}　區隔 {m.compartment}")
    for key, n in (("reactions", len(res["reactions"])), ("metabolites", len(res["metabolites"]))):
        if n > a.limit:
            print(f"※ {key} 還有 {n - a.limit} 個沒印出來，用 --limit 調多一點")
    return {"query": a.words,
            "reactions": [{"id": r.id, "name": r.name, "reaction": r.reaction}
                          for r in res["reactions"][:a.limit]],
            "metabolites": [{"id": m.id, "name": m.name, "formula": m.formula,
                             "compartment": m.compartment} for m in res["metabolites"][:a.limit]]}


def set_medium(model, a, verbose: bool = True) -> dict:
    """設定碳源吸收速率與 C/N。回傳實際設下去的值。

    C/N 用**莫耳比**：葡萄糖一個分子 6 個碳、銨一個分子 1 個氮，所以
        氮吸收速率 = 6 × 葡萄糖吸收速率 ÷ (C/N)
    """
    ex = exchanges(model)
    used = {}
    glc = model.reactions.get_by_id(a.glucose_id) if a.glucose_id else ex["glucose"]
    nh4 = model.reactions.get_by_id(a.ammonium_id) if a.ammonium_id else ex["ammonium"]
    o2 = model.reactions.get_by_id(a.oxygen_id) if a.oxygen_id else ex["oxygen"]
    if glc is None or nh4 is None:
        raise SystemExit("找不到葡萄糖或銨的交換反應。先用 find 查出 id，"
                         "再用 --glucose-id／--ammonium-id 指定")

    glc.lower_bound = -abs(a.glucose)
    used["glucose"] = {"id": glc.id, "uptake": abs(a.glucose)}
    n_uptake = 6.0 * abs(a.glucose) / a.cn
    nh4.lower_bound = -n_uptake
    used["ammonium"] = {"id": nh4.id, "uptake": round(n_uptake, 4), "c_n_molar": a.cn}
    if o2 is not None:
        o2.lower_bound = -abs(a.oxygen)
        used["oxygen"] = {"id": o2.id, "uptake": abs(a.oxygen)}
    if verbose:
        print("設定的培養基（**請自己核對一次 id 對不對**）：")
        for k, v in used.items():
            print(f"  {k:<10}{v['id']:<14}吸收上限 {v['uptake']:>7.3f} mmol/gDW/h")
        print(f"  C/N（莫耳比）＝ {a.cn}　→　氮吸收 ＝ 6 × {abs(a.glucose)} ÷ {a.cn} "
              f"＝ {n_uptake:.3f}")
    return used


def cmd_medium(model, a) -> dict:
    used = set_medium(model, a)
    bm = biomass(model)
    sol = model.optimize()
    print(f"\nFBA：μ = {sol.objective_value:.4f} /h")
    if sol.objective_value < 1e-6:
        print("※ 長不起來。常見原因：碳源 id 設錯（看上面）、模型本來就缺某個必需成分、"
              "或這個模型預設是厭氧")
        return {"medium": used, "mu": 0.0}
    pfba = cobra.flux_analysis.pfba(model)
    print(f"pFBA（同樣的生長速率，但酵素用量最小）：總通量 {pfba.objective_value:.1f}")
    print("\n分泌出來的東西（通量 > 0 的交換反應）：")
    out = []
    for r in model.exchanges:
        v = pfba.fluxes[r.id]
        if v > 1e-6:
            out.append({"id": r.id, "name": r.name, "flux": round(float(v), 4)})
            print(f"  {r.id:<14}{(r.name or '')[:42]:<44}{v:>9.3f}")
    return {"medium": used, "mu": float(sol.objective_value), "secreted": out}


def add_afs(model, a, verbose: bool = True):
    """把 α-farnesene 合成酶加進模型：FPP → α-farnesene ＋ 焦磷酸，再加一條排出去的路。"""
    fpp = model.metabolites.get_by_id(a.fpp_id) if a.fpp_id else first(model, FPP_NAMES, "m")
    if fpp is None:
        raise SystemExit(
            "找不到 FPP。用 `find <模型> farnesyl` 查出 id，再用 --fpp-id 指定。\n"
            "（如果你在用內建的大腸桿菌模型練手：它沒有 FPP，拿 `--fpp-id akg_c` 之類的\n"
            "  代謝物頂替一下就好——反應是假的，但指令怎麼動是真的。）")
    # 焦磷酸要和 FPP 在同一個區隔，不然反應接不起來
    ppi = None
    for n in PPI_NAMES:
        cands = [m for m in model.metabolites
                 if n in (m.name or "").lower() and m.compartment == fpp.compartment]
        if cands:
            ppi = sorted(cands, key=lambda m: len(m.id))[0]
            break
    if ppi is None and not a.fpp_id:
        raise SystemExit(f"在 {fpp.compartment} 這個區隔裡找不到焦磷酸。用 find 查 diphosphate，"
                         f"rhto-GEM 一定有")

    met = Metabolite(AFS_MET, formula="C15H24", name="alpha-farnesene",
                     compartment=fpp.compartment)
    rxn = Reaction(AFS_RXN, name="alpha-farnesene synthase (apple AFS1)",
                   lower_bound=0.0, upper_bound=1000.0)
    model.add_reactions([rxn])
    stoich = {fpp: -1.0, met: 1.0}
    if ppi is not None:
        stoich[ppi] = 1.0
    rxn.add_metabolites(stoich)
    rxn.gene_reaction_rule = "AFS1"
    exr = Reaction(AFS_EX, name="alpha-farnesene exchange", lower_bound=0.0, upper_bound=1000.0)
    model.add_reactions([exr])
    exr.add_metabolites({met: -1.0})
    if verbose:
        print(f"加進去的反應：{rxn.id}　{rxn.reaction}")
        print(f"  FPP      ＝ {fpp.id}　{fpp.name}（區隔 {fpp.compartment}）")
        if ppi is not None:
            print(f"  焦磷酸   ＝ {ppi.id}　{ppi.name}")
        else:
            print("  焦磷酸   ＝ **找不到，這條反應沒有配平**——"
                  "只能拿來練指令，數字不能用")
        print(f"  排出去   ＝ {exr.id}")
        print("※ 產物會揮發，實驗上要用十二烷覆蓋層收集；模型裡就是這條交換反應。")
    return rxn, exr, fpp


def cmd_afs(model, a) -> dict:
    used = set_medium(model, a)
    print()
    rxn, exr, fpp = add_afs(model, a)
    bm = biomass(model)

    mu_max = model.slim_optimize()
    print(f"\n① 讓生長最大：μ = {mu_max:.4f} /h，"
          f"α-farnesene = {model.optimize().fluxes[AFS_RXN]:.4f}")
    print("   **產物是 0，這是對的，不是壞掉。** 讓生長最大的解不會浪費碳去做產物。")

    with model:
        model.objective = AFS_RXN
        prod_max = model.slim_optimize()
    print(f"\n② 不管菌長不長，讓產物最大：{prod_max:.4f} mmol/gDW/h")
    c_yield = prod_max * 15 / (abs(used["glucose"]["uptake"]) * 6) if prod_max else 0
    print(f"   碳的理論上限：{c_yield * 100:.1f}%（每 100 個糖的碳，最多 {c_yield * 100:.1f} 個變成產物）")
    print("   **這是上限，不是預期值**——它沒檢查 ATP 和 NADPH 夠不夠，實際一定更低。")
    if c_yield > 1.0:
        print("   ※ **碳上限超過 100%，這在物理上不可能。** 你的反應沒有配平——"
              "最常見的原因是 FPP 或焦磷酸指到了錯的代謝物。回去用 find 查清楚。")

    with model:
        bm.lower_bound = mu_max * 0.5
        model.objective = AFS_RXN
        half = model.slim_optimize()
    print(f"\n③ 生長保留一半（μ ≥ {mu_max * 0.5:.4f}），再讓產物最大：{half:.4f}")
    print("   這一欄才是有意義的數字：細胞要活著，才做得出東西。")
    return {"medium": used, "mu_max": float(mu_max or 0),
            "afs_max": float(prod_max or 0), "carbon_yield_max": float(c_yield),
            "afs_at_half_growth": float(half or 0)}


def cmd_envelope(model, a) -> dict:
    """生產包絡線：每一個生長速率下，產物最多與最少能有多少。"""
    used = set_medium(model, a, verbose=False)
    add_afs(model, a, verbose=False)
    bm = biomass(model)
    mu_max = model.slim_optimize()
    if not mu_max or mu_max < 1e-6:
        raise SystemExit("長不起來，先用 medium 子指令把培養基調對")

    rows = []
    for i in range(a.points):
        mu = mu_max * i / (a.points - 1)
        with model:
            bm.lower_bound = mu * 0.999
            model.objective = AFS_RXN
            model.objective_direction = "max"
            hi = model.slim_optimize() or 0.0
            model.objective_direction = "min"
            lo = model.slim_optimize() or 0.0
        lo = 0.0 if abs(lo) < 1e-9 else lo          # 求解器的 -0.0000 不是負產量
        rows.append({"mu": round(mu, 5), "lo": round(float(lo), 5), "hi": round(float(hi), 5)})

    print(f"生產包絡線（μ_max = {mu_max:.4f}）")
    print(f"{'μ (/h)':>9}{'最少':>10}{'最多':>10}")
    for r in rows:
        print(f"{r['mu']:>9.4f}{r['lo']:>10.4f}{r['hi']:>10.4f}")
    zero_lo = all(r["lo"] < 1e-6 for r in rows)
    print("\n下限全部是 0 →　**細胞可以「只長菌、不做產物」**。" if zero_lo else
          "\n下限 > 0 →　**不做產物就長不動**（成長耦合），這是最穩的狀態。")
    print("所以產量要靠**控制培養條件**去逼它，不是模型算出來就會有。"
          if zero_lo else "恭喜，這種菌株不用一直盯著。")
    return {"mu_max": float(mu_max), "rows": rows, "growth_coupled": not zero_lo}


def cmd_scan(model, a) -> dict:
    """掃 C/N，再掃 ERG9 調降，看產物上限怎麼動。"""
    add_afs(model, a, verbose=False)
    bm = biomass(model)
    erg9 = model.reactions.get_by_id(a.erg9_id) if a.erg9_id else first(model, ERG9_NAMES, "r")

    print("一、掃 C/N（每一格都「生長保留一半，再讓產物最大」）")
    print(f"{'C/N':>7}{'氮吸收':>10}{'μ_max':>10}{'產物上限':>11}")
    cn_rows = []
    for cn in a.cn_list:
        with model:
            a.cn = cn
            set_medium(model, a, verbose=False)
            mu = model.slim_optimize() or 0.0
            bm.lower_bound = mu * 0.5
            model.objective = AFS_RXN
            hi = model.slim_optimize() or 0.0
        n_up = 6.0 * abs(a.glucose) / cn
        cn_rows.append({"c_n": cn, "n_uptake": round(n_up, 4),
                        "mu_max": round(float(mu), 5), "afs_max": round(float(hi), 5)})
        print(f"{cn:>7}{n_up:>10.3f}{mu:>10.4f}{hi:>11.4f}")

    erg_rows = []
    if erg9 is not None:
        print(f"\n二、調降 ERG9（{erg9.id}　{(erg9.name or '')[:40]}），C/N 固定在 {a.cn_list[0]}")
        print(f"{'保留':>7}{'μ_max':>10}{'產物上限':>11}")
        with model:
            a.cn = a.cn_list[0]
            set_medium(model, a, verbose=False)
            base = erg9.upper_bound
            full_mu = model.slim_optimize() or 0.0
            for frac in (1.0, 0.5, 0.25, 0.1, 0.0):
                with model:
                    erg9.upper_bound = base * frac if base < 1000 else 1000 * frac
                    mu = model.slim_optimize() or 0.0
                    bm.lower_bound = full_mu * 0.5
                    model.objective = AFS_RXN
                    hi = model.slim_optimize() or 0.0
                erg_rows.append({"erg9_fraction": frac, "mu_max": round(float(mu), 5),
                                 "afs_max": round(float(hi), 5)})
                print(f"{frac:>7.2f}{mu:>10.4f}{hi:>11.4f}")
        print("\n※ 這條曲線告訴你「值不值得花三個月去做這個菌株」，**不是**告訴你會拿到多少。")
    else:
        print("\n※ 找不到鯊烯合成酶（ERG9）。用 `find <模型> squalene` 查，再用 --erg9-id 指定")

    print("\n**一個一定要知道的限制**：FBA 算的是穩態，它**不會**自己產生"
          "「限氮 → 累積油脂」這個現象。限氮在 FBA 裡只是把生長壓低而已。"
          "油脂累積是動態與調控的結果，要用 dFBA 或分階段模擬（第 5、6 章）才看得到。")
    return {"c_n_scan": cn_rows, "erg9_scan": erg_rows}


# ── 入口 ──────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, medium=False):
        p.add_argument("model", help="SBML 檔路徑，或寫 textbook 用內建模型練手")
        p.add_argument("-o", "--out", type=Path, help="把結果存成 JSON")
        if medium:
            p.add_argument("--glucose", type=float, default=10.0, help="葡萄糖吸收上限 mmol/gDW/h")
            p.add_argument("--cn", type=float, default=40.0, help="C/N 莫耳比")
            p.add_argument("--oxygen", type=float, default=1000.0, help="氧氣吸收上限")
            p.add_argument("--glucose-id", dest="glucose_id")
            p.add_argument("--ammonium-id", dest="ammonium_id")
            p.add_argument("--oxygen-id", dest="oxygen_id")

    p = sub.add_parser("check", help="模型概況、目前培養基、長不長得起來"); common(p)
    p = sub.add_parser("find", help="用關鍵字找反應與代謝物的 id"); common(p)
    p.add_argument("words", nargs="+"); p.add_argument("--limit", type=int, default=12)
    p = sub.add_parser("medium", help="設培養基、跑 FBA 與 pFBA"); common(p, True)
    p = sub.add_parser("afs", help="加 α-farnesene 反應、算理論上限"); common(p, True)
    p.add_argument("--fpp-id", dest="fpp_id")
    p = sub.add_parser("envelope", help="生產包絡線"); common(p, True)
    p.add_argument("--fpp-id", dest="fpp_id"); p.add_argument("--points", type=int, default=11)
    p = sub.add_parser("scan", help="掃 C/N 與 ERG9 調降"); common(p, True)
    p.add_argument("--fpp-id", dest="fpp_id"); p.add_argument("--erg9-id", dest="erg9_id")
    p.add_argument("--cn-list", dest="cn_list", type=float, nargs="+",
                   default=[10.0, 40.0, 120.0])

    a = ap.parse_args()
    model = load(a.model)
    res = {"check": cmd_check, "find": cmd_find, "medium": cmd_medium, "afs": cmd_afs,
           "envelope": cmd_envelope, "scan": cmd_scan}[a.cmd](model, a)
    if a.out:
        a.out.write_text(json.dumps({"model": a.model, "cmd": a.cmd, **res},
                                    ensure_ascii=False, indent=2), "utf-8")
        print(f"\n寫入 {a.out}")


if __name__ == "__main__":
    main()
