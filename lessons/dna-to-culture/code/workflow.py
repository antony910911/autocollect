"""第 19 章：把整條流程的「操作單數字」算出來。

這支程式不做模擬，只做**換算**——把「C/N 要 20」這種說法，換成「秤幾公克葡萄糖、
幾公克硫酸銨」這種可以拿去實驗室執行的數字。

每個數字都標了出處等級，章節裡會照抄：

  `calc`  —— 化學計量算出來的，可以自己驗算（分子量、碳氮數都是定值）
  `lit`   —— 文獻來的，引用在章節裡
  `guess` —— **起始猜測**，沒有這株菌的實測值。第一批實驗就是要把它量出來

執行：
    python code/workflow.py            # 寫出 workflow.json
    python code/workflow.py --show     # 順便印出操作單
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ── 分子量與元素組成（定值，不用引用） ──────────────────────────
MW = {"glucose": 180.16, "xylose": 150.13, "AMS": 132.14,    # (NH4)2SO4
      "dodecane": 170.33, "pentadecane": 212.41}
C_PER_MOL = {"glucose": 6, "xylose": 5}
N_PER_MOL = {"AMS": 2}

# 容器與供氧能力（和第 10 章 protocol.py 的 VESSELS 同一份）
VESSELS = [("試管／深孔盤（靜置或慢搖）", 5, 20),
           ("搖瓶，裝液 40%、150 rpm", 20, 60),
           ("搖瓶，裝液 20%、200 rpm", 60, 120),
           ("搖瓶，裝液 10%、250 rpm 或加擋板", 120, 250),
           ("攪拌式發酵槽（通氣＋攪拌）", 200, 1000)]

# 碳的理論上限：見 17.8，由 code/farnesene_path.py 算出
G_PRODUCT_PER_G_GLUCOSE = 0.252


def medium(c_n: float, glucose_gL: float, carbon: str = "glucose") -> dict:
    """給定 C/N 莫耳比與糖濃度，算出要加多少硫酸銨。

    C/N 在文獻裡有兩種寫法（莫耳比、質量比），差快兩倍，看錯會整批做錯。
    這裡**一律用莫耳 C ／ 莫耳 N**，而且把兩種都印出來，避免混淆。
    """
    mol_c = glucose_gL / MW[carbon] * C_PER_MOL[carbon]
    mol_n = mol_c / c_n
    ams_gL = mol_n / N_PER_MOL["AMS"] * MW["AMS"]
    return {
        "c_n_molar": c_n,
        "carbon": carbon,
        "sugar_gL": round(glucose_gL, 2),
        "AMS_gL": round(ams_gL, 3),
        "mol_C_per_L": round(mol_c, 3),
        "mol_N_per_L": round(mol_n, 4),
        "c_n_mass": round(glucose_gL * 0.4 / (ams_gL * 0.2121), 1) if ams_gL else None,
        "note": "C/N 是莫耳比；質量比（gC/gN）另外列出來對照",
        "source": "calc",
    }


def inoculum(work_mL: float, target_od: float, seed_od: float) -> dict:
    """接種量：要從種菌接幾 mL。"""
    need = work_mL * target_od / seed_od
    return {"work_mL": work_mL, "target_od0": target_od, "seed_od": seed_od,
            "seed_mL": round(need, 2), "pct_v_v": round(need / work_mL * 100, 1),
            "source": "calc"}


def vessel(work_mL: float, flask_mL: float) -> dict:
    """裝液比例 → 供氧能力落在哪一檔。"""
    fill = work_mL / flask_mL * 100
    if fill <= 12:
        row = VESSELS[3]
    elif fill <= 25:
        row = VESSELS[2]
    elif fill <= 45:
        row = VESSELS[1]
    else:
        row = VESSELS[0]
    return {"flask_mL": flask_mL, "work_mL": work_mL, "fill_pct": round(fill, 1),
            "matches": row[0], "kla_lo": row[1], "kla_hi": row[2],
            "note": "kLa 是量級，**你自己的搖床一定要實測**（亞硫酸鈉法或動態法）",
            "source": "lit"}


def overlay(work_mL: float, pct: float = 20.0, istd_gL: float = 1.0) -> dict:
    """十二烷覆蓋層與內標。"""
    dod = work_mL * pct / 100
    return {"pct_v_v": pct, "dodecane_mL": round(dod, 1),
            "pentadecane_mg": round(dod / 1000 * istd_gL * 1000, 1),
            "istd_gL": istd_gL,
            "why": "產物會揮發；不覆蓋量到的是「還沒跑掉的那一點」",
            "source": "lit"}


def ceiling(sugar_gL: float, work_mL: float) -> dict:
    """這一瓶糖全部用完，產物最多能有多少（碳的理論上限）。"""
    g_per_L = sugar_gL * G_PRODUCT_PER_G_GLUCOSE
    return {"sugar_gL": sugar_gL, "max_product_gL": round(g_per_L, 2),
            "max_product_mg_per_flask": round(g_per_L * work_mL, 1),
            "note": "只算碳、沒檢查 ATP 與 NADPH，所以實際一定更低；"
                    "文獻實際做到的是上限的百分之幾",
            "source": "calc"}


def sampling(total_h: float = 96.0) -> list[dict]:
    """取樣時程：前期密、後期疏，但換階段的那一段要加密。"""
    plan = [
        (0, 12, 4.0, "OD、殘糖、殘氮", "確認有沒有長起來、有沒有汙染"),
        (12, 36, 6.0, "OD、殘糖、**殘氮**、乾重", "**氮歸零的那一刻是開關**，這段要盯緊"),
        (36, 72, 12.0, "全部項目", "產物與油脂開始累積"),
        (72, total_h, 24.0, "全部項目", "看有沒有平台或下降"),
    ]
    out = []
    for a, b, step, what, why in plan:
        times = []
        t = float(a)
        while t < b:
            times.append(round(t, 1))
            t += step
        out.append({"from_h": a, "to_h": b, "every_h": step,
                    "times": times, "measure": what, "why": why})
    out[-1]["times"].append(float(total_h))
    return out


def design(work_mL=50.0, flask_mL=250.0, sugar_gL=40.0) -> dict:
    """第一次實驗的完整設計：3 個 C/N × 有無覆蓋層，加三組對照。"""
    conds = []
    for tag, c_n, why in (("低（氮充足）", 10, "預期：專心長菌，產物競爭最小"),
                          ("中", 40, "預期：中間狀態，看轉折點落在哪"),
                          ("高（限氮）", 120, "預期：催油脂，看產物是不是真的被壓下去")):
        for dod in (True, False):
            conds.append({
                "label": f"C/N {c_n}{'　＋十二烷' if dod else '　無覆蓋'}",
                "c_n": c_n, "overlay": dod, "why": why,
                "medium": medium(c_n, sugar_gL),
                "overlay_spec": overlay(work_mL) if dod else None,
            })
    controls = [
        {"label": "不接種（培養基對照）", "why": "確認沒有汙染、確認 GC-MS 的背景"},
        {"label": "沒有插入的那一株（C/N 40 ＋十二烷）",
         "why": "**最重要的對照**——產物訊號要是它沒有、基改株才有，才算數"},
        {"label": "十二烷但不接種", "why": "確認覆蓋層本身不會釋出干擾峰"},
    ]
    return {
        "flasks": len(conds) + len(controls),
        "conditions": conds,
        "controls": controls,
        "vessel": vessel(work_mL, flask_mL),
        "inoculum": inoculum(work_mL, 0.2, 5.0),
        "sampling": sampling(96.0),
        "ceiling": ceiling(sugar_gL, work_mL),
        "replicates": {"n": 3, "why": "三重複是能算標準差的最低要求；搖瓶之間的差異很大",
                       "source": "guess"},
        "assumptions": [
            {"what": "起始 OD600 = 0.2", "level": "guess",
             "why": "太低遲滯期長、太高很快缺氧。0.1–0.5 都合理，挑一個記下來就好"},
            {"what": "糖 40 g/L", "level": "guess",
             "why": "搖瓶不補料，太高會滲透壓抑制。要拉高產量要改成饋料批次"},
            {"what": "96 小時", "level": "guess",
             "why": "文獻的倍半萜發酵多在 3–7 天。第一批就是要量出你的曲線長什麼樣"},
            {"what": "C/N 10／40／120", "level": "guess",
             "why": "橫跨「氮充足」到「明顯限氮」。**沒有文獻掃過 C/N 對倍半萜產量的影響**（見 18.9）"},
            {"what": "十二烷 20% v/v、內標 1 g/L", "level": "lit",
             "why": "Yaegashi 2017：700 mL 培養液 ＋ 150 mL 覆蓋層"},
        ],
    }


STAGES = [
    ("1", "確認手上的菌是什麼", "定序檔",
     "菌種、倍體性、參考基因體", "code/genome_tools.py stats",
     "搞錯菌種，後面全部的工具選擇都是錯的"),
    ("2", "確認基改進去了沒", "定序檔 ＋ 構築序列",
     "拷貝數、插入位置、哪個拷貝壞了", "code/case_rt.py",
     "不知道進去幾份，就不知道瓶頸在不在拷貝數"),
    ("3", "拿到功能註解並修正", "定序廠的註解包",
     "基因位置檔、鄰居的身分、修過的轉殖基因模型", "code/annotation.py",
     "沒有基因位置檔就不能做 RNA-seq；不修就會算錯"),
    ("4", "把基因變成模型裡的反應", "rhto-GEM ＋ 你的基因對照表",
     "可以跑 FBA 的模型", "code/engineered.py",
     "模型是用來「先篩掉不值得做的實驗」的"),
    ("5", "用模型挑要測的條件", "模型",
     "一張很短的條件清單", "code/experiments.py",
     "不要一開始就做 20 個搖瓶，先讓模型砍掉一半"),
    ("6", "做第一批實驗", "條件清單",
     "生長曲線、殘糖殘氮、油脂、色素、產物、表現量", "本章的操作單",
     "這是整條流程唯一會產生「真實數字」的一步"),
    ("7", "把數據餵回模型", "實驗數據",
     "修正過的參數、下一輪的條件", "code/calibrate.py",
     "沒有這一步，模型永遠停在教科書參數"),
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    ap.add_argument("-o", "--out", default=str(HERE / "workflow.json"))
    a = ap.parse_args(argv)

    out = {
        "stages": [dict(zip(("n", "name", "input", "output", "tool", "why"), s))
                   for s in STAGES],
        "design": design(),
        "constants": {"g_product_per_g_glucose": G_PRODUCT_PER_G_GLUCOSE,
                      "mw": MW, "source": "calc；上限見 17.8"},
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"寫入 {a.out}")

    d = out["design"]
    print(f"\n第一批實驗：{d['flasks']} 瓶（{len(d['conditions'])} 個條件 ＋ "
          f"{len(d['controls'])} 組對照），每個條件 {d['replicates']['n']} 重複")
    print(f"容器：{d['vessel']['flask_mL']:.0f} mL 搖瓶裝 {d['vessel']['work_mL']:.0f} mL"
          f"（{d['vessel']['fill_pct']}%）→ {d['vessel']['matches']}")
    print(f"接種：種菌 OD {d['inoculum']['seed_od']} 接 {d['inoculum']['seed_mL']} mL"
          f"（{d['inoculum']['pct_v_v']}% v/v），起始 OD {d['inoculum']['target_od0']}")
    if a.show:
        print("\n培養基（每公升）：")
        for c in d["conditions"][::2]:
            m = c["medium"]
            print(f"  C/N {m['c_n_molar']:>3}：葡萄糖 {m['sugar_gL']} g ＋ "
                  f"硫酸銨 {m['AMS_gL']} g　（質量比 C/N ≈ {m['c_n_mass']}）")
        o = d["conditions"][0]["overlay_spec"]
        print(f"\n覆蓋層：十二烷 {o['dodecane_mL']} mL／瓶，裡面溶 "
              f"{o['pentadecane_mg']} mg pentadecane 當內標")
        c = d["ceiling"]
        print(f"\n碳的理論上限：糖 {c['sugar_gL']} g/L 最多做出 "
              f"{c['max_product_gL']} g/L（每瓶 {c['max_product_mg_per_flask']} mg）")
        print("  ——這是上限，不是預期值。文獻實際做到的是上限的百分之幾。")


if __name__ == "__main__":
    main()
