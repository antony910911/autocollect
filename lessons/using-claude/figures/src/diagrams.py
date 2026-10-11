"""「把 Claude 用好」的示意圖。執行：python lessons/using-claude/figures/src/diagrams.py [圖名 ...]"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_tools"))
from svgkit import INK, MUTED, Svg, render, tint, wrap  # noqa: E402

OUT = Path(__file__).resolve().parent.parent
CODE = OUT.parent / "code"
BLUE, ORANGE, RED, GREEN, PURPLE, GREY, BROWN, TEAL = ("#2f6fb3", "#d9821e", "#c23b3b", "#2f9e6e",
                                                       "#7b4bb3", "#6b7280", "#8a6d3b", "#1b8a8f")


def _w(s, size):
    return sum(size if ord(ch) > 0x2E80 else size * 0.58 for ch in s)


def _wrap(txt, size, maxw):
    tokens = re.findall(r"[A-Za-z0-9²³·\.\-–—/%‰+×=（）()]+|\s+|.", txt)
    lines, cur = [], ""
    for tok in tokens:
        if tok.isspace() and not cur:
            continue
        if _w(cur + tok, size) > maxw and cur:
            lines.append(cur.rstrip())
            cur = "" if tok.isspace() else tok
        else:
            cur += tok
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def _para(s, x, y, txt, size=14, maxw=400, lh=25, color=INK, weight=400):
    for ln in _wrap(txt.replace("**", ""), size, maxw):
        s.text(x, y, ln, size=size, color=color, weight=weight)
        y += lh
    return y


def fig_landscape():
    s = Svg(1500, 880, "圖 0-1　先看懂全景：你其實在用三樣東西")
    s.text(40, 80, "很多人把這三層混在一起講，結果什麼都講不清楚。分開看就簡單了。",
           size=15.5, color=MUTED)

    layers = [
        ("③ 工具與外掛", "layers", PURPLE, "它伸得到哪裡",
         [("file-text", "讀寫檔案"), ("terminal", "執行指令"), ("github", "GitHub"),
          ("globe", "上網搜尋"), ("puzzle", "自己接的服務 MCP")],
         "決定它能碰到什麼東西"),
        ("② 介面 harness", "workflow", BLUE, "它怎麼工作",
         [("message-square", "claude.ai 聊天"), ("terminal", "Claude Code"),
          ("server", "雲端 session"), ("file-code", "API")],
         "決定它能不能自己動手、能不能跑很久"),
        ("① 模型", "cpu", TEAL, "它有多聰明",
         [("zap", "Haiku 5.5　快又便宜"), ("bot", "Sonnet 5.5　日常主力"),
          ("sparkles", "Opus 5.5　難題用這個"), ("target", "Fable 5.1　最吃力的推理")],
         "決定判斷力的上限"),
    ]
    y = 128
    for name, ic, col, what, items, why in layers:
        h = 196
        s.box(40, y, 352, h, "", color=col, fill=tint(col, 0.92))
        s.icon(ic, 68, y + 34, 34, col, 2.0)
        s.text(112, y + 60, name, size=23, weight=700, color=col)
        s.text(68, y + 96, what, size=15, color=MUTED)
        s.chip(68, y + 120, why.split("、")[0], col, size=13)

        s.box(412, y, 620, h, "", color=col, fill="#ffffff")
        for i, (iic, label) in enumerate(items):
            cx, cy = 440 + (i % 2) * 300, y + 42 + (i // 2) * 44
            s.icon(iic, cx, cy - 15, 20, col, 2.0)
            s.text(cx + 30, cy, label, size=15)

        s.box(1052, y, 408, h, "", color=col, fill=tint(col, 0.96))
        yy = y + h / 2 - (len(wrap(why, 17, 352)) - 1) * 13
        for ln in wrap(why, 17, 352):
            s.text(1080, yy, ln, size=17, weight=700, color=col)
            yy += 26
        y += h + 22

    for yy in (330, 548):
        s.arrow([(216, yy - 4), (216, yy + 22)], color=GREY, width=2.5, both=True)

    s.box(40, 786, 1420, 76, "", color=RED, fill=tint(RED, 0.95))
    s.icon("triangle-alert", 72, 810, 26, RED, 2.1)
    s.text(116, 834, "換模型不會讓它突然碰得到你的檔案；換介面也不會讓它變聰明。"
                     "卡住的時候先問：是哪一層的問題？", size=17, weight=700, color=RED)
    return s


def fig_surfaces():
    s = Svg(1460, 800, "圖 1-1　三個介面，差在「誰動手、能跑多久」")
    cards = [
        ("claude.ai 聊天", BLUE, "瀏覽器或手機 App",
         ["你問、它答", "可以讀你上傳的檔案", "可以用連接器（Gmail、行事曆…）",
          "**它不會自己改你的檔案**"],
         "適合：問問題、寫文件、看資料"),
        ("Claude Code", TEAL, "終端機／桌面 App／IDE",
         ["在**你自己的電腦**上動手", "讀寫檔案、執行指令、跑測試", "改完可以直接 commit",
          "每一步會問你要不要允許"],
         "適合：改程式、整理資料夾、跑分析"),
        ("雲端 session", PURPLE, "claude.ai/code（現在這個）",
         ["在**雲端的容器**裡動手", "repo 是開工時複製進去的", "可以跑很久、你關掉也還在",
          "容器會回收，**沒推上去的東西會不見**"],
         "適合：長時間的工作、不想佔用自己電腦"),
    ]
    for i, (name, col, where, items, good) in enumerate(cards):
        x = 40 + i * 470
        s.box(x, 140, 440, 420, "", color=col, fill=tint(col, 0.95))
        s.text(x + 28, 190, name, size=24, weight=700, color=col)
        s.text(x + 28, 222, where, size=14, color=MUTED)
        s.line(x + 28, 240, x + 412, 240, color=col)
        yy = 282
        for it in items:
            bold = it.startswith("**")
            for ln in _wrap("・" + it.replace("**", ""), 15, 384):
                s.text(x + 28, yy, ln, size=15, weight=700 if bold else 400,
                       color=RED if bold else INK)
                yy += 27
            yy += 10
        s.box(x + 24, 472, 392, 64, "", color=col, fill="#ffffff")
        s.text(x + 44, 510, good, size=15, weight=700)
    s.box(40, 596, 1380, 150, "", color=GREY, fill="#fbfbfd")
    s.text(68, 638, "同一個模型，三種身體", size=18, weight=700)
    _para(s, 68, 676, "三個都可以用同一個模型（例如 Opus 5.5）。差別不在聰不聰明，"
                      "而在**它有沒有手、手伸得到哪裡、能不能一直做下去**。"
                      "你在 claude.ai 問到一半覺得「它怎麼不直接幫我改」，不是它不肯，是那個身體沒有手。",
          size=15, maxw=1330, lh=28)
    return s


def fig_context():
    s = Svg(1460, 840, "圖 2-1　對話的物理限制：為什麼聊久了它會「忘記」")
    s.text(40, 78, "模型一次能看的字數是有上限的，這個上限叫 context window（脈絡視窗）。"
                   "目前的模型大約是 100 萬個 token——很大，但不是無限。", size=15, color=MUTED)
    X, Y, W, H = 60, 150, 1340, 120
    s.parts.append(f'<rect x="{X}" y="{Y}" width="{W}" height="{H}" rx="10" fill="#f3f4f7" '
                   f'stroke="#c7ccd6" stroke-width="2"/>')
    parts = [("系統設定\n與規矩", 0.10, GREY), ("CLAUDE.md\n專案記憶", 0.07, BROWN),
             ("載入的技能", 0.08, PURPLE), ("你丟進來的\n檔案與資料", 0.30, BLUE),
             ("對話歷程\n（越聊越長）", 0.33, ORANGE), ("留給回答\n的空間", 0.12, GREEN)]
    x = X
    for name, frac, col in parts:
        w = W * frac
        s.parts.append(f'<rect x="{x:.1f}" y="{Y}" width="{w:.1f}" height="{H}" '
                       f'fill="{tint(col, 0.72)}" stroke="{col}" stroke-width="2"/>')
        for j, ln in enumerate(name.split("\n")):
            s.text(x + w / 2, Y + 52 + j * 24, ln, size=14, anchor="middle", weight=700)
        x += w
    s.text(60, 310, "一個 token 大約是半個中文字到一個英文單字。整篇論文大概 2–5 萬 token。",
           size=14, color=MUTED)

    s.box(40, 350, 680, 240, "", color=ORANGE, fill=tint(ORANGE, 0.94))
    s.text(68, 392, "會發生什麼事", size=18, weight=700)
    for i, ln in enumerate([
            "・對話越長，留給「新內容」的空間越少",
            "・快滿的時候，系統會自動把前面的對話**摘要**掉",
            "・摘要是壓縮，細節會掉——它可能真的忘記你三小時前說過的事",
            "・丟一個 500 MB 的檔案進來不會變成知識，它只會塞爆空間"]):
        for ln2 in _wrap(ln.replace("**", ""), 15, 630):
            s.text(68, 430 + i * 38, ln2, size=15)

    s.box(756, 350, 664, 240, "", color=GREEN, fill=tint(GREEN, 0.93))
    s.text(784, 392, "所以你該怎麼做", size=18, weight=700)
    for i, ln in enumerate([
            "・**換主題就開新對話**——這是最有效的一招",
            "・重要的規矩寫進 CLAUDE.md，不要靠它記得",
            "・大檔案讓它「用程式讀」，不要整個貼進來",
            "・長工作做到一段落，請它把結論寫成檔案"]):
        s.text(784, 430 + i * 38, ln.replace("**", ""), size=15,
               weight=700 if "**" in ln else 400)

    s.box(40, 626, 1380, 180, "", color=BLUE, fill=tint(BLUE, 0.95))
    s.text(68, 668, "一個很常見的誤會", size=18, weight=700)
    _para(s, 68, 704, "「我上次跟你說過了」——除非是同一個對話，或者寫進了 CLAUDE.md，"
                      "否則它真的不知道。每一個新對話都是從零開始，它沒有跨對話的記憶。"
                      "這不是它偷懶，是設計上就這樣：你的每一次對話是獨立的。",
          size=15, maxw=1330, lh=30)
    return s


def fig_memory():
    s = Svg(1420, 780, "圖 3-1　專案記憶 CLAUDE.md：讓它每次都記得你的規矩")
    s.box(40, 150, 300, 150, "你在這個資料夾\n開一個新對話", color=BLUE, size=17)
    s.box(400, 150, 300, 150, "它自動讀取\nCLAUDE.md", color=BROWN, size=17,
          sub="你不用提醒它", sub_size=13)
    s.box(760, 150, 300, 150, "這些規矩變成\n它的預設行為", color=GREEN, size=17)
    s.arrow([(340, 225), (400, 225)], color=GREY, width=3)
    s.arrow([(700, 225), (760, 225)], color=GREY, width=3)
    s.text(1090, 200, "不用每次重講", size=16, weight=700, color=GREEN)
    s.text(1090, 232, "也不會因為對話太長", size=14, color=MUTED)
    s.text(1090, 258, "而被摘要掉", size=14, color=MUTED)

    s.box(40, 340, 660, 390, "", color=BROWN, fill=tint(BROWN, 0.94))
    s.text(68, 382, "該寫進去的", size=18, weight=700)
    for i, ln in enumerate([
            "・用什麼語言回答、用什麼術語",
            "・這個專案的資料夾怎麼擺、檔案命名規則",
            "・測試怎麼跑、程式怎麼執行",
            "・推到哪個分支、commit 訊息怎麼寫",
            "・你的研究主題背景（菌株、設備、限制）",
            "・踩過的坑（「不要用 X，因為會 Y」）"]):
        s.text(68, 422 + i * 42, ln, size=15)
    s.text(68, 690, "重點是「會重複發生」的事", size=16, weight=700, color=BROWN)

    s.box(740, 340, 640, 390, "", color=GREY, fill="#fbfbfd")
    s.text(768, 382, "不該寫進去的", size=18, weight=700)
    for i, ln in enumerate([
            "・這一次才要做的事（直接講就好）",
            "・一大段貼來的資料（放成檔案）",
            "・密碼、金鑰（這個檔會進版本庫！）",
            "・寫到幾千字（它每次都要讀，會吃空間）"]):
        s.text(768, 422 + i * 42, ln, size=15)
    s.text(768, 606, "放哪裡", size=17, weight=700)
    s.text(768, 642, "專案根目錄的 CLAUDE.md（跟著版本庫走，", size=14.5)
    s.text(768, 668, "團隊共用）；個人偏好放 ~/.claude/CLAUDE.md", size=14.5)
    s.text(768, 700, "想看實例：這個 repo 的 CLAUDE.md 就是", size=14.5, weight=700, color=BROWN)
    return s


def fig_skills():
    s = Svg(1460, 820, "圖 4-1　技能（Skill）：把「做法」封裝起來重複用")
    s.text(40, 78, "技能就是一份寫好的操作說明書。它平常不佔空間，只有在需要的時候才被打開。",
           size=15, color=MUTED)
    steps = [
        ("開對話時", GREY, "只讀每個技能的\n**名字**和**一句話描述**", "很省空間"),
        ("你提出需求", BLUE, "它比對描述，判斷\n「這件事有沒有現成做法」", "自動判斷"),
        ("命中了", PURPLE, "才把整份說明書\n讀進來照著做", "這時才佔空間"),
        ("沒命中", GREEN, "用它原本的做法", "不會變笨"),
    ]
    for i, (when, col, what, note) in enumerate(steps):
        x = 40 + i * 358
        s.box(x, 150, 330, 200, "", color=col, fill=tint(col, 0.95))
        s.text(x + 165, 192, when, size=19, weight=700, color=col, anchor="middle")
        yy = 238
        for ln in what.split("\n"):
            s.text(x + 165, yy, ln.replace("**", ""), size=15, anchor="middle")
            yy += 28
        s.text(x + 165, 320, note, size=14, color=col, anchor="middle", weight=700)
        if i < 3:
            s.arrow([(x + 332, 250), (x + 356, 250)], color=GREY, width=2.5)

    s.box(40, 396, 690, 350, "", color=PURPLE, fill=tint(PURPLE, 0.95))
    s.text(68, 438, "一個技能長什麼樣子", size=18, weight=700)
    s.text(68, 474, "一個資料夾、一個 SKILL.md，開頭幾行寫名字和描述：", size=15)
    code = ["---", "name: 週報格式", "description: 要寫生質能週報、或是要把", "  資料整理成每個事實都附來源的報告時用",
            "---", "", "（下面寫清楚步驟、格式、範例、常見錯誤）"]
    for i, ln in enumerate(code):
        s.text(92, 516 + i * 28, ln, size=14, color=INK if not ln.startswith("（") else MUTED)
    s.text(68, 726, "描述寫得好不好，決定它會不會在對的時候想起這個技能。", size=15,
           weight=700, color=PURPLE)

    s.box(766, 396, 654, 350, "", color=GREEN, fill=tint(GREEN, 0.95))
    s.text(794, 438, "什麼時候值得做一個技能", size=18, weight=700)
    for i, ln in enumerate([
            "・同樣的工作**做過三次以上**",
            "・每次都要重講一遍規矩和格式",
            "・步驟多、順序不能錯",
            "・有「別人也會用到」的價值"]):
        s.text(794, 480 + i * 40, ln.replace("**", ""), size=15)
    s.text(794, 660, "怎麼做：直接叫它幫你做", size=17, weight=700)
    s.text(794, 696, "「把我們剛才整理週報的流程寫成一個技能」", size=15, color=PURPLE)
    s.text(794, 726, "——它會自己建資料夾、寫 SKILL.md。", size=14.5, color=MUTED)
    return s


def fig_connect():
    s = Svg(1460, 860, "圖 5-1　讓它伸手到外面：連接器、MCP、外掛")
    s.box(600, 140, 260, 110, "Claude", color=TEAL, size=24)
    outs = [
        (40, 330, "連接器 Connector", BLUE, "claude.ai 設定裡一鍵連",
         ["Gmail、Google 行事曆", "Google Drive、Docs", "GitHub", "Slack、Notion…"],
         "最簡單，不用寫程式"),
        (400, 330, "MCP 伺服器", PURPLE, "自己接的服務",
         ["你實驗室的資料庫", "儀器的 API", "內部系統", "別人寫好的 MCP"],
         "要設定，但什麼都能接"),
        (760, 330, "外掛 Plugin", ORANGE, "一包打包好的東西",
         ["技能 ＋ 指令", "hooks（自動動作）", "子代理人", "MCP 設定"],
         "團隊共用設定的方式"),
        (1120, 330, "內建工具", GREY, "本來就有",
         ["讀寫檔案", "執行指令", "上網搜尋", "跑程式"],
         "不用設定"),
    ]
    for x, y, name, col, sub, items, why in outs:
        s.box(x, y, 300, 290, "", color=col, fill=tint(col, 0.95))
        s.text(x + 24, y + 44, name, size=19, weight=700, color=col)
        s.text(x + 24, y + 72, sub, size=13.5, color=MUTED)
        s.line(x + 24, y + 86, x + 276, y + 86, color=col)
        for i, it in enumerate(items):
            s.text(x + 24, y + 122 + i * 30, "・" + it, size=14.5)
        s.text(x + 24, y + 268, why, size=14, weight=700, color=col)
        s.arrow([(730, 254), (x + 150, y - 4)], color=col, width=2.5)

    s.box(40, 668, 1380, 160, "", color=RED, fill=tint(RED, 0.95))
    s.text(68, 710, "兩個你一定會遇到的狀況", size=18, weight=700)
    _para(s, 68, 746, "① **它說連不到某個網站**：雲端 session 的對外連線是有白名單的，"
                      "不是它不想連。你可以在環境設定裡開放特定網域。", size=15, maxw=1330, lh=28)
    _para(s, 68, 796, "② **它說找不到你的 repo**：雲端 session 只看得到被加進來的那幾個 repo，"
                      "其他的要先授權。", size=15, maxw=1330, lh=28)
    return s


def fig_pipeline():
    s = Svg(1460, 840, "圖 6-1　一句話怎麼變成 Folio 上的一頁：這個 repo 的實際管線")
    s.text(40, 78, "這不是示意圖——下面每一步都是這份教材真的走過的流程。", size=15, color=MUTED)
    steps = [
        ("你說一句話", BLUE, "「幫我把比對結果\n畫成圖放進第 17 章」"),
        ("它讀專案記憶", BROWN, "CLAUDE.md 告訴它：\n繁體中文、數字要算出來、\n推哪個分支"),
        ("寫程式算數字", PURPLE, "code/case_rt.py\n→ case_rt.json"),
        ("畫圖", TEAL, "figures/src/diagrams.py\n→ PNG，並且用眼睛檢查"),
        ("檢查版面", GREEN, "dry-run ＋ 重疊檢查\n＋ 跑測試"),
        ("推上分支", ORANGE, "git commit / push\n（不開 PR，除非你說要）"),
        ("CI 接手", RED, "核對每個 DOI\n→ 上傳到 Folio"),
    ]
    X, W, GAP = 40, 180, 16
    for i, (name, col, what) in enumerate(steps):
        x = X + i * (W + GAP)
        s.box(x, 150, W, 230, "", color=col, fill=tint(col, 0.94))
        s.text(x + W / 2, 192, f"{i + 1}", size=22, weight=700, color=col, anchor="middle")
        s.text(x + W / 2, 224, name, size=16, weight=700, anchor="middle")
        yy = 262
        for ln in what.split("\n"):
            for ln2 in _wrap(ln, 13, W - 24):
                s.text(x + W / 2, yy, ln2, size=13, anchor="middle", color=MUTED)
                yy += 22
        if i < len(steps) - 1:
            s.arrow([(x + W + 1, 265), (x + W + GAP - 1, 265)], color=GREY, width=2.5)

    s.box(40, 420, 690, 180, "", color=GREEN, fill=tint(GREEN, 0.94))
    s.text(68, 462, "為什麼要繞這麼一大圈", size=18, weight=700)
    _para(s, 68, 498, "因為每一步都留下可以回頭查的東西：數字有程式、圖有原始碼、"
                      "文獻有 CI 核對、改動有 commit。三個月後你想問「這個數字哪來的」，"
                      "答案在 repo 裡，不在聊天記錄裡。", size=15, maxw=640, lh=28)

    s.box(756, 420, 664, 180, "", color=RED, fill=tint(RED, 0.95))
    s.text(784, 462, "最關鍵的一件事：推上去", size=18, weight=700)
    _para(s, 784, 498, "雲端 session 的容器會被回收。**沒有 commit 並 push 的東西會消失**，"
                       "聊天記錄留著也沒用。所以每做完一段就推一次。", size=15, maxw=610, lh=28)

    s.box(40, 636, 1380, 170, "", color=BLUE, fill=tint(BLUE, 0.95))
    s.text(68, 678, "你要做的事其實只有三件", size=18, weight=700)
    for i, ln in enumerate([
            "① 把規矩寫進 CLAUDE.md（一次性，之後都不用再講）",
            "② 講清楚你要什麼，以及「什麼算做完」",
            "③ 收到結果時檢查：數字對嗎？圖看得懂嗎？它有沒有自己亂加東西？"]):
        s.text(68, 716 + i * 32, ln, size=15)
    return s


def fig_automation():
    s = Svg(1420, 880, "圖 7-1　三種自動化，怎麼選")
    s.box(530, 130, 360, 90, "你想自動做什麼？", color=INK, size=19, fill="#ffffff")
    opts = [
        (40, 300, "固定時間做", PURPLE, "每週一早上整理週報",
         ["用 Routine（排程）", "可以指定「每次開新對話」", "或「回到同一個對話繼續」"],
         "像鬧鐘：時間到就觸發"),
        (420, 300, "有事發生才做", ORANGE, "PR 的 CI 紅了就修",
         ["訂閱 PR 事件", "它會被事件叫醒", "不用一直輪詢"],
         "像門鈴：有人按才回應"),
        (800, 300, "盯著直到完成", TEAL, "等一個很久的運算跑完",
         ["背景執行＋通知", "或 /loop 自己定節奏", "做完才回來找你"],
         "像計時器：盯著某件事"),
        (1180, 300, "其實不用自動", GREY, "只做一次的事",
         ["直接叫它做就好", "不要為了一次性的事", "去架排程"],
         "最常見的正確答案"),
    ]
    for x, y, name, col, example, items, why in opts:
        w = 340 if x < 1180 else 200
        s.box(x, y, w, 330, "", color=col, fill=tint(col, 0.95))
        s.text(x + 24, y + 46, name, size=19, weight=700, color=col)
        for ln in _wrap("例：" + example, 13.5, w - 48):
            s.text(x + 24, y + 76, ln, size=13.5, color=MUTED)
        s.line(x + 24, y + 92, x + w - 24, y + 92, color=col)
        yy = y + 126
        for it in items:
            for ln in _wrap("・" + it, 14, w - 48):
                s.text(x + 24, yy, ln, size=14)
                yy += 24
            yy += 8
        for ln in _wrap(why, 14, w - 48):
            s.text(x + 24, y + 290, ln, size=14, weight=700, color=col)
        s.arrow([(710, 224), (x + w / 2, y - 4)], color=col, width=2.2)

    s.box(40, 666, 1340, 180, "", color=RED, fill=tint(RED, 0.95))
    s.text(68, 708, "排程最容易出的兩個錯", size=18, weight=700)
    _para(s, 68, 744, "① **為了等三分鐘而設排程**。背景工作做完會自己通知，不用排程去問。"
                      "排程是給「它自己不會通知你」的外部事情用的。", size=15, maxw=1290, lh=28)
    _para(s, 68, 794, "② **排程做了會動到外面世界的事**（寄信、發布、刪東西）。"
                      "排程觸發時沒有人在看，所以這類動作要先問過你，不要讓它自己決定。",
          size=15, maxw=1290, lh=28)
    return s


def fig_opensource():
    s = Svg(1420, 900, "圖 8-1　GitHub 上的東西要不要用：五個問題")
    s.text(40, 78, "開源不等於可以直接拿。這五個問題照順序問，任何一關不過就先停下來。",
           size=15, color=MUTED)
    qs = [
        ("① 它在做什麼？", BLUE, "看 README 和範例",
         "叫 Claude 讀整個 repo 幫你講重點——這件事它很擅長，比你自己翻快很多"),
        ("② 還活著嗎？", TEAL, "最後一次更新、issue 有沒有人回",
         "兩年沒更新的科學套件通常裝不起來（相依套件早就變了）"),
        ("③ 授權能用嗎？", ORANGE, "看 LICENSE 檔",
         "MIT／BSD／Apache：幾乎都能用。GPL：你的程式可能也要開源。沒有 LICENSE：預設不可用"),
        ("④ 裝得起來嗎？", PURPLE, "先在乾淨環境試裝",
         "讓 Claude 開一個新資料夾試，不要直接裝進你的主環境"),
        ("⑤ 結果可信嗎？", RED, "用你已知答案的資料試一次",
         "**這一步不能跳。**拿一組你知道答案的資料跑，對得上才能用在真資料上"),
    ]
    y = 150
    for name, col, how, why in qs:
        s.box(40, y, 300, 120, name, color=col, size=19)
        s.box(360, y, 360, 120, "", color=col, fill="#ffffff")
        yy = y + 46
        for ln in _wrap(how, 15, 320):
            s.text(384, yy, ln, size=15)
            yy += 26
        s.box(740, y, 640, 120, "", color=col, fill=tint(col, 0.95))
        yy = y + 46
        for ln in _wrap(why.replace("**", ""), 14.5, 596):
            s.text(764, yy, ln, size=14.5)
            yy += 26
        y += 136

    s.box(40, 832, 1340, 0)
    s.text(40, 862, "小訣竅：把 repo 網址丟給 Claude，叫它「幫我評估這五點」。"
                    "它會把 README、LICENSE、最後更新時間一次看完——這是它最省你時間的用法之一。",
           size=15.5, weight=700, color=GREEN)
    return s


def fig_ladder():
    d = json.loads((CODE / "models.json").read_text("utf-8"))
    s = Svg(1480, 900, "圖 9-1　要不要自己訓練模型？先爬這四階")
    s.text(40, 78, "「訓練自己的模型」通常不是你要的答案。先從第一階往上爬，"
                   "大多數研究者在第二階就解決問題了。", size=15, color=MUTED)
    cols = [GREEN, TEAL, ORANGE, RED]
    H = 130
    for i, (st, col) in enumerate(zip(d["ladder"], cols)):
        y = 600 - i * (H + 16)
        x = 40 + i * 40
        w = 1380 - i * 40
        s.box(x, y, w, H, "", color=col, fill=tint(col, 0.93))
        s.text(x + 28, y + 46, st["step"], size=20, weight=700, color=col)
        s.text(x + 28, y + 76, st["en"], size=13, color=MUTED)
        cells = [("要多少資料", st["data"]), ("成本", st["cost"]),
                 ("要多久", st["time"]), ("資料更新時", st["keeps_up"])]
        cx = x + 330
        for label, val in cells:
            s.text(cx, y + 44, label, size=12.5, color=MUTED)
            for j, ln in enumerate(_wrap(val, 14, 230)):
                s.text(cx, y + 70 + j * 22, ln, size=14)
            cx += 250
        for j, ln in enumerate(_wrap("什麼時候用：" + st["use"].replace("**", ""), 14, w - 360)):
            s.text(x + 330, y + 118 + j * 22, ln, size=14, weight=700, color=col)

    s.box(40, 752, 1400, 124, "", color=PURPLE, fill=tint(PURPLE, 0.95))
    s.text(68, 794, "給你的結論", size=18, weight=700)
    _para(s, 68, 832, "你要的多半是**第二階（RAG）**：把你的文獻、實驗紀錄、SOP 建成一個可以檢索的庫，"
                      "需要的時候讓它去查。資料一更新就生效，不用重新訓練，成本是微調的幾十分之一。",
          size=15, maxw=1350, lh=28)
    return s


def fig_workflow():
    s = Svg(1460, 900, "圖 10-1　把這些組起來：一個研究者的實際配置")
    s.text(40, 78, "以這個 repo 為例——紅酵母專案從定序資料到 Folio 教材的整套配置。",
           size=15, color=MUTED)
    blocks = [
        (40, 150, 420, 230, "① 一個 repo 當家", BROWN,
         ["程式、資料、教材、設定都在裡面", "CLAUDE.md 寫規矩", "code/ 放算數字的程式",
          "figures/ 放畫圖的程式"],
         "所有東西有一個家"),
        (520, 150, 420, 230, "② 技能處理重複的事", PURPLE,
         ["「寫一章教材」的標準流程", "「跑一次基因體比對」", "「產週報」",
          "做過三次就包成技能"],
         "不用每次重講"),
        (1000, 150, 420, 230, "③ 連接器接外面", BLUE,
         ["GitHub：程式與 CI", "Folio：教材上架", "Gmail／行事曆：提醒",
          "需要時再加"],
         "伸得到該伸的地方"),
        (40, 420, 420, 230, "④ CI 當守門員", GREEN,
         ["自動核對每個 DOI", "自動上傳到 Folio", "錯了就擋下來",
          "不靠人記得"],
         "品質不靠自律"),
        (520, 420, 420, 230, "⑤ 排程做週期性的事", ORANGE,
         ["每週收集資料、產週報", "PR 有動靜時叫醒它", "長工作背景跑",
          "一次性的事不要排程"],
         "該自動的才自動"),
        (1000, 420, 420, 230, "⑥ 你負責判斷", RED,
         ["數字對不對", "結論有沒有過度延伸", "哪些是推論、哪些是量測",
          "**這一項不能外包**"],
         "它很快，但不負責"),
    ]
    for x, y, w, h, name, col, items, tag in blocks:
        s.box(x, y, w, h, "", color=col, fill=tint(col, 0.95))
        s.text(x + 24, y + 46, name, size=19, weight=700, color=col)
        s.line(x + 24, y + 62, x + w - 24, y + 62, color=col)
        yy = y + 96
        for it in items:
            for ln in _wrap("・" + it.replace("**", ""), 14.5, w - 48):
                s.text(x + 24, yy, ln, size=14.5,
                       weight=700 if "**" in it else 400, color=RED if "**" in it else INK)
                yy += 25
        s.text(x + 24, y + 212, tag, size=15, weight=700, color=col)

    s.box(40, 692, 1380, 180, "", color=TEAL, fill=tint(TEAL, 0.94))
    s.text(68, 734, "一句話總結這十章", size=19, weight=700)
    _para(s, 68, 772, "把「會重複的事」交給設定（CLAUDE.md、技能、CI、排程），"
                      "把「每次都不一樣的判斷」留給自己。配置做得越好，你花在重講規矩上的時間越少，"
                      "花在真正的研究判斷上的時間越多。", size=16, maxw=1330, lh=30)
    s.text(68, 860, "從哪裡開始：先寫 CLAUDE.md。十分鐘，效果最大。", size=16, weight=700, color=RED)
    return s


FIGS2 = {"fig6-1-pipeline": fig_pipeline, "fig7-1-automation": fig_automation,
         "fig8-1-opensource": fig_opensource, "fig9-1-ladder": fig_ladder,
         "fig10-1-workflow": fig_workflow}

def fig_artifact_types():
    s = Svg(1460, 930, "圖 11-1　五種「成品」，以及設計系統為什麼站在中間")
    s.text(40, 78, "Claude 不是只會回你一段文字。它可以直接做出五種成品，"
                   "其中「設計系統」比較特別——它本身不是成品，是「給其他成品看的規格書」。",
           size=15, color=MUTED)

    types = [
        (40, 170, "Design", PURPLE, "設計畫布", "網站、登陸頁、App 畫面、\n海報、社群圖；\n一塊可以擺很多張稿的畫布"),
        (330, 170, "Slides", BLUE, "簡報", "16:9 投影片，\n可以播、可以下載"),
        (620, 170, "Dashboard", TEAL, "儀表板", "圖表、數字、表格；\n每個數字都標來源"),
        (910, 170, "Docs", BROWN, "文件", "可以一起編輯、\n留言的活文件"),
    ]
    for x, y, name, col, sub, what in types:
        s.box(x, y, 260, 230, "", color=col, fill=tint(col, 0.94))
        s.text(x + 24, y + 46, name, size=20, weight=700, color=col)
        s.text(x + 24, y + 72, sub, size=14, color=MUTED)
        s.line(x + 24, y + 86, x + 236, y + 86, color=col)
        yy = y + 118
        for ln in what.split("\n"):
            s.text(x + 24, yy, ln, size=13.5)
            yy += 24

    s.box(40, 470, 1140, 236, "", color=ORANGE, fill=tint(ORANGE, 0.92))
    s.text(68, 516, "Design System　設計系統", size=22, weight=700, color=ORANGE)
    s.text(68, 548, "一份給機器讀的品牌規格書", size=14.5, color=MUTED)
    for i, ln in enumerate([
            "・**色彩 token**：每個顏色有名字、深淺兩種值、以及「什麼時候用」的說明",
            "・**字體與字級**、**間距**、**圓角**、**陰影**",
            "・**元件**（按鈕、卡片⋯）的規範與活的預覽",
            "・**README**：寫清楚語氣、用色規則、禁止事項"]):
        s.text(68, 594 + i * 30, ln.replace("**", ""), size=14.5)
    for x in (170, 460, 750, 1040):
        s.arrow([(x, 466), (x, 404)], color=ORANGE, width=2.5)
    s.text(1210, 510, "它不是拿來看的，", size=15, weight=700, color=ORANGE)
    s.text(1210, 540, "是拿來「被引用」的。", size=15, weight=700, color=ORANGE)
    s.text(1210, 580, "做投影片、做設計稿時，", size=14, color=MUTED)
    s.text(1210, 608, "它會先讀這一份，", size=14, color=MUTED)
    s.text(1210, 636, "再決定用什麼顏色、字體。", size=14, color=MUTED)

    s.box(40, 742, 1380, 160, "", color=GREEN, fill=tint(GREEN, 0.94))
    s.text(68, 786, "你現在的狀況", size=18, weight=700)
    _para(s, 68, 824, "你的帳號裡已經有兩個設計系統，其中一個叫 **Beamup**，"
                      "而且是從你的 app 原始碼（github:antony910911/thought\\_task\\_entry）建出來的。"
                      "但**沒有設成預設**——所以每次要做設計稿時，它不知道要用哪一套。設一下就好。",
          size=15, maxw=1330, lh=30)
    return s


def fig_design_code():
    s = Svg(1460, 900, "圖 11-3　設計系統和程式碼：三個方向")
    s.text(40, 78, "這是你問的「design 能不能跟 code 一起用」的答案——可以，而且有三個方向。",
           size=15, color=MUTED)

    s.box(120, 190, 330, 150, "你的程式碼", color=BLUE, size=22,
          sub="thought\\_task\\_entry\ncss/style.css、js/themes.js", sub_size=13)
    s.box(1010, 190, 330, 150, "設計系統", color=ORANGE, size=22,
          sub="Beamup\n18 色 ＋ 9 字級 ＋ 間距圓角", sub_size=13)

    s.arrow([(450, 230), (730, 196), (1010, 230)], color=GREEN, width=3.5, curve=True)
    s.text(730, 164, "① 從程式碼建系統　✓ 已完成", size=17, weight=700, color=GREEN,
           anchor="middle")
    s.arrow([(1010, 300), (730, 336), (450, 300)], color=RED, width=3.5, curve=True)
    s.text(730, 372, "② 把 token 推回程式碼　← 你還沒做這一步", size=17, weight=700,
           color=RED, anchor="middle")

    s.box(40, 420, 440, 230, "", color=GREEN, fill=tint(GREEN, 0.94))
    s.text(68, 462, "① 從程式碼建系統", size=18, weight=700, color=GREEN)
    _para(s, 68, 498, "把 repo 給它，它讀出你現在實際用的顏色、字級、間距，"
                      "整理成一份有名字、有說明、有深淺模式的規格。",
          size=14, maxw=384, lh=26)
    s.text(68, 600, "你的 Beamup 就是這樣來的。", size=14.5, weight=700, color=GREEN)
    s.text(68, 628, "裡面標 proposed 的是「建議改成這樣」。", size=13.5, color=MUTED)

    s.box(510, 420, 440, 230, "", color=RED, fill=tint(RED, 0.94))
    s.text(538, 462, "② 把 token 推回程式碼", size=18, weight=700, color=RED)
    _para(s, 538, 498, "把那 18 個顏色寫成 CSS 變數，然後把程式裡寫死的色碼"
                       "一個一個換成變數。", size=14, maxw=384, lh=26)
    s.text(538, 574, "做完之後：換色只要改一個檔案，", size=14.5, weight=700, color=RED)
    s.text(538, 602, "深色模式自動跟上，", size=14.5, weight=700, color=RED)
    s.text(538, 630, "而且對比度是驗算過的。", size=14.5, weight=700, color=RED)

    s.box(980, 420, 440, 230, "", color=PURPLE, fill=tint(PURPLE, 0.94))
    s.text(1008, 462, "③ 新畫面先畫稿再實作", size=18, weight=700, color=PURPLE)
    _para(s, 1008, 498, "要加新功能時，先用 Design 畫布做幾個版本，挑一個，"
                        "再叫它照著實作。", size=14, maxw=384, lh=26)
    s.text(1008, 574, "比直接寫程式快，", size=14.5, weight=700, color=PURPLE)
    s.text(1008, 602, "因為改一張稿比改一版 code 便宜。", size=14.5, weight=700, color=PURPLE)

    s.box(40, 690, 1380, 180, "", color=TEAL, fill=tint(TEAL, 0.94))
    s.text(68, 732, "第 ② 步具體怎麼講", size=18, weight=700)
    code = ['「讀我的 Beamup 設計系統，把 color、spacing、radius 的 token 寫成',
            ' css/tokens.css 的 CSS 變數（含 prefers-color-scheme 深色），',
            ' 然後把 css/style.css 裡寫死的色碼換成對應的變數。',
            ' 不要改任何版面與行為，只換顏色的來源。改完給我 diff。」']
    for i, ln in enumerate(code):
        s.text(68, 772 + i * 28, ln, size=14.5, color=INK)
    return s


FIGS1 = {"fig0-1-landscape": fig_landscape, "fig1-1-surfaces": fig_surfaces,
         "fig2-1-context": fig_context, "fig3-1-memory": fig_memory,
         "fig4-1-skills": fig_skills, "fig5-1-connect": fig_connect}
FIGS3 = {"fig11-1-artifact-types": fig_artifact_types,
         "fig11-3-design-code": fig_design_code}
FIGS = {**FIGS1, **FIGS2, **FIGS3}

if __name__ == "__main__":
    want = sys.argv[1:] or list(FIGS)
    render({k: FIGS[k]() for k in want if k in FIGS}, OUT)
