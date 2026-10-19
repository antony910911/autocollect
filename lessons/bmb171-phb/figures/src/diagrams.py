"""BMB171 PHB 的示意圖。執行：python lessons/bmb171-phb/figures/src/diagrams.py [圖名 ...]

注意：svgkit 的 _rich() 會把底線當下標，所以 `3hbcoa_c` 這種 id 要寫成 `3hbcoa\\_c`。
圖的標題交給 Svg(...) 的第三個參數畫（它會畫在 (24, 40)），不要自己再畫一次。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_tools"))
from svgkit import INK, MUTED, Svg, render, tint, wrap  # noqa: E402

OUT = Path(__file__).resolve().parent.parent
CODE = OUT.parent / "code"
BLUE, ORANGE, RED, GREEN, PURPLE, GREY, BROWN, TEAL = ("#2f6fb3", "#d47c18", "#c23b3b", "#2f9e6e",
                                                       "#7b4bb3", "#6b7280", "#8a6d3b", "#1b8a8f")
W = 1000
D = json.loads((CODE / "checks.json").read_text("utf-8"))


def fig_overview():
    """這份分析從基因體走到數字，一共三段。"""
    s = Svg(W, 740, "圖 0-1　從基因體到「該讓菌長多快」，中間有三段")
    s.text(26, 72, "每一段都有自己的產出，也都有自己會出錯的地方。", size=16, color=MUTED)

    bands = [
        (128, BLUE, "①", "基因：這株菌到底有沒有完整的 PHB 路徑", [
            ("從 NCBI 下載基因體", "BMB171，GCA 000092165.1"),
            ("篩出候選 CDS", "關鍵字＋product 比對，得到 15 個"),
            ("判讀基因簇", "phaP–phaQ–phaR–phaB–phaC")]),
        (320, PURPLE, "②", "模型：把基因變成可以計算的代謝網路", [
            ("CarveMe 建草稿", "用 Gram-positive 模板自動裁切"),
            ("MEMOTE 品質檢查", "質量、電荷、註解、接不上的反應"),
            ("人工補上 PhaB 與 PhaR/PhaC", "自動建的草稿沒有這幾條")]),
        (512, TEAL, "③", "數字：在什麼條件下 PHB 最多", [
            ("定培養基、找氧氣飽和點", "葡萄糖 10、氧氣 60 當基準"),
            ("剔除三個基因做負控制", "PHB 全部歸零 → 路徑鎖住了"),
            ("Growth–PHB 取捨曲線", "甜蜜區 10–25% μmax")]),
    ]
    xs = [40, 368, 696]
    for y, color, no, title, items in bands:
        s.text(40, y, f"{no}　{title}", size=19, weight=700, color=color)
        for x, (lab, sub) in zip(xs, items):
            s.box(x, y + 18, 264, 96, lab, color=color, size=17, sub=sub, sub_size=13.5)
        for x in xs[:-1]:
            s.arrow([(x + 272, y + 66), (x + 320, y + 66)], color=color, width=2.6)
        if y < 500:
            s.arrow([(500, y + 124), (500, y + 172)], color=MUTED, width=2.4)

    s.box(40, 630, 920, 96, "", color=RED, fill=tint(RED, 0.95))
    s.icon("triangle-alert", 72, 660, 26, RED, 2.1)
    s.text(116, 666, "第 ② 段最大的一個坑", size=18, weight=700, color=RED)
    s.text(116, 694, "資料庫裡的 3hbcoa\\_c 是 (S) 型，不是 PHB 要的 (R) 型。不另外建一個專屬代謝物，",
           size=15)
    s.text(116, 716, "模型會繞過你補的 PhaB——數字照樣跑得出來，但是假的。", size=15)
    return s


def fig_trust():
    """哪些是算出來的、哪些是這裡查核過的、哪些還只是推論。"""
    s = Svg(W, 724, "圖 1-1　三種強度的結論，不要混在一起用")
    s.text(26, 72, "同一份筆記裡，有實際算出來的、有算得對但意義被講過頭的、也有還沒驗的推論。",
           size=16, color=MUTED)

    c = D["ceiling"]
    cards = [
        (GREEN, "circle-check", "可以直接用", [
            "・基因簇的排列與座標（有 GenBank 原始註解為憑）",
            "・剔除 PhaB／PhaR／PhaC 之後 PHB 歸零",
            "・表格每一欄的算術：通量、產率、氮需求、代謝 C/N——重算過，完全一致"]),
        (ORANGE, "circle-alert", "算得對，但不能照字面用", [
            f"・{c['mass_yield_g_g']} g/g 是**模型的**化學計量上限，不是實驗可達產率"
            f"（課本路徑只有 {c['textbook_mass_yield_g_g']} g/g，差 {c['ratio_to_textbook']:g} 倍）",
            "・代謝 C/N 是細胞實際吃進去的比例，**不是培養基配方**",
            "・「10–25% μmax」是模型的建議區間，不是已驗證的操作條件"]),
        (RED, "circle-x", "還只是推論，要再做", [
            "・60% μmax 的轉折是哪一條碳流在變——要跑 pFBA／FVA",
            "・phaJ 只憑 product 名稱認定，還沒做序列層次確認",
            "・**沒有任何一個數字做過培養驗證**"]),
    ]
    y = 104
    for color, icon, title, items in cards:
        h = s.card(40, y, 920, items, title=title, color=color, icon=icon, size=15.5, lh=27)
        y += h + 18
    return s


def fig_cluster():
    """基因簇：方向相反的兩個模組，phaZ 離得很遠。"""
    s = Svg(W, 596, "圖 2-1　五個基因全落在 3,765 bp 裡，phaZ 離了 1.9 Mb")
    s.text(26, 72, "合成的基因聚在一起，分解的那個放在很遠的地方——這件事會決定你什麼時候收菌。",
           size=16, color=MUTED)

    s.box(60, 118, 470, 96, "", color=TEAL, fill=tint(TEAL, 0.96), dash=True)
    s.text(72, 110, "1,295,466 – 1,299,230 bp", size=13.5, weight=700, color=TEAL)
    genes = [("phaP", 72, 74, ORANGE, "←"), ("phaQ", 152, 74, ORANGE, "←"),
             ("phaR", 244, 74, PURPLE, "→"), ("phaB", 330, 74, GREEN, "→"),
             ("phaC", 418, 86, PURPLE, "→")]
    for name, x, w, color, arrow in genes:
        s.box(x, 134, w, 40, f"{arrow} {name}" if arrow == "←" else f"{name} {arrow}",
              color=color, size=15, r=6)
    for x, gap in [(146, "42"), (226, "198"), (318, "150"), (404, "84")]:
        s.text(x + 7, 200, f"{gap} bp", size=11.5, color=MUTED, anchor="middle")

    s.box(760, 130, 150, 48, "phaZ", color=RED, size=17, sub="約 3.18 Mb", sub_size=12.5, r=6)
    s.line(60, 240, 940, 240, color=BROWN, width=3)
    s.text(60, 270, "染色體（BMB171，約 5.6 Mb）", size=14, color=MUTED)
    s.line(835, 182, 835, 240, color=RED, width=1.6, dash=True)
    s.line(295, 218, 295, 240, color=TEAL, width=1.6, dash=True)
    s.arrow([(544, 154), (750, 154)], color=MUTED, width=2, dash=True,
            label="相隔約 1.9 Mb", label_dy=-12, size=14, label_color=MUTED)

    rows = [
        (TEAL, "phaP、phaQ", "顆粒表面蛋白與調控蛋白。方向和後面三個相反，是另一個轉錄單元。"),
        (PURPLE, "phaR ＋ phaC", "**合起來才是一個有活性的酵素。**要過表現不能只動 phaC。"),
        (GREEN, "phaB", "把 acetoacetyl-CoA 還原成 (R)-3HB-CoA，吃 NADPH。"),
        (RED, "phaZ", "**把 PHB 分解回去。**離合成簇很遠 → 收穫時間是關鍵變因。"),
    ]
    y = 306
    for color, name, desc in rows:
        s.box(40, y, 150, 50, name, color=color, size=16, r=8)
        for i, ln in enumerate(wrap(desc, 16, 740)):
            s.text(212, y + 24 + i * 24, ln, size=16)
        y += 64
    return s


def fig_stereo():
    """最大的那個坑：模型繞過你補的 PhaB。"""
    s = Svg(W, 686, "圖 5-1　數字跑得出來，但 PhaB 的通量是 0")
    s.text(26, 72, "這代表模型根本沒走你補的那條路。它找到了一條繞過去的。", size=16, color=MUTED)

    s.box(40, 108, 920, 232, "", color=RED, fill=tint(RED, 0.97))
    s.chip(64, 126, "校正 v1：錯的", RED, 14)
    y = 196
    s.box(64, y, 150, 56, "acetoacetyl-CoA", color=BLUE, size=15, r=8)
    s.box(320, y, 180, 56, "3hbcoa\\_c", color=GREY, size=15, sub="資料庫裡是 (S) 型", sub_size=12)
    s.box(612, y, 140, 56, "PHB", color=TEAL, size=16, r=8)
    s.arrow([(220, y + 28), (314, y + 28)], color=RED, width=2.6,
            label="你補的 PhaB", label_dy=-13, size=14)
    s.text(267, y + 54, "通量 0", size=14, weight=700, color=RED, anchor="middle")
    s.arrow([(506, y + 28), (606, y + 28)], color=GREY, width=2.6)
    s.arrow([(410, y + 80), (410, y + 62)], color=RED, width=2.6)
    s.text(410, y + 106, "ECOAH1（β 氧化的水合酶）可以反向做出同一個代謝物",
           size=15, weight=700, color=RED, anchor="middle")
    s.text(410, y + 130, "→ 模型直接從這裡抄捷徑，完全不碰 PhaB",
           size=14, color=MUTED, anchor="middle")

    s.box(40, 364, 920, 202, "", color=GREEN, fill=tint(GREEN, 0.96))
    s.chip(64, 382, "校正 v2：對的", GREEN, 14)
    y2 = 450
    s.box(64, y2, 150, 56, "acetoacetyl-CoA", color=BLUE, size=15, r=8)
    s.box(320, y2, 180, 56, "3hbcoa\\_R\\_c", color=GREEN, size=15,
          sub="自己新建的 (R) 型", sub_size=12)
    s.box(612, y2, 140, 56, "PHB", color=TEAL, size=16, r=8)
    s.arrow([(220, y2 + 28), (314, y2 + 28)], color=GREEN, width=2.6,
            label="PhaB", label_dy=-13, size=14)
    s.arrow([(506, y2 + 28), (606, y2 + 28)], color=GREEN, width=2.6,
            label="PhaR/PhaC", label_dy=-13, size=14)
    s.box(790, y2 - 8, 148, 72, "沒有別的\n反應接得上", color=GREEN, size=15, r=8)
    s.text(64, y2 + 96, "**驗收標準**：印出 (R)-3HB-CoA 連到的反應，只能有 PhaB 和 PhaR/PhaC 兩條。",
           size=15)

    s.box(40, 588, 920, 84, "", color=ORANGE, fill=tint(ORANGE, 0.95))
    s.icon("circle-alert", 72, 618, 24, ORANGE, 2.1)
    s.text(116, 624, "兩個版本算出來的最大 PHB 都是 12.5——**數字一樣不代表模型一樣對**。",
           size=16, weight=700)
    s.text(116, 652, "所以每補一條反應，都要回去看那條反應的通量是不是真的大於 0。", size=15)
    return s


def fig_knockout():
    """負控制：剔掉就歸零，才代表路徑真的鎖在這三個基因上。"""
    s = Svg(W, 486, "圖 6-1　剔掉任一個，PHB 就歸零")
    s.text(26, 72, "如果剔掉之後 PHB 還在，代表模型裡還有一條你不知道的替代路徑。",
           size=16, color=MUTED)

    cases = [("野生型", "PHB 通量 12.50", TEAL), ("剔除 PhaB", "PHB 通量 0", RED),
             ("剔除 PhaR", "PHB 通量 0", RED), ("剔除 PhaC", "PHB 通量 0", RED)]
    x = 40
    for name, sub, color in cases:
        s.box(x, 116, 212, 112, name, color=color, size=18, sub=sub, sub_size=15)
        x += 228
    s.text(40, 266, "剔除 PhaB 實際印出來是 −5.7E−15（小數點後 14 個 0）。那是求解器的浮點誤差，當作 0。",
           size=15, color=MUTED)

    s.card(40, 296, 920, [
        "・**剔除不等於調降。**在 FBA 裡「把表現量降一半」沒有對應的做法——不綁住等於沒做，",
        "　綁死就等於剔除。要模擬調降得用酵素限制模型。",
        "・這一步過了，才能說後面的取捨曲線是這條路徑算出來的。"],
        title="這張圖只證明了一件事：模型結構是對的", color=GREEN, icon="circle-check",
        size=15.5, lh=27)
    return s


FIGS = {"fig0-1-overview": fig_overview, "fig1-1-trust": fig_trust,
        "fig2-1-cluster": fig_cluster, "fig5-1-stereo": fig_stereo,
        "fig6-1-knockout": fig_knockout}

if __name__ == "__main__":
    want = sys.argv[1:] or list(FIGS)
    render({k: FIGS[k]() for k in want if k in FIGS}, OUT)
