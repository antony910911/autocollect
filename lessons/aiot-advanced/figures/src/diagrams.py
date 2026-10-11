"""進階教材的概念圖。執行：python lessons/aiot-advanced/figures/src/diagrams.py [圖名 ...]"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_tools"))
from svgkit import INK, MUTED, Svg, render, tint, wrap  # noqa: E402

OUT = Path(__file__).resolve().parent.parent
BLUE, ORANGE, RED, GREEN, PURPLE, GREY, BROWN = ("#2f6fb3", "#d9821e", "#c23b3b", "#2f9e6e", "#7b4bb3", "#6b7280",
                                                 "#8a6d3b")


def fig0():
    s = Svg(1200, 560, "學習地圖：從問題定義到上線維運")
    rows = [
        ("準備", BROWN, [("1", "問題定義\n與資料盤點"), ("2", "模型家族地圖\n怎麼挑模型"), ("3", "實作 0\n資料準備")]),
        ("實作", BLUE, [("4", "實作 1\n產氣預測"), ("5", "實作 2\nVFA 軟感測"), ("6", "實作 3\n數位孿生 EKF")]),
        ("應用", GREEN, [("7", "實作 4\n預警與感測器健康"), ("8", "實作 5\n進料建議與維運")]),
        ("延伸", PURPLE, [("9", "國內外文獻\n與工具"), ("10", "創新思路")]),
    ]
    y = 76
    for name, col, items in rows:
        s.box(24, y, 120, 92, name, color=col, size=20)
        x = 180
        for i, (n, lab) in enumerate(items):
            s.box(x, y, 300, 92, f"第 {n} 章", color=col, size=15, sub=lab, sub_size=17, fill="#ffffff")
            if i < len(items) - 1:
                s.arrow([(x + 302, y + 46), (x + 333, y + 46)], color=col)
            x += 335
        y += 112
    s.text(24, 548, "第 3–8 章都附可執行的 Python 程式（lessons/aiot-advanced/code/），把資料換成自己廠的就能照著做。", size=15, color=MUTED)
    return s


def fig1():
    s = Svg(1200, 640, "圖 1-1　建模前的「問題定義卡」：五個問題答不出來，先別開始寫程式")
    qs = [
        ("① 預測什麼？", "目標變數要具體：\n「明天甲烷 Nm³」\n「此刻 VFA mg/L」", BLUE),
        ("② 提前多久？", "決定能用哪些資料：\n預測明天，就不能用\n明天才知道的數據", ORANGE),
        ("③ 給誰用？", "操作員、廠長、\n售電排程、\n自動控制器", GREEN),
        ("④ 用來做什麼決定？", "調整進料、加鹼、\n安排維修、\n通知值班人員", PURPLE),
        ("⑤ 錯了代價多大？", "漏報（沒抓到酸化）\nvs 誤報（狼來了）\n哪個比較貴？", RED),
    ]
    for i, (h, b, c) in enumerate(qs):
        x = 24 + i * 234
        s.box(x, 80, 218, 64, h, color=c, size=17)
        s.box(x, 154, 218, 140, "", color=c, fill="#ffffff")
        s.text(x + 109, 224, b, size=14, anchor="middle-v")
    s.box(24, 330, 1152, 280, "", color=GREY, fill="#fbfbfd")
    s.text(48, 366, "接著盤點資料：做一張「資料字典」", size=18, weight=700)
    cols = ["資料來源", "例子", "頻率", "注意"]
    rows = [
        ("線上儀表（SCADA）", "產氣流量、CH₄%、pH、溫度、液位", "每分鐘", "單位、量程、校正紀錄、缺漏"),
        ("實驗室", "VFA、鹼度、FOS/TAC、TS/VS、氨氮", "每週 1–3 次", "記「採樣時間」不是分析時間"),
        ("進料紀錄", "原料種類、重量、批次 COD", "每批／每天", "最常是紙本 → 先數位化"),
        ("事件紀錄", "停機、換料、加藥、清槽、校正", "不定期", "沒有它，模型會把事件當正常"),
    ]
    xs = [48, 270, 640, 800]
    for x, c in zip(xs, cols):
        s.text(x, 404, c, size=15, weight=700, color=MUTED)
    for r, row in enumerate(rows):
        for x, c in zip(xs, row):
            s.text(x, 444 + r * 40, c, size=15)
    return s


def fig2():
    s = Svg(1200, 680, "圖 2-1　模型家族地圖：依「需要多少機理知識」與「需要多少資料」")
    x0, y0, w, h = 120, 90, 960, 500
    s.line(x0, y0 + h, x0 + w, y0 + h, color=INK, width=2)
    s.line(x0, y0, x0, y0 + h, color=INK, width=2)
    s.text(x0 + w / 2, y0 + h + 44, "需要的歷史資料量 →", size=16, anchor="middle")
    s.text(60, y0 + h / 2, "需\n要\n的\n機\n理\n知\n識\n↑", size=15, anchor="middle-v")
    items = [
        (180, 120, 300, 110, "機理模型", BLUE, "ADM1（26 個狀態）\nAM2（6 個狀態）\n可外推、參數多"),
        (560, 210, 300, 120, "混合模型", PURPLE, "機理模型＋EKF 資料同化\n機理＋機器學習修正誤差\n物理約束神經網路"),
        (720, 420, 320, 120, "資料驅動模型", ORANGE, "線性迴歸、隨機森林\n梯度提升樹、LSTM\n只會內插、要大量資料"),
        (160, 420, 300, 120, "規則與統計", GREY, "固定門檻、移動平均\nCUSUM、控制圖\n最便宜、最好解釋"),
    ]
    for x, y, bw, bh, head, col, body in items:
        s.box(x, y, bw, bh, head, color=col, size=18, sub=body, sub_size=13)
    s.arrow([(462, 480), (718, 480)], color=MUTED, dash=True, label="① 加機器學習", size=13, label_color=MUTED)
    s.arrow([(880, 418), (800, 332)], color=MUTED, dash=True, label="② 結合機理", label_at=0.5, label_dx=12, size=13,
            label_color=MUTED, label_anchor="start")
    s.text(600, 610, "大多數沼氣廠的起點：先用規則與統計，再加機器學習，最後走向混合模型", size=14, color=MUTED, anchor="middle")
    s.text(24, 664, "依 Batstone et al. (2002)、Bernard et al. (2001)、Andrade Cruz et al. (2022)、Rutland et al. (2023) 整理。", size=13,
           color=MUTED)
    return s


def fig6():
    s = Svg(1200, 560, "圖 6-1　擴展卡爾曼濾波（EKF）：「模型預測」和「量測修正」輪流進行")
    s.box(60, 120, 330, 150, "① 預測", color=BLUE, size=20, sub="用 AM2 模型往前算 1 小時\n（輸入：進料量、進料濃度）\n同時估計「我有多不確定」", sub_size=14)
    s.box(810, 120, 330, 150, "② 修正", color=GREEN, size=20, sub="拿實際量到的\n甲烷、CO₂ 流量與 pH 比對\n差多少，就把狀態拉回多少", sub_size=14)
    s.box(435, 330, 330, 120, "③ 更新後的估計", color=PURPLE, size=20, sub="槽內 VFA、鹼度、菌量……\n（包括量不到的）", sub_size=14)
    s.arrow([(392, 170), (808, 170)], color=MUTED, label="預測值 vs 量測值", size=15, label_color=INK)
    s.arrow([(975, 272), (975, 390), (767, 390)], color=MUTED)
    s.arrow([(433, 390), (225, 390), (225, 272)], color=MUTED, label="下一個小時", label_at=0.5, label_dx=-8, size=14,
            label_color=INK, label_anchor="end")
    s.text(600, 500, "卡爾曼增益決定「信模型多一點，還是信感測器多一點」：感測器雜訊大就少修正，模型不確定就多修正。", size=15, color=MUTED,
           anchor="middle")
    s.text(600, 530, "依 Kalman (1960) 與 AM2 狀態估計文獻整理。", size=13, color=MUTED, anchor="middle")
    return s


def fig8():
    s = Svg(1200, 620, "圖 8-2　模型上線後的維運循環（MLOps）")
    import math
    cx, cy, r = 600, 340, 210
    steps = [("上線運作", GREEN, "每天產生預測與建議"), ("監控", BLUE, "預測誤差、資料分布、\n感測器健康"),
             ("觸發檢討", ORANGE, "誤差變大、換原料、\n季節改變"), ("重新訓練", PURPLE, "加入新資料\n依時間切分驗證"),
             ("人工審核", RED, "工程師與操作員\n確認後才換版")]
    pos = []
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        pos.append((cx + r * 1.6 * math.cos(a), cy + r * math.sin(a)))
    for (h, c, b), (x, y) in zip(steps, pos):
        s.box(x - 140, y - 50, 280, 100, h, color=c, size=18, sub=b, sub_size=13)
    for i in range(5):
        (x1, y1), (x2, y2) = pos[i], pos[(i + 1) % 5]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        s.arrow([(x1 + (x2 - x1) * 0.3, y1 + (y2 - y1) * 0.3), (cx + (mx - cx) * 0.8, cy + (my - cy) * 0.8),
                 (x1 + (x2 - x1) * 0.7, y1 + (y2 - y1) * 0.7)], color=MUTED, curve=True, width=2)
    s.box(cx - 150, cy - 40, 300, 80, "版本紀錄", color=GREY, size=17, sub="哪一版模型、用哪些資料、\n什麼時候上線", sub_size=12)
    s.text(600, 604, "概念漂移的處理方式參考 Gama et al. (2014) 的回顧；換版前必須通過和舊版相同的驗證。", size=13, color=MUTED, anchor="middle")
    return s


def fig9():
    s = Svg(1200, 520, "圖 9-1　90 天起步計畫：用自己廠的資料走完一次")
    phases = [
        ("第 1–2 週", BROWN, "寫問題定義卡\n列資料字典\n找出缺的資料"),
        ("第 3–6 週", BLUE, "匯出一年資料\n對齊時間、標事件\n實驗室數據電子化"),
        ("第 7–9 週", ORANGE, "跑簡單基準\n線性＋隨機森林\n依時間切分驗證"),
        ("第 10–12 週", GREEN, "每天產出預測或警示\n與操作員檢討\n記錄有沒有幫上忙"),
        ("第 13 週", PURPLE, "成果報告：\n比基準好多少？\n下一步做什麼？"),
    ]
    for i, (h, c, b) in enumerate(phases):
        x = 24 + i * 236
        s.box(x, 80, 218, 60, h, color=c, size=18)
        s.box(x, 150, 218, 150, "", color=c, fill="#ffffff")
        s.text(x + 109, 225, b, size=15, anchor="middle-v")
        if i < 4:
            s.arrow([(x + 220, 110), (x + 234, 110)], color=MUTED)
    s.box(24, 336, 1152, 150, "", color=GREEN, fill=tint(GREEN, .92))
    s.text(48, 372, "90 天後你會有：", size=18, weight=700, color=GREEN)
    s.text(48, 406, "• 一份乾淨、可重複使用的資料集　• 一個比「明天＝今天」更準的預測（或證明目前資料還不夠）", size=15)
    s.text(48, 438, "• 操作員的回饋：哪些警示有用、哪些是雜訊　• 下一階段要補的儀表與實驗室項目清單", size=15)
    s.text(48, 470, "程式範本：lessons/aiot-advanced/code/（把 plant.py 換成讀取你們廠的 CSV）", size=15, color=MUTED)
    return s


def fig3_feature_time():
    """做決定的那一刻，你手上真的有什麼？——特徵能不能用，看的是時間不是相關性。"""
    s = Svg(1420, 980, "圖 3-2　特徵能不能用，看的是「做決定的那一刻拿不拿得到」")
    s.text(40, 80, "第 4.5 節的「偷看未來」是結果，這張圖是原因。"
                   "挑特徵時唯一要問的問題：**模型上線那天，這個數字在做決定前就有了嗎？**",
           size=15.5, color=MUTED)

    T = 760  # 做決定的時刻
    s.line(60, 300, 1360, 300, color=GREY, width=3)
    s.raw(f'<line x1="{T}" y1="180" x2="{T}" y2="560" stroke="{RED}" stroke-width="4" '
          f'stroke-dasharray="9 6"/>')
    s.text(T, 164, "做決定的這一刻", size=19, weight=700, color=RED, anchor="middle")
    s.text(T, 588, "（今天傍晚決定明天餵多少）", size=14, color=MUTED, anchor="middle")
    s.text(80, 272, "過去", size=17, weight=700, color=GREEN)
    s.text(1340, 272, "未來", size=17, weight=700, color=RED, anchor="end")
    s.arrow([(1340, 300), (1362, 300)], color=GREY, width=3)

    s.text(92, 350, "可以用：做決定前已經量到了", size=17, weight=700, color=GREEN)
    for i, name in enumerate(["今天／昨天／前天產氣", "7 日平均產氣",
                              "今天／昨天／前天 COD 負荷", "今天的 pH、CH_4_%"]):
        y = 392 + i * 42
        s.raw(f'<rect x="92" y="{y - 24}" width="628" height="34" rx="17" '
              f'fill="{tint(GREEN, 0.9)}" stroke="{GREEN}" stroke-width="1.6"/>')
        s.icon("check", 106, y - 20, 20, GREEN, 2.4)
        s.text(136, y, name, size=15)

    s.text(800, 350, "不能用：那時候還不知道", size=17, weight=700, color=RED)
    for i, name in enumerate(["明天的 pH", "明天的 CH_4_%", "明天實際產氣",
                              "這一週的平均（含明天）"]):
        y = 392 + i * 42
        s.raw(f'<rect x="800" y="{y - 24}" width="560" height="34" rx="17" '
              f'fill="{tint(RED, 0.93)}" stroke="{RED}" stroke-width="1.6"/>')
        s.icon("x", 814, y - 20, 20, RED, 2.4)
        s.text(844, y, name, size=15)

    # 例外：明天的計畫進料
    s.raw(f'<rect x="800" y="620" width="560" height="126" rx="12" fill="{tint(ORANGE, 0.93)}" '
          f'stroke="{ORANGE}" stroke-width="2"/>')
    s.icon("circle-alert", 824, 648, 24, ORANGE, 2.1)
    s.text(860, 668, "一個例外：明天計畫的 COD 負荷", size=17, weight=700, color=ORANGE)
    for j, ln in enumerate(wrap("它在未來，但**是操作員事先決定的**，做決定時就在手上——"
                                "所以合法，而且正是進料建議要調的那個量。", 14.5, 512)):
        s.text(824, 702 + j * 24, ln, size=14.5)

    s.card(40, 620, 700, ["缺漏只能用**過去**的值往前填，不能用後面的值回填",
                          "移動平均的視窗只能往回看，不能置中",
                          "標準化的平均值與標準差只能從訓練期算，不能用全部資料算"],
           title="同一個原則的三個常見破口", icon="triangle-alert", color=PURPLE, size=14.5,
           foot="這三個都不會報錯，只會讓驗證分數好看得不真實")

    s.box(40, 830, 1320, 116, "", color=BLUE, fill=tint(BLUE, 0.95))
    s.icon("list-checks", 72, 862, 26, BLUE, 2.1)
    s.text(116, 884, "一句話的檢查法", size=18, weight=700)
    s.text(116, 918, "每做一個特徵就問一次：「這個欄位，我在做決定的那一刻打開系統看得到嗎？」"
                     "看不到就刪掉——驗證分數會變差，但那才是上線後真正的分數。", size=15)
    return s


FIGS = {"fig0-1-roadmap": fig0, "fig1-1-problem-card": fig1, "fig2-1-model-map": fig2, "fig6-1-ekf-loop": fig6,
        "fig3-2-feature-time": fig3_feature_time, "fig8-2-mlops": fig8, "fig9-1-90days": fig9}

if __name__ == "__main__":
    only = set(sys.argv[1:])
    render({k: f() for k, f in FIGS.items() if not only or k in only}, OUT)
