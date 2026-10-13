"""把模型的內容與單基因剔除結果匯出成 JSON，給網頁介面查。

Streamlit 那種介面最有用的兩件事是「搜尋反應」和「剔除某個基因會怎樣」。
第一件只是資料；第二件可以事先算完。兩件都不需要瀏覽器跑求解器。

    python rhto_afs_export.py <模型.json> -o rhto_afs_model.json [--glucose 10]

單基因剔除的做法很重要：**每一個基因都在「固定生長下限」下算產物**，
不是各自取自己的一半。不固定的話，任何讓菌長得慢的剔除看起來都像在增加產物
（第 21.3 節踩過這個坑）。
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import cobra  # noqa: E402

BM, GLC = "r_2111", "r_1714"
AFS_EX = "EX_alpha_farnesene"


def reactions(model) -> list:
    out = []
    for r in model.reactions:
        out.append({
            "i": r.id,
            "n": (r.name or "")[:90],
            "e": r.reaction[:200],
            "lb": round(r.lower_bound, 3), "ub": round(r.upper_bound, 3),
            "g": str(r.gene_reaction_rule)[:160],
            "s": sorted({m.compartment for m in r.metabolites}),
        })
    return out


def deletions(model, glucose: float, floor_frac: float = 0.1, timeout: int = 20) -> dict:
    """每個基因剔除一次，在固定生長下限下看產物與生長怎麼變。

    兩個加速，都是精確的、不是近似：

    1. **先問「這個基因剔掉之後，有沒有反應真的被關掉」**。OR 規則裡有備援的
       基因剔掉之後規則還是成立，等於什麼都沒動——這種直接抄野生型的值。
    2. **會關掉同一組反應的基因，只解一次**（例如同一個複合體的多個次單元）。

    另外給求解器一個時限。第一版沒給，結果卡在某一個剔除上空轉了四十分鐘
    （GLPK 在退化的解上繞不出來），整個掃描永遠跑不完。
    """
    def knocked_out(gene):
        """剔掉這個基因之後，哪些反應的 GPR 不再成立。有備援的就不會在裡面。"""
        return frozenset(r.id for r in gene.reactions
                         if r.gene_reaction_rule and not r.gpr.eval([gene.id]))

    try:
        model.solver.configuration.timeout = timeout
    except Exception:
        pass

    with model:
        model.reactions.get_by_id(GLC).lower_bound = -glucose
        mu0 = model.slim_optimize() or 0.0
        floor = mu0 * floor_frac
        with model:
            model.reactions.get_by_id(BM).lower_bound = floor
            model.objective = AFS_EX
            afs0 = model.slim_optimize() or 0.0

        genes = sorted(model.genes, key=lambda g: g.id)
        groups = {}
        noop = []
        for gene in genes:
            off = knocked_out(gene)
            if off:
                groups.setdefault(off, []).append(gene.id)
            else:
                noop.append(gene.id)
        print(f"  {len(noop)} 個基因有備援，剔掉不會關掉任何反應 → 直接抄野生型")
        print(f"  剩下 {len(genes) - len(noop)} 個基因、{len(groups)} 組不同的影響，"
              f"只要解 {len(groups)} 次", flush=True)

        solved = {}
        for n, off in enumerate(groups, 1):
            with model:
                for rid in off:
                    model.reactions.get_by_id(rid).knock_out()
                mu = model.slim_optimize()
                mu = 0.0 if mu is None or mu != mu else float(mu)
                afs = 0.0
                if mu >= floor - 1e-9:
                    with model:
                        model.reactions.get_by_id(BM).lower_bound = floor
                        model.objective = AFS_EX
                        v = model.slim_optimize()
                        afs = 0.0 if v is None or v != v else float(v)
            solved[off] = (round(mu, 5), round(afs, 5))
            if n % 50 == 0:
                print(f"  {n}/{len(groups)} 組", flush=True)

        by_gene = {}
        for off, ids in groups.items():
            for gid in ids:
                by_gene[gid] = solved[off]
        rows = []
        for gene in genes:
            mu, afs = by_gene.get(gene.id, (round(mu0, 5), round(afs0, 5)))
            rows.append({"i": gene.id, "mu": mu, "afs": afs,
                         "b": gene.id in by_gene,
                         "n": sorted(r.id for r in gene.reactions)[:6]})
    return {"glucose": glucose, "mu_wt": round(mu0, 5), "floor": round(floor, 5),
            "afs_wt": round(afs0, 5), "n_groups": len(groups), "n_noop": len(noop),
            "rows": rows,
            "note": "產物都在同一個固定生長下限下算，才互相可比。"
                    "b=false 代表這個基因有備援，剔掉不會關掉任何反應"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--glucose", type=float, default=10.0)
    ap.add_argument("--skip-deletions", action="store_true")
    a = ap.parse_args()

    m = cobra.io.load_json_model(str(a.model))
    rx = reactions(m)
    print(f"反應 {len(rx)}、基因 {len(m.genes)}")
    res = {"reactions": rx,
           "compartments": dict(sorted(m.compartments.items())) if m.compartments else {}}
    if not a.skip_deletions:
        print(f"單基因剔除掃描（葡萄糖 {a.glucose}）：")
        res["deletions"] = deletions(m, a.glucose)
        d = res["deletions"]
        hurt = [r for r in d["rows"] if r["mu"] < d["floor"] - 1e-9]
        up = [r for r in d["rows"] if r["afs"] > d["afs_wt"] + 1e-6]
        print(f"\n野生：μ {d['mu_wt']}、固定生長下限 {d['floor']}、產物 {d['afs_wt']}")
        print(f"剔除後長不到下限（必需基因）：{len(hurt)} 個")
        print(f"剔除後產物變多：{len(up)} 個")
        for r in sorted(up, key=lambda x: -x["afs"])[:10]:
            print(f"  {r['i']:<12}產物 {r['afs']:.4f}"
                  f"（＋{100*(r['afs']/d['afs_wt']-1):.1f}%）、μ {r['mu']:.4f}")
    a.out.write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), "utf-8")
    print(f"\n寫入 {a.out}（{a.out.stat().st_size/1024:.0f} KB）")


if __name__ == "__main__":
    main()
