"""把文獻上的「氨氮耐受門檻」全部換算成同一個尺度（游離氨 NH3-N），才能互相比較。

為什麼要做這件事：文獻報耐受度的方式至少有四種——總氨氮（TAN）、NH4+-N、游離氨（NH3-N）、
mM。而且同一個 TAN 在不同 pH 下，真正有毒的游離氨差兩個數量級。不換算就會得到
「浮萍耐 250 mg/L」和「浮萍 8 mg/L 就死」這種看起來矛盾的結論（其實兩篇都對）。

換算公式和氨氮教材第 1 章同一套（Emerson et al. 1975 的 pKa）：
    pKa = 0.09018 + 2729.92 / T(K)
    NH3 佔總氨氮的比例 = 1 / (1 + 10^(pKa - pH))

執行：python lessons/aquatic-plants/code/tolerance.py
輸出：tolerance.json（圖與章節都引用這一份）

**所有文獻數字的可信度都只到摘要層級**（這個環境連不到期刊全文，只能靠 WebSearch 的摘要）。
每一筆都標了 conf：
    abstract  = 摘要或資料庫紀錄裡明確寫出的數字
    secondary = 回顧文章或搜尋摘要的轉述，連原始摘要都沒核對過
引用前請自己開全文核對。
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent


def pka(t_c: float) -> float:
    return 0.09018 + 2729.92 / (t_c + 273.15)


def nh3_fraction(ph: float, t_c: float) -> float:
    """游離氨（NH3）佔總氨氮的比例。"""
    return 1.0 / (1.0 + 10 ** (pka(t_c) - ph))


def tan_to_nh3(tan_mgN_L: float, ph: float, t_c: float) -> float:
    """總氨氮（以 N 計）→ 游離氨（以 N 計）。"""
    return tan_mgN_L * nh3_fraction(ph, t_c)


def nh3_to_tan(nh3_mgN_L: float, ph: float, t_c: float) -> float:
    """反過來：要讓游離氨不超過某個值，總氨氮最多可以是多少。"""
    return nh3_mgN_L / nh3_fraction(ph, t_c)


# ── 文獻門檻表 ────────────────────────────────────────────────────
# value_kind: "TAN"（總氨氮，以 N 計）／"NH3"（游離氨，以 N 計）／"NH4"（銨態氮，以 N 計）
# 沒寫 pH／溫度的，就用 assumed_* 欄位註明是我們假設的（換算結果只能當數量級看）。
LIT = [
    dict(key="myrio_26mM", zh="粉綠狐尾藻", sp="Myriophyllum aquaticum",
         endpoint="可存活（畜牧廢水中）", value=26.0, value_kind="mM_NH4", ph=7.5, t_c=25.0,
         assumed_ph=True, conf="abstract", ref="r_myrio_regnet",
         note="原文寫 >26 mM NH4+；pH 未在摘要中給出，這裡假設 7.5"),
    dict(key="canna_200", zh="美人蕉", sp="Canna indica",
         endpoint="自我修復門檻（之下生長受影響小）", value=200.0, value_kind="TAN", ph=7.5, t_c=25.0,
         assumed_ph=True, conf="abstract", ref="r_wang2016",
         note="100–200 mg/L 區間甚至促進生長"),
    dict(key="typha_200", zh="香蒲", sp="Typha orientalis",
         endpoint="自我修復門檻", value=200.0, value_kind="TAN", ph=7.5, t_c=25.0,
         assumed_ph=True, conf="abstract", ref="r_wang2016"),
    dict(key="scirpus_100", zh="水蔥", sp="Scirpus validus",
         endpoint="明顯受抑制的起點", value=100.0, value_kind="TAN", ph=7.5, t_c=25.0,
         assumed_ph=True, conf="secondary", ref="r_wang2016"),
    dict(key="iris_100", zh="鳶尾", sp="Iris tectorum",
         endpoint="明顯受抑制的起點", value=100.0, value_kind="TAN", ph=7.5, t_c=25.0,
         assumed_ph=True, conf="secondary", ref="r_wang2016"),
    dict(key="lemna_gibba_death", zh="浮萍（Lemna gibba）", sp="Lemna gibba",
         endpoint="致死（游離氨）", value=8.0, value_kind="NH3", ph=None, t_c=None,
         conf="abstract", ref="r_korner2001",
         note="生長隨游離氨上升線性下降，超過 8 mg N/L 死亡"),
    dict(key="lemna_minor_ec50", zh="浮萍（Lemna minor）", sp="Lemna minor",
         endpoint="50% 生長抑制（游離氨，pH 8.5）", value=7.2, value_kind="NH3", ph=8.5, t_c=25.0,
         conf="secondary", ref="r_korner2001",
         note="轉述自回顧文章，沒核對過原始摘要"),
    dict(key="lemna_minor_250", zh="浮萍（Lemna minor）", sp="Lemna minor",
         endpoint="生長未受影響（總氨氮上限）", value=250.0, value_kind="TAN", ph=6.0, t_c=25.0,
         assumed_ph=True, conf="secondary", ref="r_lemna_high_nh4",
         note="搜尋摘要轉述；pH 未知，這裡假設偏酸（6.0）才說得通"),
    dict(key="duckweed_op60", zh="浮萍（操作建議）", sp="Lemna minor",
         endpoint="實務操作上限（避免毒害）", value=60.0, value_kind="TAN", ph=7.5, t_c=25.0,
         assumed_ph=True, conf="abstract", ref="r_abr_lemna"),
    dict(key="duckweed_op30", zh="浮萍（操作最適）", sp="Lemna minor",
         endpoint="最適氮濃度", value=30.0, value_kind="TAN", ph=7.5, t_c=25.0,
         assumed_ph=True, conf="secondary", ref="r_wur_manure"),
    dict(key="nitrifier_fa", zh="硝化菌（不是植物）", sp="AOB/NOB",
         endpoint="硝化受抑制（游離氨）", value=14.75, value_kind="NH3", ph=None, t_c=None,
         conf="abstract", ref="r_mesocosm2019",
         note="原文 13.3–16.2 mg N/L，這裡取中點；放進來是為了對照：植物先掛還是菌先掛"),
]

# 酸化那組實驗單獨處理：它是整份教材最強的對照（同一份沼液，pH 差 1.7 就翻盤）
ACID = dict(
    ref="r_aber_ph", conf="abstract", t_c=20.0,
    note=("同一份厭氧消化牛糞液：未調 pH（8.2）時連稀釋到 5% 浮萍都長不起來；"
          "酸化到 pH 6.5 後，稀釋到 20%（TAN 239.3 mg/L）仍是正成長。"),
    unamended=dict(ph=8.2, dilution_pct=5.0),
    acidified=dict(ph=6.5, dilution_pct=20.0, tan=239.3),
)


def build() -> dict:
    out: dict = {"method": {
        "pka_formula": "pKa = 0.09018 + 2729.92 / T(K)（Emerson et al. 1975）",
        "fraction_formula": "f_NH3 = 1 / (1 + 10^(pKa - pH))",
        "caveat": "所有文獻數字只到摘要層級；pH 未知的項目用 assumed_ph 標註。",
    }}

    # 1. 比例表：pH × 溫度 → 游離氨比例
    out["fraction_table"] = {
        f"pH{ph}_T{t}": round(nh3_fraction(ph, t) * 100, 4)
        for t in (15, 20, 25, 30) for ph in (6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0)
    }
    out["pka"] = {str(t): round(pka(t), 3) for t in (15, 20, 25, 30)}

    # 2. 文獻門檻換算
    rows = []
    for e in LIT:
        r = dict(e)
        t_c = e["t_c"] if e["t_c"] is not None else 25.0
        if e["value_kind"] == "mM_NH4":
            r["tan_mgN_L"] = round(e["value"] * 14.007, 1)
        elif e["value_kind"] in ("TAN", "NH4"):
            r["tan_mgN_L"] = e["value"]
        else:
            r["tan_mgN_L"] = None
        if e["value_kind"] == "NH3":
            r["nh3_mgN_L"] = e["value"]
            # 這個游離氨門檻，換算成不同 pH 下的總氨氮上限
            r["tan_equiv"] = {f"pH{ph}": round(nh3_to_tan(e["value"], ph, t_c), 1)
                              for ph in (6.5, 7.0, 7.5, 8.0, 8.5)}
        else:
            r["nh3_mgN_L"] = round(tan_to_nh3(r["tan_mgN_L"], e["ph"], t_c), 2)
        r["t_c_used"] = t_c
        rows.append(r)
    out["thresholds"] = rows

    # 3. 安全曲線：要讓游離氨不超過 X，總氨氮最多多少
    out["safe_tan_curve"] = {
        f"NH3_{lim}": {f"pH{ph:.1f}": round(nh3_to_tan(lim, ph, 25.0), 1)
                       for ph in [6.0 + 0.25 * i for i in range(13)]}
        for lim in (0.5, 2.0, 8.0)
    }

    # 4. 酸化對照：算出兩組的游離氨差幾倍
    a = dict(ACID)
    acid, un = ACID["acidified"], ACID["unamended"]
    tan_full = acid["tan"] / (acid["dilution_pct"] / 100.0)      # 原液 TAN
    tan_un = tan_full * un["dilution_pct"] / 100.0               # 未調 pH 那組的 TAN
    fa_un = tan_to_nh3(tan_un, un["ph"], ACID["t_c"])
    fa_ac = tan_to_nh3(acid["tan"], acid["ph"], ACID["t_c"])
    a["derived"] = dict(
        tan_full_strength=round(tan_full, 0),
        unamended_tan=round(tan_un, 1), unamended_nh3=round(fa_un, 2),
        acidified_tan=acid["tan"], acidified_nh3=round(fa_ac, 3),
        tan_ratio=round(acid["tan"] / tan_un, 1),
        nh3_ratio=round(fa_un / fa_ac, 1),
        comment=("總氨氮高 %.1f 倍的那一組反而活得好，因為游離氨低了 %.0f 倍。"
                 % (acid["tan"] / tan_un, fa_un / fa_ac)),
    )
    out["acidification"] = a
    return out


if __name__ == "__main__":
    d = build()
    (OUT / "tolerance.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
    print("pKa(20°C) =", d["pka"]["20"])
    for r in d["thresholds"]:
        print(f'{r["zh"]:<18} {r["endpoint"]:<24} TAN={r["tan_mgN_L"]}  NH3-N={r["nh3_mgN_L"]}  [{r["conf"]}]')
    print("酸化對照：", d["acidification"]["derived"])
    print("安全曲線（游離氨 ≤2 mg N/L，25°C）：", d["safe_tan_curve"]["NH3_2.0"])
