"""水生植物教材的示意圖。執行：python lessons/aquatic-plants/figures/src/diagrams.py [圖名 ...]

注意（都是踩過的坑）：
 - svgkit 不會自動換行，長句要自己用 wrap() 按實際寬度斷行。
 - card() 的自動換行會從 **粗體** 中間切斷，所以每一項盡量一行講完，或把粗體放句首。
 - 圖裡不要用反引號（svgkit 不支援，會原樣印出來）。
 - 畫布開太矮時 card() 的下半截會被切掉，check_geometry 的「文字出界」抓不到，要自己看。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_tools"))
from svgkit import INK, MUTED, Svg, render, tint, wrap, _text_w  # noqa: E402
from tokens import C  # noqa: E402

OUT = Path(__file__).resolve().parent.parent
CODE = OUT.parent / "code"
T = json.loads((CODE / "tolerance.json").read_text("utf-8"))
S = json.loads((CODE / "sizing.json").read_text("utf-8"))
L = json.loads((CODE / "literature.json").read_text("utf-8"))

W = 1000
BLUE, ORANGE, TEAL, PURPLE, GREEN, RED, BROWN, GREY = (
    C["blue"], C["orange"], C["teal"], C["purple"], C["green"], C["red"], C["brown"], C["grey"])


def sub(s: Svg, text: str, y: int = 72):
    s.text(26, y, text, size=16, color=MUTED)


def note(s: Svg, x: int, y: int, w: int, text: str, color=GREY, icon=None, size=14.5):
    """底部的註腳條。回傳高度。"""
    lines = wrap(text, size, w - (76 if icon else 48))
    h = 26 + len(lines) * 22
    s.box(x, y, w, h, "", color=color, fill=tint(color, 0.95))
    if icon:
        s.icon(icon, x + 20, y + 15, 22, color, 2.0)
    for i, ln in enumerate(lines):
        s.text(x + (56 if icon else 24), y + 32 + i * 22, ln, size=size, color=INK)
    return h


# ── 導讀：學習地圖 ────────────────────────────────────────────
def fig0_1_roadmap():
    s = Svg(W, 760, "圖 0-1　這門教材怎麼走")
    sub(s, "三個分區：先搞懂植物與氨氮的關係，再看別人怎麼做，最後自己算一套設計。")
    bands = [
        (112, GREEN, "分區一", "原理與物種篩選", [
            "1　去除不等於降解", "2　植物怎麼用氨氮", "3　耐受度看游離氨",
            "4　浮水植物圖鑑", "5　挺水與可食物種", "6　怎麼篩選"]),
        (320, BLUE, "分區二", "廢水處理的實際應用", [
            "1　人工濕地", "2　速率與面積", "3　高濃度廢水",
            "4　讀實場數據", "5　台灣的現況"]),
        (528, PURPLE, "分區三", "硝化槽＋植體槽", [
            "1　為什麼先硝化", "2　耦合與解耦", "3　設計計算",
            "4　誰做過", "5　還有什麼應用"]),
    ]
    for y, color, tag, title, chaps in bands:
        s.box(40, y, 206, 128, tag, color=color, size=22, sub=title, sub_size=15)
        x = 272
        for i, ch in enumerate(chaps):
            cx = x + (i % 3) * 232
            cy = y + (i // 3) * 64
            s.box(cx, cy, 216, 52, ch, color=color, size=15.5, fill="#ffffff", weight=400)
        if y < 500:
            s.arrow([(143, y + 136), (143, y + 200)], color=MUTED, width=2.4)
    note(s, 40, 678, 920,
         "每一章的數字都由 code/ 的三支程式算出來，章節只引用結果。文獻數字一律標了可信度："
         "abstract（摘要寫的）／secondary（轉述的）——這個環境連不到期刊全文。",
         color=GREY, icon="circle-alert")
    return s


# ── 分區一第 1 章：氨氮的五個去向 ──────────────────────────────
def fig1_1_fates():
    s = Svg(W, 760, "圖 1-2　氨氮進了植物池，會往五個方向跑")
    sub(s, "只有兩條路真的把氮帶出系統。其他三條只是搬家——不收割、不量總氮，就會把搬家當成移除。")
    rows = [
        (GREEN, "leaf", "① 植物吸收", "變成植物體內的蛋白質",
         "收割才算移除", True, "不收割，植株死掉就全部還回水裡"),
        (GREEN, "wind", "② 根圈脫硝", "硝酸鹽變成氮氣跑掉",
         "真的移除", True, "需要缺氧微區與碳源，根的周圍剛好有"),
        (BLUE, "refresh-cw", "③ 根圈硝化", "氨氮變成硝酸鹽",
         "只是換個形態", False, "氨氮數字會漂亮下降，但總氮沒有少"),
        (ORANGE, "arrow-up-from-line", "④ 揮發", "NH_3_ 跑到空氣裡",
         "變成空氣污染", False, "pH 越高越嚴重；浮水植物蓋住水面反而會壓低這條"),
        (BROWN, "layers", "⑤ 沉澱與吸附", "有機氮沉到底泥",
         "暫時寄放", False, "底泥累積到一定程度會回吐（見第二分區第 4 章）"),
    ]
    y = 108
    for color, ic, title, what, verdict, ok, tail in rows:
        s.box(40, y, 920, 92, "", color=color, fill=tint(color, 0.96))
        s.icon(ic, 66, y + 34, 26, color, 2.1)
        s.text(110, y + 36, title, size=18, weight=700, color=color)
        s.text(110, y + 62, what, size=15, color=INK)
        s.text(400, y + 36, tail, size=14.5, color=MUTED)
        s.icon("circle-check" if ok else "circle-alert", 790, y + 30, 22,
               GREEN if ok else ORANGE, 2.1)
        s.text(822, y + 46, verdict, size=16, weight=700, color=GREEN if ok else ORANGE)
        y += 104
    note(s, 40, y + 6, 920,
         "要分辨這五條，最少要量：氨氮、亞硝酸鹽、硝酸鹽、總氮、pH、水溫，加上植體的乾重與含氮量。"
         "少量總氮，就沒辦法說「氮去哪了」。", color=PURPLE, icon="list-checks")
    return s


# ── 分區一第 2 章：植物怎麼用氨氮，為什麼過量會中毒 ────────────
def fig2_1_uptake():
    s = Svg(W, 820, "圖 2-1　同一件事的兩面：氨氮是養分，也是毒")
    sub(s, "植物吸銨比吸硝酸省能量，所以偏好它；但吸進來必須立刻同化掉，來不及就中毒。")

    s.box(40, 108, 440, 236, "", color=GREEN, fill=tint(GREEN, 0.96))
    s.icon("leaf", 66, 128, 24, GREEN, 2.1)
    s.text(102, 146, "當養分：便宜的氮", size=19, weight=700, color=GREEN)
    for i, ln in enumerate([
            "NH_4_^+^ 進細胞後直接被麩醯胺合成酶（GS）接走，",
            "變成麩醯胺酸，再由 GOGAT 分配給其他胺基酸。",
            "",
            "硝酸鹽要先還原成銨才能用，那一步要耗還原力。",
            "所以同樣一個氮，吸銨比吸硝酸便宜。"]):
        if ln:
            s.text(66, 186 + i * 28, ln, size=15)
    s.text(66, 326, "→ 這就是浮萍偏好氨氮的原因", size=15.5, weight=700, color=GREEN)

    s.box(520, 108, 440, 236, "", color=RED, fill=tint(RED, 0.96))
    s.icon("triangle-alert", 546, 128, 24, RED, 2.1)
    s.text(582, 146, "當毒物：三條路一起壞事", size=19, weight=700, color=RED)
    for i, ln in enumerate([
            "1. 游離氨 NH_3_ 不帶電，直接穿過細胞膜，",
            "　 在細胞內解離、把 pH 攪亂。",
            "2. 同化來不及，銨在組織裡累積。",
            "3. 細胞不斷把銨排出去又漏回來，白燒能量。"]):
        s.text(546, 186 + i * 28, ln, size=15)
    s.text(546, 326, "→ 所以門檻要用游離氨來訂（第 3 章）", size=15.5, weight=700, color=RED)

    s.text(40, 392, "一個例外值得記住", size=19, weight=700, color=PURPLE)
    s.box(40, 410, 920, 104, "", color=PURPLE, fill=tint(PURPLE, 0.95))
    s.icon("sparkles", 70, 440, 24, PURPLE, 2.1)
    for i, ln in enumerate([
            "粉綠狐尾藻會把吸進來的銨在體內轉成硝酸鹽再存起來——等於自己幫自己解毒。",
            "這是它能在銨超過 26 mM（約 364 mg N/L）的畜牧廢水裡活下來的機制之一。"]):
        s.text(110, 446 + i * 30, ln, size=15.5)

    s.text(40, 560, "誰先倒下：植物還是硝化菌？", size=19, weight=700, color=INK)
    bars = [("浮萍致死", 8.0, RED), ("粉綠狐尾藻可存活", 6.42, PURPLE),
            ("硝化菌受抑制", 14.75, BLUE), ("保守操作值", 0.5, GREEN)]
    x0, scale = 320, 36
    for i, (lab, v, color) in enumerate(sorted(bars, key=lambda b: b[1])):
        yy = 596 + i * 42
        s.text(300, yy + 6, lab, size=15, anchor="end")
        s.box(x0, yy - 12, max(v * scale, 20), 26, "", color=color, fill=color, r=5)
        s.text(x0 + v * scale + 12, yy + 6, f"{v:g} mg N/L", size=14.5, color=color, weight=700)
    s.text(40, 776, "游離氨 NH_3_-N（同一個尺度下比較，見第 3 章的換算）",
           size=14, color=MUTED)
    return s


# ── 分區一第 4 章：浮水植物圖鑑 ────────────────────────────────
def _species_cards(s, keys, y0, color_map, cols=2, w=448, gap=24):
    sp = {x["zh"]: x for x in L["species"]}
    x0 = 40
    y = y0
    col_y = [y0, y0]
    for i, k in enumerate(keys):
        d = sp[k]
        col = i % cols
        x = x0 + col * (w + gap)
        color = color_map(d)
        tag = {"native": "台灣原生", "exotic": "外來", "invasive": "外來入侵",
               "crop": "栽培作物", "mixed": "原生與外來都有", "n/a": "—"}[d["tw"]]
        items = [f'・{d["n_evidence"]}', f'・**好處**：{d["pros"]}', f'・**限制**：{d["cons"]}']
        h = s.card(x, col_y[col], w, items, title=f'{d["zh"]}（{tag}）',
                   sub=d["sp"], color=color, icon="leaf", size=14.5, lh=24,
                   foot=f'值得測的理由：{d["why"]}')
        col_y[col] += h + 20
    return max(col_y)


def fig4_1_floating():
    s = Svg(W, 1180, "圖 4-1　浮水植物：好撈、好收，但怕游離氨")
    sub(s, "浮在水面、根垂在水裡。優點是收割容易——而收割才等於移除。")
    cmap = lambda d: RED if d["tw"] == "invasive" else GREEN if d["tw"] == "native" else BLUE
    end = _species_cards(s, ["青萍", "紫萍", "無根萍", "滿江紅", "大萍（水芙蓉）", "布袋蓮"],
                         104, cmap)
    note(s, 40, end + 10, 920,
         "綠框＝台灣原生，紅框＝外來入侵種（要圍封、收割的植體不可隨意丟棄）。"
         "每一筆證據的強度都只到摘要層級，引用前請自己開全文核對。",
         color=GREY, icon="circle-alert")
    return s


def fig5_1_emergent():
    s = Svg(W, 1420, "圖 5-1　挺水、沉水與可食用：耐得住，但收割比較麻煩")
    sub(s, "根長在底泥或介質裡、莖葉伸出水面。耐受度普遍比浮萍高，植物吸收佔比則比較低。")
    cmap = lambda d: (RED if d["tw"] == "invasive" else GREEN if d["tw"] == "native"
                      else ORANGE if d["tw"] == "crop" else BLUE)
    end = _species_cards(s, ["粉綠狐尾藻", "香蒲", "美人蕉", "風車草／莎草屬",
                             "空心菜", "水芹菜", "茭白筍", "香根草"], 104, cmap)
    note(s, 40, end + 10, 920,
         "橘框＝可收成販賣的作物。注意：食用作物接觸廢水有衛生與法規問題，"
         "拿來處理廢水的那一批不要直接進食用鏈（第二分區第 5 章）。",
         color=ORANGE, icon="triangle-alert")
    return s


# ── 分區一第 6 章：篩選流程 ───────────────────────────────────
def fig6_1_screen():
    s = Svg(W, 880, "圖 6-1　一個水桶就能開始的篩選流程")
    sub(s, "照 OECD 221 的骨架改的：固定 pH、固定光溫、比生長率當終點、七天。")
    steps = [
        (BLUE, "flask-conical", "① 配五個濃度", "同一份水稀釋成 5 個濃度，外加一組不加氨氮的對照"),
        (PURPLE, "gauge", "② 把 pH 釘住", "用緩衝液或每天回調；pH 不固定，結果就沒辦法解讀"),
        (TEAL, "timer", "③ 養七天", "固定光照與水溫，每天記錄 pH、水溫、蒸發量"),
        (GREEN, "chart-line", "④ 算比生長率", "用葉狀體數或乾重；取對數斜率，不是只比最後的重量"),
    ]
    x = 40
    for color, ic, title, body in steps:
        s.box(x, 108, 218, 150, "", color=color, fill=tint(color, 0.96))
        s.icon(ic, x + 22, 126, 24, color, 2.1)
        s.text(x + 56, 144, title, size=17, weight=700, color=color)
        for i, ln in enumerate(wrap(body, 14, 174)):
            s.text(x + 22, 182 + i * 23, ln, size=14)
        if x < 700:
            s.arrow([(x + 222, 140), (x + 252, 140)], color=MUTED, width=2.4)
        x += 246

    s.text(40, 304, "四組對照，缺一組就會得到錯的結論", size=19, weight=700, color=INK)
    controls = [
        (GREEN, "植物 ＋ 水", "你想測的那一組"),
        (BLUE, "只有水，沒有植物", "沒有這組，就不知道「氨氮自己會掉多少」"),
        (ORANGE, "植物 ＋ 抑制硝化菌", "分開「植物吸收」與「根圈微生物」"),
        (PURPLE, "同一濃度、不同 pH", "證明門檻是游離氨而不是總氨氮"),
    ]
    x = 40
    for color, title, why in controls:
        s.box(x, 328, 218, 116, "", color=color, r=10)
        s.text(x + 109, 356, title, size=16, weight=700, anchor="middle")
        for i, ln in enumerate(wrap(why, 13.5, 186)):
            s.text(x + 109, 384 + i * 21, ln, size=13.5, color=MUTED, anchor="middle")
        x += 246

    s.text(40, 492, "一定要量的東西", size=19, weight=700, color=INK)
    cols = [
        (BLUE, "water", "水", ["氨氮（TAN）", "亞硝酸鹽、硝酸鹽", "總氮", "pH、水溫、溶氧"]),
        (GREEN, "leaf", "植體", ["鮮重、乾重", "含氮量（凱氏法或元素分析）", "葉片數或葉狀體數",
                                 "外觀：黃化、壞疽"]),
        (PURPLE, "settings", "條件", ["光強度與光週期", "蒸發補水量", "起始接種量",
                                      "每天的 pH 變化"]),
    ]
    x = 40
    for color, _ic, title, items in cols:
        s.card(x, 516, 298, [f"・{i}" for i in items], title=title, color=color,
               icon={"水": "droplet", "植體": "leaf", "條件": "settings"}[title],
               size=14.5, lh=25)
        x += 314
    note(s, 40, 732, 920,
         "為什麼要量蒸發補水量：浮萍池七天會蒸發掉可觀的水，不補水的話濃度自己會升上去，"
         "你會把「濃縮」誤判成「沒有去除」。這一條在 OECD 221 裡沒有，是實務上的坑。",
         color=ORANGE, icon="triangle-alert")
    return s


# ── 分區二第 1 章：人工濕地四型 ───────────────────────────────
def figb1_1_cwtypes():
    s = Svg(W, 900, "圖 1-1　人工濕地四型：差別在氧氣在哪裡")
    sub(s, "氮要走完「硝化→脫硝」需要先有氧再缺氧。單一型態提供不了兩種環境，所以才有混合式。")
    types = [
        (BLUE, "表面流（FWS）", "水在植物之間流過，看得到水面",
         ["氧氣：水面與植株附近有", "缺氧區：底泥", "像一座淺池塘"], "1.0–1.3（台灣實測）"),
        (TEAL, "水平流（HF）", "水在礫石床裡水平流動，看不到水",
         ["氧氣：很少", "缺氧區：整個床體", "脫硝強、硝化弱"], "1.13 ± 2.01"),
        (ORANGE, "垂直流（VF）", "水從上面間歇灑下，空氣跟著進去",
         ["氧氣：灑水間隔時補充", "缺氧區：少", "硝化強、脫硝弱"], "1.85 ± 3.66"),
        (GREEN, "混合式（VF＋HF 等）", "把上面兩種串起來",
         ["先硝化、再脫硝", "含表面流段的最高", "也最佔地"], "4.24 ± 5.12"),
    ]
    y = 104
    for color, title, what, bullets, rate in types:
        s.box(40, y, 920, 164, "", color=color, fill=tint(color, 0.96))
        s.text(70, y + 40, title, size=19, weight=700, color=color)
        s.text(70, y + 70, what, size=15, color=INK)
        for i, b in enumerate(bullets):
            s.text(70, y + 102 + i * 24, f"・{b}", size=14.5, color=MUTED)
        s.box(700, y + 44, 230, 78, rate, color=color, size=19,
              sub="總氮去除（g N/m²/d）", sub_size=13, fill="#ffffff")
        y += 176
    note(s, 40, y + 4, 920,
         "數字來自回顧文章的平均值，標準差比平均還大——代表實場變異極大，"
         "拿來估面積只能當數量級參考（第 2 章會算給你看）。", color=GREY, icon="circle-alert")
    return s


# ── 分區二第 3 章：高濃度廢水的四種策略 ───────────────────────
def figb3_1_highstrength():
    s = Svg(W, 880, "圖 3-1　沼液太濃，有四種方法可以降游離氨")
    d = T["acidification"]["derived"]
    sub(s, f'目標不是把總氨氮降到多低，而是把游離氨降到植物撐得住的範圍。')
    cards = [
        (BLUE, "droplet", "稀釋", [
            "・最直接，也最浪費水",
            f'・沼液 800 mg N/L 要稀到浮萍的 60 mg N/L，需要 13.3 倍',
            "・30 m³/d 的沼液要再加 370 m³/d 的水"],
         "適合：有大量回收水可用的場"),
        (ORANGE, "beaker", "酸化", [
            "・pH 8.2 → 6.5，游離氨降到約 1/12",
            f'・文獻：酸化後稀釋到 20%（TAN {d["acidified_tan"]:g}）浮萍仍正成長',
            "・要持續加酸，成本與安全要算進去"],
         "適合：想省水、接受加藥"),
        (PURPLE, "refresh-cw", "先硝化", [
            "・把氨氮變成硝酸鹽，毒性問題直接消失",
            "・但會消耗鹼度（7.14 g CaCO_3_/g N），pH 自己會掉",
            "・這就是第三分區的「硝化槽＋植體槽」"],
         "適合：濃度高又不想一直加水"),
        (TEAL, "leaf", "換耐受度高的植物", [
            "・粉綠狐尾藻可在約 364 mg N/L 存活",
            "・香蒲、美人蕉的門檻約 200 mg N/L",
            "・但耐得住不等於長得好、也不等於去除得快"],
         "適合：先用它開路，之後再接細緻處理"),
    ]
    y = 104
    for i, (color, ic, title, items, foot) in enumerate(cards):
        x = 40 + (i % 2) * 472
        yy = y + (i // 2) * 268
        s.card(x, yy, 448, items, title=title, color=color, icon=ic, size=14.5, lh=25,
               foot=foot, min_h=248)
    note(s, 40, 652, 920,
         "四種可以疊著用，順序會影響成本：先酸化再稀釋，需要的水量比先稀釋再酸化少很多。"
         "但酸化會把鹼度吃掉，後面若還要硝化就得補回來——兩章要一起看。",
         color=PURPLE, icon="lightbulb")
    s.box(40, 764, 920, 86, "", color=RED, fill=tint(RED, 0.95))
    s.icon("circle-x", 70, 792, 24, RED, 2.1)
    s.text(110, 798, "不要做的事：直接把高濃度沼液倒進植物池，想說「植物會慢慢吃掉」。",
           size=16, weight=700, color=RED)
    s.text(110, 826, "植物會先死，接著藻類接管，水質比進流還糟。", size=15)
    return s


# ── 分區二第 4 章：讀實場數據的陷阱 ───────────────────────────
def figb4_1_traps():
    s = Svg(W, 900, "圖 4-1　看到「氨氮去除 98%」時，要先問的五件事")
    sub(s, "同一座濕地，颱風前 98.9%、颱風後 35.1%。百分比本身幾乎沒有資訊量。")
    traps = [
        (RED, "circle-help", "① 百分比還是負荷？",
         "進流 5 mg/L 去除 90%，和進流 500 mg/L 去除 90%，是完全不同的兩件事。"
         "要看 g N/m²/d。"),
        (ORANGE, "thermometer-sun", "② 哪一季？",
         "低溫時植物停長、硝化菌也變慢。只報年平均會蓋掉冬天那三個月的難看數字。"),
        (BLUE, "waves", "③ 水有沒有真的走完全程？",
         "短流（走捷徑）是濕地最常見的失效模式。要做停留時間試驗（示蹤劑）才知道。"),
        (PURPLE, "leaf", "④ 有沒有無植物對照？",
         "空心菜浮床那篇：有植物 91.8%、沒植物 88.5%，差異不顯著。沒有對照就不知道植物貢獻多少。"),
        (BROWN, "layers", "⑤ 氮真的離開了嗎？",
         "氨氮降了、硝酸鹽升了，總氮沒變，就只是換形態。另外底泥會累積，老化的濕地會回吐氨氮。"),
    ]
    y = 104
    for color, ic, title, body in traps:
        lines = wrap(body, 15, 740)
        h = 44 + len(lines) * 26
        s.box(40, y, 920, h, "", color=color, fill=tint(color, 0.96))
        s.icon(ic, 68, y + 18, 24, color, 2.1)
        s.text(104, y + 36, title, size=17.5, weight=700, color=color)
        for i, ln in enumerate(lines):
            s.text(104, y + 64 + i * 26, ln, size=15)
        y += h + 16
    note(s, 40, y + 4, 920,
         "台灣的實際例子：同一群人工濕地，101 年度的氨氮去除率打鳥埤 97%、新海一期 81%、"
         "新海二期與三期各 44%。差這麼多，不會是「植物種類」一個原因就解釋得完。",
         color=GREY, icon="circle-alert")
    return s


# ── 分區二第 5 章：台灣 ──────────────────────────────────────
def figb5_1_taiwan():
    s = Svg(W, 980, "圖 5-1　在台灣做這件事，要先知道的三件事")
    sub(s, "法規、既有案例、外來種管理。三件都不是技術問題，但三件都會卡住計畫。")
    h1 = s.card(40, 104, 448, [
        "・放流水標準的**氨氮 10 mg/L** 只適用於排放到",
        "　自來水水質水量保護區內的情形",
        "・金屬表面處理、電鍍、製革等產業另有分階段",
        "　加嚴的氨氮標準",
        "・沼液沼渣要施灌農地，走水污法第 70 條之 1",
        "　的使用計畫審查",
        "・地下水氨氮若達監測標準或超過背景值 1.5 倍，",
        "　要立即停灌"],
        title="一、法規", color=BLUE, icon="shield", size=14.5, lh=26,
        foot="各產業適用的附表不同，正式申報前到全國法規資料庫確認現行版本")
    h2 = s.card(512, 104, 448, [
        "・大漢溪沿岸有一整群人工濕地（新海、浮洲、",
        "　打鳥埤、城林、鹿角溪）",
        "・新海一期處理 6,000 CMD，101 年度氨氮去除 81%",
        "・鹿角溪設計處理 12,000 CMD，官方寫的是",
        "　「削減 70% 以上」的設計目標",
        "・彰化有結合智慧監測的人工浮島試驗"],
        title="二、已經有人做了", color=TEAL, icon="globe", size=14.5, lh=26,
        foot="這些是可以去看、可以要資料的現場——不用從零開始說服人")

    y = 104 + max(h1, h2) + 24
    s.box(40, y, 920, 150, "", color=RED, fill=tint(RED, 0.96))
    s.icon("triangle-alert", 70, y + 24, 26, RED, 2.1)
    s.text(112, y + 44, "三、外來種：布袋蓮、大萍、粉綠狐尾藻都是外來種", size=19,
           weight=700, color=RED)
    for i, ln in enumerate([
            "試驗池要圍封，溢流口要有攔截網；收割的植體不可以丟進自然水體或溝渠。",
            "粉綠狐尾藻耐受度最好，但它也是逸出風險最高的一種——要用它就要把圍封寫進計畫書。",
            "本土的替代選項：香蒲、開卡蘆、風車草、水芹菜、茭白筍（耐受度資料較少，要自己建）。"]):
        s.text(112, y + 78 + i * 28, ln, size=15)
    y += 166
    y += note(s, 40, y, 920,
              "一個還沒有人認真做的題目：台灣原生水生植物的氨氮耐受度曲線。"
              "文獻裡的門檻幾乎都來自中國、歐洲與美國的物種與氣候，"
              "台灣的夏季水溫與 pH 條件不一樣。", color=PURPLE, icon="lightbulb") + 18
    s.box(40, y, 920, 150, "", color=GREEN, fill=tint(GREEN, 0.96))
    s.icon("list-checks", 70, y + 22, 24, GREEN, 2.1)
    s.text(110, y + 42, "如果你要在台灣開始，建議的順序", size=18, weight=700, color=GREEN)
    for i, ln in enumerate([
            "1. 先量自己的水：TAN、pH、水溫、總氮、鹼度（決定一切的四個數字）",
            "2. 用第一分區第 6 章的流程，篩 3–4 種植物（含一種本土、一種高耐受）",
            "3. 去看一座現有的人工濕地，問他們冬天怎麼辦、底泥多久清一次"]):
        s.text(110, y + 74 + i * 26, ln, size=15)
    return s


# ── 分區三第 1 章：為什麼先硝化 ───────────────────────────────
def figc1_1_why():
    s = Svg(W, 672, "圖 1-1　為什麼要在植體槽前面放一個硝化槽")
    sub(s, "三個理由，外加一個如果沒做完整會踩到的坑。")
    reasons = [
        (RED, "triangle-alert", "理由一：毒性消失",
         "氨氮變成硝酸鹽之後，游離氨的問題就不存在了。"
         "同樣一份水，硝化前要稀釋十幾倍，硝化後可以直接用。"),
        (BLUE, "gauge", "理由二：兩邊可以各自調 pH",
         "魚要 pH 7 左右，多數作物的養液要 5.5–6.5。放在同一個迴路只能各讓一步，"
         "分開就能各自最適化。"),
        (TEAL, "refresh-cw", "理由三：負荷變穩",
         "硝化槽當緩衝，投餵量的波動不會直接打到植物根上。"),
    ]
    y = 104
    for color, ic, title, body in reasons:
        lines = wrap(body, 15.5, 760)
        h = 44 + len(lines) * 27
        s.box(40, y, 920, h, "", color=color, fill=tint(color, 0.96))
        s.icon(ic, 68, y + 18, 24, color, 2.1)
        s.text(104, y + 36, title, size=18, weight=700, color=color)
        for i, ln in enumerate(lines):
            s.text(104, y + 66 + i * 27, ln, size=15.5)
        y += h + 18

    s.text(40, y + 26, "坑：硝化只做一半，比完全不做還糟", size=20, weight=700, color=RED)
    y += 46
    chain = [("NH_4_^+^", BLUE, "氨氮"), ("NO_2_^−^", RED, "亞硝酸鹽"),
             ("NO_3_^−^", GREEN, "硝酸鹽")]
    x = 150
    for i, (formula, color, name) in enumerate(chain):
        s.box(x, y, 180, 88, formula, color=color, size=22, sub=name, sub_size=14)
        if i < 2:
            s.arrow([(x + 184, y + 44), (x + 256, y + 44)], color=MUTED, width=2.6)
        x += 260
    s.text(500, y + 116, "卡在這裡 ＝ 植物矮化", size=15.5, weight=700, color=RED,
           anchor="middle")
    note(s, 40, y + 140, 920,
         "文獻實例：未處理的厭氧消化液拿去種萵苣，植株被部分硝化產生的亞硝酸毒害而矮化；"
         "同一份水做完整硝化之後，生長與標準養液沒有顯著差異。亞硝酸鹽是「中途產物」，"
         "它累積代表第二段（NOB）沒跟上——通常是溶氧或停留時間不夠。",
         color=RED, icon="circle-x")
    return s


# ── 分區三第 2 章：耦合 vs 解耦 ──────────────────────────────
def figc2_1_loops():
    s = Svg(W, 820, "圖 2-1　同一套設備，接法不同就是兩種系統")
    sub(s, "差別只在一條回水管。但那條管子決定了 pH 要聽誰的。")

    def unit(x, y, w, h, label, color, icon_name, subtext=""):
        s.box(x, y, w, h, "", color=color, fill=tint(color, 0.94))
        s.icon(icon_name, x + 16, y + 14, 22, color, 2.1)
        s.text(x + w / 2, y + 52, label, size=17, weight=700, color=INK, anchor="middle")
        if subtext:
            s.text(x + w / 2, y + 76, subtext, size=13.5, color=MUTED, anchor="middle")

    s.text(40, 112, "耦合式（單迴路）", size=19, weight=700, color=BLUE)
    yy = 134
    unit(40, yy, 230, 96, "養殖槽", BLUE, "waves", "魚要 pH 約 7")
    unit(320, yy, 230, 96, "硝化濾床", TEAL, "refresh-cw", "氨氮 → 硝酸鹽")
    unit(600, yy, 230, 96, "植栽槽", GREEN, "leaf", "作物要 pH 5.5–6.5")
    s.arrow([(274, yy + 48), (316, yy + 48)], color=MUTED, width=2.6)
    s.arrow([(554, yy + 48), (596, yy + 48)], color=MUTED, width=2.6)
    # 回水：繞下方，直角折線
    s.arrow([(830, yy + 48), (880, yy + 48), (880, yy + 132), (155, yy + 132),
             (155, yy + 100)], color=ORANGE, width=2.6)
    s.text(500, yy + 152, "水回到魚那邊 → pH 只能取一個折衷值", size=15, weight=700,
           color=ORANGE, anchor="middle")

    s.text(40, 374, "解耦式（雙迴路）", size=19, weight=700, color=PURPLE)
    yy = 396
    unit(40, yy, 230, 96, "養殖槽", BLUE, "waves", "自己的迴路，pH 顧魚")
    unit(320, yy, 230, 96, "硝化／礦化槽", TEAL, "refresh-cw", "可以再加厭氧段")
    unit(600, yy, 230, 96, "植栽槽", GREEN, "leaf", "自己的迴路，pH 顧作物")
    s.arrow([(274, yy + 48), (316, yy + 48)], color=MUTED, width=2.6)
    s.arrow([(554, yy + 48), (596, yy + 48)], color=MUTED, width=2.6,
            label="單向", label_dy=-14, size=13.5)
    s.arrow([(380, yy + 100), (380, yy + 146), (155, yy + 146), (155, yy + 102)],
            color=BLUE, width=2.4)
    s.arrow([(880, yy + 100), (880, yy + 146), (700, yy + 146), (700, yy + 102)],
            color=GREEN, width=2.4)
    s.text(268, yy + 174, "養殖自己的循環（水回到魚）", size=14, color=BLUE, anchor="middle")
    s.text(790, yy + 174, "植栽自己的循環（水不回魚）", size=14, color=GREEN, anchor="middle")

    s.card(40, 604, 448, [
        "・兩邊各自最適化，作物那邊可以補微量元素",
        "・水只往一個方向走，植栽槽的藥不會流回魚池",
        "・文獻中試：果實產量高約 36%，魚的產量相當"],
        title="解耦式的好處", color=GREEN, icon="circle-check", size=14.5, lh=25)
    s.card(512, 604, 448, [
        "・設備與管路變多，要兩套泵與兩個水位控制",
        "・植栽槽的水最後還是要處理或排掉",
        "・小規模時複雜度可能不划算"],
        title="代價", color=ORANGE, icon="circle-alert", size=14.5, lh=25)
    return s


# ── 分區三第 4 章：誰做過 ────────────────────────────────────
def figc4_1_cases():
    s = Svg(W, 940, "圖 4-1　「硝化槽＋植體槽」這件事，已經有人做過哪些版本")
    sub(s, "同一個骨架，餵給它的水不同，就變成四條不同的應用線。")
    lines = [
        (BLUE, "waves", "魚菜共生", "養殖排水",
         ["最成熟，有商業規模的設計準則", "投餵率 60–100 g 飼料/m²/d 是通用的起點",
          "解耦式的果實產量較高"]),
        (BROWN, "flask-conical", "沼液水耕", "厭氧消化液",
         ["硝化後萵苣與標準養液沒有顯著差異", "未硝化會被亞硝酸毒害",
          "番茄長 6 個月需要額外補鎂鈣硫磷與微量元素"]),
        (PURPLE, "droplet", "尿液回收", "分離尿液",
         ["硝化先把氮穩住，再蒸餾濃縮", "氮損失低於 3%",
          "有研究用硝化尿液取代 NFT 番茄 100% 的氮而產量不減"]),
        (TEAL, "beaker", "酸性硝化", "沼液（pH 約 3）",
         ["在酸性下硝化，順便溶出超過 70% 的磷", "萵苣鮮重與商用養液相當",
          "解決了沼液「磷卡在沉澱裡」的老問題"]),
    ]
    y = 104
    for color, ic, title, feed, bullets in lines:
        s.box(40, y, 920, 172, "", color=color, fill=tint(color, 0.96))
        s.icon(ic, 70, y + 26, 26, color, 2.1)
        s.text(112, y + 46, title, size=19, weight=700, color=color)
        ptext = f"進料：{feed}"
        pw = _text_w(ptext, 13) + 16
        s.pill(112 + _text_w(title, 19) + 28 + pw / 2, y + 42, ptext, color, size=13)
        for i, b in enumerate(bullets):
            s.text(112, y + 84 + i * 28, f"・{b}", size=15)
        y += 184
    note(s, 40, y + 4, 920,
         "共同點：硝化那一段是「把氮變成植物吃得安全的形態」，不是「把氮去掉」。"
         "氮最後是被植物收走的——所以植體怎麼處理，決定了這套系統算不算真的處理了廢水。",
         color=PURPLE, icon="lightbulb")
    return s


# ── 分區三第 5 章：延伸應用與決策樹 ──────────────────────────
def figc5_1_apps():
    s = Svg(W, 1000, "圖 5-1　除了「把氮去掉」，這些植體還能做什麼")
    sub(s, "把氮當成要丟的東西，和把氮當成要回收的東西，會做出完全不同的系統。")
    apps = [
        (GREEN, "package", "飼料蛋白", "浮萍乾重 25–45% 粗蛋白；實場豬糞塘量到 68 t 乾重/ha/年、蛋白 35%"),
        (TEAL, "leaf", "綠肥與生物肥", "滿江紅固氮，稻田有幾百年使用史；收割的植體可堆肥回田"),
        (BROWN, "zap", "厭氧消化產沼氣", "布袋蓮 BMP 約 143–193 mL CH_4_/g VS；正好接回生質能那條線"),
        (ORANGE, "beaker", "澱粉與乙醇", "浮萍在缺氮時把澱粉堆到乾重六成以上，可做燃料乙醇"),
        (PURPLE, "atom", "氮肥回收", "尿液／沼液硝化後直接當水耕養液，氮損失可低於 3%"),
        (BLUE, "bot", "發電（CW-MFC）", "濕地加電極同時處理水與發電；目前電壓只有毫伏級，離實用還遠"),
        (RED, "circle-alert", "人類食品", "無根萍（Mankai）已送審，但 EFSA 對錳含量有安全疑慮，尚未過關"),
        (GREY, "eye", "生物指標", "浮萍對游離氨敏感，可當便宜的早期警示——看它什麼時候開始黃化"),
        (BROWN, "waves", "景觀與滯洪", "浮島可放進現有池塘、滯洪池，不用另外挖地"),
    ]
    y = 104
    for i, (color, ic, title, body) in enumerate(apps):
        x = 40 + (i % 3) * 312
        yy = y + (i // 3) * 196
        s.box(x, yy, 296, 180, "", color=color, fill=tint(color, 0.96))
        s.icon(ic, x + 20, yy + 18, 24, color, 2.1)
        s.text(x + 54, yy + 38, title, size=17, weight=700, color=color)
        for j, ln in enumerate(wrap(body, 14.5, 254)):
            s.text(x + 20, yy + 78 + j * 25, ln, size=14.5)
    note(s, 40, 710, 920,
         "這九個不是平行的選項。先問一件事：你的目標是「讓放流水達標」還是「把氮變成有價值的東西」。"
         "前者要的是速率與穩定，後者要的是植體的品質與可販售性——兩者的設計會往不同方向走。",
         color=PURPLE, icon="lightbulb")
    s.box(40, 820, 920, 150, "", color=ORANGE, fill=tint(ORANGE, 0.96))
    s.icon("triangle-alert", 70, 842, 24, ORANGE, 2.1)
    s.text(110, 862, "共同的限制：收割的植體含水量很高", size=18, weight=700, color=ORANGE)
    for i, ln in enumerate([
            "浮萍與布袋蓮鮮重的九成以上是水。乾燥要能量，不乾燥就不能運、不能存。",
            "所以上面每一條應用，真正的瓶頸幾乎都不是「長得夠不夠快」，而是「脫水與運輸」。",
            "就地利用（餵旁邊的魚、堆在旁邊的田、進旁邊的消化槽）比運出去划算得多。"]):
        s.text(110, 894 + i * 26, ln, size=15)
    return s


def figc5_2_decision():
    s = Svg(W, 900, "圖 5-2　你的水該走哪一條路")
    sub(s, "四個問題，決定要不要用植物、用哪一種、要不要先硝化。")
    q = [
        (BLUE, "① 你的總氨氮多少？（配上 pH）",
         [("< 60 mg N/L", "植物可以直接上", GREEN),
          ("60–200", "選耐受度高的，或先酸化", ORANGE),
          ("> 200", "先稀釋／酸化／硝化，不要硬種", RED)]),
        (TEAL, "② 你要的是達標，還是回收？",
         [("達標", "人工濕地或混合式，重視速率與穩定", BLUE),
          ("回收", "浮萍、滿江紅，重視植體品質", GREEN),
          ("兩個都要", "前段濕地、後段浮萍收成", PURPLE)]),
        (PURPLE, "③ 有多少地？",
         [("充足", "表面流濕地最省心", GREEN),
          ("有限", "垂直流或浮島，或往硝化槽耦合走", ORANGE),
          ("幾乎沒有", "植物方案不適合，回去看生物處理", RED)]),
        (ORANGE, "④ 冬天怎麼辦？",
         [("不能停", "挺水植物＋硝化槽，不要只靠浮萍", BLUE),
          ("可以降載", "浮萍塘，冬季減量運轉", GREEN),
          ("還沒想過", "先去量一次一月的水溫", RED)]),
    ]
    y = 104
    for color, title, opts in q:
        s.text(40, y + 24, title, size=18.5, weight=700, color=color)
        x = 40
        for lab, action, c in opts:
            s.box(x, y + 40, 296, 104, "", color=c, fill="#ffffff")
            s.text(x + 148, y + 72, lab, size=17, weight=700, color=c, anchor="middle")
            for j, ln in enumerate(wrap(action, 14, 256)):
                s.text(x + 148, y + 102 + j * 22, ln, size=14, color=MUTED, anchor="middle")
            x += 312
        y += 176
    note(s, 40, y + 4, 920,
         "這張圖是我們依前面各章整理出來的判斷順序，不是哪一篇文獻的建議——"
         "沒有一篇文獻同時涵蓋這四個問題。拿去用之前，先確認你的情境和表裡的假設一樣。",
         color=PURPLE, icon="circle-alert")
    return s


FIGS = {
    "fig0-1-roadmap": fig0_1_roadmap,
    "fig1-2-fates": fig1_1_fates,
    "fig2-1-uptake": fig2_1_uptake,
    "fig4-1-floating": fig4_1_floating,
    "fig5-1-emergent": fig5_1_emergent,
    "fig6-1-screen": fig6_1_screen,
    "figb1-1-cwtypes": figb1_1_cwtypes,
    "figb3-1-highstrength": figb3_1_highstrength,
    "figb4-1-traps": figb4_1_traps,
    "figb5-1-taiwan": figb5_1_taiwan,
    "figc1-1-why": figc1_1_why,
    "figc2-1-loops": figc2_1_loops,
    "figc4-1-cases": figc4_1_cases,
    "figc5-1-apps": figc5_1_apps,
    "figc5-2-decision": figc5_2_decision,
}

if __name__ == "__main__":
    want = sys.argv[1:] or list(FIGS)
    render({k: FIGS[k]() for k in want if k in FIGS}, OUT)
