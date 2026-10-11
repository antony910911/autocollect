"""AIoT 教材的示意圖。執行：python lessons/aiot/figures/src/diagrams.py [圖名 ...]"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_tools"))
from svgkit import INK, MUTED, Svg, render, tint  # noqa: E402

OUT = Path(__file__).resolve().parent.parent
# 這門教材的語意色：感測、連網、資料、AI、執行、人
SENSE, NET, DATA, AI, ACT, HUMAN, RISK = "#2f6fb3", "#6b7280", "#7b4bb3", "#d47c18", "#2f9e6e", "#8a6d3b", "#c23b3b"


def fig0_roadmap():
    s = Svg(1200, 470, "學習地圖：沼氣與廢水處理的 AIoT")
    rows = [
        ("觀念", SENSE, [("1", "AIoT 是什麼？\n和機器學習的異同"), ("2", "沼氣廠要量什麼？\n為什麼難控制")]),
        ("判斷", DATA, [("3", "到什麼程度\n才叫 AIoT"), ("4", "國內外案例\n與業界共識"), ("5", "機器學習在\n厭氧消化的應用")]),
        ("行動", ACT, [("6", "怎麼建置：\n架構、步驟、資安"), ("7", "沼氣中心該做到\n什麼地步"), ("8", "業界還沒做的\n創新思路")]),
    ]
    y = 80
    for name, col, items in rows:
        s.box(24, y, 130, 96, name, color=col, size=21)
        x = 190
        for i, (n, label) in enumerate(items):
            s.box(x, y, 300, 96, f"第 {n} 章", color=col, size=15, sub=label, sub_size=17, fill="#ffffff")
            if i < len(items) - 1:
                s.arrow([(x + 302, y + 48), (x + 333, y + 48)], color=col)
            x += 335
        y += 120
    s.text(24, 456, "先讀 1–3 建立共通語言；評估廠商提案前讀 4、5；寫計畫書或規劃建置讀 6–8。", size=15, color=MUTED)
    return s


def fig1_loop():
    s = Svg(1200, 700, "圖 1-1　AIoT 是一個「感測 → 判斷 → 行動」的閉迴路")
    cx, cy, r = 600, 390, 230
    nodes = [
        ("① 感測", SENSE, "感測器、儀表、攝影機\npH、溫度、氣體流量、CH₄、H₂S"),
        ("② 連網", NET, "PLC／SCADA、閘道器\n有線、4G/5G、LoRa"),
        ("③ 資料", DATA, "時序資料庫、實驗室數據\n清理、對齊時間、標記"),
        ("④ 智慧（AI）", AI, "預測、軟感測、異常偵測\n最佳化建議"),
        ("⑤ 行動", ACT, "自動調整設定值\n或通知人員決策"),
    ]
    import math
    pos = []
    for i, _ in enumerate(nodes):
        a = -math.pi / 2 + i * 2 * math.pi / len(nodes)
        pos.append((cx + r * 1.55 * math.cos(a), cy + r * math.sin(a)))
    for i, ((head, col, sub), (x, y)) in enumerate(zip(nodes, pos)):
        s.box(x - 160, y - 55, 320, 110, head, color=col, size=20, sub=sub, sub_size=14)
    for i in range(len(nodes)):
        (x1, y1), (x2, y2) = pos[i], pos[(i + 1) % len(nodes)]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        k = 0.78
        sx, sy = x1 + (x2 - x1) * 0.28, y1 + (y2 - y1) * 0.28
        ex, ey = x1 + (x2 - x1) * 0.72, y1 + (y2 - y1) * 0.72
        cxx, cyy = cx + (mx - cx) * k, cy + (my - cy) * k
        s.arrow([(sx, sy), (cxx, cyy), (ex, ey)], color=MUTED, curve=True, width=2)
    s.box(cx - 150, cy - 50, 300, 100, "製程本身", color=HUMAN, size=20, sub="厭氧消化槽、曝氣池\n（被量測、也被控制）", sub_size=14)
    s.text(24, 680, "IoT 只做到 ①②③（看得到）；機器學習是 ④ 裡的一種方法；AIoT 要把迴路接回 ⑤，讓判斷真的影響現場。", size=15, color=MUTED)
    return s


def fig1_venn():
    s = Svg(1200, 600, "圖 1-2　常見名詞的關係")
    s.raw(f'<circle cx="400" cy="320" r="220" fill="{tint(AI, .85)}" stroke="{AI}" stroke-width="2" fill-opacity=".8"/>')
    s.raw(f'<circle cx="400" cy="380" r="140" fill="{tint(AI, .7)}" stroke="{AI}" stroke-width="2" fill-opacity=".8"/>')
    s.raw(f'<circle cx="400" cy="430" r="70" fill="{tint(AI, .5)}" stroke="{AI}" stroke-width="2" fill-opacity=".8"/>')
    s.raw(f'<circle cx="760" cy="320" r="220" fill="{tint(SENSE, .85)}" stroke="{SENSE}" stroke-width="2" fill-opacity=".6"/>')
    s.text(300, 150, "人工智慧 AI", size=20, color=AI, weight=700, anchor="middle")
    s.text(330, 270, "機器學習 ML", size=18, color=AI, weight=700, anchor="middle")
    s.text(400, 438, "深度學習", size=16, color=AI, weight=700, anchor="middle")
    s.text(860, 150, "物聯網 IoT", size=20, color=SENSE, weight=700, anchor="middle")
    s.text(870, 330, "感測、連網、\n雲端儲存、儀表板", size=15, color=SENSE, anchor="middle-v")
    s.text(580, 300, "AIoT", size=26, color=INK, weight=700, anchor="middle")
    s.text(580, 336, "AI 跑在物聯網\n資料上並回饋現場", size=14, color=INK, anchor="middle-v")
    s.box(960, 420, 220, 70, "SCADA／PLC", color=NET, size=16, sub="既有的自動控制骨幹", sub_size=12)
    s.box(960, 500, 220, 70, "數位孿生", color=DATA, size=16, sub="模型＋即時資料的虛擬廠", sub_size=12)
    s.text(24, 586, "AI ⊃ ML ⊃ 深度學習。AIoT 是「應用架構」不是「演算法」；它常建立在既有 SCADA 上，數位孿生是其中一種進階形式。", size=14,
           color=MUTED)
    return s


def fig2_plant():
    s = Svg(1200, 560, "圖 2-1　沼氣廠的流程與量測點（藍點＝建議線上量測）")
    y = 260
    units = [
        (30, "進料／前處理", "破碎、除雜、\n調配、加熱"),
        (270, "厭氧消化槽", "水解→酸化→\n乙酸化→產甲烷"),
        (530, "儲氣與脫硫", "生物或化學脫硫\n除濕"),
        (770, "利用", "發電機（CHP）\n鍋爐、純化"),
        (1010, "消化液", "固液分離、\n沼液沼渣利用"),
    ]
    for i, (x, head, sub) in enumerate(units):
        col = [HUMAN, ACT, DATA, AI, SENSE][i]
        s.box(x, y, 170, 120, head, color=col, size=18, sub=sub, sub_size=14)
        if i < len(units) - 1:
            s.arrow([(x + 172, y + 60), (units[i + 1][0] - 2, y + 60)], color=MUTED)
    pts = [
        (115, "進料量、TS/VS\n（重量計、含水率）"),
        (355, "溫度、pH、液位、\n攪拌電流、壓力"),
        (355, "VFA、鹼度、FOS/TAC\n氨氮（多半離線）"),
        (615, "沼氣流量、CH₄、\nCO₂、H₂S、O₂"),
        (855, "發電量、引擎狀態\n排氣"),
        (1095, "消化液 pH、氨氮、\nCOD、殘餘產氣"),
    ]
    used = {}
    for x, label in pts:
        k = used.get(x, 0)
        used[x] = k + 1
        yy = 150 - k * 0 if k == 0 else 450
        s.raw(f'<circle cx="{x}" cy="{y + (0 if k == 0 else 120)}" r="9" fill="{SENSE}"/>')
        if k == 0:
            s.line(x, y, x, 215, color=SENSE)
            s.text(x, 180, label, size=13, color=SENSE, anchor="middle-v")
        else:
            s.line(x, y + 120, x, 410, color=SENSE)
            s.text(x, 440, label, size=13, color=RISK, anchor="middle-v")
    s.text(24, 500, "紅字：最能提早警告「消化槽快酸化」的指標，偏偏最難線上量測 → 這正是軟感測與 AI 最有價值的地方（第 5 章）。", size=15, color=RISK)
    s.text(24, 532, "依 Drosg (2013) IEA Bioenergy Task 37 與 Jimenez et al. (2015) 整理。", size=13, color=MUTED)
    return s


def fig3_levels():
    s = Svg(1200, 700, "圖 3-1　AIoT 成熟度階梯（本教材整理）")
    levels = [
        ("L0", "人工", "紙本紀錄、人工巡檢\n手動操作", HUMAN),
        ("L1", "自動化", "PLC／SCADA 控制\n固定設定值、警報", NET),
        ("L2", "連網可視化", "數據集中、雲端儀表板\n遠端監看（多數 IoT 停在這）", SENSE),
        ("L3", "分析預測", "趨勢分析、異常偵測\n軟感測、產氣預測", DATA),
        ("L4", "建議與閉迴路", "AI 給設定值建議，\n經人確認或限範圍自動執行", AI),
        ("L5", "自主運轉", "系統自行決策與調整\n人只監督例外", ACT),
    ]
    base_y = 620
    for i, (lv, name, desc, col) in enumerate(levels):
        x = 40 + i * 190
        h = 160 + i * 70
        s.box(x, base_y - h, 175, h, "", color=col, fill=tint(col, .82 - i * 0.04))
        s.text(x + 87, base_y - h + 36, lv, size=26, color=col, weight=700, anchor="middle")
        s.text(x + 87, base_y - h + 66, name, size=18, weight=700, anchor="middle")
        s.text(x + 87, base_y - h + 100, desc, size=13, color=INK, anchor="middle")
    lx = 40 + 3 * 190 - 8
    s.line(lx, 125, lx, base_y + 10, color=RISK, width=2, dash=True)
    s.text(lx, 110, "← IoT　｜　AIoT →", size=18, color=RISK, weight=700, anchor="middle")
    s.text(lx + 12, 150, "有「AI 判斷」，", size=14, color=RISK)
    s.text(lx + 12, 170, "而且被用來做決定，", size=14, color=RISK)
    s.text(lx + 12, 190, "才開始算 AIoT", size=14, color=RISK)
    s.text(24, 660, "參考 Yokogawa IA2IA 自主化等級與 IWA Digital Water 採用曲線，改寫成水處理／沼氣廠可對照的版本。", size=13, color=MUTED)
    s.text(24, 684, "業界共識：多數場站目標是穩定的 L3、局部 L4；L5 目前只在少數單元或研究中出現。", size=13, color=MUTED)
    return s


def fig5_pipeline():
    s = Svg(1200, 560, "圖 5-1　機器學習專案在沼氣廠的實際流程")
    steps = [
        ("定義問題", HUMAN, "要預測什麼？\n提早多久？\n誤報代價？"),
        ("資料盤點", SENSE, "感測資料＋實驗室\n＋進料紀錄\n至少涵蓋一年季節"),
        ("清理對齊", DATA, "時間戳對齊、\n補值、去除異常、\n標記事件"),
        ("特徵與模型", AI, "滯後特徵、移動平均\n從簡單模型開始\n（線性、樹模型）"),
        ("驗證", AI, "依時間切分\n不可隨機打散\n與現行做法比較"),
        ("上線與維護", ACT, "儀表板或建議\n監控漂移\n定期重新訓練"),
    ]
    for i, (head, col, body) in enumerate(steps):
        x = 24 + i * 196
        s.box(x, 80, 180, 60, head, color=col, size=18)
        s.box(x, 150, 180, 150, "", color=col, fill="#ffffff")
        s.text(x + 90, 225, body, size=14, anchor="middle-v")
        if i < len(steps) - 1:
            s.arrow([(x + 182, 110), (x + 194, 110)], color=MUTED, width=2)
    s.arrow([(1100, 302), (1100, 360), (114, 360), (114, 302)], color=MUTED, width=2, dash=True)
    s.text(600, 384, "模型上線後不是結束：原料、季節、菌群改變都會讓模型變不準（概念漂移），要持續回到前面的步驟", size=14, color=MUTED,
           anchor="middle")
    tasks = [("預測", "產氣量、甲烷濃度\n發電量"), ("軟感測", "用便宜的線上訊號\n推估 VFA、FOS/TAC"),
             ("異常偵測", "提早發現酸化、\n起泡、設備故障"), ("最佳化", "進料配方與速率\n攪拌、加熱排程")]
    for i, (h, b) in enumerate(tasks):
        x = 24 + i * 296
        s.box(x, 420, 280, 110, h, color=AI, size=18, sub=b, sub_size=14, fill=tint(AI, .9))
    return s


def fig6_arch():
    s = Svg(1200, 790, "圖 6-1　建議架構與資安分區（由下往上）")
    layers = [
        ("第 0–1 層：現場", SENSE, "感測器、分析儀、閥門、泵浦、變頻器、PLC", 600),
        ("第 2 層：控制", NET, "SCADA／HMI、控制迴路（安全連鎖留在這層，不交給 AI）", 500),
        ("工控 DMZ", RISK, "單向傳輸或防火牆、資料閘道；遠端維護走跳板機＋多因素驗證", 400),
        ("第 3 層：營運資料", DATA, "時序資料庫（historian）、實驗室資料（LIMS）、維護紀錄", 300),
        ("第 4 層：分析與 AI", AI, "邊緣運算或雲端；模型、儀表板、警示；只輸出「建議設定值」", 200),
        ("人與決策", HUMAN, "操作員確認／否決，所有變更留紀錄（稽核軌跡）", 100),
    ]
    for name, col, desc, y in layers:
        s.box(40, y, 300, 80, name, color=col, size=18)
        s.box(360, y, 800, 80, "", color=col, fill=tint(col, .9))
        s.text(380, y + 46, desc, size=16)
    s.arrow([(1180, 670), (1180, 110)], color=MUTED, width=3)
    s.text(1170, 88, "資料往上 ↑", size=14, color=MUTED, anchor="end")
    s.arrow([(20, 140), (20, 560)], color=AI, width=3, dash=True)
    s.text(30, 730, "建議值往下要經過人或限範圍規則；緊急停機與安全連鎖永遠在 PLC 層獨立運作。依 IEC 62443 分區概念與 CISA AA21-042A 事件教訓整理。",
           size=13, color=MUTED)
    s.text(30, 756, "左側虛線：AI 建議回到現場的路徑。", size=13, color=AI)
    return s


def fig6_roadmap():
    s = Svg(1200, 520, "圖 6-2　建置路線圖：每階段都要有可驗收的成果")
    phases = [
        ("階段 0\n盤點（1–2 月）", HUMAN, "列出儀表與資料\n找出痛點與 KPI\n資安現況檢查"),
        ("階段 1\n看得到（3–6 月）", SENSE, "補齊關鍵儀表\n集中資料、儀表板\n實驗室數據數位化"),
        ("階段 2\n看得懂（6–12 月）", DATA, "基準線與警示規則\n第一個預測模型\n與操作員一起驗證"),
        ("階段 3\n會建議（1–2 年）", AI, "設定值建議\n限範圍閉迴路\n效益量化"),
        ("階段 4\n持續改善", ACT, "模型維護與再訓練\n擴展到其他單元\n跨場域比較"),
    ]
    for i, (head, col, body) in enumerate(phases):
        x = 24 + i * 236
        s.box(x, 80, 218, 90, head, color=col, size=17)
        s.box(x, 180, 218, 150, "", color=col, fill="#ffffff")
        s.text(x + 109, 255, body, size=15, anchor="middle-v")
        if i < len(phases) - 1:
            s.arrow([(x + 220, 125), (x + 234, 125)], color=MUTED)
    s.box(24, 370, 1152, 120, "", color=RISK, fill=tint(RISK, .93))
    s.text(48, 404, "常見失敗原因（各案例與綜述反覆提到）", size=18, weight=700, color=RISK)
    s.text(48, 436, "• 先買 AI 平台、後補感測器 → 資料不夠，模型做不出來　• 感測器沒有維護校正 → 垃圾進、垃圾出", size=15)
    s.text(48, 466, "• 操作員沒參與 → 建議沒人用　• 遠端連線沒做資安 → 製造新風險　• 沒有基準線 → 無法證明節省多少", size=15)
    return s


def fig7_types():
    s = Svg(1200, 720, "圖 7-1　三種沼氣場站的特性與建議 AIoT 目標")
    cols = [
        ("濕式消化\n（污泥、廚餘漿、工業廢水）", SENSE,
         "TS 約 < 15%，完全混合\n可線上量 pH、溫度、液位\n進料可泵送、可細調", "建議目標：L3 全面、L4 局部",
         "VFA／FOS-TAC 軟感測\n進料速率建議\n起泡與攪拌異常警示"),
        ("乾式消化\n（廚餘、園藝、固體有機物）", HUMAN,
         "TS 約 20–40%，柱塞流或批次\n槽內不均勻、難取樣\n進料靠鏟裝或螺旋輸送", "建議目標：L2–L3 為主",
         "進料紀錄數位化\n產氣曲線預測\n滲出液回灌排程"),
        ("養豬場\n（三段式＋沼氣）", ACT,
         "規模小、人力少、預算有限\n水量隨清洗與季節變動\n脫硫與發電機最常出問題", "建議目標：L2 穩定、L3 重點",
         "H₂S 與脫硫警示\n發電機遠端監控\n沼液沼渣施灌紀錄"),
    ]
    for i, (head, col, feat, goal, focus) in enumerate(cols):
        x = 30 + i * 392
        s.box(x, 70, 360, 90, head, color=col, size=18)
        s.box(x, 172, 360, 190, "", color=col, fill="#ffffff")
        s.text(x + 180, 268, feat, size=15, anchor="middle-v")
        s.box(x, 374, 360, 56, goal, color=col, size=17, fill=tint(col, .8))
        s.box(x, 442, 360, 150, "", color=col, fill=tint(col, .93))
        s.text(x + 20, 472, "優先做：", size=15, weight=700, color=col)
        s.text(x + 180, 532, focus, size=15, anchor="middle-v")
    s.text(24, 640, "TS 範圍為一般分類方式，實際依技術供應商而定。目標等級為本教材依案例與綜述整理的建議，不是法規要求。", size=13, color=MUTED)
    s.text(24, 666, "共同底線：關鍵儀表會校正、數據有時間戳並集中保存、警報有人負責、遠端連線有資安防護。", size=15, color=RISK, weight=700)
    return s


FIGS = {
    "fig0-1-roadmap": fig0_roadmap,
    "fig1-1-aiot-loop": fig1_loop,
    "fig1-2-terms": fig1_venn,
    "fig2-1-plant-sensors": fig2_plant,
    "fig3-1-maturity": fig3_levels,
    "fig5-1-ml-pipeline": fig5_pipeline,
    "fig6-1-architecture": fig6_arch,
    "fig6-2-roadmap": fig6_roadmap,
    "fig7-1-plant-types": fig7_types,
}

if __name__ == "__main__":
    only = set(sys.argv[1:])
    render({k: f() for k, f in FIGS.items() if not only or k in only}, OUT)
