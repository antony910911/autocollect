"""教材的示意圖（流程、機制）。執行：python lessons/ammonia/figures/src/diagrams.py"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from svgkit import C, INK, MUTED, Svg, render, tint  # noqa: E402

OUT = Path(__file__).resolve().parent.parent


def fig0_roadmap():
    s = Svg(1200, 520, "學習地圖：從化學到微生物，再到實務")
    groups = [
        ("基礎", C["nh4"], [("1", "氨氮是什麼？\npH 與 NH_3_/NH_4_^+^"), ("2", "硝化、脫硝\n與新型脫氮"), ("3", "怎麼量？\n正式檢測方法")]),
        ("微生物", C["amx"], [("4", "相關微生物\n與功能基因"), ("5", "活性測試\n與菌群分析"), ("6", "qPCR 定量\n設計與驗證")]),
        ("生物選項", C["n2"], [("7", "酵母菌\n能降解氨氮嗎？"), ("8", "水芙蓉與\n水生植物")]),
        ("實務", C["no3"], [("9", "你還應該知道的\n實驗設計與法規")]),
    ]
    y = 90
    for name, color, items in groups:
        s.box(24, y, 130, 86, name, color=color, size=20)
        x = 190
        for i, (num, label) in enumerate(items):
            s.box(x, y, 290, 86, f"第 {num} 章", color=color, size=15, sub=label, sub_size=17, weight=700,
                  fill="#ffffff")
            if i < len(items) - 1:
                s.arrow([(x + 292, y + 43), (x + 330, y + 43)], color=color)
            x += 335
        y += 104
    s.text(24, 506, "建議閱讀順序：1 → 2 → 3 先建立共通語言；做實驗前讀 5、6；評估酵母或植物方案前讀 7、8；寫計畫書前讀 9。",
           size=15, color=MUTED)
    return s


def fig1_cycle():
    s = Svg(1200, 800, "圖 1-1　氮的氧化數階梯與主要轉化途徑")
    ys = {-3: 700, -2: 620, -1: 540, 0: 460, 1: 380, 2: 300, 3: 220, 5: 100}
    s.line(96, 80, 96, 730, color=MUTED, width=1.5)
    for k, y in ys.items():
        s.line(90, y, 102, y, color=MUTED)
        s.text(80, y + 5, f"{k:+d}" if k else "0", size=15, color=MUTED, anchor="end")
    s.text(40, 420, "氮\n的\n氧\n化\n數", size=15, color=MUTED, anchor="middle-v")
    bw, bh = 150, 52

    def node(key, x, k, label, color):
        y = ys[k]
        s.box(x - bw / 2, y - bh / 2, bw, bh, label, color=color, size=18)
        return x, y

    org = node("org", 190, -3, "有機氮\nR–NH_2_", C["org"])
    nh4 = node("nh4", 450, -3, "NH_4_^+^ ⇌ NH_3_", C["nh4"])
    nh2oh = node("nh2oh", 450, -1, "NH_2_OH 羥胺", C["nh4"])
    no2 = node("no2", 640, 3, "NO_2_^−^ 亞硝酸鹽", C["no2"])
    no3 = node("no3", 640, 5, "NO_3_^−^ 硝酸鹽", C["no3"])
    no = node("no", 890, 2, "NO", C["gas"])
    n2o = node("n2o", 890, 1, "N_2_O（溫室氣體）", C["gas"])
    n2 = node("n2", 890, 0, "N_2_ 氮氣", C["n2"])
    n2h4 = node("n2h4", 1080, -2, "N_2_H_4_ 聯氨", C["amx"])

    blue, red, green, purple, brown = C["nh4"], C["no3"], C["n2"], C["amx"], C["org"]
    # 硝化
    s.arrow([(nh4[0] - 20, nh4[1] - 27), (nh2oh[0] - 20, nh2oh[1] + 27)], color=blue, label="① 硝化", label_dx=-14,
            label_anchor="end", size=16)
    s.arrow([(nh2oh[0] - 10, nh2oh[1] - 27), (no2[0] - 70, no2[1] + 27)], color=blue)
    s.arrow([(no2[0] - 30, no2[1] - 27), (no3[0] - 30, no3[1] + 27)], color=blue)
    s.text(340, 470, "需氧、自營菌\nAOB/AOA → NOB\n或 comammox", size=14, color=blue, anchor="middle")
    # 脫硝
    s.arrow([(no3[0] + 30, no3[1] + 27), (no2[0] + 30, no2[1] - 27)], color=green)
    s.arrow([(no2[0] + 76, no2[1] + 10), (no[0] - 76, no[1] - 10)], color=green)
    s.arrow([(no[0], no[1] + 27), (n2o[0], n2o[1] - 27)], color=green)
    s.arrow([(n2o[0], n2o[1] + 27), (n2[0], n2[1] - 27)], color=green)
    s.text(1000, 150, "② 脫硝 = 反硝化\n（缺氧、異營菌、\n需要有機碳）", size=16, color=green, anchor="middle", weight=700)
    s.arrow([(960, 190), (900, 270)], color=green, width=1.5, dash=True)
    # Anammox
    s.arrow([(nh4[0] + 76, nh4[1]), (1000, 700), (n2h4[0] - 30, n2h4[1] + 27)], color=purple, curve=True)
    s.arrow([(no2[0] + 76, no2[1] - 10), (1190, 200), (n2h4[0] + 40, n2h4[1] - 27)], color=purple, curve=True, dash=True)
    s.arrow([(n2h4[0] - 40, n2h4[1] - 27), (n2[0] + 50, n2[1] + 27)], color=purple)
    s.text(1080, 730, "③ 厭氧氨氧化 Anammox\nNH_4_^+^ + NO_2_^−^ → N_2_（不需有機碳）", size=15, color=purple, anchor="middle",
           weight=700)
    # DNRA
    s.arrow([(no2[0] - 40, no2[1] + 27), (560, 520), (nh4[0] + 50, nh4[1] - 27)], color=brown, curve=True, dash=True,
            label="④ DNRA", label_at=0.55, label_dx=40, size=15)
    # 氨化 / 同化
    s.arrow([(org[0] + 76, org[1] - 10), (nh4[0] - 76, nh4[1] - 10)], color=brown, label="氨化", label_dy=-12, size=14)
    s.arrow([(nh4[0] - 76, nh4[1] + 12), (org[0] + 76, org[1] + 12)], color=brown, label="同化", label_dy=30, size=14)
    s.text(190, 760, "同化：微生物、酵母、植物把氨氮做成蛋白質", size=13, color=brown, anchor="middle")
    # 固氮
    s.arrow([(n2[0] - 76, n2[1]), (560, 470), (nh4[0] + 30, nh4[1] - 27)], color=C["grey"], curve=True, dash=True,
            label="固氮", label_at=0.35, label_dy=-10, size=14)
    s.text(24, 790, "顏色：藍＝氨氮系、橘＝亞硝酸鹽、紅＝硝酸鹽、綠＝最終變成氮氣離開水體、紫＝厭氧氨氧化。依 Kuypers et al. (2018) 重繪簡化。",
           size=13, color=MUTED)
    return s


def fig2_processes():
    s = Svg(1200, 760, "圖 2-2　常見生物脫氮流程")
    s.text(24, 80, "(a) 前置缺氧 A/O（MLE）：最常見的「硝化＋脫硝」組合", size=18, weight=700)
    y = 110
    s.text(40, y + 62, "進流水\n（含 NH_4_^+^、\n有機物）", size=14, anchor="middle")
    s.arrow([(80, y + 55), (130, y + 55)])
    s.box(130, y, 260, 110, "缺氧槽", color=C["n2"], sub="脫硝：NO_3_^−^ → N_2_\n用進流水的有機物當碳源\n不曝氣、只攪拌", sub_size=14)
    s.arrow([(390, y + 55), (450, y + 55)])
    s.box(450, y, 300, 110, "好氧槽", color=C["nh4"], sub="硝化：NH_4_^+^ → NO_3_^−^\n曝氣 DO ≥ 2 mg/L\n消耗鹼度，pH 會下降", sub_size=14)
    s.arrow([(750, y + 55), (810, y + 55)])
    s.box(810, y, 180, 110, "沉澱池", color=C["grey"], sub="泥水分離", sub_size=14)
    s.arrow([(990, y + 55), (1050, y + 55)])
    s.text(1110, y + 60, "放流水", size=15, anchor="middle")
    s.arrow([(600, y + 112), (600, y + 160), (290, y + 160), (290, y + 113)], color=C["no3"])
    s.text(445, y + 186, "內循環：硝酸鹽送回缺氧槽（回流比常見 2–4 倍）", size=14, color=C["no3"], anchor="middle", weight=700)
    s.arrow([(900, y + 112), (900, y + 230), (180, y + 230), (180, y + 113)], color=MUTED)
    s.text(540, y + 256, "污泥回流（把生長慢的硝化菌留在系統裡）", size=14, color=MUTED, anchor="middle", weight=700)
    # (b) SND
    s.text(24, 420, "(b) 同步硝化脫硝（SND）", size=18, weight=700)
    cx, cy = 190, 570
    s.raw(f'<circle cx="{cx}" cy="{cy}" r="120" fill="{tint(C["nh4"], .8)}" stroke="{C["nh4"]}" stroke-width="2"/>')
    s.raw(f'<circle cx="{cx}" cy="{cy}" r="62" fill="{tint(C["n2"], .75)}" stroke="{C["n2"]}" stroke-width="2"/>')
    s.text(cx, cy - 82, "外層有氧：硝化", size=15, color=C["nh4"], anchor="middle", weight=700)
    s.text(cx, cy + 6, "內層缺氧：\n脫硝", size=15, color=C["n2"], anchor="middle-v", weight=700)
    s.text(330, 520, "同一個槽、低 DO（約 0.3–1 mg/L）\n污泥膠羽或生物膜內部\n自然形成氧氣梯度。\n省曝氣，但控制難度高。", size=14,
           color=INK)
    # (c) PN/A
    s.text(600, 420, "(c) 部分亞硝化＋厭氧氨氧化（PN/A）", size=18, weight=700)
    cx, cy = 770, 570
    s.raw(f'<circle cx="{cx}" cy="{cy}" r="120" fill="{tint(C["no2"], .8)}" stroke="{C["no2"]}" stroke-width="2"/>')
    s.raw(f'<circle cx="{cx}" cy="{cy}" r="66" fill="{tint(C["amx"], .75)}" stroke="{C["amx"]}" stroke-width="2"/>')
    s.text(cx, cy - 92, "外層 AOB：\n約一半 NH_4_^+^→NO_2_^−^", size=13, color=C["no2"], anchor="middle", weight=700)
    s.text(cx, cy + 4, "內層 Anammox：\nNH_4_^+^＋NO_2_^−^→N_2_", size=14, color=C["amx"], anchor="middle-v", weight=700)
    s.text(910, 520, "顆粒污泥或生物膜。\n要壓制 NOB（不讓 NO_2_^−^\n變成 NO_3_^−^）。\n適合高氨氮、低碳廢水\n（例如厭氧消化液）。", size=14)
    s.text(24, 748, "示意圖。數值為常見操作範圍，實際依水質與設計而定；參考 Metcalf & Eddy (2014)、Lackner et al. (2014)。", size=13,
           color=MUTED)
    return s


def fig3_parameters():
    s = Svg(1200, 540, "圖 3-1　氮的分析項目怎麼互相組成")
    s.box(30, 70, 1140, 270, "", color=C["grey"], fill="#fbfbfd")
    s.text(54, 104, "總氮 TN", size=22, weight=700)
    s.box(60, 120, 600, 200, "", color=C["org"], fill="#ffffff")
    s.text(84, 152, "凱氏氮 TKN（還原態的氮）", size=18, weight=700, color=C["org"])
    s.box(84, 172, 260, 128, "有機氮 Org-N", color=C["org"], size=18, sub="蛋白質、尿素、胺基酸…", sub_size=14)
    s.box(372, 172, 264, 128, "氨氮 NH_3_-N", color=C["nh4"], size=18, sub="= NH_4_^+^ + NH_3_\n（以氮計，mg N/L）", sub_size=14)
    s.box(690, 120, 456, 200, "", color=C["no3"], fill="#ffffff")
    s.text(714, 152, "氧化態的氮 NO_x_-N", size=18, weight=700, color=C["no3"])
    s.box(714, 172, 200, 128, "亞硝酸鹽氮", color=C["no2"], size=18, sub="NO_2_^−^-N", sub_size=14)
    s.box(930, 172, 200, 128, "硝酸鹽氮", color=C["no3"], size=18, sub="NO_3_^−^-N", sub_size=14)
    s.text(1146, 104, "TN ＝ TKN ＋ NO_2_^−^-N ＋ NO_3_^−^-N　　TKN ＝ 有機氮 ＋ 氨氮", size=18, anchor="end", weight=700)
    rows = [
        (214, C["org"], "不直接測：\nTKN − 氨氮"),
        (504, C["nh4"], "靛酚比色 W448.52B\n流動注入 W437\n廢水通常先蒸餾"),
        (814, C["no2"], "比色法 W418\n離子層析 W415"),
        (1030, C["no3"], "離子層析 W415\n鎘還原 W436\nUV 分光 W419"),
    ]
    for x, col, t in rows:
        s.arrow([(x, 304), (x, 366)], color=col, width=1.5, dash=True)
        s.box(x - 100, 368, 200, 100, "", color=col, fill="#ffffff")
        s.text(x, 420, t, size=14, anchor="middle-v")
    s.text(24, 500, "NIEA 編號為台灣環境部（國家環境研究院）公告方法系列；正式申報要用最新公告版次。總氮可依 NIEA W423.53C 以「加總」求得。", size=13,
           color=MUTED)
    s.text(24, 524, "注意：濃度一律寫成「以氮計（as N）」。1 mg NH_4_^+^/L 只有 0.78 mg N/L；1 mg NO_3_^−^/L 只有 0.23 mg N/L。", size=13,
           color=MUTED)
    return s


def fig3_choose():
    s = Svg(1200, 700, "圖 3-2　怎麼選檢測方法")
    s.box(420, 66, 360, 70, "你的數據要拿來做什麼？", color=INK, size=20, fill="#f3f4f7")
    cols = [
        (40, C["no3"], "對外申報、法規、合約", "委託認證實驗室\n用 NIEA 公告方法\n（或合約指定的 Standard\nMethods / US EPA 方法）",
         "優點：有公信力\n缺點：慢、貴、樣品量少"),
        (430, C["nh4"], "研發、批次試驗、大量樣品", "實驗室分光比色\n（靛酚、水楊酸法，可用微量盤）\nNO_2_^−^/NO_3_^−^ 用 IC 或比色\n或流動注入分析儀",
         "要做：標準曲線、空白、\n添加回收、重複樣"),
        (820, C["n2"], "現場、即時監控", "試劑包、比色計\n離子選擇電極（ISE）\n線上氨氮分析儀",
         "一定要定期用標準方法\n比對、校正"),
    ]
    for x, col, head, body, note in cols:
        s.arrow([(600, 138), (x + 170, 196)], color=MUTED, width=1.5)
        s.box(x, 200, 340, 64, head, color=col, size=18)
        s.box(x, 280, 340, 160, "", color=col, fill="#ffffff")
        s.text(x + 170, 360, body, size=15, anchor="middle-v")
        s.text(x + 170, 486, note, size=14, color=MUTED, anchor="middle-v")
    s.box(40, 540, 1120, 130, "", color=C["grey"], fill="#fbfbfd")
    s.text(64, 574, "不管選哪一種，採樣與保存決定一半的品質", size=18, weight=700)
    s.text(64, 606, "• 氨氮：加硫酸到 pH < 2、4 °C 冷藏，最長 28 天；不加酸就要盡快分析（細菌會繼續轉化氨氮）。", size=15)
    s.text(64, 632, "• 亞硝酸鹽、硝酸鹽（分開測）：4 °C、48 小時內分析，不要加酸。生物試驗樣品：0.45 µm 過濾後立即測或冷凍。", size=15)
    s.text(64, 658, "• 高鹽、色度、濁度、含胺類或硫化物的樣品會干擾比色 → 先蒸餾、稀釋或做添加回收確認。", size=15)
    return s


def fig4_genes():
    s = Svg(1200, 900, "圖 4-1　氮轉化步驟、酵素與功能基因（qPCR 的靶標就在箭頭上）")

    def chain(y, title, color, nodes, enzymes, orgs):
        s.text(24, y - 18, title, size=18, weight=700, color=color)
        n = len(nodes)
        gap = (1150 - 40) / n
        w = min(150, gap - 70)
        xs = [40 + gap * i + (gap - w) / 2 for i in range(n)]
        for (label, c), x in zip(nodes, xs):
            s.box(x, y, w, 50, label, color=c, size=16)
        for i, (enz, gene) in enumerate(enzymes):
            if not enz:
                continue
            x1, x2 = xs[i] + w + 4, xs[i + 1] - 4
            s.arrow([(x1, y + 25), (x2, y + 25)], color=color, width=2.5)
            s.text((x1 + x2) / 2, y + 2, enz, size=12, color=MUTED, anchor="middle")
            s.pill((x1 + x2) / 2, y + 72, gene, color, size=13)
        s.text(40, y + 112, orgs, size=14, color=INK)

    chain(100, "硝化（好氧）", C["nh4"],
          [("NH_3_", C["nh4"]), ("NH_2_OH", C["nh4"]), ("NO", C["gas"]), ("NO_2_^−^", C["no2"]), ("NO_3_^−^", C["no3"])],
          [("AMO", "amoA/B/C"), ("HAO", "hao"), ("（機制研究中）", "—"), ("NXR", "nxrA/nxrB")],
          "AOB：Nitrosomonas、Nitrosospira　AOA：Nitrososphaera、Nitrosopumilus（沒有 hao）\n"
          "NOB：Nitrospira、Nitrobacter、Nitrotoga　comammox：Nitrospira（同時有 amoA 與 nxr，一隻做完）")
    chain(320, "脫硝＝反硝化（缺氧、異營）", C["n2"],
          [("NO_3_^−^", C["no3"]), ("NO_2_^−^", C["no2"]), ("NO", C["gas"]), ("N_2_O", C["gas"]), ("N_2_", C["n2"])],
          [("Nar / Nap", "narG / napA"), ("NirK / NirS", "nirK / nirS"), ("Nor", "cnorB / qnorB"), ("Nos", "nosZ (I / II)")],
          "Pseudomonas、Paracoccus、Thauera、Azoarcus、Zoogloea、Hyphomicrobium（甲醇）等，種類非常多\n"
          "許多菌只有其中幾步 → 少了 nosZ 就停在 N_2_O；nosZ clade II 菌是重要的 N_2_O 消耗者")
    chain(540, "厭氧氨氧化 Anammox（缺氧、自營）", C["amx"],
          [("NO_2_^−^", C["no2"]), ("NO", C["gas"]), ("N_2_H_4_\n（+NH_4_^+^）", C["amx"]), ("N_2_", C["n2"])],
          [("Nir", "nirS / nirK"), ("HZS", "hzsA/B/C"), ("HDH", "hdh")],
          "Candidatus Brocadia、Kuenenia、Jettenia、Anammoxoglobus（廢水）；Scalindua（海洋）\n"
          "全部尚未純培養（所以叫 Candidatus）；生長很慢 → 用 16S rRNA 或 hzsB 做 qPCR 追蹤")
    s.text(24, 745, "其他會讓「氨氮變多或變少」的路徑", size=18, weight=700, color=C["org"])
    s.box(40, 766, 340, 104, "DNRA：NO_2_^−^ → NH_4_^+^", color=C["org"], size=16, sub="基因 nrfA；高 C/N、缺氧時\n會把硝酸鹽「變回」氨氮",
          sub_size=13)
    s.box(420, 766, 360, 104, "同化：NH_4_^+^ → 菌體胺基酸", color=C["org"], size=16,
          sub="amt 運輸蛋白；glnA（GS）、gdhA（GDH）\n所有微生物、酵母、植物都會", sub_size=13)
    s.box(820, 766, 340, 104, "固氮：N_2_ → NH_4_^+^", color=C["grey"], size=16, sub="nifH；廢水中通常不重要\n（氮已經很多）",
          sub_size=13)
    return s


def fig5_toolbox():
    s = Svg(1200, 640, "圖 5-1　微生物分析工具箱：先問清楚你要回答哪個問題")
    cols = [
        ("誰在那裡？", C["n2"], "組成", ["16S rRNA 擴增子定序", "（V3–V4、V4 區）", "FISH 螢光原位雜交", "宏基因體（metagenomics）"]),
        ("有多少？", C["nh4"], "數量", ["qPCR / ddPCR", "（功能基因或 16S）", "FISH＋影像計數", "流式細胞儀（總菌數）"]),
        ("有在工作嗎？", C["no2"], "表現", ["RT-qPCR（mRNA）", "宏轉錄體", "宏蛋白質體", "^15^N-DNA-SIP"]),
        ("做得多快？", C["no3"], "速率", ["批次活性試驗", "（氨／硝酸鹽消耗速率）", "OUR＋抑制劑", "^15^N 同位素、N_2_O 量測"]),
    ]
    for i, (q, col, tag, items) in enumerate(cols):
        x = 30 + i * 292
        s.box(x, 70, 272, 70, q, color=col, size=22)
        s.box(x, 156, 272, 250, "", color=col, fill="#ffffff")
        for j, it in enumerate(items):
            s.text(x + 136, 200 + j * 50, it, size=17 if not it.startswith("（") else 14,
                   color=INK if not it.startswith("（") else MUTED, anchor="middle")
        s.pill(x + 136, 438, tag, col, size=15)
    s.arrow([(40, 490), (1160, 490)], color=MUTED, width=2)
    s.text(40, 524, "DNA 層級：潛力", size=15, color=MUTED)
    s.text(600, 524, "RNA／蛋白質：正在表現", size=15, color=MUTED, anchor="middle")
    s.text(1160, 524, "化學量測：實際速率", size=15, color=MUTED, anchor="end")
    s.box(30, 548, 1140, 72, "最常見的錯誤：「qPCR 測到很多 amoA」不等於「氨氮被去除得很快」。\n基因數量 → 一定要搭配化學量測（氮質量平衡、活性試驗）一起看。",
          color=C["no3"], size=16, weight=400, fill=tint(C["no3"], .93))
    return s


def fig6_workflow():
    s = Svg(1200, 600, "圖 6-1　自己做 qPCR 定量的八個步驟")
    steps = [
        ("1 決定靶標", "哪個功能群？\n功能基因或 16S？\n優先用文獻引子"),
        ("2 電腦檢查", "Primer-BLAST\nSILVA TestPrime\n比對你的定序資料"),
        ("3 標準品", "質體或合成 DNA\n（gBlock）\n算 copies/µL"),
        ("4 條件最佳化", "溫度梯度 PCR\n單一條帶、單一\n熔解峰；定序確認"),
        ("5 樣品 DNA", "固定體積或重量\n萃取空白\nA260/280、稀釋測抑制"),
        ("6 上機", "標準曲線 6–8 點\n三重複、NTC\n每盤都放標準品"),
        ("7 品管", "效率 90–110%\nR² ≥ 0.98\n熔解曲線單峰"),
        ("8 換算報告", "copies/mL、/g\n或 ÷16S 比例\n依 MIQE 寫方法"),
    ]
    for i, (head, body) in enumerate(steps):
        r, c = divmod(i, 4)
        x, y = 30 + c * 292, 80 + r * 250
        col = [C["nh4"], C["n2"], C["no2"], C["amx"], C["no3"], C["org"], C["nh4"], C["n2"]][i]
        s.box(x, y, 250, 56, head, color=col, size=19)
        s.box(x, y + 64, 250, 130, "", color=col, fill="#ffffff")
        s.text(x + 125, y + 128, body, size=15, anchor="middle-v")
        if c < 3:
            s.arrow([(x + 252, y + 28), (x + 290, y + 28)], color=MUTED)
    s.arrow([(1155, 135), (1185, 135), (1185, 305), (15, 305), (15, 358), (28, 358)], color=MUTED, width=2)
    s.text(600, 588, "依 Bustin et al. (2009) MIQE 準則與 Smith & Osborn (2009) 整理", size=13, color=MUTED, anchor="middle")
    return s


def fig7_yeast():
    s = Svg(1200, 640, "圖 7-1　「氨氮不見了」的三種生物機制：酵母菌屬於哪一種？")
    cols = [
        ("A. 自營硝化菌", C["nh4"], "AOB / AOA / NOB",
         "能量：氧化氨氮\n碳源：CO_2_（不需有機物）\n產物：NO_2_^−^、NO_3_^−^\n→ 氮還在水裡，\n要再脫硝才真的去除"),
        ("B. 異營同化", C["org"], "酵母菌、一般異營菌、藻類、植物",
         "NH_4_^+^ 被吸進細胞\n→ 做成蛋白質、核酸\n需要大量有機碳\n（C/N 高才吃得多）\n→ 氮在菌體：要排泥或收菌體"),
        ("C. 異營硝化–好氧脫硝", C["n2"], "HN-AD 細菌；少數酵母",
         "NH_4_^+^ → NH_2_OH → … → N_2_O / N_2_\n有氧下同時進行\n需要高 C/N\n文獻例：Candida boidinii L21、\nBarnettozyma californica K1"),
    ]
    for i, (head, col, who, body) in enumerate(cols):
        x = 30 + i * 392
        s.box(x, 70, 360, 64, head, color=col, size=21)
        s.text(x + 180, 160, who, size=15, color=col, anchor="middle", weight=700)
        s.box(x, 176, 360, 230, "", color=col, fill="#ffffff")
        s.text(x + 180, 292, body, size=16, anchor="middle-v")
    s.box(30, 430, 1140, 180, "", color=C["grey"], fill="#fbfbfd")
    s.text(54, 466, "怎麼分辨是哪一種？做氮質量平衡", size=19, weight=700)
    s.text(54, 502, "• 只看氨氮下降不夠：要同時量 NH_4_^+^、NO_2_^−^、NO_3_^−^、溶解性 TN，以及菌體氮（或總氮含菌體）。", size=16)
    s.text(54, 534, "• 水中 TN 下降、但「水中 TN + 菌體氮」不變 → 主要是同化（B）。", size=16)
    s.text(54, 566, "• 兩者加起來都下降，且排除氣提（密閉瓶、無菌對照）→ 才是真的轉成氣體（C）。", size=16)
    s.text(54, 598, "• 酵母常見的是 B；C 只在部分分離株被報導，要用自己的菌株驗證。", size=16, color=C["no3"])
    return s


def fig8_plant():
    s = Svg(1200, 680, "圖 8-1　浮水植物去除氨氮的途徑")
    wy = 230
    s.raw(f'<rect x="0" y="{wy}" width="1200" height="400" fill="#eaf3fb"/>')
    s.line(0, wy, 1200, wy, color=C["nh4"], width=2)
    s.raw(f'<rect x="0" y="600" width="1200" height="80" fill="#efe6d8"/>')
    s.text(1180, wy + 26, "水面", size=14, color=C["nh4"], anchor="end")
    s.text(1180, 640, "底泥（缺氧）", size=14, color=C["org"], anchor="end")
    # 植物
    for dx in (-80, 0, 80):
        s.raw(f'<ellipse cx="{430 + dx}" cy="{wy - 40}" rx="70" ry="34" fill="#7cc58f" stroke="#2f7d4a" stroke-width="2" '
              f'transform="rotate({dx / 4} {430 + dx} {wy - 40})"/>')
    for i in range(14):
        x0 = 380 + i * 8
        s.raw(f'<path d="M{x0},{wy} q{(i - 7) * 6},90 {(i - 7) * 10},{150 + (i % 3) * 30}" stroke="#7a6a48" '
              f'stroke-width="2" fill="none"/>')
    s.text(430, wy - 92, "浮水植物（布袋蓮、大萍、浮萍…）", size=16, anchor="middle", weight=700)
    # 1 吸收
    s.arrow([(150, 340), (360, 320)], color=C["nh4"])
    s.text(40, 300, "① 根吸收 NH_4_^+^ → 植物體（同化）", size=15, color=C["nh4"], weight=700)
    # 2 收割
    s.arrow([(520, wy - 50), (700, 90)], color=C["org"], label="② 定期收割：氮才真正離開系統", label_at=1, label_dx=10,
            label_dy=4, label_anchor="start", size=15)
    # 3 根圈微生物
    s.box(620, 300, 300, 90, "③ 根表面生物膜", color=C["n2"], size=16, sub="根系泌氧 → 硝化；\n缺氧微區 → 脫硝 → N_2_", sub_size=14)
    s.arrow([(780, 300), (900, 175)], color=C["n2"], label="N_2_", label_at=1, label_dx=18, label_dy=4, size=16)
    # 4 底泥脫硝
    s.arrow([(200, 620), (200, 480)], color=C["n2"], label="④ 底泥脫硝 → N_2_", label_at=1, label_dx=14, label_dy=10,
            label_anchor="start", size=15)
    # 5 遮光
    s.box(950, 420, 220, 110, "⑤ 遮光抑藻", color=C["grey"], size=16, sub="水面被覆蓋 → 藻類少\n→ pH 與 DO 都降低", sub_size=13)
    # 6 揮發
    s.arrow([(1110, 210), (1110, 150)], color=C["gas"], dash=True, label="⑥ pH 高時 NH_3_ 揮發", label_at=1, label_dy=-8,
            size=15)
    s.text(24, 668, "多數研究認為：植物直接吸收只佔一部分，根圈微生物與收割管理同樣重要（Brix 1997；Vymazal 2007）。", size=13, color=MUTED)
    return s


def fig9_options():
    s = Svg(1200, 620, "圖 9-1　非生物的氨氮處理技術：氮最後去了哪裡？")
    s.box(470, 250, 260, 100, "水中的\nNH_4_^+^ / NH_3_", color=C["nh4"], size=22)
    opts = [
        (40, 70, C["gas"], "氣提（Air stripping）", "pH 調到 10.5–11.5 → NH_3_ 變氣體\n用酸吸收 → 硫酸銨（可回收）"),
        (820, 70, C["no3"], "折點加氯", "Cl_2_ : NH_3_-N 理論約 7.6 : 1\n→ N_2_；可能生成氯胺、副產物"),
        (40, 440, C["n2"], "離子交換／沸石吸附", "NH_4_^+^ 被吸附；飽和後再生\n再生液含高濃度氨氮需處理"),
        (820, 440, C["org"], "鳥糞石沉澱（Struvite）", "Mg^2+^ + NH_4_^+^ + PO_4_^3−^ → MgNH_4_PO_4_·6H_2_O\npH 約 8.5–9.5；同時回收磷"),
    ]
    for x, y, col, head, body in opts:
        s.box(x, y, 340, 110, head, color=col, size=18, sub=body, sub_size=14)
    s.arrow([(470, 270), (382, 160)], color=C["gas"])
    s.arrow([(730, 270), (818, 160)], color=C["no3"])
    s.arrow([(470, 330), (382, 450)], color=C["n2"])
    s.arrow([(730, 330), (818, 450)], color=C["org"])
    s.text(600, 420, "共同點：都和第 1 章的\nNH_3_/NH_4_^+^ 平衡有關", size=15, color=MUTED, anchor="middle-v")
    s.text(24, 600, "依 Metcalf & Eddy (2014)、Hedström (2001)、Le Corre et al. (2009) 整理；化學藥劑成本與副產物要一起評估。", size=13, color=MUTED)
    return s


FIGS = {
    "fig0-1-roadmap": fig0_roadmap,
    "fig1-1-n-cycle": fig1_cycle,
    "fig2-2-processes": fig2_processes,
    "fig3-1-n-parameters": fig3_parameters,
    "fig3-2-method-choice": fig3_choose,
    "fig4-1-genes": fig4_genes,
    "fig5-1-toolbox": fig5_toolbox,
    "fig6-1-qpcr-workflow": fig6_workflow,
    "fig7-1-yeast": fig7_yeast,
    "fig8-1-plants": fig8_plant,
    "fig9-1-physchem": fig9_options,
}

if __name__ == "__main__":
    only = set(sys.argv[1:])
    render({k: f() for k, f in FIGS.items() if not only or k in only}, OUT)
