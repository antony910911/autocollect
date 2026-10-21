"""「Claude Code 操作手冊」分區的示意圖。

執行：python lessons/using-claude/figures/src/cc_diagrams.py [圖名 ...]

和同目錄的 diagrams.py 分開，因為那一支是觀念篇的圖。檔名一律 fc 開頭。
圖的標題交給 Svg(...) 的第三個參數畫（畫在 (24, 40)），不要自己再畫一次。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_tools"))
from svgkit import INK, MUTED, Svg, render, tint, wrap  # noqa: E402

OUT = Path(__file__).resolve().parent.parent
BLUE, ORANGE, RED, GREEN, PURPLE, GREY, BROWN, TEAL = ("#2f6fb3", "#d47c18", "#c23b3b", "#2f9e6e",
                                                       "#7b4bb3", "#6b7280", "#8a6d3b", "#1b8a8f")
W = 1000


def fig_map():
    """十一章各自解決什麼，分成四組。"""
    s = Svg(W, 598, "圖 0-1　十一章解決的十一件事")
    s.text(26, 72, "前三組是「先搞懂」，最後一組是「查表」。第 1 章一定要讀，後面兩章從它長出來。",
           size=16, color=MUTED)

    groups = [
        (BLUE, "先搞懂花在哪", ["1　一次對話裝了什麼", "2　token 怎麼看、怎麼省"]),
        (PURPLE, "調兩個旋鈕", ["3　選模型", "4　思考等級"]),
        (TEAL, "學會操作", ["5　/ @ ! 三個符號", "6　CLAUDE.md 與專案",
                            "7　技能", "8　外掛、MCP"]),
        (ORANGE, "接力與查表", ["9　換對話與交接清單", "10　和 Codex 接力", "11　一頁查表"]),
    ]
    x = 40
    for color, title, items in groups:
        w = 220
        s.box(x, 112, w, 56, title, color=color, size=18)
        y = 184
        for it in items:
            s.box(x, y, w, 62, it, color=color, size=15.5,
                  fill=tint(color, 0.93))
            y += 74
        x += 230

    s.box(40, 490, 920, 86, "", color=GREEN, fill=tint(GREEN, 0.95))
    s.icon("circle-check", 72, 520, 26, GREEN, 2.1)
    s.text(116, 526, "只讀一章的話，讀第 1 章", size=18, weight=700, color=GREEN)
    s.text(116, 554, "「每問一句，整段對話重送一次」——省 token 和換對話的時機，都是這一句推出來的。",
           size=15.5)
    return s


def fig_turn():
    """一次對話裡裝了什麼：第三輪的那一包。"""
    s = Svg(W, 680, "圖 1-1　你問第三句時，送出去的是這一整包")
    s.text(26, 72, "不是只送那一句。前面全部，加上它讀過的每一個檔案，一起重送。",
           size=16, color=MUTED)

    rows = [
        (GREY, "系統提示", "每次都在", 44),
        (PURPLE, "CLAUDE.md ＋ 自動記憶", "每次都在", 52),
        (PURPLE, "技能名字與說明、MCP 工具名字", "每次都在", 44),
        (BLUE, "你的第 1 句", "", 36),
        (TEAL, "它的回答 ①", "", 36),
        (BROWN, "它讀的 utils.py（420 行）", "讀過就一直留著", 52),
        (BLUE, "你的第 2 句", "", 36),
        (TEAL, "它的回答 ②", "", 36),
        (BROWN, "pytest 的輸出（180 行）", "跑過就一直留著", 52),
        (ORANGE, "你的第 3 句 ← 你只打了這一行", "", 44),
    ]
    y = 112
    for color, label, note, h in rows:
        s.box(60, y, 600, h - 6, label, color=color, size=15.5, r=6,
              fill=tint(color, 0.93))
        if note:
            s.text(680, y + (h - 6) / 2 + 5, note, size=14, color=MUTED)
        y += h

    s.line(44, 112, 44, y - 6, color=INK, width=3)
    s.text(44, y + 22, "這一整包，每問一句就重送一次", size=15, weight=700)

    s.box(40, 580, 920, 84, "", color=RED, fill=tint(RED, 0.95))
    s.icon("triangle-alert", 72, 610, 24, RED, 2.1)
    s.text(116, 616, "兩個棕色的區塊是關鍵", size=17, weight=700, color=RED)
    s.text(116, 644, "檔案和指令輸出讀過就留著。一個開一整天的對話，問「現在幾點」都很貴。",
           size=15)
    return s


def fig_two_budgets():
    """空間和額度是兩回事。"""
    s = Svg(W, 650, "圖 2-1　空間與額度是兩回事")
    s.text(26, 72, "兩個都叫「token 用量」，但滿了之後發生的事完全不同。", size=16, color=MUTED)

    s.card(40, 108, 448, [
        "・**是什麼**：這一包還裝得下多少",
        "・**滿了會怎樣**：自動壓縮，繼續用",
        "・**用什麼看**：/context",
        "・**怎麼解決**：/clear 或 /compact"],
        title="空間（context）", sub="這次對話的容器有多大",
        color=BLUE, icon="layers", size=15.5, lh=30, min_h=236)

    s.card(512, 108, 448, [
        "・**是什麼**：你這段期間還能用多少",
        "・**滿了會怎樣**：**要等重置**才能再用",
        "・**用什麼看**：/usage",
        "・**怎麼解決**：等、換模型、或加購"],
        title="額度（usage）", sub="你的方案這輪還剩多少",
        color=ORANGE, icon="gauge", size=15.5, lh=30, min_h=236)

    s.box(40, 368, 920, 68, "空間滿了不要緊，額度滿了你才會卡住",
          color=INK, size=19, fill="#f4f5f8")

    s.card(40, 456, 920, [
        "・對話內容佔一大半 → 這個對話開太久了，/clear 或 /compact",
        "・CLAUDE.md 佔好幾萬 → 搬一部分到技能裡",
        "・MCP 工具名字佔很多 → /mcp 關掉沒在用的"],
        title="/context 看到什麼就做什麼", color=TEAL, icon="scan-search",
        size=15.5, lh=27)
    return s


def fig_pick_model():
    """換不換模型的決策。"""
    s = Svg(W, 608, "圖 3-1　要不要換模型")
    s.text(26, 72, "預設就是 Opus。只有兩條路會走到「要換」。", size=16, color=MUTED)

    s.stadium(360, 108, 280, 56, "預設：Opus", color=TEAL, size=20,
              fill=tint(TEAL, 0.9))
    s.arrow([(500, 170), (500, 206)], color=MUTED, width=2.4)
    s.diamond(500, 254, 300, 88, "出現額度訊息了嗎？", color=INK, size=17,
              fill="#f4f5f8")

    s.arrow([(348, 254), (250, 254)], color=GREEN, width=2.4,
            label="沒有", label_dy=-12, size=14, label_color=GREEN)
    s.box(40, 222, 206, 64, "不用動", color=GREEN, size=19)

    s.arrow([(652, 254), (752, 254)], color=ORANGE, width=2.4,
            label="有", label_dy=-12, size=14, label_color=ORANGE)
    s.box(756, 206, 204, 96, "看是哪一種\n額度訊息", color=ORANGE, size=17)

    s.arrow([(858, 306), (858, 344)], color=MUTED, width=2.2)
    s.box(512, 348, 448, 72, "「Opus 限制」", color=BLUE, size=17,
          sub="單一模型的額度 → /model sonnet 就能繼續", sub_size=14)
    s.text(736, 436, "或", size=15, weight=700, color=MUTED, anchor="middle")
    s.box(512, 448, 448, 72, "「session／weekly 限制」", color=RED, size=17,
          sub="整個方案的額度 → **換模型沒有用**，等重置或加購", sub_size=14)

    s.card(40, 348, 448, [
        "・幾小時的重構、一次改幾十個檔案",
        "・很難的除錯",
        "・**先試 Opus**：新模型低設定常贏過舊模型最高設定"],
        title="另一條路：這件事真的很難", sub="那就 /model fable（它不是預設）",
        color=PURPLE, icon="zap", size=15, lh=26)
    return s


def fig_effort():
    """五個等級。"""
    s = Svg(W, 620, "圖 4-1　思考等級：調的是「想多久」")
    s.text(26, 72, "模型沒換，換的是它花多少力氣。多數時候不用動。", size=16, color=MUTED)

    levels = [("low", 56, GREY, "問事實、改錯字"), ("medium", 92, BLUE, "日常問答"),
              ("high", 134, TEAL, "寫程式、多步驟"), ("xhigh", 176, ORANGE, "困難除錯"),
              ("max", 218, RED, "錯了很麻煩的事")]
    x = 60
    for name, h, color, use in levels:
        s.box(x, 300 - h, 150, h, "", color=color, fill=tint(color, 0.88), r=8)
        s.text(x + 75, 326, name, size=18, weight=700, color=color, anchor="middle")
        for i, ln in enumerate(wrap(use, 14, 146)):
            s.text(x + 75, 352 + i * 20, ln, size=14, color=MUTED, anchor="middle")
        x += 176

    s.text(60, 100, "想得越久 →", size=14, color=MUTED)
    s.line(60, 300, 940, 300, color=INK, width=2)

    s.card(40, 404, 448, [
        "・/effort high 直接設，/effort 開滑桿",
        "・滑桿裡 **Enter ＝ 存成預設，s ＝ 只有這次**",
        "・句子裡加 **ultrathink**：只有這一回合想久一點"],
        title="怎麼設", color=TEAL, icon="settings", size=15, lh=26)

    s.card(512, 404, 448, [
        "・多數模型預設 high",
        "・**Opus 5.5／Sonnet 5.5／Haiku 5.5 是 medium**",
        "・這幾個模型**關不掉思考**，只能調深淺"],
        title="預設值", color=PURPLE, icon="circle-dot", size=15, lh=26)
    return s


def fig_symbols():
    """三個符號。"""
    s = Svg(W, 660, "圖 5-1　對話框裡的三個符號")
    s.text(26, 72, "這一章最快見效。看完馬上會用。", size=16, color=MUTED)

    items = [
        (BLUE, "@", "指一個檔案", "句子的**任何位置**都能打",
         ["幫我看 **@code/checks.py** 第 40 行", "資料夾也可以：**@lessons/aiot/**"],
         "省掉它自己去找的那一輪，而且指定的是哪一個檔案很明確"),
        (PURPLE, "/", "下指令", "**只有句首**才算",
         ["**/compact** 專心保留圖的部分", "**/model** sonnet"],
         "後面接的字就是參數。打 / 會跳出清單，繼續打字會過濾"),
        (ORANGE, "!", "跑終端機", "句首",
         ["**!git status**", "**!python -m pytest -q tests**"],
         "直接在你的終端機跑，輸出進到對話裡讓它看到"),
    ]
    y = 108
    for color, sym, what, where, examples, why in items:
        s.box(40, y, 92, 92, sym, color=color, size=40, fill=tint(color, 0.9))
        s.text(156, y + 30, what, size=21, weight=700, color=color)
        s.text(156, y + 58, where, size=15, color=MUTED)
        ex_y = y + 22
        for e in examples:
            s.text(430, ex_y, e, size=15)
            ex_y += 26
        s.text(430, y + 84, why, size=13.5, color=MUTED)
        y += 112

    s.card(40, 452, 920, [
        "・/clear 換題目　　・/compact 要留什麼 同題太長　　・/context 還剩多少空間",
        "・/usage 額度與建議　・/model 換模型　　　　　　・/effort 調思考等級",
        "・**壞掉就 /doctor，忘記就 /help**"],
        title="七個最常用的指令", color=TEAL, icon="terminal", size=15.5, lh=28)
    return s


def fig_layers():
    """四層設定什麼時候進到對話裡。"""
    s = Svg(W, 600, "圖 6-1　四層設定，什麼時候進到對話裡")
    s.text(26, 72, "前兩層每一句話都要付，後兩層平常幾乎不佔位子。", size=16, color=MUTED)

    rows = [
        (PURPLE, "CLAUDE.md", "你寫的專案規矩", "每次都在", True, "每次都要遵守的規矩"),
        (PURPLE, "自動記憶", "它自己記的筆記", "每次都在", True, "它從你的糾正裡學到的"),
        (TEAL, ".claude/rules/", "分路徑的規矩", "碰到對應檔案才進來", False,
         "只對某類檔案適用的"),
        (TEAL, "技能", "一整套做法", "名字每次都在，內容用到才載入", False, "整套流程"),
    ]
    y = 112
    for color, name, what, when, always, put in rows:
        s.box(40, y, 220, 76, name, color=color, size=17, sub=what, sub_size=13)
        chip_color = RED if always else GREEN
        s.chip(284, y + 26, when, chip_color, 14)
        s.text(640, y + 46, put, size=15, color=MUTED)
        y += 92

    s.box(40, 492, 920, 88, "", color=ORANGE, fill=tint(ORANGE, 0.95))
    s.icon("circle-alert", 72, 522, 24, ORANGE, 2.1)
    s.text(116, 528, "原則就一句", size=18, weight=700, color=ORANGE)
    s.text(116, 558, "**每次都要用到的放上面兩層，只有某些時候才用到的往下放。**"
                     "CLAUDE.md 官方建議 200 行以內。", size=15.5)
    return s


def fig_skill_load():
    """技能分三階段載入。"""
    s = Svg(W, 600, "圖 7-1　技能平常只有名字在，用到才整份載入")
    s.text(26, 72, "這是它比 CLAUDE.md 省的原因。", size=16, color=MUTED)

    stages = [
        (GREY, "①", "對話一開始", "只有每個技能的\n**名字與說明**", "幾十個 token"),
        (BLUE, "②", "你的需求對上了", "載入整份\n**SKILL.md**", "幾百到幾千"),
        (TEAL, "③", "說明書叫它去看附檔", "那些附檔\n才載入", "用到才算"),
    ]
    x = 40
    for color, no, when, what, cost in stages:
        s.box(x, 112, 286, 160, what, color=color, size=17,
              sub=cost, sub_size=14)
        s.text(x + 143, 100, f"{no}　{when}", size=16, weight=700, color=color,
               anchor="middle")
        if x < 600:
            s.arrow([(x + 294, 192), (x + 326, 192)], color=MUTED, width=2.4)
        x += 334

    s.card(40, 300, 448, [
        "・它是**唯一永遠在那裡**的東西",
        "・也是 Claude 判斷要不要載入的依據",
        "・**關鍵使用時機寫在最前面**"],
        title="description 是最重要的一行", color=ORANGE, icon="pencil",
        size=15, lh=26)

    s.card(512, 300, 448, [
        "・壓縮後每個技能最多 **5,000 token**",
        "・全部技能共用 **25,000 token**",
        "・截斷是從後面切 → **重要的話寫前面**",
        "・/skill-doctor 找出佔空間卻沒用的"],
        title="技能不是免費的", color=RED, icon="triangle-alert",
        size=15, lh=26)

    s.box(40, 512, 920, 64, "同一套做法做到第三次，就該做一個技能",
          color=GREEN, size=19, fill=tint(GREEN, 0.93))
    return s


def fig_plugin():
    """外掛是一包東西。"""
    s = Svg(W, 614, "圖 8-1　外掛是一包東西，裡面常常裝著技能")
    s.text(26, 72, "外掛不是另一種功能，它是打包的方式。", size=16, color=MUTED)

    s.box(40, 108, 420, 300, "", color=PURPLE, fill=tint(PURPLE, 0.96), dash=True)
    s.icon("package", 72, 132, 24, PURPLE, 2.1)
    s.text(112, 138, "一個外掛", size=20, weight=700, color=PURPLE)
    inner = [("技能", TEAL, "叫的時候加前綴：/外掛名:技能名"),
             ("子代理", BLUE, "可以派工作過去的分身"),
             ("hook", ORANGE, "在特定時機自動跑的指令"),
             ("MCP 伺服器", BROWN, "伸手到外面的工具")]
    y = 170
    for name, color, desc in inner:
        s.box(68, y, 364, 50, "", color=color, fill=tint(color, 0.93), r=8)
        s.text(86, y + 31, name, size=16, weight=700, color=color)
        s.text(200, y + 31, desc, size=13.5, color=MUTED)
        y += 58

    s.card(492, 108, 468, [
        "・把技能放 ~/.claude/skills/，每個專案都用得到",
        "・子代理、hook、MCP 也一樣，單獨都能設"],
        title="這四樣單獨都能用", sub="不需要外掛", color=GREEN,
        icon="circle-check", size=15, lh=26)

    s.card(492, 272, 468, [
        "・想**一次裝好幾個**",
        "・想拿**別人做好的一整套**，一個指令裝完、之後能更新",
        "・想**把自己的一套給同事**"],
        title="什麼時候才需要外掛", color=BLUE, icon="users", size=15, lh=26)

    s.box(40, 452, 920, 136, "", color=RED, fill=tint(RED, 0.96))
    s.icon("triangle-alert", 72, 482, 24, RED, 2.1)
    s.text(116, 488, "裝之前要知道的兩件事", size=18, weight=700, color=RED)
    for i, ln in enumerate([
            "**① 啟用的外掛在你每一個對話裡都佔位子**，不是只有用到它的時候。裡面每個技能、",
            "　　子代理、指令的名字和說明，每一回合都在你的包裡。/context 看得到。",
            "**② 外掛跑的東西，是用你的身分跑的。** 它能做的事跟你一樣多——裝之前先看是誰做的。"]):
        s.text(116, 520 + i * 24, ln, size=15)
    return s


def fig_when_to_switch():
    """三個指令怎麼選。"""
    s = Svg(W, 552, "圖 9-1　清空、壓縮、倒帶：怎麼選")
    s.text(26, 72, "判斷只有一句：接下來要做的事，需不需要用到剛才那些東西。",
           size=16, color=MUTED)

    cards = [
        (BLUE, "refresh-cw", "/clear", "清空，全新開始", "**換題目了**",
         ["舊對話對新題目沒幫助", "只會佔位子、花錢、搞混", "先 /rename 再清，之後 /resume"]),
        (TEAL, "layers", "/compact", "換成摘要，繼續同一題", "同一題但太長了",
         ["**一定要講要留什麼**", "/compact 專心保留 OO", "不講它自己猜，常常猜錯"]),
        (ORANGE, "history", "/rewind", "退回先前某一點", "**走錯路了**",
         ["對話和程式碼一起退", "空輸入框連按兩下 Esc 也是", "比叫它改回來可靠"]),
    ]
    x = 40
    for color, icon, cmd, what, when, notes in cards:
        s.box(x, 108, 294, 76, cmd, color=color, size=22, sub=what, sub_size=14)
        s.chip(x + 14, 200, when, color, 14)
        yy = 248
        for n in notes:
            for ln in wrap("・" + n, 15, 266):
                s.text(x + 14, yy, ln, size=15)
                yy += 24
            yy += 4
        x += 314

    s.box(40, 372, 920, 156, "", color=RED, fill=tint(RED, 0.96))
    s.icon("triangle-alert", 72, 402, 24, RED, 2.1)
    s.text(116, 408, "壓縮之後最容易掉的三樣", size=18, weight=700, color=RED)
    for i, ln in enumerate([
            "**① 你們討論出來的結論**　　**② 試過但失敗的方法**　　**③ 第六個以後的檔案**",
            "（壓縮後只會自動重讀最近改過的五個檔案，超過 5,000 token 的只留路徑）",
            "",
            "**所以交接清單一定要寫「試過但失敗的」**——不寫，新對話會把錯的方法再試一次。"]):
        s.text(116, 440 + i * 24, ln, size=15)
    return s


def fig_handoff():
    """Claude Code 和 Codex 共用規矩。"""
    s = Svg(W, 648, "圖 10-1　兩個工具怎麼共用同一份規矩")
    s.text(26, 72, "規矩用 AGENTS.md 共用；進度靠 git 和一份進度檔。", size=16, color=MUTED)

    s.box(60, 112, 240, 70, "Claude Code", color=PURPLE, size=19)
    s.box(700, 112, 240, 70, "Codex", color=GREY, size=19)
    s.box(360, 244, 280, 76, "AGENTS.md", color=TEAL, size=20,
          sub="兩邊都讀得到的共通規矩", sub_size=13.5)
    s.arrow([(304, 162), (486, 238)], color=PURPLE, width=2.4)
    s.arrow([(800, 190), (580, 238)], color=GREY, width=2.4)

    s.box(60, 206, 268, 100, "CLAUDE.md", color=PURPLE, size=18,
          sub="第一行寫 @AGENTS.md\n底下放 Claude 專屬的", sub_size=13.5,
          fill=tint(PURPLE, 0.95))
    s.arrow([(330, 262), (354, 268)], color=PURPLE, width=2.2, dash=True)

    s.card(40, 344, 448, [
        "・只有 AGENTS.md → **讀 AGENTS.md**",
        "・兩個都有 → **只讀 CLAUDE.md**",
        "・CLAUDE.md 裡寫 @AGENTS.md → 兩份都進來"],
        title="Claude Code 什麼時候讀 AGENTS.md", color=BLUE, icon="book-open",
        size=15, lh=26)

    s.card(512, 344, 448, [
        "・改完就 **commit**，不要留在工作目錄裡",
        "・一份 notes/handoff.md，兩邊都用 @ 帶進去",
        "・**分支分開**，不要同時動同一個"],
        title="進度沒有自動機制", sub="靠這三樣", color=ORANGE, icon="git-branch",
        size=15, lh=26)

    s.box(40, 556, 920, 72, "", color=GREEN, fill=tint(GREEN, 0.95))
    s.icon("circle-help", 72, 584, 24, GREEN, 2.1)
    s.text(116, 590, "先問一句：你為什麼要兩個都用？", size=17, weight=700, color=GREEN)
    s.text(116, 616, "如果只是因為額度用完了，/model sonnet 換個模型繼續比較簡單，"
                     "不用維護兩套設定。", size=15)
    return s


def fig_day():
    """一天的工作流。"""
    s = Svg(W, 756, "圖 11-1　一天大概長這樣")
    s.text(26, 72, "照這個順序做，大部分的浪費都避開了。", size=16, color=MUTED)

    steps = [
        (BLUE, "play", "開工", ["cd 到專案資料夾，開 claude",
                                "第一次用這個專案先 /init，再自己改"]),
        (TEAL, "pencil", "做事", ["複雜的先 Shift+Tab 進計畫模式",
                                  "用 @ 指檔案，不要讓它自己找",
                                  "**走偏就 Esc，不要等它做完**"]),
        (ORANGE, "refresh-cw", "換題目", ["/rename 取個名字", "/clear"]),
        (PURPLE, "file-text", "交接或收工", ["叫它寫交接清單（要有「試過但失敗的」）",
                                             "存成 notes/handoff.md，commit 上去"]),
        (GREY, "gauge", "偶爾", ["/usage 看誰在吃額度，有建議就照做",
                                 "/skill-doctor 清掉沒在用的技能"]),
    ]
    y = 108
    for color, icon, title, lines in steps:
        h = 36 + len(lines) * 26
        s.box(40, y, 200, h, title, color=color, size=18)
        s.icon(icon, 60, y + 14, 20, color, 2.1)
        yy = y + 32
        for ln in lines:
            s.text(272, yy, "・" + ln, size=15.5)
            yy += 26
        y += h + 14

    s.box(40, 654, 920, 84, "", color=RED, fill=tint(RED, 0.95))
    s.icon("triangle-alert", 72, 684, 24, RED, 2.1)
    s.text(116, 690, "最常犯的兩個錯", size=18, weight=700, color=RED)
    s.text(116, 720, "**① 捨不得 /clear**（整天的對話，問一句都在重送整天的東西）"
                     "　**② 等它做完才講它做錯了**", size=15.5)
    return s


FIGS = {"fc0-1-map": fig_map, "fc1-1-turn": fig_turn,
        "fc2-1-two-budgets": fig_two_budgets, "fc3-1-pick-model": fig_pick_model,
        "fc4-1-effort": fig_effort, "fc5-1-symbols": fig_symbols,
        "fc6-1-layers": fig_layers, "fc7-1-skill-load": fig_skill_load,
        "fc8-1-plugin": fig_plugin, "fc9-1-when-to-switch": fig_when_to_switch,
        "fc10-1-handoff": fig_handoff, "fc11-1-day": fig_day}

if __name__ == "__main__":
    want = sys.argv[1:] or list(FIGS)
    render({k: FIGS[k]() for k in want if k in FIGS}, OUT)
