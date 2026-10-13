"""把「A13_4 ＋ AFS」模型事先算成一張查表，給網頁介面用。

為什麼要事先算：瀏覽器跑不動線性規劃求解器（第 19.5 節）。
所以在這裡把每一格都解一次，存成 JSON，網頁只負責查表與畫圖。

    python rhto_afs_grid.py <A13_4_AFS_draft_v2.json> -o rhto_afs_grid.json

格點：葡萄糖吸收 1–15、C/N 10–120、生長下限 0–100%。
每一格都問同一件事：**在這個條件下、菌至少要長這麼快，產物最多能有多少。**
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import cobra  # noqa: E402

BM, GLC, NH4 = "r_2111", "r_1714", "r_1654"
AFS_EX = "EX_alpha_farnesene"
MW_FARNESENE, MW_GLC = 204.36, 180.16
GLC_GRID = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15]
CN_GRID = [10, 15, 20, 30, 40, 60, 80, 100, 120]
FRACS = [i / 20 for i in range(21)]


def row(model, glucose, cn=None):
    """一個培養條件：掃生長下限，每一格求產物最大值。"""
    with model:
        model.reactions.get_by_id(GLC).lower_bound = -glucose
        if cn is not None:
            model.reactions.get_by_id(NH4).lower_bound = -(6.0 * glucose / cn)
        mu = model.slim_optimize() or 0.0
        if mu < 1e-9:
            return {"mu_max": 0.0, "afs": [0.0] * len(FRACS), "g_per_g": [0.0] * len(FRACS)}
        afs = []
        for f in FRACS:
            with model:
                model.reactions.get_by_id(BM).lower_bound = mu * f
                model.objective = AFS_EX
                v = model.slim_optimize() or 0.0
            afs.append(round(max(0.0, float(v)), 5))
    return {"mu_max": round(float(mu), 5),
            "afs": afs,
            "g_per_g": [round(v * MW_FARNESENE / (glucose * MW_GLC), 4) for v in afs]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    a = ap.parse_args()

    m = cobra.io.load_json_model(str(a.model))
    print(f"模型 {len(m.reactions)} 反應，開始算 "
          f"{len(GLC_GRID)} × {len(FRACS)} ＋ {len(CN_GRID)} × {len(FRACS)} 格")

    glucose = {}
    for g in GLC_GRID:
        glucose[str(g)] = row(m, g)
        print(f"  糖 {g:>3} → μmax {glucose[str(g)]['mu_max']:.4f}、"
              f"產物上限 {glucose[str(g)]['afs'][0]:.4f}", flush=True)

    cn = {}
    for c in CN_GRID:
        cn[str(c)] = row(m, 10.0, cn=c)
        print(f"  C/N {c:>3} → μmax {cn[str(c)]['mu_max']:.4f}、"
              f"產物（半生長）{cn[str(c)]['afs'][10]:.4f}", flush=True)

    a.out.write_text(json.dumps({
        "source": "A13_4_AFS_draft_v2（rhto-GEM ＋ 候選 AFS）",
        "glucose_grid": GLC_GRID, "cn_grid": CN_GRID, "fracs": FRACS,
        "cn_glucose": 10.0,
        "glucose": glucose, "cn": cn,
        "note": "每一格是「菌至少長這麼快時，產物的最大模型通量」，單位 mmol/gDW/h。"
                "這是上限，不是預測，也不是 g/L。",
    }, ensure_ascii=False, separators=(",", ":")), "utf-8")
    print(f"\n寫入 {a.out}（{a.out.stat().st_size/1024:.0f} KB）")


if __name__ == "__main__":
    main()
