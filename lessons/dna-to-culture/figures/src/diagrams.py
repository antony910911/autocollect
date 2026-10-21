"""「從 DNA 到最適培養」的概念圖與代謝流量圖。執行：python lessons/dna-to-culture/figures/src/diagrams.py [圖名 ...]"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_tools"))
from svgkit import C, INK, MUTED, Svg, render, tint, wrap  # noqa: E402

OUT = Path(__file__).resolve().parent.parent
CODE = OUT.parent / "code"
BLUE, ORANGE, RED, GREEN, PURPLE, GREY, BROWN, TEAL = ("#2f6fb3", "#d47c18", "#c23b3b", "#2f9e6e", "#7b4bb3",
                                                       "#6b7280", "#8a6d3b", "#1b8a8f")


def fig0():
    s = Svg(1460, 600, "學習地圖：從一段 DNA 序列，到看得見的最適培養條件")
    steps = [
        ("DNA 序列", "定序、組裝\n品質檢查", BROWN, "2"),
        ("功能註解", "這株菌有\n哪些基因、酵素", ORANGE, "2"),
        ("代謝模型 GEM", "基因 → 反應\n→ 代謝網路", PURPLE, "3"),
        ("FBA", "給定環境\n算出代謝流量", BLUE, "4"),
        ("動態模擬 dFBA", "加上時間：\n生長曲線與階段", TEAL, "5–6"),
        ("最適化", "分階段調參數\n貝氏最適化", GREEN, "6–8"),
        ("視覺化介面", "拉動參數\n立刻看到變化", RED, "9"),
        ("操作建議", "換算成實驗室\n真的做得出來的事", "#1b8a8f", "10"),
        ("數據餵回模型", "校正參數\n模型越用越準", "#8a6d3b", "11"),
        ("換成你的菌", "酵母菌、基改菌株\n要改什麼", "#b8860b", "15–16"),
    ]
    x = 24
    for i, (h, b, c, ch) in enumerate(steps):
        s.box(x, 90, 130, 70, h, color=c, size=14.5)
        s.box(x, 170, 130, 86, "", color=c, fill="#ffffff")
        s.text(x + 65, 213, b, size=13, anchor="middle-v")
        s.pill(x + 65, 284, f"第 {ch} 章", c, size=12.5)
        if i < len(steps) - 1:
            s.arrow([(x + 132, 125), (x + 144, 125)], color=c)
        x += 143
    s.box(24, 330, 1412, 112, "", color=GREY, fill="#fbfbfd")
    s.text(48, 364, "實驗室資料一路回饋（第 5、7、8、11 章）", size=17, weight=700)
    s.text(48, 396, "生長曲線、基質與產物濃度、溶氧、pH、溫度 → 校正吸收速率、找出溫度與 pH 的最適範圍、檢查模型預測對不對。", size=15)
    s.text(48, 424, "模型負責「縮小範圍、解釋原因」；實驗負責「驗證、提供模型算不出來的參數」。兩者交替，越轉越準。", size=15)
    s.box(24, 470, 452, 100, "第 1 章", color=BROWN, size=15, sub="先回答你的問題：\n能做到什麼、做不到什麼", sub_size=15,
          fill="#ffffff")
    s.box(504, 470, 452, 100, "第 12 章", color=GREEN, size=15, sub="怎麼開始：步驟、分工\n你要收集什麼、AI 能幫什麼", sub_size=15,
          fill="#ffffff")
    s.box(984, 470, 452, 100, "第 13–14 章", color=PURPLE, size=15, sub="國內外文獻與資源\n更創新的做法", sub_size=15,
          fill="#ffffff")
    return s


def fig1():
    s = Svg(1200, 640, "圖 1-1　DNA 告訴你「能做什麼」，培養條件決定「實際做什麼」")
    rows = [
        ("基因體（DNA）", "有哪些基因、酵素、代謝路徑\n能不能用某種碳源、能不能固氮、有沒有呼吸鏈", BROWN, "註解工具＋資料庫就能回答", GREEN),
        ("代謝模型（GEM）", "在某個培養基、某個供氧下\n最多能長多快、會分泌什麼", PURPLE, "FBA 可以算，但要實驗校正", ORANGE),
        ("基因表現與調控", "哪些基因此刻真的打開？\n（轉錄、轉譯、酵素活性）", BLUE, "DNA 看不出來，要轉錄體等資料", RED),
        ("溫度、pH、鹽度", "最適溫度、pH、耐鹽、\n遲滯期長短、抑制濃度", TEAL, "GEM 算不出來，要實驗或經驗模型", RED),
    ]
    y = 80
    for i, (h, b, c, verdict, vc) in enumerate(rows):
        s.box(24, y, 220, 104, h, color=c, size=18)
        s.box(260, y, 540, 104, "", color=c, fill="#ffffff")
        s.text(280, y + 44, b.split("\n")[0], size=16)
        s.text(280, y + 74, b.split("\n")[1], size=15, color=MUTED)
        s.box(816, y, 360, 104, verdict, color=vc, size=16)
        y += 120
    s.text(24, 612, "越往下越接近「實際培養會怎樣」，也越需要實驗資料。這就是為什麼只丟 DNA 進去，得不到完整的最適培養條件。",
           size=15, color=MUTED)
    return s


def fig2():
    s = Svg(1200, 660, "圖 2-1　從定序資料到功能註解：每一步用什麼工具、得到什麼")
    steps = [
        ("① 品質檢查", "FastQC\nfastp", "去掉低品質讀段", GREY),
        ("② 組裝", "SPAdes（短讀）\nFlye（長讀）", "得到 contigs", BROWN),
        ("③ 組裝品質", "CheckM2\nQUAST", "完整度 > 95%\n汙染 < 5%", ORANGE),
        ("④ 物種鑑定", "GTDB-Tk\n16S＋BLAST", "知道是誰\n找近緣種資料", BLUE),
        ("⑤ 基因預測與註解", "Bakta / Prokka\nRAST", "基因位置\n初步功能", PURPLE),
    ]
    x = 24
    for i, (h, tools, out, c) in enumerate(steps):
        s.box(x, 76, 214, 56, h, color=c, size=16)
        s.box(x, 140, 214, 76, "", color=c, fill="#ffffff")
        s.text(x + 107, 178, tools, size=14, anchor="middle-v")
        s.box(x, 224, 214, 62, out, color=c, size=14, weight=400, fill=tint(c, 0.93))
        if i < len(steps) - 1:
            s.arrow([(x + 216, 104), (x + 232, 104)], color=c)
        x += 232
    s.arrow([(1100, 290), (1100, 330)], color=PURPLE)
    s.text(24, 340, "⑥ 功能深入註解（同一份基因序列，丟進不同資料庫，各回答一個問題）", size=17, weight=700)
    dbs = [
        ("eggNOG-mapper", "直系同源群、\nGO、KEGG 編號", ORANGE),
        ("KEGG（KofamKOALA）", "代謝路徑圖：\n哪些路徑完整", GREEN),
        ("InterProScan", "蛋白質結構域\n家族", BLUE),
        ("dbCAN", "醣類分解酵素\n（能吃什麼糖）", BROWN),
        ("antiSMASH", "二級代謝物\n基因簇", PURPLE),
        ("AI 預測", "CLEAN、DeepEC：\n預測 EC 編號", RED),
    ]
    x = 24
    for h, b, c in dbs:
        s.box(x, 360, 182, 50, h, color=c, size=14)
        s.box(x, 416, 182, 72, "", color=c, fill="#ffffff")
        s.text(x + 91, 452, b, size=13, anchor="middle-v")
        x += 194
    s.box(24, 512, 1152, 120, "", color=TEAL, fill=tint(TEAL, 0.92))
    s.text(48, 546, "⑦ 培養條件的線索（第 2.5 節）", size=17, weight=700)
    s.text(48, 578, "BacDive／MediaDive：近緣菌株已知的培養基、溫度、pH、氧氣需求。基因體預測模型：最適生長溫度、pH 偏好、需氧與否。", size=14.5)
    s.text(48, 606, "→ 這些是「起始範圍」，不是答案；真正的最適值要用實驗確認（第 7、8 章）。", size=14.5, color=MUTED)
    return s


def fig3():
    s = Svg(1200, 620, "圖 3-1　建立基因體尺度代謝模型（GEM）的流程")
    steps = [
        ("草稿模型", "CarveMe / gapseq /\nModelSEED（KBase）\n從基因體自動產生", PURPLE),
        ("定義培養基", "列出培養基成分\n對應到模型的\n交換反應", BROWN),
        ("補洞（gap-filling）", "加入必要但\n沒被註解到的反應\n讓模型能長", ORANGE),
        ("品質檢查", "MEMOTE 分數\n質量／電荷平衡\n有沒有「免費能量」", BLUE),
        ("實驗驗證", "碳源利用（Biolog）\n生長率、產率\n必需基因", GREEN),
    ]
    x = 24
    for i, (h, b, c) in enumerate(steps):
        s.box(x, 80, 214, 60, h, color=c, size=17)
        s.box(x, 148, 214, 110, "", color=c, fill="#ffffff")
        s.text(x + 107, 203, b, size=14, anchor="middle-v")
        if i < len(steps) - 1:
            s.arrow([(x + 216, 110), (x + 232, 110)], color=c)
        x += 232
    s.arrow([(1060, 262), (1060, 300), (140, 300), (140, 262)], color=GREY, dash=True)
    s.text(600, 322, "和實驗不符 → 回頭修正（通常要來回好幾輪）", size=14, color=MUTED, anchor="middle", weight=700)
    s.text(24, 350, "一個 GEM 裡有什麼？", size=18, weight=700)
    parts = [
        ("反應", "數百到數千個生化反應\n（含化學計量）", PURPLE),
        ("基因–蛋白–反應規則", "哪些基因負責哪個反應\n（AND／OR 關係）", ORANGE),
        ("生物質組成方程式", "做出 1 g 細胞需要多少\n胺基酸、核苷酸、脂質、ATP", GREEN),
        ("交換反應與上下限", "培養基能提供什麼、\n最多能吸收多快", BLUE),
    ]
    x = 24
    for h, b, c in parts:
        s.box(x, 370, 278, 50, h, color=c, size=15)
        s.box(x, 426, 278, 76, "", color=c, fill="#ffffff")
        s.text(x + 139, 464, b, size=14, anchor="middle-v")
        x += 291
    s.text(24, 540, "怎麼選工具（第 3.2 節有比較表）：", size=15, weight=700)
    s.text(24, 570, "・菌在 BiGG／文獻已有手工模型 → 直接用　・新菌、要快 → CarveMe　・要較準的碳源與發酵產物預測 → gapseq", size=14.5)
    s.text(24, 596, "・不想裝軟體 → KBase 網頁（ModelSEED）　・不管哪一種，都要經過品質檢查與實驗驗證", size=14.5)
    return s


def flux_maps():
    res = json.loads((CODE / "results.json").read_text("utf-8"))["fba"]
    lay = json.loads((CODE / "map_layout.json").read_text("utf-8"))
    W, H = lay["size"]
    sc = 0.5
    pw = W * sc
    s = Svg(1200, 450, "圖 7-5　同一個代謝網路，三種供氧條件下的流量分布（線越粗流量越大，mmol/gDW/h）")
    s.raw(f'<defs><marker id="fx" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="9" markerHeight="9" '
          f'markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{GREEN}"/></marker></defs>')
    for p, (name, flux) in enumerate(res["maps"].items()):
        ox, oy = 18 + p * (pw + 22), 92
        ex = res["maps_exchange"][name]
        o2txt = {"好氧": "氧氣充足", "缺氧": "氧氣上限 5", "厭氧": "無氧"}[name]
        s.text(ox + pw / 2, 66, f"{name}（{o2txt}）　μ = {ex['mu']:.2f}/h", size=16, weight=700, anchor="middle")
        s.raw(f'<rect x="{ox}" y="{oy - 6}" width="{pw}" height="{H * sc + 8}" rx="8" fill="#fbfbfd" stroke="#e3e6ec"/>')
        N = lay["nodes"]
        for e in lay["edges"]:
            v = sum(c * flux.get(r, 0.0) for r, c in e["flux"].items())
            a, b = N[e["from"]], N[e["to"]]
            if v < 0:
                a, b = b, a
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy)
            ux, uy = dx / ln, dy / ln
            x1, y1 = ox + (a[0] + ux * 24) * sc, oy + (a[1] + uy * 17) * sc
            x2, y2 = ox + (b[0] - ux * 30) * sc, oy + (b[1] - uy * 21) * sc
            av = abs(v)
            if av < 0.05:
                s.line(x1, y1, x2, y2, color="#b8bec9", width=1, dash=True)
            else:
                w = min(9, 1.0 + av * 0.38)
                s.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{GREEN}" '
                      f'stroke-width="{w:.1f}" stroke-linecap="round" marker-end="url(#fx)"/>')
        for nid, (x, y, lab) in N.items():
            wbox = max(34, len(lab) * 9 + 10)
            s.raw(f'<rect x="{ox + x * sc - wbox / 2:.1f}" y="{oy + y * sc - 9:.1f}" width="{wbox}" height="18" rx="4" '
                  f'fill="#ffffff" stroke="#c9ced8"/>')
            s.text(ox + x * sc, oy + y * sc + 4, lab, size=10, anchor="middle")
        s.text(ox + 8, oy + H * sc + 26,
               f"分泌：乙酸 {max(ex['ac'], 0):.1f}、乙醇 {ex['etoh']:.1f}、甲酸 {ex['for']:.1f}、CO₂ {max(ex['co2'], 0):.1f}",
               size=12.5, color=MUTED)
    return s


def fig5():
    s = Svg(1200, 640, "圖 4-2　培養的每個階段：看什麼指標、可以調什麼")
    cols = [
        ("遲滯期", GREY, "OD 幾乎不變\n耗氧低", "種菌狀態\n接種量\n培養基相近度"),
        ("指數生長", GREEN, "ln(OD) 直線上升\n耗氧指數上升\nRQ ≈ 1", "溫度、pH 最適\n供氧跟得上\n不要讓糖太高"),
        ("轉換期（缺氧／溢流）", ORANGE, "溶氧掉到接近 0\n乙酸上升、RQ 改變\n耗氧速率貼上限", "提高通氣、轉速\n降溫減慢代謝\n改分批補料"),
        ("產物期（第二階段）", BLUE, "生長變慢\n產物濃度上升\n糖持續消耗", "切換條件（停氣、\n降溫、誘導）\n維持吃糖速度"),
        ("停滯期", "#9aa3b2", "OD 持平\n耗氧驟降\n溶氧回升", "收穫時機\n補料延長\n或結束"),
    ]
    x = 24
    for i, (h, c, ind, knob) in enumerate(cols):
        s.box(x, 80, 218, 56, h, color=c, size=16)
        s.text(x + 10, 164, "看什麼", size=14, weight=700, color=c)
        s.box(x, 172, 218, 110, "", color=c, fill="#ffffff")
        s.text(x + 109, 227, ind, size=14, anchor="middle-v")
        s.text(x + 10, 312, "調什麼", size=14, weight=700, color=c)
        s.box(x, 320, 218, 110, "", color=c, fill=tint(c, 0.92))
        s.text(x + 109, 375, knob, size=14, anchor="middle-v")
        if i < len(cols) - 1:
            s.arrow([(x + 220, 108), (x + 232, 108)], color=c)
        x += 232
    s.box(24, 456, 1152, 156, "", color=GREY, fill="#fbfbfd")
    s.text(48, 490, "最值得投資的線上指標（依性價比）", size=17, weight=700)
    s.text(48, 522, "1. OD600 或線上濁度：最基本，算 μ 與階段。　2. 溶氧（DO）：最早告訴你供氧不足。　3. pH：自動加酸鹼的量本身就是代謝訊號。", size=14.5)
    s.text(48, 552, "4. 尾氣 O₂／CO₂（OUR、CER、RQ）：最能看出代謝路徑切換，但設備較貴。　5. 定時取樣 HPLC：糖、有機酸、產物（校正模型必備）。", size=14.5)
    s.text(48, 584, "原則：每個階段的「開始」與「結束」至少要有一個指標能抓到；指標的轉折點就是調參數的時機。", size=14.5, color=MUTED)
    return s


def fig6():
    s = Svg(1200, 600, "圖 5-4　分階段調參數的決策流程：每一階段要調什麼、怎麼知道")
    boxes = [
        (24, 80, "1 定義目標", "最大菌數？最大產量？\n最高生產速率？\n（三者的最佳條件不同）", BROWN),
        (318, 80, "2 找出階段", "跑一批基準培養\n用 OD、DO、pH、RQ\n標出階段轉折點", TEAL),
        (612, 80, "3 每階段找關鍵參數", "篩選實驗或模型敏感度\n只留 2–4 個\n最有影響的參數", ORANGE),
        (906, 80, "4 決定切換規則", "用時間？用 OD 門檻？\n用 DO 或 RQ 轉折？\n（指標觸發較穩）", PURPLE),
        (24, 320, "5 各階段最適化", "階段一：最大菌量／速率\n階段二：產物速率與產率\n用 RSM 或貝氏最適化", GREEN),
        (318, 320, "6 整體一起微調", "切換時間與各階段參數\n有交互作用（第 8 章）\n最後要一起最佳化", BLUE),
        (612, 320, "7 驗證與放大", "重複 3 批以上\n搖瓶 → 小型發酵槽\n供氧條件會變", RED),
        (906, 320, "8 回饋模型", "把新資料加回模型\n下一輪更準\n（第 8、14 章）", GREY),
    ]
    for x, y, h, b, c in boxes:
        s.box(x, y, 270, 52, h, color=c, size=16)
        s.box(x, y + 58, 270, 112, "", color=c, fill="#ffffff")
        s.text(x + 135, y + 114, b, size=14, anchor="middle-v")
    for x in (294, 588, 882):
        s.arrow([(x, 106), (x + 22, 106)], color=INK)
        s.arrow([(x, 346), (x + 22, 346)], color=INK)
    s.arrow([(1041, 252), (1041, 285), (159, 285), (159, 318)], color=INK)
    s.arrow([(1176, 400), (1190, 400), (1190, 70), (1041, 70), (1041, 78)], color=GREY, dash=True)
    s.text(24, 540, "什麼時候需要模型？當參數超過 3 個、或階段之間互相影響時，用模型先篩選範圍，可以省下大量實驗。", size=15)
    s.text(24, 570, "只有 1–2 個參數、單一階段時，傳統實驗設計（第 7 章）就夠了。", size=15, color=MUTED)
    return s


def fig7():
    s = Svg(1200, 520, "圖 6-2　實驗設計的漏斗：從很多個可能的參數，到最適條件")
    stages = [
        ("篩選", "Plackett–Burman\n部分因子設計", "8–15 個因子\n→ 找出 3–4 個重要的", "約 12–20 批", BROWN, 1150),
        ("找方向", "最陡上升法\n（steepest ascent）", "沿著改善最快的\n方向移動", "約 5–8 批", ORANGE, 1000),
        ("找最適點", "反應曲面法 RSM\n（中心合成設計）", "2–4 個因子\n擬合二次曲面", "約 13–30 批", GREEN, 850),
        ("或：貝氏最適化", "高斯過程＋\n期望改善", "邊做邊決定\n下一批做什麼", "常可少做實驗（第 8 章）", BLUE, 700),
    ]
    y = 70
    for h, m, d, n, c, w in stages:
        x = 600 - w / 2
        s.box(x, y, w, 90, "", color=c, fill=tint(c, 0.88))
        s.text(x + 24, y + 36, h, size=18, weight=700, color=c)
        s.text(x + 24, y + 64, n, size=13.5, color=MUTED)
        s.text(640, y + 46, m, size=14, anchor="middle-v")
        s.text(850, y + 46, d, size=14, anchor="middle-v")
        y += 104
    s.text(24, 500, "批次數是常見的量級，實際依因子數與重複數而定。溫度、pH 這類「有最適值、兩邊都會下降」的參數，一定要用能擬合曲面的設計。",
           size=14, color=MUTED)
    return s


def fig8():
    s = Svg(1200, 560, "圖 8-3　模型與實驗的循環：貝氏最適化＋代謝模型的混合做法")
    s.box(470, 80, 260, 80, "代理模型", color=BLUE, size=18, sub="高斯過程：預測值＋不確定性", sub_size=14)
    s.box(860, 230, 300, 90, "選下一批實驗", color=PURPLE, size=18, sub="期望改善最大的條件\n（兼顧「看起來好」和「還不確定」）", sub_size=13)
    s.box(470, 400, 260, 80, "做實驗", color=GREEN, size=18, sub="同時做 4–8 批（平行化）", sub_size=14)
    s.box(40, 230, 300, 90, "量測與紀錄", color=ORANGE, size=18, sub="產量、菌數、條件\n寫進同一個資料表", sub_size=13)
    s.arrow([(732, 130), (930, 130), (930, 226)], color=INK, label="1", label_at=0.3)
    s.arrow([(1010, 324), (1010, 440), (734, 440)], color=INK, label="2", label_at=0.3)
    s.arrow([(466, 440), (190, 440), (190, 324)], color=INK, label="3", label_at=0.3)
    s.arrow([(190, 226), (190, 120), (466, 120)], color=INK, label="4", label_at=0.3)
    s.box(430, 210, 340, 120, "", color=TEAL, fill=tint(TEAL, 0.9), dash=True)
    s.text(600, 238, "代謝模型（GEM／dFBA）可以放進來", size=15, weight=700, color=TEAL, anchor="middle")
    s.text(600, 270, "① 給代理模型「先驗」：先用模擬縮小範圍", size=13.5, anchor="middle")
    s.text(600, 294, "② 當特徵：模型算出的流量餵給機器學習", size=13.5, anchor="middle")
    s.text(600, 318, "③ 解釋結果：為什麼這組條件比較好", size=13.5, anchor="middle")
    s.text(24, 530, "循環到「連續幾輪沒有明顯進步」或「預算用完」就停。每一輪的資料都要保存，下一株菌或下一個產物可以重複利用。",
           size=14.5, color=MUTED)
    return s


def fig10():
    s = Svg(1200, 700, "圖 12-1　起步路線圖：你要做的事 vs AI／工具能幫的事")
    phases = [
        ("第 1 個月", "定義與資料", BROWN),
        ("第 2–3 個月", "定序與註解", ORANGE),
        ("第 3–5 個月", "基準培養與模型", PURPLE),
        ("第 5–8 個月", "最適化循環", GREEN),
        ("之後", "介面與放大", BLUE),
    ]
    x0, wcol = 190, 197
    for i, (t, h, c) in enumerate(phases):
        x = x0 + i * wcol
        s.box(x, 70, wcol - 10, 62, t, color=c, size=15, sub=h, sub_size=14)
    lanes = [
        ("你（實驗室）", GREEN, [
            "決定目標產物\n與評估指標\n盤點設備",
            "送定序\n（長讀＋短讀）\n確認純菌",
            "跑 3 批基準\n生長曲線＋\nHPLC＋DO",
            "每輪 4–8 批\n依建議做實驗\n記錄所有條件",
            "放大驗證\n搖瓶→\n發酵槽",
        ]),
        ("AI 與工具", BLUE, [
            "整理文獻\n找近緣菌\nBacDive 資料",
            "註解流程\n（Bakta、eggNOG\nKEGG、GTDB-Tk）",
            "建 GEM、補洞\nFBA 預測碳源\n設計培養基",
            "貝氏最適化\n建議下一批\n更新模型",
            "模擬器介面\n報表、警示\n知識累積",
        ]),
        ("需要合作", PURPLE, [
            "生資核心設施\n或定序公司",
            "生物資訊人員\n檢查組裝品質",
            "系統生物學\n團隊（GEM\n手工修正）",
            "統計或\n機器學習\n夥伴",
            "發酵工程\n放大經驗",
        ]),
    ]
    y = 150
    for name, c, cells in lanes:
        s.box(24, y, 150, 138, name, color=c, size=16)
        for i, txt in enumerate(cells):
            x = x0 + i * wcol
            s.box(x, y, wcol - 10, 138, "", color=c, fill="#ffffff")
            s.text(x + (wcol - 10) / 2, y + 69, txt, size=14, anchor="middle-v")
        y += 152
    s.text(24, 625, "時程是單一菌株、一個產物、有基本發酵設備時的粗估；第一輪重點是把資料格式與流程建立起來，後面每一輪會越來越快。",
           size=14, color=MUTED)
    s.text(24, 655, "AI 可以寫程式、跑註解、整理文獻、建議實驗；但培養、量測、判斷資料品質與生物安全，仍然要由你負責。", size=14,
           color=MUTED)
    return s



# ───────── 第 15–16 章：酵母菌與基改菌株 ─────────
def figr1_compare():
    s = Svg(1200, 790, "圖 1-1　基礎課那 14 章，換成酵母菌要改哪些？")
    rows = [
        ("完全通用", GREEN, "邏輯和菌種無關，數字換成你的菌就好", [
            ("4", "FBA"), ("6", "分階段最適化"), ("7", "溫度 pH 與實驗設計"),
            ("8", "AI 少做實驗"), ("9", "視覺化介面"), ("11", "數據餵回模型"), ("14", "創新做法")]),
        ("小改", ORANGE, "流程一樣，要換幾個數字或加一段注意事項", [
            ("1", "先回答你的問題"), ("5", "動態培養"), ("10", "操作建議"),
            ("12", "怎麼開始"), ("13", "文獻資源")]),
        ("要換掉", RED, "工具鏈完全不同，照細菌版做會失敗", [
            ("2", "從序列到功能"), ("3", "建立代謝模型")]),
    ]
    y = 86
    for name, col, why, chaps in rows:
        h = 112
        s.box(24, y, 150, h, name, color=col, size=19)
        s.text(190, y + 30, why, size=15, color=MUTED)
        x = 190
        for n, label in chaps:
            w = max(118, len(label) * 15 + 26)
            s.box(x, y + 46, w, 52, f"第 {n} 章", color=col, size=13, sub=label, sub_size=14, fill="#ffffff")
            x += w + 12
        y += h + 16
    s.box(24, 456, 1152, 108, "", color=TEAL, fill=tint(TEAL, 0.9))
    s.text(48, 490, "換句話說：14 章裡有 7 章原封不動、5 章小修，只有 2 章要整個換掉。", size=17, weight=700)
    s.text(48, 522, "會變的是「怎麼從序列得到模型」；不會變的是「有了模型之後怎麼用」。", size=15)
    s.text(48, 550, "第 15 章補上要換掉的那兩章，第 16 章補上基改菌株特有的部分。", size=15, color=MUTED)
    s.box(24, 584, 1152, 160, "", color=GREY, fill="#fbfbfd")
    s.text(48, 618, "最大的三個差別", size=17, weight=700)
    diffs = [("真核生物", "有內含子、胞器區隔；\n細菌的基因預測與鑑定工具不適用"),
             ("多半已有現成模型", "先查有沒有人發表過你這株菌的模型，\n有的話不要從頭建"),
             ("酵母菌之間也差很多", "釀酒酵母與產油酵母的代謝完全不同，\n不能互相套用（圖 15-3）")]
    x = 48
    for h2, b in diffs:
        s.text(x, 652, h2, size=15, weight=700, color=TEAL)
        s.text(x, 678, b, size=13.5, color=MUTED)
        x += 380
    return s


def figr1_annotate():
    s = Svg(1200, 696, "圖 1-2　酵母菌的註解流程：和細菌版（圖 2-1）哪裡不一樣")
    s.text(24, 70, "路線 A：已知是 S. cerevisiae 或近緣種 → 用參考基因體比對（快、準、建議優先）", size=17,
           weight=700, color=GREEN)
    a = [("定序讀段", "Illumina 或\nNanopore", GREY),
         ("比對到參考基因體", "bwa / minimap2\nS288C（SGD）", GREEN),
         ("變異分析", "GATK / bcftools\n看和參考差在哪", GREEN),
         ("找插入的片段", "比對不到參考的讀段\n＝外來基因或質體", PURPLE),
         ("直接套用註解", "參考基因體的註解\n（約 6,000 個基因）", GREEN)]
    x = 24
    for i, (h, b, c) in enumerate(a):
        s.box(x, 88, 210, 52, h, color=c, size=15)
        s.box(x, 146, 210, 70, "", color=c, fill="#ffffff")
        s.text(x + 105, 181, b, size=13, anchor="middle-v")
        if i < len(a) - 1:
            s.arrow([(x + 212, 114), (x + 228, 114)], color=c)
        x += 228
    s.text(24, 262, "路線 B：非模式酵母菌、或要完整的新基因體 → 從頭組裝與註解（真核專用工具）", size=17,
           weight=700, color=ORANGE)
    b = [("組裝", "Flye／SPAdes\n（長讀較佳，\n才能跨重複序列）", BROWN),
         ("完整度檢查", "BUSCO\n（saccharomycetes_odb10）\n不是 CheckM2", ORANGE),
         ("基因預測", "AUGUSTUS／BRAKER\nFunannotate\n（處理內含子）", RED),
         ("功能註解", "eggNOG-mapper、KEGG\nInterProScan\n（這些真核也能用）", BLUE),
         ("物種鑑定", "ITS／多基因親緣樹\n不是 GTDB-Tk", PURPLE)]
    x = 24
    for i, (h, bb, c) in enumerate(b):
        s.box(x, 280, 210, 52, h, color=c, size=15)
        s.box(x, 338, 210, 86, "", color=c, fill="#ffffff")
        s.text(x + 105, 381, bb, size=13, anchor="middle-v")
        if i < len(b) - 1:
            s.arrow([(x + 212, 306), (x + 228, 306)], color=c)
        x += 228
    s.box(24, 450, 1152, 90, "", color=RED, fill=tint(RED, 0.93))
    s.text(48, 484, "照細菌版做會失敗的三個地方", size=17, weight=700, color=RED)
    s.text(48, 514, "① Prokka／Bakta：資料庫是細菌的，也不處理內含子　② CheckM2：只支援細菌與古菌　"
                    "③ GTDB-Tk：只收錄細菌與古菌", size=15)
    s.box(24, 556, 1152, 122, "", color=GREY, fill="#fbfbfd")
    s.text(48, 590, "基改菌株還要多做一件事：確認「插進去的東西」", size=17, weight=700)
    s.text(48, 620, "插入位置（整合到哪條染色體？還是在質體上）、拷貝數、啟動子與終止子、選擇標記、", size=15)
    s.text(48, 648, "以及插入有沒有破壞到原本的基因。這些用短讀很難確定，長讀或定點 PCR 比較可靠。", size=15)
    return s


def figr1_culture():
    s = Svg(1240, 720, "圖 1-3　酵母菌之間差很多：釀酒酵母的經驗不能直接套到產油酵母")
    cols = [("釀酒酵母\nS. cerevisiae", BLUE), ("產油酵母\n例：Rhodotorula toruloides", ORANGE)]
    x0 = 330
    for i, (h, c) in enumerate(cols):
        s.box(x0 + i * 452, 76, 440, 62, h, color=c, size=16)
    rows = [
        ("主要代謝特徵", "Crabtree 正效應：糖一多，\n就算有氧也大量產乙醇",
         "Crabtree 陰性：有氧時把糖\n氧化掉，不產乙醇"),
        ("想要的產物從哪來", "乙醇＝主要發酵產物",
         "油脂（TAG）與類胡蘿蔔素；\n天然甲羥戊酸（MVA）通量高"),
        ("觸發累積的條件", "糖過量＋限氧",
         "**氮限制（高 C/N 比）**：\n氮用完後碳才轉去做油脂"),
        ("氧氣需求", "可厭氧生長，\n但要補麥角固醇與不飽和脂肪酸",
         "需氧；做油脂與類胡蘿蔔素\n都要氧氣"),
        ("可用碳源", "葡萄糖為主，\n木糖要改造才能用",
         "可直接用木糖、乙酸、甘油，\n適合木質纖維素水解液"),
        ("量 OD 的陷阱", "菌體是白色／米色",
         "**菌體是紅色的**（類胡蘿蔔素），\nOD600 會被色素干擾，檢量線一定要自己做"),
    ]
    y = 150
    for label, a, b in rows:
        s.box(24, y, 290, 76, label, color=GREY, size=15, fill="#f4f6f9")
        s.box(330, y, 440, 76, "", color=BLUE, fill="#ffffff")
        s.text(550, y + 38, a.replace("**", ""), size=13.5, anchor="middle-v")
        s.box(782, y, 440, 76, "", color=ORANGE, fill=tint(ORANGE, 0.94))
        s.text(1002, y + 38, b.replace("**", ""), size=13.5, anchor="middle-v")
        y += 82
    s.text(24, 676, "結論：第 5、10 章的動力學與操作參數要重新量；但第 6 章的「分階段」邏輯反而更適用——"
           "產油酵母本來就是先長菌、氮用完再累積產物。", size=14.5, color=MUTED)
    return s


def figr2_gene_to_reaction():
    s = Svg(1200, 640, "圖 2-1　基改菌株：把「插進去的基因」變成模型裡的反應")
    cols = [
        ("① 你知道的", BROWN, "插入了哪個基因\n（名稱、來源生物、序列）\n例：Z. mobilis 的 pdc"),
        ("② 查它催化什麼反應", BLUE, "UniProt／KEGG／BRENDA\n查 EC 編號與反應式\n例：丙酮酸 → 乙醛 + CO₂"),
        ("③ 對應到模型的代謝物", PURPLE, "找出模型裡的 id\n（pyr_c、acald_c、co2_c）\n要確認區隔（細胞質？粒線體？）"),
        ("④ 加進模型", GREEN, "新增反應、設上下限\n寫上基因對應規則\n（程式見 engineered.py）"),
        ("⑤ 看它改變什麼", TEAL, "最大產率、生產包絡線\n要不要再剔除競爭路徑\n（圖 16-2）"),
    ]
    x = 24
    for i, (h, c, b) in enumerate(cols):
        s.box(x, 84, 210, 58, h, color=c, size=15)
        s.box(x, 148, 210, 104, "", color=c, fill="#ffffff")
        s.text(x + 105, 200, b, size=13, anchor="middle-v")
        if i < len(cols) - 1:
            s.arrow([(x + 212, 113), (x + 228, 113)], color=c)
        x += 228
    s.box(24, 286, 1152, 132, "", color=RED, fill=tint(RED, 0.93))
    s.text(48, 320, "模型「加了反應」不等於「菌真的會做」", size=18, weight=700, color=RED)
    s.text(48, 352, "FBA 預設這個酵素的能力無限大。真實情況取決於：啟動子強度、拷貝數、密碼子使用、", size=15)
    s.text(48, 380, "蛋白質有沒有正確摺疊、輔因子夠不夠、產物有沒有毒性。模型算的是「上限」，不是「會發生」。", size=15)
    s.text(48, 406, "所以第 11 章的校正特別重要：用實測的產率回來修正這個反應的上限。", size=15, color=MUTED)
    s.box(24, 436, 1152, 186, "", color=GREY, fill="#fbfbfd")
    s.text(48, 470, "基改菌株的實驗紀錄要多記四欄（第 11 章的條件表）", size=17, weight=700)
    extra = [("插入位置", "染色體整合或質體"), ("拷貝數", "qPCR 或長讀定序"),
             ("誘導條件", "誘導劑種類、濃度、加入時間"), ("選擇壓力", "抗生素／營養缺陷，有沒有持續")]
    x = 48
    for h, b in extra:
        s.box(x, 490, 258, 48, h, color=TEAL, size=15)
        s.text(x + 129, 562, b, size=13.5, anchor="middle", color=MUTED)
        x += 276
    s.text(48, 600, "沒有這幾欄，批次之間產量不同時，你分不清是培養條件的問題還是菌株不穩定。", size=15, color=MUTED)
    return s



def figr2_fpp():
    s = Svg(1240, 760, "圖 2-2　你的案例：α-farnesene 在和誰搶原料")
    # 左側主幹
    s.box(40, 92, 220, 60, "糖（葡萄糖／木糖）", color=BROWN, size=15)
    s.arrow([(150, 154), (150, 184)], color=BROWN)
    s.box(40, 186, 220, 60, "乙醯輔酶 A", color=BROWN, size=17)
    s.arrow([(262, 216), (318, 216)], color=RED, width=4)
    s.box(318, 178, 250, 76, "油脂（TAG）", color=RED, size=16,
          sub="產油酵母最大的碳匯\n氮限制時大量累積", sub_size=12.5)
    s.text(443, 274, "最大的競爭對手", size=14, color=RED, anchor="middle", weight=700)
    s.arrow([(150, 248), (150, 288)], color=PURPLE)
    s.box(40, 290, 220, 66, "甲羥戊酸途徑（MVA）", color=PURPLE, size=15)
    s.text(150, 378, "紅酵母天生通量就高", size=13.5, color=PURPLE, anchor="middle")
    s.arrow([(150, 386), (150, 420)], color=PURPLE)
    s.box(40, 422, 220, 74, "FPP", color=PURPLE, size=22, sub="法呢基焦磷酸（C15）", sub_size=12.5)
    s.text(150, 516, "三條路搶同一個 FPP", size=14.5, color=INK, anchor="middle", weight=700)
    # 三條分支
    outs = [
        (40, "α-farnesene（目標）", GREEN, "你插入的蘋果 AFS。產物會揮發，\n要用十二烷等有機相覆蓋收集。"),
        (440, "角鯊烯 → 麥角固醇", ORANGE, "ERG9（squalene synthase）。\n細胞膜必需，只能調降、不能關掉。"),
        (840, "GGPP → 類胡蘿蔔素", RED, "紅酵母紅色的來源。\n調降可以把 FPP 讓出來。"),
    ]
    for x, label, c, note in outs:
        cx = x + 180
        s.arrow([(150, 500), (cx, 540), (cx, 572)], color=c, width=3.5 if c == GREEN else 2.2, curve=True)
        s.box(x, 574, 360, 60, label, color=c, size=16)
        s.text(cx, 660, note, size=13.5, color=MUTED, anchor="middle")
    # 右側：模型能回答什麼
    s.box(620, 92, 580, 300, "", color=TEAL, fill=tint(TEAL, 0.92))
    s.text(648, 128, "模型能幫你回答的四個問題", size=18, weight=700, color=TEAL)
    qs = ["① 理論上每克糖最多能產多少 α-farnesene？",
          "② 油脂路徑要降多少，產物才明顯上升？代價是什麼？",
          "③ 降 ERG9 還是降類胡蘿蔔素，釋出的 FPP 比較多？",
          "④ NADPH 夠不夠？（油脂與萜類都要，常是隱藏瓶頸）"]
    yy = 172
    for q in qs:
        s.text(648, yy, q, size=14.5)
        yy += 38
    s.text(648, 340, "要用 rhto-GEM 跑（第 15 章），不要用釀酒酵母的模型。", size=14, color=MUTED)
    s.text(648, 368, "文獻：同樣從 FPP 出發的 α-bisabolene，在這株菌已做到 g/L 等級。", size=14, color=MUTED)
    s.text(40, 724, "注意：模型算的是「碳與輔因子的上限」。實際產量還受酵素活性、拷貝數、產物毒性與揮發影響——"
                    "這些要用第 11 章的校正補回來。", size=14, color=MUTED)
    return s


# ───────── 第 17 章：實際案例（紅酵母 α-farnesene 基改株的定序比對）─────────
def _case():
    return json.loads((CODE / "case_rt.json").read_text("utf-8"))


def figr3_overview():
    d = _case()
    km, a = d["kmer"], d["assembly"]
    arr = d["array"]
    carrier, host = arr["carrier"], ("mut" if arr["carrier"] == "wt" else "wt")
    names = {"wt": d["provenance"]["wt_file"], "mut": d["provenance"]["mut_file"]}
    n_afs = {t: len(d[t + "_afs_copies"]) for t in ("wt", "mut")}
    s = Svg(1280, 790, "圖 3-1　兩份組裝比對的結論：轉殖基因陣列只在其中一份裡")

    for tag, x in ((carrier, 40), (host, 720)):
        st = a[tag]
        col = TEAL if tag == carrier else GREY
        s.box(x, 86, 520, 104, names[tag], color=col, size=20,
              sub=f'{st["contigs"]} contigs　{st["total_bp"]:,} bp　N50 {st["n50"]:,}\n'
                  f'GC {st["gc_pct"]:.2f}%　未知鹼基 N＝{st["n_bases"]}', sub_size=14)
    s.box(580, 86, 120, 104, f'{km["shared_frac_of_mut"] * 100:.3f}%', color=PURPLE, size=20,
          sub=f'{km["k"]}-mer\n共有', sub_size=13)
    s.text(640, 216, "→ 兩份是同一株菌，差別只在那一個插入", size=15, color=MUTED, anchor="middle")

    rows = [("α-farnesene 合成酶 CDS", f'{n_afs[carrier]} 個拷貝', f'{n_afs[host]} 個'),
            ("該 CDS 的 31-mer 存在比例", "100.00%", "0.00%"),
            ("農桿菌 T-DNA border", "2 處", "0 處"),
            ("插入陣列", f'{arr["contig"]} 約 {arr["span"] / 1000:.0f} kb', "無")]
    y = 248
    for name, lv, rv in rows:
        s.line(40, y, 1240, y, color="#e3e6ec")
        s.text(640, y + 32, name, size=15, color=MUTED, anchor="middle")
        s.text(420, y + 34, lv, size=19, weight=700, color=TEAL, anchor="end")
        s.text(860, y + 34, rv, size=19, weight=700, color=GREY)
        y += 52
    s.line(40, y, 1240, y, color="#e3e6ec")

    s.box(40, y + 24, 1200, 230, "", color=RED, fill=tint(RED, 0.94))
    s.text(68, y + 62, "標示為「野生株」的那一份帶有完整的轉殖基因陣列，標示為「基改株」的完全沒有。",
           size=18, weight=700)
    s.text(68, y + 98, "兩種可能，要從實驗紀錄判斷：", size=15)
    s.box(68, y + 112, 560, 72, "① 兩管樣品或檔名交換了", color=ORANGE, size=15,
          sub="最常見。送驗、回傳、改檔名任一步都可能發生", sub_size=13, fill="#ffffff")
    s.box(652, y + 112, 560, 72, "② 這一株把構築丟掉了", color=ORANGE, size=15,
          sub="串聯重複會同源重組；沒施加選擇壓力就容易丟", sub_size=13, fill="#ffffff")
    s.text(68, y + 214, "怎麼分辨：對兩株各做一次 AFS 的 PCR 或 qPCR——引子用比對出來的 CDS 序列設計即可。"
                        "這是整個分析裡最該先做的一步。", size=15, weight=700)
    return s


def _track(s, x0, w, c0, c1, elems, y, label, colmap, flip=False):
    """把構築的一段畫成水平軌道；小於 14 px 的元件改用引線標在軌道外側。"""
    sc = w / (c1 - c0)
    s.parts.append(f'<rect x="{x0}" y="{y}" width="{w}" height="46" rx="4" fill="#f3f4f7" stroke="#c7ccd6"/>')
    s.text(x0, y - 120, label, size=15, weight=700)
    small = []
    for e in elems:
        if e["c1"] <= c0 or e["c0"] >= c1:
            continue
        ex = x0 + (e["c0"] - c0) * sc
        ew = (e["c1"] - e["c0"]) * sc
        col = colmap[e["kind"]]
        s.parts.append(f'<rect x="{ex:.1f}" y="{y}" width="{max(ew, 3):.1f}" height="46" rx="3" '
                       f'fill="{tint(col, 0.62)}" stroke="{col}" stroke-width="2"/>')
        tag = "?" if e["evidence"] == "unknown" else ("≈" if e["evidence"] == "inferred" else "")
        if ew >= _w(e["name"] + tag, 14) + 16:
            s.text(ex + ew / 2, y + 29, e["name"] + tag, size=14, weight=700, anchor="middle")
            s.text(ex + ew / 2, y + 94, f'{e["c0"]:,}–{e["c1"]:,}', size=12, color=MUTED, anchor="middle")
        else:
            small.append((ex + ew / 2, e["name"] + tag, f'{e["c0"]:,}', col))
    small.sort()
    # 三層交錯的引線會穿過鄰居的標籤。先把線全部畫完，再鋪白底遮罩，最後才畫字：
    # SVG 是後畫的蓋前畫的，順序錯了就會看到線從字中間穿過去。
    placed = []
    for i, (cx, nm, pos, col) in enumerate(small):
        ty = y - 40 - (i % 3) * 30
        s.line(cx, y - 2, cx, ty + 6, color=col, width=1.4)
        placed.append((cx, ty, f"{nm}　{pos}", col))
    for cx, ty, lab, col in placed:
        tw = _w(lab, 12.5)
        s.parts.append(f'<rect x="{cx - tw / 2 - 5:.1f}" y="{ty - 12}" '
                       f'width="{tw + 10:.1f}" height="17" fill="#ffffff"/>')
        s.text(cx, ty, lab, size=12.5, color=col, anchor="middle", weight=700)
    # 座標尺
    step = 1000
    t = ((c0 // step) + 1) * step
    while t < c1:
        tx = x0 + (t - c0) * sc
        s.line(tx, y + 46, tx, y + 56, color=MUTED, width=1.2)
        s.text(tx, y + 72, f"{t // 1000}k", size=11.5, color=MUTED, anchor="middle")
        t += step


def figr3_construct():
    d = _case()
    el = d["elements"]
    L = d["provenance"]["construct_bp"]
    colmap = {"border": RED, "promoter": ORANGE, "gene": TEAL, "terminator": PURPLE,
              "vector": GREY, "ori": BROWN}
    s = Svg(1420, 790, f'圖 17-2　你設計的構築（{L:,} bp，環狀）上面有什麼')
    s.text(60, 76, "兩條軌道的比例尺不同（上 5,700 bp／下 6,050 bp 各佔滿 1,300 px）；"
                   "構築是環狀，下軌右端接回上軌左端。", size=13.5, color=MUTED)
    _track(s, 60, 1300, 0, 5700, el, 270, "T-DNA：LB → RB，5,447 bp　會被送進染色體的就是這一段", colmap)
    _track(s, 60, 1300, 5597, L, el, 530, "載體骨架：6,050 bp　本來應該留在農桿菌裡", colmap)
    lg = [("邊界 border", RED), ("啟動子", ORANGE), ("基因", TEAL), ("終止子", PURPLE),
          ("複製起點", BROWN), ("載體殘跡", GREY)]
    x = 60
    for nm, col in lg:
        s.parts.append(f'<rect x="{x}" y="646" width="22" height="16" rx="3" fill="{tint(col, 0.62)}" '
                       f'stroke="{col}" stroke-width="2"/>')
        s.text(x + 30, 660, nm, size=13.5)
        x += 30 + _w(nm, 13.5) + 26
    s.text(60, 704, "標記說明：名稱後面沒有符號＝逐字比對上已知序列（border 共識、nos terminator／promoter、"
                    "多選殖位、pUC 複製起點）；", size=13.5, color=MUTED)
    s.text(60, 730, "「≈」＝依保守模體推定（KanR、ParA 的 Walker A、GNAT 乙醯轉移酶）；"
                    "「?」＝身分未知，需要 BLAST 才能確認。", size=13.5, color=MUTED)
    s.text(60, 766, "兩個啟動子在宿主基因體裡找不到 → 不是這株紅酵母的原生啟動子。"
                    "它是組成型還是受氮限制調控，會直接決定第 6 章的分階段策略怎麼設計。",
           size=14.5, weight=700, color=RED)
    return s


def _w(s, size):
    return sum(size if ord(ch) > 0x2E80 else size * 0.58 for ch in s)


def figr3_array():
    d = _case()
    arr = d["array"]
    segs = d[arr["carrier"] + "_trace"]["segments"]
    copies = d[arr["carrier"] + "_afs_copies"]
    g0, g1 = arr["g0"], arr["g1"]
    X0, W = 150, 1180
    sc = W / (g1 - g0)
    s = Svg(1460, 760, f'圖 17-3　轉殖基因在染色體上的實際排列：{arr["span"]:,} bp 的串聯陣列')
    y = 300
    s.box(28, y - 4, 112, 54, "宿主", color=BROWN, size=15, sub="染色體", sub_size=12)
    s.box(1340, y - 4, 92, 54, "宿主", color=BROWN, size=15, sub="染色體", sub_size=12)
    s.line(140, y + 23, X0, y + 23, color=BROWN, width=3)
    s.line(X0 + W, y + 23, 1340, y + 23, color=BROWN, width=3)
    broken = {c["pos"] for c in copies if not c["intact"]}
    for sg in segs:
        lo, hi = sorted((sg["c0"], sg["c1"]))
        kind = "tdna" if hi <= 5700 else ("mix" if lo < 5700 else "back")
        trunc = any(sg["g0"] <= p <= sg["g1"] for p in broken)
        col = RED if trunc else (TEAL if kind == "tdna" else (PURPLE if kind == "mix" else GREY))
        x = X0 + (sg["g0"] - g0) * sc
        w = max((sg["g1"] - sg["g0"]) * sc, 3.5)
        s.parts.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="46" rx="3" '
                       f'fill="{tint(col, 0.6)}" stroke="{col}" stroke-width="1.8"/>')
    for i, c in enumerate(sorted(copies, key=lambda c: c["pos"]), 1):
        cx = X0 + (c["pos"] - g0) * sc
        col = RED if not c["intact"] else TEAL
        s.parts.append(f'<path d="M{cx:.1f},{y - 8} l-7,-13 l14,0 z" fill="{col}"/>')
        s.text(cx, y - 30, str(i), size=13, weight=700, color=col, anchor="middle")
    s.text(X0, y - 58, "▲ 每個 AFS 拷貝的起點（12 個，全部在負股、方向一致）", size=14, weight=700)
    for g, lab in ((g0, f"{g0:,}"), (g1, f"{g1:,}")):
        gx = X0 + (g - g0) * sc
        s.line(gx, y + 46, gx, y + 68, color=MUTED, width=1.2)
        s.text(gx, y + 88, lab, size=13, color=MUTED, anchor="middle")
    s.text(X0 + W / 2, y + 88, f'{arr["contig"]}　共 {arr["span"]:,} bp', size=14, weight=700, anchor="middle")

    j = arr.get("junction") or {}
    if j.get("left") and j.get("right"):
        lj, rj = j["left"], j["right"]
        gapbp = abs(rj["start"] - lj["end"])
        s.box(150, 486, 1180, 96, "", color=BROWN, fill=tint(BROWN, 0.93))
        s.text(176, 522, "插入點：在沒有插入的那一株，陣列的左右側翼是直接相鄰的", size=17, weight=700)
        s.text(176, 556, f'左側翼落在 {lj["contig"]} {lj["start"]:,}–{lj["end"]:,}，'
                         f'右側翼落在 {rj["contig"]} {rj["start"]:,}–{rj["end"]:,}'
                         f'——中間只隔 {gapbp:,} bp。單一插入位點，沒有染色體重排。', size=14.5)
        for side, gx in (("left", X0), ("right", X0 + W)):
            s.arrow([(gx, y + 104), (gx, 486)], color=BROWN, width=1.6, dash=True)

    lg = [("完整的 T-DNA", TEAL), ("T-DNA ＋ 骨架", PURPLE), ("載體骨架", GREY), ("截短的 T-DNA", RED)]
    x = 150
    for nm, col in lg:
        s.parts.append(f'<rect x="{x}" y="196" width="22" height="16" rx="3" fill="{tint(col, 0.6)}" '
                       f'stroke="{col}" stroke-width="2"/>')
        s.text(x + 30, 210, nm, size=14)
        x += 30 + _w(nm, 14) + 28
    s.text(150, 162, f'{len(segs)} 段片段，合計 {arr["mapped_bp"]:,} bp '
                     f'（陣列的 {arr["mapped_bp"] / arr["span"] * 100:.1f}%）全部能逐段對回構築——'
                     f'沒有來源不明的 DNA，也沒有宿主序列被夾進中間。', size=14.5)
    s.text(150, 620, "寬度按比例畫，但小於 3.5 px 的片段放大到 3.5 px 才看得見（最小的是 84 bp）。",
           size=13, color=MUTED)
    s.text(150, 656, "為什麼是串聯陣列：農桿菌轉形時 T-DNA 一條接一條進去同一個斷點，"
                     "首尾相接形成重複；最後一條常常只進去一半（拷貝 ③）。", size=14.5)
    s.text(150, 690, "要注意：串聯重複之間會同源重組，拷貝數會隨傳代下降。"
                     "維持選擇壓力，並每隔幾代用 qPCR 確認。", size=14.5, weight=700, color=RED)
    s.text(150, 726, "拷貝數 12 是組裝給的下限（高度相同的重複可能被壓縮）。"
                     "要定量得把原始讀段比回單一拷貝算深度。", size=13.5, color=MUTED)
    return s


def figr3_junction():
    d = _case()
    carrier = d["array"]["carrier"]
    bad = [c for c in d[carrier + "_afs_copies"] if not c["intact"]]
    s = Svg(1280, 760, "圖 3-5　12 個拷貝裡壞掉的那一個：不是突變，是陣列的接合點")
    if not bad:
        s.text(40, 120, "這一次的資料裡每個拷貝都是完整的。", size=16)
        return s
    c = bad[0]
    fd = c["first_diff"]
    s.text(40, 96, f'拷貝 ③（{c["contig"]} {c["pos"]:,}）前 {fd:,} bp 與設計完全一致，'
                   f'之後就不是 AFS 了。', size=16)
    y = 150
    s.box(40, y, 420, 64, "載體骨架", color=GREY, size=16, sub="構築 8,956–9,374", sub_size=13)
    s.box(460, y, 760, 64, "T-DNA 片段", color=RED, size=16,
          sub="構築 2,928 → 222：只有啟動子 P1 ＋ 殘缺的 AFS", sub_size=13)
    s.arrow([(460, y + 108), (460, y + 72)], color=RED, width=2.2)
    s.text(460, y + 132, "接合點", size=15, weight=700, color=RED, anchor="middle")

    y = 330
    s.box(40, y, 1200, 112, "", color=GREY, fill="#fbfbfd")
    s.text(64, y + 34, "接合點兩側的實際序列（AFS CDS 內座標 " + f'{fd:,}' + " bp 處）", size=15, weight=700)
    s.text(64, y + 68, "構築（正確）", size=13.5, color=MUTED)
    s.text(230, y + 68, "…TCACCACCAACCAGGTCCCG", size=14)
    s.text(530, y + 68, "TTCCTCTCGTCGTTCATGAACAACGCC…", size=14, color=TEAL, weight=700)
    s.text(64, y + 96, "拷貝 ③", size=13.5, color=MUTED)
    s.text(230, y + 96, "…TCACCACCAACCAGGTCCCG", size=14)
    s.text(530, y + 96, "GTTAGATGGGAAACCGCCATCAGTACC…", size=14, color=RED, weight=700)
    s.line(524, y + 52, 524, y + 104, color=RED, width=2)

    y = 486
    s.text(40, y, "對蛋白質的影響", size=16, weight=700)
    full, got, stop = 576, c["protein_aa"], c["stop_codon"]
    X0, W = 40, 1100
    s.parts.append(f'<rect x="{X0}" y="{y + 20}" width="{W}" height="40" rx="5" fill="{tint(TEAL, 0.72)}" '
                   f'stroke="{TEAL}" stroke-width="2"/>')
    cut = W * (stop - 11) / full
    s.parts.append(f'<rect x="{X0 + cut:.1f}" y="{y + 20}" width="{W * 11 / full:.1f}" height="40" '
                   f'fill="{tint(RED, 0.5)}" stroke="{RED}" stroke-width="2"/>')
    s.parts.append(f'<rect x="{X0 + W * stop / full:.1f}" y="{y + 20}" width="{W * (full - stop) / full:.1f}" '
                   f'height="40" fill="#ffffff" stroke="{GREY}" stroke-width="2" stroke-dasharray="6 5"/>')
    s.text(X0 + cut / 2, y + 46, f"正常的 AFS：1–{stop - 11} aa", size=14.5, weight=700, anchor="middle")
    s.text(X0 + W, y + 88, f"紅色＝接合處的 11 個外來胺基酸　　虛線＝缺掉的 C 端 {full - stop + 1} 個胺基酸", size=13.5, color=MUTED, anchor="end")
    s.line(X0 + W * stop / full, y + 20, X0 + W * stop / full, y - 6, color=RED, width=2)
    s.text(X0 + W * stop / full, y - 14, f"第 {stop} 個密碼子提前終止", size=14, weight=700,
           color=RED, anchor="middle")
    s.text(X0, y + 128, f'接合處讀出 11 個外來胺基酸就撞到終止密碼子 → {got} aa（正常 {full} aa）。'
                        f'缺掉的 C 端含萜類合成酶的 C 端結構域，這個拷貝不可能有活性。', size=14.5)
    s.text(X0, y + 162, "這不影響另外 11 個拷貝——它們與設計逐鹼基零差異。"
                        "ATMT 的串聯整合常常就是這樣收尾的。", size=14.5, weight=700)
    s.text(X0, y + 200, "教訓：取拷貝序列時一定要記錄探針命中的是正股還是負股。"
                        "我們第一輪忘了，拿正股直接截取，結果每個拷貝都「有 313–383 bp 突變」——全是假的。",
           size=13.5, color=MUTED)
    return s


def figr3_pathway():
    d = json.loads((CODE / "farnesene_path.json").read_text("utf-8"))
    f = d["per_farnesene"]
    gy = d["yield"]["glucose"]
    s = Svg(1480, 950, "圖 3-6　轉進去一個基因，代謝上改變了什麼")
    s.text(40, 78, "灰底＝紅酵母原本就有的路徑　　虛線框＝轉殖加進去的　　橘色＝搶同一批原料的競爭者",
           size=14.5, color=MUTED)

    s.box(40, 150, 190, 80, "葡萄糖／木糖", color=GREY, size=16,
          sub="紅酵母可直接用木糖\n與乙酸", sub_size=12)
    s.box(300, 150, 200, 80, "細胞質乙醯輔酶A", color=GREY, size=16,
          sub="所有下游的共同起點", sub_size=12)
    s.arrow([(230, 190), (300, 190)], color=GREY, label="糖解", label_dy=-10, size=12.5)

    # 油脂分支（競爭者）
    s.box(300, 330, 200, 72, "丙二醯輔酶A", color=ORANGE, size=15)
    s.box(300, 450, 200, 72, "脂肪酸", color=ORANGE, size=15)
    s.box(300, 570, 200, 72, "三酸甘油酯（油脂）", color=ORANGE, size=15,
          sub="產油酵母的本業", sub_size=12)
    s.arrow([(400, 230), (400, 330)], color=ORANGE, width=3)
    s.arrow([(400, 402), (400, 450)], color=ORANGE, width=3)
    s.arrow([(400, 522), (400, 570)], color=ORANGE, width=3)
    s.text(520, 372, "氮限制（高 C/N）會把通量\n往這裡推——這是紅酵母的\n預設行為，不是故障",
           size=13.5, color=ORANGE, weight=700)
    s.text(520, 476, "每 1 分子硬脂酸：\n9 乙醯輔酶A、16 NADPH", size=13, color=MUTED)

    # MVA → FPP
    s.box(560, 150, 210, 80, "MVA 路徑", color=PURPLE, size=16, sub="6 步，HMG1 是限速步驟", sub_size=12)
    s.box(830, 150, 150, 80, "IPP／DMAPP", color=PURPLE, size=15, sub="C5 單元", sub_size=12)
    s.box(1040, 150, 130, 80, "FPP", color=RED, size=20, sub="C15，分岔點", sub_size=12)
    s.arrow([(500, 190), (560, 190)], color=PURPLE, width=3)
    s.arrow([(770, 190), (830, 190)], color=PURPLE, width=3)
    s.arrow([(980, 190), (1040, 190)], color=PURPLE, width=3, label="×3", label_dy=-10, size=13)
    ipp = d["per_ipp"]
    s.text(560, 266, f'每 1 個 C5 單元要 {ipp["acetyl_coa"]} 乙醯輔酶A、{ipp["nadph"]} NADPH、'
                     f'{ipp["atp"]} ATP，並丟掉 1 個 CO_2_', size=13, color=MUTED)

    # FPP 的去向
    outs = [(60, "α-farnesene", TEAL, f'★ 轉殖加進去的（{d["copies_functional"]} 個功能性拷貝）', True),
            (180, "角鯊烯 → 麥角固醇", ORANGE, "ERG9；細胞膜必需，只能調降不能剔除", False),
            (300, "GGPP → 類胡蘿蔔素", ORANGE, "紅酵母之所以是紅的；會干擾 OD600", False),
            (420, "蛋白質法呢基化", GREY, "量少，但必需", False)]
    for y0, name, col, note, new in outs:
        s.box(1240, y0, 210, 76, name, color=col, size=15, fill="#ffffff" if not new else tint(col, 0.5))
        s.arrow([(1170, 190), (1240, y0 + 38)], color=col, width=3 if new else 2)
        s.text(1240, y0 + 100, note, size=12.5, color=col if new else MUTED, weight=700 if new else 400)
    s.parts.append('<rect x="1232" y="52" width="226" height="92" rx="12" fill="none" '
                   f'stroke="{TEAL}" stroke-width="3" stroke-dasharray="7 5"/>')

    s.box(716, 396, 506, 246, "", color=GREY, fill="#fbfbfd")
    s.text(742, 434, "想提高產量，可以動的四個地方", size=16.5, weight=700)
    s.text(742, 462, "（都要先用模型算，不要一次動兩個）", size=13, color=MUTED)
    for i, line in enumerate([
            "① 把 HMG1 拉高：MVA 的限速步驟，文獻上對倍半萜最有效",
            "② 調降 ERG9：FPP 最大的去向，但細胞膜必需，只能弱化",
            "③ 調降類胡蘿蔔素：釋出 FPP，順便讓 OD600 好量",
            "④ 挑氮限制的時機：限氮催油脂，會把乙醯輔酶A 搶走"]):
        s.text(742, 500 + i * 34, line, size=13.5)
    s.box(40, 690, 690, 212, "", color=TEAL, fill=tint(TEAL, 0.93))
    s.text(68, 728, "多出來的負擔（化學計量，可以自己驗算）", size=17, weight=700)
    s.text(68, 764, f'每做出 1 分子 α-farnesene：{f["acetyl_coa"]} 個乙醯輔酶A、'
                    f'{f["nadph"]} NADPH、{f["atp"]} ATP，路上丟掉 {f["co2"]} 個 CO_2_。', size=15)
    s.text(68, 796, f'碳的理論上限：{gy["sugar_mol"]} 莫耳糖換 1 莫耳產物 → 碳產率 '
                    f'{gy["carbon_yield"] * 100:.1f}%，質量 {gy["mass_yield_g_per_g"]:.3f} g/g 糖。', size=15)
    s.text(68, 836, "注意：油脂每 9 個乙醯輔酶A 要 16 NADPH，萜類只要 6——"
                    "搶輔因子的是油脂，不是你的產物。", size=14, color=MUTED)

    s.box(760, 690, 690, 212, "", color=RED, fill=tint(RED, 0.95))
    s.text(788, 728, "三件會讓你量錯或做白工的事", size=17, weight=700)
    for i, line in enumerate([
            "① α-farnesene 會揮發。不加十二烷等有機相覆蓋，量到的產量嚴重低估。",
            "② 萜類對細胞膜有毒。高產菌株長得特別差時先懷疑這個，不要一直調溫度。",
            "③ 菌體是紅的，而且會塞滿油滴：OD600 換算成菌量的係數會隨階段漂移。",
            "　 稀釋修的是線性，修不了這個係數——每個階段都要自己做乾重校正線。"]):
        s.text(788, 764 + i * 33, line, size=14)
    s.text(40, 932, "本圖是生化計量與文獻整理，不是模擬結果；要算「調降 ERG9 能多拿多少 FPP」"
                    "需要跑 rhto-GEM（第 15、16 章）。", size=13, color=MUTED)
    return s


def figr3_states():
    d = json.loads((CODE / "farnesene_path.json").read_text("utf-8"))
    s = Svg(1460, 880, "圖 3-8　四種狀態：什麼時候產油、什麼時候產色素、什麼時候產 farnesene")
    s.text(40, 78, "兩個開關決定細胞在做什麼：氮還有沒有，以及有沒有逆境訊號（光照、靜止期、高溶氧、產物毒性）。"
                   "象限的邊界是推論，不是量出來的。", size=14.5, color=MUTED)

    X0, X1, Y0, Y1 = 150, 850, 150, 700
    XM, YM = (X0 + X1) // 2, (Y0 + Y1) // 2
    quads = [
        (X0, YM, "專心生長", GREEN, "碳 → 蛋白質、核酸、膜脂\n油脂低、色素低",
         "★ farnesene 競爭最小", True),
        (XM, YM, "產油", ORANGE, "氮一耗盡就觸發\n油脂可到 50–70% 乾重", "乙醯輔酶A 被搶走", False),
        (X0, Y0, "產類胡蘿蔔素", RED, "抗氧化防禦：光照、靜止期\n高溶氧、產物毒性", "FPP 被分流", False),
        (XM, Y0, "油脂 ＋ 色素同時", BROWN, "一般批次培養的後期\n兩個開關都按下了", "兩邊都被搶", False),
    ]
    for x, y, name, col, body, cost, best in quads:
        s.parts.append(f'<rect x="{x}" y="{y}" width="{(X1 - X0) // 2}" height="{(Y1 - Y0) // 2}" '
                       f'fill="{tint(col, 0.9 if not best else 0.78)}" stroke="{col}" stroke-width="2"/>')
        s.text(x + 24, y + 48, name, size=20, weight=700, color=col)
        for i, line in enumerate(body.split("\n")):
            s.text(x + 24, y + 86 + i * 26, line, size=14)
        s.text(x + 24, y + 86 + 2 * 26 + 16, cost, size=14.5, weight=700,
               color=GREEN if best else RED)

    s.text(X0, Y1 + 26, "氮充足", size=15, weight=700)
    s.text(X1, Y1 + 26, "氮耗盡", size=15, weight=700, anchor="end")
    s.text((X0 + X1) // 2, Y1 + 26, "培養基裡的氮", size=15, anchor="middle", color=MUTED)
    s.arrow([(X0, Y1 + 44), (X1, Y1 + 44)], color=MUTED, width=2)
    s.text(X0 - 16, Y0 - 16, "逆境訊號高", size=14, weight=700, anchor="end")
    s.text(X0 - 16, Y1 + 6, "逆境訊號低", size=14, weight=700, anchor="end")
    s.arrow([(X0 - 30, Y1), (X0 - 30, Y0)], color=MUTED, width=2)

    # 一般批次培養的軌跡
    s.arrow([(X0 + 110, Y1 - 70), (XM + 60, YM + 40), (X1 - 120, Y0 + 90)],
            color=PURPLE, width=3, dash=True, curve=True)
    s.text(XM + 150, Y0 + 170, "批次培養會自己\n走到右上角", size=14, weight=700, color=PURPLE, anchor="end")

    s.box(884, 150, 540, 250, "", color=GREEN, fill=tint(GREEN, 0.93))
    s.text(910, 190, "要產 farnesene，就得把菌留在左下角", size=17, weight=700)
    for i, line in enumerate([
            "• 饋料批次：糖和氮一起補，不要讓氮歸零",
            "• 遮光：光會誘導類胡蘿蔔素，遮光是零成本的事",
            "• 十二烷覆蓋：把揮發又有毒的產物一直拉走",
            "• 顧好溶氧，但不要過度曝氣（高溶氧本身是逆境）",
            "• 用殘餘氮當指標，不要用時間"]):
        s.text(910, 228 + i * 32, line, size=14)

    eq = {c["carotenoid_mg_per_gdw"]: c["farnesene_equiv_mg_per_gdw"] for c in d["carotenoid_equiv"]}
    s.box(884, 424, 540, 276, "", color=RED, fill=tint(RED, 0.95))
    s.text(910, 464, "但色素不是主要的競爭者", size=17, weight=700)
    s.text(910, 500, "把類胡蘿蔔素全部關掉，最多只能多拿：", size=14)
    yy = 536
    for v in (1.0, 3.0, 5.0):
        s.text(930, yy, f"類胡蘿蔔素 {v:g} mg/g 乾重　→　α-farnesene 最多 +{eq[v]:.1f} mg/g",
               size=14, weight=700)
        yy += 30
    s.text(910, 640, "（以異戊二烯 C5 單元換算；C40 色素 ＝ 8 個 C5，"
                     "farnesene ＝ 3 個）", size=13, color=MUTED)
    s.text(910, 668, "同一時間油脂是 500–700 mg/g。要搶碳，該動的是油脂。", size=14, weight=700)

    s.box(40, 760, 1384, 96, "", color=GREY, fill="#fbfbfd")
    s.text(68, 798, "菌變紅不是「不能產了」，而是一個指標：它告訴你細胞已經感覺到逆境或進入靜止期。",
           size=15.5, weight=700)
    s.text(68, 830, "該做的是回頭查原因（氮是不是早就沒了？溶氧？光？產物毒性？），"
                    "而不是急著去改色素那條路。", size=15)
    return s


def _wrap(txt, size, maxw):
    """依實際寬度斷行；ASCII 單字不切開，行首不留標點。"""
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


def figr7_strategy():
    d = json.loads((CODE / "literature_terpenes.json").read_text("utf-8"))
    steps = d["steps"]
    s = Svg(1480, 860, "圖 7-2　八年三步：別人是怎麼從 680 mg/L 走到 20 g/L 的")
    s.text(40, 78, "三篇論文、同一株菌、同一個前驅物（FPP）。每一步解決的是不同的瓶頸。",
           size=14.5, color=MUTED)

    cols = [GREY, BLUE, TEAL]
    X, W, GAP = 40, 440, 24
    for i, (st, col) in enumerate(zip(steps, cols)):
        x = X + i * (W + GAP)
        s.box(x, 150, W, 400, "", color=col, fill=tint(col, 0.93))
        s.text(x + 24, 196, f'{st["year"]}', size=26, weight=700, color=col)
        s.text(x + 24, 232, st["title"], size=20, weight=700)
        s.line(x + 24, 250, x + W - 24, 250, color=col)
        yy = 286
        for line in st["what"]:
            bold = line.startswith("**")
            txt = line.replace("**", "")
            for ln in _wrap(txt, 13.5, W - 48):
                s.text(x + 24, yy, ln, size=13.5, weight=700 if bold else 400,
                       color=RED if bold else INK)
                yy += 25
            yy += 12
        s.text(x + 24, 500, "這一步做到", size=13, color=MUTED)
        s.text(x + W - 24, 506, f'{st["best"] / 1000:.1f} g/L', size=26, weight=700,
               color=col, anchor="end")
        s.text(x + 24, 534, d["sources"][st["key"]]["cite"], size=11.5, color=MUTED)
        if i < 2:
            s.arrow([(x + W + 2, 350), (x + W + GAP - 2, 350)], color=MUTED, width=3)

    # 你在這裡
    x2 = X + 1 * (W + GAP)
    s.arrow([(x2 + W / 2, 132), (x2 + W / 2, 148)], color=RED, width=3)
    s.text(x2 + W / 2, 124, "你已經做到這一步了（11 個功能性拷貝）", size=16, weight=700,
           color=RED, anchor="middle")

    s.box(40, 586, 1400, 150, "", color=GREEN, fill=tint(GREEN, 0.93))
    s.text(68, 626, "對你的意義", size=18, weight=700)
    s.text(68, 662, "拷貝數這一關你已經過了——而且是用和 2017 那篇一樣的農桿菌隨機嵌入做到的。"
                    "接下來該做的是 2025 那一步：", size=15)
    s.text(68, 696, "補強 MVA 路徑（尤其 HMG1）＋ 削弱往油脂的通量。"
                    "那一步在文獻上帶來 6–7 倍的提升，是目前所有手段裡最大的一個。", size=15, weight=700)
    s.text(40, 772, "注意：這三篇做的是 α-bisabolene（C15 倍半萜，和 α-farnesene 同樣從 FPP 出發、同樣揮發），"
                    "不是 α-farnesene 本身。", size=13.5, color=MUTED)
    s.text(40, 800, "合成酶不同，產物毒性與揮發性也不會完全一樣，所以這些數字是「可以期待的量級」，"
                    "不是你一定做得到的數字。", size=13.5, color=MUTED)
    s.text(40, 832, "本圖的數字全部來自論文摘要或轉述（這個環境連不上期刊網站），"
                    "引用前請自己核對全文。", size=13.5, color=RED)
    return s


# ───────── 手寫 SVG 插畫（不是方塊圖，是真的畫出來）─────────
def _vessel(s, cx, top, bot, w, culture_top, overlay=None, seed=0):
    """發酵槽切面：槽體、培養液（紅酵母是紅的）、氣泡、攪拌軸葉片、通氣管。"""
    import random
    hw, r = w / 2, w / 2
    body = (f"M{cx - hw},{top} L{cx - hw},{bot - r} "
            f"A{r},{r} 0 0 0 {cx + hw},{bot - r} L{cx + hw},{top}")
    cid = f"clip{cx}_{seed}"
    s.raw(f'<defs><clipPath id="{cid}"><path d="{body} Z"/></clipPath>'
          f'<linearGradient id="gr{cid}" x1="0" y1="0" x2="0" y2="1">'
          f'<stop offset="0" stop-color="#e8907f"/><stop offset="1" stop-color="#b8453a"/>'
          f'</linearGradient></defs>')
    s.raw(f'<rect x="{cx - hw}" y="{culture_top}" width="{w}" height="{bot - culture_top}" '
          f'fill="url(#gr{cid})" clip-path="url(#{cid})"/>')
    if overlay:
        oy0, oy1 = overlay
        s.raw(f'<rect x="{cx - hw}" y="{oy0}" width="{w}" height="{oy1 - oy0}" '
              f'fill="#f6d9a8" opacity="0.92" clip-path="url(#{cid})"/>')
        s.raw(f'<line x1="{cx - hw}" y1="{oy1}" x2="{cx + hw}" y2="{oy1}" '
              f'stroke="{ORANGE}" stroke-width="2.5"/>')
    rng = random.Random(seed)
    for _ in range(26):
        bx = cx + rng.uniform(-hw + 18, hw - 18)
        by = rng.uniform(culture_top + 22, bot - 30)
        s.raw(f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="{rng.uniform(2.5, 6):.1f}" '
              f'fill="#ffffff" opacity="0.45" clip-path="url(#{cid})"/>')
    s.raw(f'<rect x="{cx - 5}" y="{top - 46}" width="10" height="{bot - 86 - top}" '
          f'rx="4" fill="#b9bfca"/>')
    for yy in (bot - 120, bot - 72):
        s.raw(f'<rect x="{cx - 44}" y="{yy}" width="88" height="11" rx="5" fill="#9aa2b1"/>')
    s.raw(f'<rect x="{cx - 34}" y="{top - 62}" width="68" height="20" rx="6" fill="#8a93a3"/>')
    s.raw(f'<path d="M{cx - hw - 52},{bot - 150} L{cx - hw - 52},{bot - 46} L{cx - 56},{bot - 46}" '
          f'fill="none" stroke="{BLUE}" stroke-width="5" stroke-linecap="round"/>')
    s.text(cx - hw - 58, bot - 158, "通氣", size=13, color=BLUE, anchor="end")
    s.raw(f'<path d="{body}" fill="none" stroke="#5b6475" stroke-width="4" '
          f'stroke-linejoin="round"/>')
    s.raw(f'<line x1="{cx - hw - 14}" y1="{top}" x2="{cx + hw + 14}" y2="{top}" '
          f'stroke="#5b6475" stroke-width="5" stroke-linecap="round"/>')


def figr3_overlay():
    s = Svg(1420, 900, "圖 3-9　為什麼沒有有機相覆蓋，你量到的產量是假的")
    s.text(40, 80, "α-farnesene 是揮發性倍半萜。它一邊被做出來，一邊從培養液裡跑掉——"
                   "你取水相去量，只會量到「還沒跑掉的那一點」。", size=15.5, color=MUTED)

    L, R = 350, 1000
    _vessel(s, L, 236, 666, 300, 356, seed=1)
    _vessel(s, R, 236, 666, 300, 356, overlay=(284, 356), seed=2)
    s.text(L, 714, "不加有機相", size=19, weight=700, anchor="middle")
    s.text(R, 714, "加十二烷覆蓋層", size=19, weight=700, anchor="middle")

    for i, yy in enumerate((222, 188, 156, 132)):
        op = 0.85 - i * 0.18
        s.raw(f'<circle cx="{L - 40 + i * 26}" cy="{yy}" r="{7 - i}" fill="{TEAL}" '
              f'opacity="{op:.2f}"/>')
        s.raw(f'<circle cx="{L + 48 + i * 22}" cy="{yy + 14}" r="{6 - i * 0.8}" '
              f'fill="{TEAL}" opacity="{op * 0.8:.2f}"/>')
    s.arrow([(L, 222), (L, 146)], color=TEAL, width=3, dash=True)
    s.text(L, 120, "產物揮發掉了", size=16, weight=700, color=TEAL, anchor="middle")
    s.icon("triangle-alert", L + 148, 176, 26, RED, 2.2)
    s.text(L + 182, 196, "量到的產量嚴重低估", size=15, weight=700, color=RED)

    import random
    for i in range(14):
        rr = random.Random(100 + i)
        s.raw(f'<circle cx="{R - 130 + rr.uniform(0, 260):.0f}" '
              f'cy="{292 + rr.uniform(0, 56):.0f}" r="{rr.uniform(3, 6):.1f}" '
              f'fill="{TEAL}" opacity="0.9"/>')
    s.arrow([(R + 212, 316), (R + 162, 316)], color=TEAL, width=3)
    s.text(R + 220, 308, "產物往上跑，", size=15, weight=700, color=TEAL)
    s.text(R + 220, 332, "被十二烷留住", size=15, weight=700, color=TEAL)
    s.text(R + 220, 372, "取樣取這一層做 GC-MS", size=14, color=MUTED)
    s.chip(R - 152, 222, "十二烷　約 20% v/v", ORANGE, size=13, icon="droplet")

    s.card(40, 752, 660, ["覆蓋層裡加 1 g/L pentadecane 當內標",
                          "因為十二烷自己也會揮發，要用不揮發的內標把損失還原回去"],
           title="還要再加一個內標", icon="flask-conical", color=ORANGE, size=14.5)
    s.card(740, 752, 640, ["Yaegashi 2017：700 mL 培養液 ＋ 150 mL 覆蓋層（約 21% v/v）",
                           "這是這株菌做倍半萜的標準配置，見第 18 章"],
           title="文獻怎麼做", icon="book-open", color=BLUE, size=14.5)
    return s


def figr1_cell():
    s = Svg(1440, 900, "圖 1-4　為什麼細菌的工具鏈不能用在酵母菌上")
    s.text(40, 80, "差別不是「比較複雜」而已，是結構上不同——而那些工具的假設，就建立在那些結構上。",
           size=15.5, color=MUTED)

    # 左：細菌（原核）
    bx, by = 330, 400
    s.raw(f'<ellipse cx="{bx}" cy="{by}" rx="210" ry="128" fill="#eef3f9" '
          f'stroke="{BLUE}" stroke-width="4"/>')
    s.raw(f'<ellipse cx="{bx}" cy="{by}" rx="198" ry="116" fill="none" '
          f'stroke="{BLUE}" stroke-width="2" opacity="0.5"/>')
    s.raw(f'<path d="M{bx - 110},{by + 10} C{bx - 60},{by - 56} {bx + 10},{by + 60} '
          f'{bx + 60},{by - 20} S{bx + 140},{by + 30} {bx + 120},{by - 2}" '
          f'fill="none" stroke="{PURPLE}" stroke-width="5" stroke-linecap="round"/>')
    import random
    rr = random.Random(7)
    for _ in range(34):
        a, b = rr.uniform(-180, 180), rr.uniform(-100, 100)
        if (a / 190) ** 2 + (b / 110) ** 2 < 1:
            s.raw(f'<circle cx="{bx + a:.0f}" cy="{by + b:.0f}" r="3.2" fill="{GREY}" '
                  f'opacity="0.5"/>')
    s.text(bx, by - 164, "細菌（原核）", size=21, weight=700, anchor="middle", color=BLUE)
    # 標籤放在橢圓左上角的外面：y 再低一點就會被細胞外框切到（橢圓越往中間越寬）
    s.line(bx - 170, by - 90, bx - 100, by - 8, color=PURPLE, width=1.4)
    s.text(bx - 286, by - 96, "DNA 散在細胞質裡", size=13.5, color=PURPLE)
    s.text(bx + 60, by + 150, "沒有胞器、沒有核膜", size=13.5, color=MUTED, anchor="middle")

    # 右：酵母（真核）
    yx, yy2 = 1020, 400
    s.raw(f'<circle cx="{yx}" cy="{yy2}" r="178" fill="#f3f0fa" stroke="{PURPLE}" '
          f'stroke-width="4"/>')
    s.raw(f'<circle cx="{yx}" cy="{yy2}" r="166" fill="none" stroke="{PURPLE}" '
          f'stroke-width="2" opacity="0.5"/>')
    # 細胞核
    s.raw(f'<circle cx="{yx - 42}" cy="{yy2 - 48}" r="62" fill="#ded5f3" '
          f'stroke="{PURPLE}" stroke-width="3"/>')
    s.raw(f'<circle cx="{yx - 42}" cy="{yy2 - 48}" r="22" fill="{PURPLE}" opacity="0.45"/>')
    s.text(yx - 42, yy2 - 48 + 5, "核", size=15, weight=700, anchor="middle", color="#ffffff")
    # 粒線體
    for mx, my, rot in ((yx + 70, yy2 - 66, -24), (yx + 88, yy2 + 28, 14)):
        s.raw(f'<g transform="translate({mx},{my}) rotate({rot})">'
              f'<rect x="-40" y="-19" width="80" height="38" rx="19" fill="#d8ecd9" '
              f'stroke="{GREEN}" stroke-width="3"/>'
              + "".join(f'<path d="M{-28 + i * 14},-15 q7,15 0,30" fill="none" '
                        f'stroke="{GREEN}" stroke-width="2.2"/>' for i in range(5))
              + '</g>')
    # 液泡
    s.raw(f'<circle cx="{yx - 78}" cy="{yy2 + 78}" r="48" fill="#dff1f2" '
          f'stroke="{TEAL}" stroke-width="3"/>')
    # 油滴（產油酵母的重點）
    for ox, oy, orr in ((yx + 22, yy2 + 92, 26), (yx + 62, yy2 + 118, 17), (yx - 12, yy2 + 126, 13)):
        s.raw(f'<circle cx="{ox}" cy="{oy}" r="{orr}" fill="#f7dfa6" stroke="{ORANGE}" '
              f'stroke-width="2.6"/>')
    s.text(yx, yy2 - 206, "酵母菌（真核）", size=21, weight=700, anchor="middle", color=PURPLE)
    for tx, ty, tt, col in ((yx - 196, yy2 - 118, "核膜包起來的染色體", PURPLE),
                            (yx + 158, yy2 - 96, "粒線體（有自己的代謝）", GREEN),
                            (yx - 212, yy2 + 118, "液泡", TEAL),
                            (yx + 120, yy2 + 150, "油滴 ← 產油酵母的本業", ORANGE)):
        s.text(tx, ty, tt, size=13.5, color=col, weight=700,
               anchor="end" if tx < yx else "start")

    s.card(40, 606, 440, ["Prokka／Bakta（細菌基因預測）", "CheckM2（細菌完整度）",
                          "GTDB-Tk（細菌分類）", "CarveMe／gapseq（細菌建模）"],
           title="這些工具不能用", icon="circle-x", color=RED, size=14.5,
           foot="它們假設「基因沒有內含子、一條環狀染色體」")
    s.card(510, 606, 440, ["BUSCO（真核完整度）", "Funannotate／BRAKER（真核基因預測）",
                           "eggNOG-mapper（功能註解）", "rhto-GEM（現成的紅酵母模型）"],
           title="要換成這些", icon="circle-check", color=GREEN, size=14.5,
           foot="第 15 章的註解流程就是這一套")
    s.card(980, 606, 420, ["胞器之間要分區隔，不能全部丟同一個池子",
                           "萜類在細胞質、油脂在細胞質與 ER、TCA 在粒線體"],
           title="模型也要跟著改", icon="layers", color=PURPLE, size=14.5,
           foot="加反應時最容易錯的就是區隔")
    return s


def fig10_vessels():
    d = json.loads((CODE / "protocol.json").read_text("utf-8"))
    need = d["kla"]["required"] if isinstance(d.get("kla"), dict) and "required" in d["kla"] \
        else None
    vs = d["vessels"]
    s = Svg(1460, 840, "圖 10-4　供氧能力決定你要用哪一種容器")
    s.text(40, 80, "模型算出來的供氧需求（OTR）要換成 kLa，再對照容器能給多少。"
                   "容器選錯，條件再準也做不出來。", size=15.5, color=MUTED)

    X0, W = 70, 1320
    n = len(vs)
    step = W // n
    for i, v in enumerate(vs):
        cx = X0 + step * i + step // 2
        col = {"可以": GREEN, "不足": RED, "綽綽有餘": BLUE}[v["fit"]]
        base = 490
        BASEY = base - 10          # 所有容器的底部對齊同一條線

        def flask(liquid_h):
            """三角燒瓶：瓶頸 (cx±20) → 瓶底 (cx±80)，液面寬度依高度算，不會溢出瓶身。"""
            s.raw(f'<path d="M{cx - 20},{base - 184} L{cx - 20},{base - 112} '
                  f'L{cx - 80},{BASEY} L{cx + 80},{BASEY} L{cx + 20},{base - 112} '
                  f'L{cx + 20},{base - 184} Z" fill="#ffffff" stroke="#5b6475" '
                  f'stroke-width="3.5" stroke-linejoin="round"/>')
            hw_top = 20 + 60 * (102 - liquid_h) / 102
            s.raw(f'<path d="M{cx - hw_top:.1f},{BASEY - liquid_h} '
                  f'L{cx + hw_top:.1f},{BASEY - liquid_h} L{cx + 80},{BASEY} '
                  f'L{cx - 80},{BASEY} Z" fill="#e8907f"/>')
            return hw_top

        if i == 0:                                    # 試管
            s.raw(f'<path d="M{cx - 26},{base - 184} L{cx - 26},{BASEY - 26} '
                  f'A26,26 0 0 0 {cx + 26},{BASEY - 26} L{cx + 26},{base - 184}" '
                  f'fill="#ffffff" stroke="#5b6475" stroke-width="3.5"/>')
            s.raw(f'<path d="M{cx - 26},{BASEY - 96} L{cx + 26},{BASEY - 96} '
                  f'L{cx + 26},{BASEY - 26} A26,26 0 0 1 {cx - 26},{BASEY - 26} Z" '
                  f'fill="#e8907f"/>')
        elif i == 1:                                  # 裝液 40%
            flask(66)
        elif i == 2:                                  # 裝液 20%
            flask(38)
        elif i == 3:                                  # 裝液 10% ＋ 擋板
            hw = flask(22)
            for dx in (-0.62, -0.22, 0.22, 0.62):     # 擋板貼著瓶壁
                x0 = cx + dx * 80
                s.raw(f'<line x1="{x0:.0f}" y1="{BASEY - 2}" x2="{x0 * 0.72 + cx * 0.28:.0f}" '
                      f'y2="{BASEY - 46}" stroke="{BROWN}" stroke-width="5" '
                      f'stroke-linecap="round" opacity="0.85"/>')
        else:                                         # 攪拌式發酵槽
            _vessel(s, cx, base - 150, BASEY, 132, base - 96, seed=9)
        s.chip(cx - 44, base + 36, v["fit"], col, size=13)
        for j, ln in enumerate(wrap(v["vessel"], 13.5, step - 26)):
            s.text(cx, base + 94 + j * 22, ln, size=13.5, anchor="middle")
        s.text(cx, base + 166, f'kLa {v["kla_lo"]}–{v["kla_hi"]}', size=16,
               weight=700, anchor="middle", color=col)
        s.text(cx, base + 190, "h⁻¹", size=12, anchor="middle", color=MUTED)

    s.box(40, 704, 1380, 108, "", color=TEAL, fill=tint(TEAL, 0.94))
    s.icon("gauge", 72, 736, 26, TEAL, 2.1)
    s.text(116, 758, "怎麼換算", size=18, weight=700)
    s.text(116, 790, "需要的 kLa ＝ 需要的 OTR ÷ 飽和溶氧。"
                     "算出來之後照上面挑容器——「不足」的就算條件全對也長不起來。", size=15)
    return s

def fig13_resources():
    s = Svg(1480, 960, "圖 13-1　你會用到的資料庫與資源：按「想問什麼」分")
    s.text(40, 80, "資源不是越多越好。先問「我現在要回答哪一個問題」，再去對應的那一格。",
           size=15.5, color=MUTED)

    groups = [
        (40, 140, "這株菌是什麼？", "scan-search", BLUE,
         [("NCBI Taxonomy", "物種分類與命名"),
          ("JGI MycoCosm", "真菌基因體，**你的 IFO 0880 在這裡**"),
          ("菌種保存中心", "BCRC／NBRC／ATCC／DSMZ，查編號與來源")],
         "先確定菌名與編號，後面才查得到"),
        (510, 140, "它有哪些基因？", "dna", PURPLE,
         [("UniProt", "蛋白質功能與結構域"),
          ("KEGG", "代謝路徑與 EC 編號"),
          ("InterPro／eggNOG", "結構域與直系同源群")],
         "拿基因名來查它催化什麼"),
        (980, 140, "有沒有現成的模型？", "cpu", TEAL,
         [("BiGG Models", "品質最好的 GEM 收錄庫"),
          ("rhto-GEM（GitHub）", "**紅酵母就用這個**，不要用 Yeast8"),
          ("MetaNetX", "不同模型之間的 id 對照")],
         "有現成的就不要從頭建（第 3、15 章）"),
        (40, 496, "怎麼培養？", "flask-conical", ORANGE,
         [("BacDive", "培養條件的結構化資料"),
          ("MediaDive", "培養基配方"),
          ("保存中心的菌株頁", "官方建議的培養基與溫度")],
         "基因體算不出溫度與 pH（第 7 章）"),
        (510, 496, "別人做到哪了？", "book-open", GREEN,
         [("PubMed", "同儕審查的文獻"),
          ("bioRxiv", "預印本，比期刊快半年到一年"),
          ("Google Scholar", "追引用，找到後續的研究")],
         "新舊學名都要試（見下方）"),
        (980, 496, "程式與工具？", "github", BROWN,
         [("GitHub", "工具與模型的原始碼"),
          ("Bioconda", "生資工具的安裝來源"),
          ("COBRApy 文件", "代謝模型的操作")],
         "用之前先跑第 8 章的五個問題"),
    ]
    for x, y, title, ic, col, items, foot in groups:
        s.box(x, y, 460, 316, "", color=col, fill=tint(col, 0.95))
        s.icon(ic, x + 26, y + 30, 26, col, 2.1)
        s.text(x + 64, y + 52, title, size=19, weight=700, color=col)
        s.line(x + 26, y + 70, x + 434, y + 70, color=col)
        yy = y + 106
        for name, what in items:
            s.text(x + 26, yy, name, size=15, weight=700)
            yy += 23
            for ln in wrap(what, 13.5, 408):
                s.text(x + 26, yy, ln, size=13.5, color=MUTED)
                yy += 20
            yy += 15
        for j, ln in enumerate(wrap(foot, 13.5, 408)):
            s.text(x + 26, y + 286 + j * 20, ln, size=13.5, weight=700, color=col)

    s.box(40, 836, 1400, 100, "", color=RED, fill=tint(RED, 0.95))
    s.icon("triangle-alert", 72, 866, 26, RED, 2.1)
    s.text(116, 888, "兩個查資料時最常犯的錯", size=18, weight=700)
    s.text(116, 920, "① 用舊學名查不到：*Rhodosporidium toruloides* 與 *Rhodotorula toruloides* "
                     "是同一種，兩個都要試。　② 把資料庫的預測值當實測值——"
                     "KEGG 的路徑是推定的，不是你的菌真的有。", size=14.5)
    return s


def fig2_clues():
    """基因體給的是「起始範圍」，不是最適條件。"""
    s = Svg(1460, 1000, "圖 2-2　從基因體找培養條件的線索：拿到的是起始範圍，不是答案")
    s.text(40, 80, "這一步常被跳過，但它能省下很多瞎試的時間。"
                   "**注意它產出的是「掃描範圍」，不是「最適值」**——最適值只有實驗能給。",
           size=15.5, color=MUTED)

    srcs = [
        (40, BLUE, "scan-search", "① 查近緣菌株已知的條件",
         ["GTDB-Tk 找最近緣的已知菌種", "BacDive 查溫度、pH、需氧性",
          "MediaDive 查培養基配方"],
         "最可靠的一條：那是別人量出來的"),
        (500, PURPLE, "cpu", "② 用基因體特徵預測",
         ["最適生長溫度：已有 ML 模型", "pH 偏好：2023 年找出相關基因",
          "誤差不小，只能定起始範圍"],
         "當粗略指針用，不要當結論"),
        (960, TEAL, "dna", "③ 從註解推培養基",
         ["有沒有固氮基因 → 要不要加氮源", "缺哪些維生素／胺基酸路徑",
          "能不能吃便宜碳源（木糖、乙酸）"],
         "第 3、4 章的模型能把這一條系統化"),
    ]
    for x, col, ic, name, items, foot in srcs:
        s.box(x, 140, 420, 276, "", color=col, fill=tint(col, 0.95))
        s.icon(ic, x + 26, 170, 26, col, 2.1)
        s.text(x + 64, 192, name, size=18, weight=700, color=col)
        s.line(x + 26, 212, x + 394, 212, color=col)
        yy = 248
        for it in items:
            for ln in wrap("・" + it, 14.5, 368):
                s.text(x + 26, yy, ln, size=14.5)
                yy += 23
            yy += 7
        for j, ln in enumerate(wrap(foot, 14, 368)):
            s.text(x + 26, 382 + j * 21, ln, size=14, weight=700, color=col)
        s.arrow([(x + 210, 418), (x + 210, 456)], color=col, width=2.6)

    # 起始條件卡
    s.box(40, 464, 1340, 290, "", color=GREEN, fill=tint(GREEN, 0.95))
    s.icon("file-text", 72, 494, 26, GREEN, 2.1)
    s.text(116, 516, "產出：一張「起始條件卡」", size=20, weight=700, color=GREEN)
    s.text(420, 516, "（下面是示範格式與示範數值，換成你的菌的結果）", size=14, color=MUTED)
    cols = [(92, 150, "項目"), (252, 430, "線索來源"), (700, 400, "實驗怎麼掃"),
            (1120, 232, "誰給的")]
    for x, w, h in cols:
        s.text(x, 566, h, size=15.5, weight=700, color=GREEN)
    s.line(72, 580, 1348, 580, color=GREEN)
    rows = [("溫度", "近緣菌株 30–37 °C；預測最適 35 °C", "掃 25–42 °C", "①＋②"),
            ("pH", "近緣菌株 6.5–7.5", "掃 5.5–8.5", "①"),
            ("氧氣", "有完整呼吸鏈，也有發酵路徑", "好氧長菌、限氧產物都試", "③"),
            ("碳源", "有木糖代謝基因", "葡萄糖為基準，加測木糖", "③"),
            ("營養缺陷", "缺維生素 B12 合成基因", "培養基補 B12", "③")]
    for i, (a, b, c, d) in enumerate(rows):
        y = 612 + i * 28
        s.text(92, y, a, size=14.5, weight=700)
        s.text(252, y, b, size=14.5)
        s.text(700, y, c, size=14.5)
        s.text(1120, y, d, size=14.5, color=MUTED)

    s.card(40, 788, 660, ["基因體說「有木糖代謝基因」，不等於「用木糖長得好」",
                          "預測模型的誤差動輒好幾度，只夠決定掃描範圍",
                          "註解本身就有錯誤率，缺一個基因可能只是沒註解到"],
           title="它給不了什麼", icon="circle-x", color=RED, size=14.5,
           foot="所以這張卡的欄位叫「實驗怎麼掃」，不叫「最適值」")
    s.card(740, 788, 640, ["把掃描範圍縮到做得完的大小（第 7 章的實驗設計）",
                           "避免一開始就漏掉必需的營養而白做一批",
                           "讓第 3 章建模型時知道該放哪些交換反應"],
           title="它真正的價值", icon="circle-check", color=GREEN, size=14.5,
           foot="省下的是「瞎試」的時間，不是「做實驗」的時間")
    return s



def figr3_independent():
    """兩個互不知情的方法得到同一個答案——以及唯一不吻合的那一項。"""
    a = json.loads((CODE / "annotation.json").read_text("utf-8"))
    c = json.loads((CODE / "case_rt.json").read_text("utf-8"))
    d = a["delta"]
    ap = a["afs_predicted"]
    copies = c["wt_afs_copies"]
    intact = sum(1 for x in copies if x["intact"])
    site = a["insertion_site"]

    s = Svg(1480, 1100, "圖 3-10　兩個獨立方法得到同一個答案")
    s.text(40, 80, "一個只比對鹼基、不管功能；一個只看蛋白質結構域、不知道構築長什麼樣子。"
                   "**兩邊對上了，結論才算數。**", size=15.5, color=MUTED)

    L, R, W = 40, 780, 660
    s.box(L, 140, W, 92, "", color=BLUE, fill=tint(BLUE, 0.93))
    s.icon("dna", L + 26, 168, 26, BLUE, 2.1)
    s.text(L + 64, 190, "方法 A：k-mer 錨點追蹤", size=19, weight=700, color=BLUE)
    s.text(L + 26, 218, "拿構築序列去基因體上逐鹼基比對。不知道那是什麼基因。", size=14, color=MUTED)

    s.box(R, 140, W, 92, "", color=PURPLE, fill=tint(PURPLE, 0.93))
    s.icon("scan-search", R + 26, 168, 26, PURPLE, 2.1)
    s.text(R + 64, 190, "方法 B：定序廠的功能註解", size=19, weight=700, color=PURPLE)
    s.text(R + 26, 218, "AUGUSTUS 預測基因，再用 Pfam／KEGG 比對結構域。不知道有構築。",
           size=14, color=MUTED)

    rows = [
        (f'{len(copies)} 個 AFS 拷貝', f'萜類合成酶 {d["terpene_synthase"]["wt"]} 個'
         f'（另一株 {d["terpene_synthase"]["mut"]} 個）'),
        ('T-DNA 進去 11–12 份', f'GNAT 乙醯轉移酶 {d["gnat"]["wt"]} vs {d["gnat"]["mut"]}'
         f'，差 {d["gnat"]["delta"]} 個'),
        ('骨架 2–3 份', f'RepA／Resolvase／ParA 各 {d["rep_initiator"]["wt"]} vs '
         f'{d["rep_initiator"]["mut"]}'),
        (f'{intact} 個與設計零差異、1 個斷掉',
         f'{ap["n"] - 1} 個同長度、1 個長度不同'),
    ]
    for i, (a_txt, b_txt) in enumerate(rows):
        y = 268 + i * 62
        s.box(L, y, W, 52, "", color=BLUE, fill="#ffffff")
        for j, ln in enumerate(wrap(a_txt, 15, W - 48)):
            s.text(L + 24, y + 32 + j * 20, ln, size=15)
        s.box(R, y, W, 52, "", color=PURPLE, fill="#ffffff")
        for j, ln in enumerate(wrap(b_txt, 15, W - 48)):
            s.text(R + 24, y + 32 + j * 20, ln, size=15)
        s.icon("equal", 722, y + 14, 24, GREEN, 2.4)

    s.box(40, 528, 1400, 86, "", color=GREEN, fill=tint(GREEN, 0.93))
    s.icon("circle-check", 72, 556, 26, GREEN, 2.1)
    s.text(116, 578, "四項全部對上", size=19, weight=700, color=GREEN)
    s.text(116, 604, "拷貝數不是 k-mer 方法的假象。剩下要解釋的只有一件事："
                     "為什麼標示為基改株的那一份反而沒有插入。", size=15)

    s.card(40, 646, 700, [
        f'AUGUSTUS 把 {ap["exon_counts"].get("3", 0)} 個拷貝切成 3 個 exon，'
        f'預測成 {max(ap["aa_counts"], key=lambda k: ap["aa_counts"][k])} aa',
        f'正確答案是**單一 exon、{ap["true_aa"]} aa**——AFS 是 cDNA 來的，本來就沒有內含子',
        "AUGUSTUS 是真核預測器，它的先驗就是「基因有內含子」",
    ], title="但有一項不吻合", icon="triangle-alert", color=RED, size=14.5,
        foot="直接拿這份 GFF 做 RNA-seq 計數，AFS 的讀序會被分到錯的轉錄本模型上")

    s.card(770, 646, 670, [
        "先用 annotation.py 的 fix-gff 把陣列那段換成單 exon 模型",
        "11 個拷貝序列完全相同，計數時要當成**一個單位**，不要分 11 個基因算",
        "修過之後翻譯驗證：11 個都是 576 aa、起頭 MEFRVHLQA",
    ], title="所以要先修再用", icon="wrench" if False else "settings", color=GREEN, size=14.5,
        foot="這一步不修不會報錯，只會讓表現量算錯——和第 3 章資料洩漏同一類的坑")

    u, dn = site["upstream"], site["downstream"]
    gid = lambda g: g["id"].replace("_", "\\_")   # noqa: E731  svgkit 的 _ 是下標記號
    s.box(40, 880, 1400, 190, "", color=BROWN, fill=tint(BROWN, 0.95))
    s.icon("map-pin" if False else "target", 72, 910, 26, BROWN, 2.1)
    s.text(116, 932, "順便回答了一個之前答不出來的問題：插入點有沒有打斷基因", size=19,
           weight=700, color=BROWN)
    s.text(72, 972, f'沒有。{site["contig"]} {site["start"]:,}–{site["end"]:,} 落在兩個基因**之間**：'
                    f'上游 {gid(u)} 隔 {u["distance_bp"]} bp、下游 {gid(dn)} 隔 '
                    f'{dn["distance_bp"]} bp。', size=15)
    s.text(72, 1004, f'但 **下游只隔 {dn["distance_bp"]} bp**——76 kb 的陣列幾乎確定坐在 '
                     f'{gid(dn)} 的啟動子區裡，那個基因的表現很可能被改掉了。', size=15)
    s.text(72, 1036, "而且這兩個鄰居在註解裡沒有任何 KEGG／GO／Pfam 命中，"
                     "所以「被影響的是什麼」目前答不出來。", size=15, color=MUTED)
    return s



def figr3_site():
    """白話版：那 76 kb 插在哪裡，動到了什麼。"""
    a = json.loads((CODE / "annotation.json").read_text("utf-8"))
    s_ = a["insertion_site"]
    up, dn = s_["upstream"], s_["downstream"]

    s = Svg(1460, 1020, "圖 3-11　那段外來 DNA 插在哪裡：兩個基因中間的空地")
    s.text(40, 80, "基因在染色體上不是一個挨著一個，中間有空地。"
                   "這次 76,217 bp 的外來 DNA **正好插在空地上**——所以沒有壓壞任何一個基因。",
           size=15.5, color=MUTED)

    GA, GB = TEAL, BLUE
    # ── 上排：插入之前 ──
    y = 160
    s.text(40, y - 16, "插入之前", size=19, weight=700)
    s.box(40, y, 300, 76, "基因 A", color=GA, size=18, sub="它的結尾在這裡", sub_size=13)
    s.raw(f'<rect x="352" y="{y}" width="340" height="76" rx="8" fill="#f3f4f7" '
          f'stroke="#c7ccd6" stroke-width="2" stroke-dasharray="7 5"/>')
    s.text(522, y + 34, "空地", size=18, weight=700, anchor="middle", color=MUTED)
    s.text(522, y + 58, "240 bp，沒有基因", size=13.5, anchor="middle", color=MUTED)
    s.box(704, y, 300, 76, "基因 B", color=GB, size=18, sub="它的開頭在這裡", sub_size=13)
    s.text(1032, y + 30, "基因 B 的「開關」就住在", size=14, color=GB, weight=700)
    s.text(1032, y + 54, "空地靠近它的那一段", size=14, color=GB, weight=700)

    # ── 下排：插入之後 ──
    y2 = 332
    s.text(40, y2 - 16, "插入之後", size=19, weight=700)
    s.box(40, y2, 300, 76, "基因 A", color=GA, size=18, sub="完好", sub_size=13)
    s.raw(f'<rect x="352" y="{y2}" width="92" height="76" rx="6" fill="#f3f4f7" '
          f'stroke="#c7ccd6" stroke-width="2"/>')
    s.text(398, y2 + 42, f'{up["distance_bp"] + 1} bp', size=13.5, anchor="middle", color=MUTED)
    s.raw(f'<rect x="452" y="{y2}" width="80" height="76" rx="6" fill="{tint(RED, 0.9)}" '
          f'stroke="{RED}" stroke-width="2" stroke-dasharray="5 4"/>')
    s.text(492, y2 + 36, "59 bp", size=13.5, anchor="middle", weight=700, color=RED)
    s.text(492, y2 + 58, "被鏟掉", size=13, anchor="middle", color=RED)
    # 外來 DNA：比例差太多，中間用斷尺符號
    s.raw(f'<rect x="540" y="{y2}" width="574" height="76" rx="8" fill="{tint(PURPLE, 0.86)}" '
          f'stroke="{PURPLE}" stroke-width="2.5"/>')
    s.raw(f'<path d="M812,{y2} l-14,38 l14,38" fill="none" stroke="#ffffff" stroke-width="5"/>')
    s.raw(f'<path d="M826,{y2} l-14,38 l14,38" fill="none" stroke="#ffffff" stroke-width="5"/>')
    s.text(676, y2 + 34, "外來 DNA 陣列", size=18, weight=700, anchor="middle", color=PURPLE)
    s.text(676, y2 + 58, "76,217 bp（圖上畫不下，中間折斷）", size=12.5, anchor="middle", color=PURPLE)
    s.text(972, y2 + 44, "12 份產物基因", size=13.5, anchor="middle", color=PURPLE)
    s.raw(f'<rect x="1122" y="{y2}" width="46" height="76" rx="6" fill="{tint(ORANGE, 0.88)}" '
          f'stroke="{ORANGE}" stroke-width="2"/>')
    s.text(1145, y2 + 44, f'{dn["distance_bp"] - 1}', size=13.5, anchor="middle",
           weight=700, color=ORANGE)
    s.text(1145, y2 + 104, f'只剩 {dn["distance_bp"] - 1} bp', size=13, anchor="middle",
           color=ORANGE, weight=700)
    s.text(1145, y2 + 126, "原本的開關區", size=13, anchor="middle", color=ORANGE)
    s.box(1180, y2, 240, 76, "基因 B", color=GB, size=18, sub="本體完好", sub_size=13)

    s.card(40, 496, 440, ["基因 B 做出來的蛋白質和原本**逐字完全相同**",
                          "1,441 個胺基酸，一個都沒差",
                          "基因 A 也一樣，沒有被切到"],
           title="好消息：基因本身都沒事", icon="circle-check", color=GREEN, size=15,
           foot="所以這不是「把某個基因打壞了」的那種基改")

    s.card(510, 496, 440, [f'開關區原本有 240 bp，現在只剩 {dn["distance_bp"] - 1} bp',
                           "基因還在，但它「什麼時候開、開多大」",
                           "很可能已經不照原本的規則了"],
           title="壞消息：基因 B 的開關被蓋住", icon="triangle-alert", color=ORANGE, size=15,
           foot="開關＝基因前面那一小段 DNA，決定這個基因何時工作")

    s.card(980, 496, 440, ["KEGG、GO、Pfam 三個資料庫都查不到",
                           "在這株菌自己的蛋白質裡也找不到親戚",
                           "所以「被影響的是什麼功能」現在答不出來"],
           title="問題：基因 B 是做什麼的？", icon="circle-help", color=RED, size=15,
           foot="序列已經抽出來放在 code/insertion-neighbours/，拿去 BLAST 就知道")

    s.box(40, 756, 1380, 118, "", color=BLUE, fill=tint(BLUE, 0.95))
    s.icon("lightbulb", 72, 786, 26, BLUE, 2.1)
    s.text(116, 808, "「開關」是什麼意思", size=18, weight=700)
    s.text(72, 844, "每個基因前面都有一小段不會被做成蛋白質的 DNA，它決定這個基因什麼時候開工、開多大。"
                    "把它換掉，基因本身還是好的，", size=15)
    s.text(72, 868, "但它可能在該忙的時候睡覺、在該休息的時候加班——"
                    "所以「基因沒壞」和「基因照常工作」是兩件事。", size=15)

    s.box(40, 896, 1380, 104, "", color=GREEN, fill=tint(GREEN, 0.94))
    s.icon("target", 72, 924, 26, GREEN, 2.1)
    s.text(116, 946, "怎麼確認它到底有沒有被影響", size=18, weight=700)
    s.text(72, 982, "拿兩株菌做 RNA-seq，比較基因 B 的表現量差多少。這是唯一直接的辦法——"
                    "而且用 annotation.py 修過的 GFF 就能做。", size=15)
    return s


def figr3_fpp_users():
    """白話版：FPP 是好幾個人共用的一桶原料。"""
    s = Svg(1480, 1040, "圖 3-12　FPP 這桶原料，本來就有六個人在用")
    s.text(40, 80, "轉進去的酵素不是去搶一個沒人要的東西。**FPP 是細胞裡的共用原料**，"
                   "原本就有六條路在拿它，現在多了第七條。", size=15.5, color=MUTED)

    CX, CY = 300, 440
    s.raw(f'<rect x="{CX - 130}" y="{CY - 80}" width="260" height="160" rx="16" '
          f'fill="{tint(TEAL, 0.84)}" stroke="{TEAL}" stroke-width="3"/>')
    s.text(CX, CY - 24, "FPP", size=34, weight=700, anchor="middle", color=TEAL)
    s.text(CX, CY + 10, "一桶共用的原料", size=16, anchor="middle")
    s.text(CX, CY + 40, "（法呢基焦磷酸）", size=13, anchor="middle", color=MUTED)

    s.box(40, 170, 520, 92, "", color=BROWN, fill=tint(BROWN, 0.93))
    s.icon("droplet", 68, 198, 24, BROWN, 2.1)
    s.text(104, 218, "更上游：乙醯輔酶A", size=18, weight=700, color=BROWN)
    s.text(68, 248, "做 FPP 要先有它——而**油脂也跟它拿**，這才是搶碳的主戰場。", size=14.5)
    s.arrow([(300, 266), (300, 356)], color=BROWN, width=3)

    users = [
        (GREEN, "leaf", "麥角固醇", "細胞膜的硬度調節",
         "膜太軟太硬都長不好；這條不能關掉"),
        (RED, "sun", "類胡蘿蔔素", "紅色色素、抗氧化",
         "就是害 OD600 量不準的那個"),
        (PURPLE, "link", "蛋白質的「標籤」", "讓訊息蛋白黏得住膜",
         "量很少，但少了訊息傳不出去"),
        (BLUE, "zap", "泛醌（CoQ）", "呼吸鏈的送電員",
         "常被忘記；它出問題會先反映在耗氧量"),
        (ORANGE, "layers", "dolichol", "幫蛋白質接糖鏈的輸送帶",
         "常被忘記；它出問題細胞壁會變弱"),
        (GREY, "cpu", "heme A", "呼吸鏈最後一棒的零件",
         "常被忘記；也是呼吸那一邊的"),
    ]
    for i, (col, ic, name, what, note) in enumerate(users):
        yy = 170 + i * 128
        x = 700
        s.box(x, yy, 740, 104, "", color=col, fill=tint(col, 0.95))
        s.icon(ic, x + 24, yy + 26, 24, col, 2.1)
        s.text(x + 60, yy + 46, name, size=18, weight=700, color=col)
        s.text(x + 230, yy + 46, what, size=15.5)
        s.text(x + 24, yy + 80, note, size=14, color=MUTED)
        s.arrow([(CX + 132, CY), (620, CY), (620, yy + 52), (x - 4, yy + 52)],
                color=col, width=2.2)

    s.raw(f'<rect x="700" y="938" width="740" height="88" rx="10" '
          f'fill="{tint(TEAL, 0.88)}" stroke="{TEAL}" stroke-width="3"/>')
    s.icon("star", 724, 962, 24, TEAL, 2.2)
    s.text(760, 982, "α-farnesene", size=18, weight=700, color=TEAL)
    s.text(930, 982, "你要的產物（第七個來拿原料的）", size=15.5)
    s.text(724, 1012, "12 份拷貝一起拿——但實際拿走多少，要量了才知道", size=14, color=MUTED)
    s.arrow([(CX + 132, CY), (620, CY), (620, 982), (696, 982)], color=TEAL, width=3)

    s.card(40, 560, 520, ["這六條分支是生化課本上的事實",
                          "但**你的菌被搶走多少，目前沒有數據**",
                          "而且很可能小到量不出來"],
           title="這張圖是在講「有哪些人在排隊」", icon="circle-alert", color=MUTED, size=14.5,
           foot="不是在講「每個人被搶走多少」——那要實驗才知道")

    s.card(40, 790, 520, ["把色素全部關掉，最多換回 1–5 mg/g 產物",
                          "同一時間，油脂是 500–700 mg/g",
                          "所以真正該動的是油脂那一邊，不是色素"],
           title="一個有數字的例子", icon="chart-column", color=BROWN, size=14.5,
           foot="算法見 17.9；用異戊二烯單元換算")
    return s




# ───────────────────────────────────────────────────────────────
# 第 19 章的圖。全部畫在 1000 px 寬、內文 ≥17 px——
# Folio 把圖縮到 880 px，這樣縮完還有 15 px，看得清楚。
# ───────────────────────────────────────────────────────────────
WR4 = 1000
T_TITLE, T_H, T_BODY, T_NOTE = 26, 20, 17, 15


def _wf():
    return json.loads((CODE / "workflow.json").read_text("utf-8"))



def figr3_blast():
    """BLASTp 查鄰居基因的結果：沒查到功能，但解決了三件事。"""
    b = json.loads((CODE / "blast_neighbours.json").read_text("utf-8"))
    L = b["query"]["len"]
    core_a, core_b = b["conservation"]["core_blocks"][0]
    lc = b["composition"][0]
    tm = b["hydrophobic"][0]
    far = b["conservation"]["n_far_hits"]
    named = len(b["named_hits"])

    s = Svg(1000, 1060, "圖 3-13　BLAST 查完那個鄰居：沒查到功能，但解決了三件事")
    s.text(40, 78, f'把那個 {L} 個胺基酸的鄰居丟進 blastp，{b["n_hits"]} 筆命中裡'
                   f'**只有 {named} 筆有名字，而且都靠不住**。', size=17, color=MUTED)

    X0, X1, Y, H = 64, 936, 190, 54
    px = lambda a: X0 + (X1 - X0) * (a - 1) / (L - 1)  # noqa: E731

    s.text(40, Y - 26, "這個蛋白質長什麼樣", size=20, weight=700, color=INK)
    # 低複雜度區
    s.box(px(1), Y, px(lc["to"]) - px(1), H, "", color=BROWN, fill=tint(BROWN, 0.9))
    s.text((px(1) + px(lc["to"])) / 2, Y + 24, "低複雜度區", size=18, weight=700,
           anchor="middle", color=BROWN)
    s.text((px(1) + px(lc["to"])) / 2, Y + 45, f'P＋A＋S＋T 佔 {lc["spta_pct"]}%',
           size=15, anchor="middle", color=MUTED)
    # 保守核心
    s.box(px(core_a), Y, px(core_b) - px(core_a), H, "", color=TEAL, fill=tint(TEAL, 0.88))
    s.text((px(core_a) + px(core_b)) / 2, Y + 24, "保守核心", size=18, weight=700,
           anchor="middle", color=TEAL)
    s.text((px(core_a) + px(core_b)) / 2, Y + 45, f'{core_b - core_a + 1} aa',
           size=15, anchor="middle", color=MUTED)
    # 疏水段
    s.raw(f'<rect x="{px(tm["from"]):.1f}" y="{Y - 9}" width="{px(tm["to"]) - px(tm["from"]):.1f}" '
          f'height="{H + 18}" rx="4" fill="{ORANGE}" opacity="0.85"/>')
    s.arrow([(px(tm["from"]) - 60, Y - 44), (px(tm["from"]) - 6, Y - 14)], color=ORANGE, width=2.2)
    s.text(px(tm["from"]) - 66, Y - 48, f'疑似膜錨 {tm["from"]}–{tm["to"]}',
           size=15, weight=700, anchor="end", color=ORANGE)

    for a in (1, lc["to"], L):
        s.line(px(a), Y + H, px(a), Y + H + 8, color=MUTED, width=1.4)
        s.text(px(a), Y + H + 28, str(a), size=15, anchor="middle", color=MUTED)

    # 插入點：貼著起始密碼子畫，不要放到別的區塊去
    s.arrow([(px(1), Y + H + 74), (px(1), Y + H + 44)], color=RED, width=2.6)
    s.text(px(1) + 16, Y + H + 70, "插入點在這裡（起始密碼子前 39 bp）"
                                   "——**在基因外面，不在裡面**", size=17, weight=700, color=RED)

    # 保守度剖面：只有遠緣物種還留著的那一段，就是核心
    PY_ = Y + H + 136
    s.text(40, PY_ - 6, f'遠緣物種（{far} 筆種外命中）還保留哪一段',
           size=17, weight=700, color=MUTED)
    prof = b["conservation"]["profile"]
    bw = (X1 - X0) / len(prof)
    for i, f in enumerate(prof):
        h = max(2, f * 54)
        col = TEAL if f >= 0.5 else C["hairline"]
        s.raw(f'<rect x="{X0 + i * bw:.1f}" y="{PY_ + 16 + 54 - h:.1f}" width="{bw - 1.6:.1f}" '
              f'height="{h:.1f}" fill="{col}"/>')
    s.text(X0 + (X1 - X0) * 0.24, PY_ + 58, "N 端這一半只有自己這一種留著",
           size=15, anchor="middle", color=MUTED)

    y = PY_ + 100
    # 先畫比較高的那一張，再用它的高度把另一張補齊，兩張才會切齊
    hh = s.card(520, y, 440, [
        f'{b["n_hits"] - named} 筆是 hypothetical／uncharacterized',
        "「proteophosphoglycan ppg4」是低複雜度區造成的誤標",
        "「UDP-galactose transporter」只有 31% 相似、覆蓋 35%",
    ], title="沒問出來的", icon="circle-alert", color=RED, size=16,
        foot="功能仍然不知道——而且這是結論，不是失敗")
    s.card(40, y, 440, [
        f'{b["n_hits"]} 筆命中、{len(b["genera"])} 個屬，**全部是紅酵母與近緣真菌**',
        "相似度隨親緣遞減：同種 96→83%、同屬 40–47%、更遠的 31–39%",
        "同種的 3 筆從第 1 個胺基酸就對得上",
    ], title="問出來的", icon="circle-check", color=GREEN, size=16,
        foot="所以這是一個真的基因，不是註解程式亂猜出來的", min_h=hh)

    s.card(40, y + hh + 26, 920, [
        "**查 Coradetti 2018 的適應度資料**——那份 T-DNA 突變庫做在 IFO 0880，和你的參考基因體同一株。先把這條蛋白質比回 JGI 拿到基因編號，再去查那篇的補充檔，不用做實驗就可能有表型",
        "**用結構找遠親**（HHpred／Foldseek／AlphaFold DB）——只拿保守核心那段去比。BLASTp 看不到的遠源相似，結構看得到",
        "**上游那個 423 aa 的鄰居還沒查**——序列就在 upstream.faa，同一套流程再跑一次",
    ], title="下一步，照這個順序", icon="list-checks", color=BLUE, size=16,
        foot="但不管查不查得到，兩株的生長曲線一比就知道有沒有影響——那是第一批實驗本來就會做的")
    return s



# ── 第 20 章：把 rhto-GEM 跑起來 ────────────────────────────────────────

WR5 = 1000


def _demo():
    return json.loads((CODE / "rhto_demo.json").read_text("utf-8"))


def figr5_run():
    """六個指令：每一步問什麼、看什麼、會踩什麼坑。"""
    s = Svg(WR5, 1060, "圖 5-1　把 rhto-GEM 跑起來：六個指令")
    s.text(40, 78, "每一步都先看一個東西再往下走。**跳過第 2 步是最常見的失敗方式。**",
           size=17, color=MUTED)

    steps = [
        ("check", "模型長什麼樣、長不長得起來", "區隔有十幾個嗎？只有 1–2 個代表你載到細菌模型了",
         BLUE, "search"),
        ("find", "用名字查出你要的反應 id", "**不要把 r_#### 寫死**。版本一換就安靜地找不到",
         RED, "key"),
        ("medium", "設碳源與 C/N，跑 FBA", "μ 是 0 就別往下走——先把培養基調對", ORANGE, "beaker"),
        ("afs", "把 α-farnesene 那條反應加進去", "碳上限超過 100% ＝ 你的反應沒配平", PURPLE,
         "git-branch"),
        ("envelope", "生產包絡線", "下限是 0 ＝ 菌可以不做產物，要靠條件逼它", TEAL, "chart-line"),
        ("scan", "掃 C/N 與 ERG9 調降", "拿來**排序選項**，不要拿來預測數字", GREEN, "list-checks"),
    ]
    X, BW, y = 64, 600, 150
    for i, (cmd, what, trap, col, icon) in enumerate(steps):
        s.box(X, y, BW, 112, "", color=col, fill=tint(col, 0.95))
        s.icon(icon, X + 24, y + 26, 24, col, 2.1)
        s.text(X + 60, y + 36, f"{i + 1}　rhto.py {cmd}", size=21, weight=700, color=col)
        s.text(X + 60, y + 64, what, size=17)
        for j, ln in enumerate(wrap(trap, 15, BW - 92)):
            s.text(X + 60, y + 90 + j * 20, ln, size=15, color=MUTED)
        if i < len(steps) - 1:
            s.arrow([(X + BW / 2, y + 112), (X + BW / 2, y + 150)], color=MUTED, width=2.4)
        y += 150

    s.card(700, 150, 260, [
        "pip install cobra",
        "git clone 那個 repo",
        "ls model/*.xml",
    ], title="先做這三件事", icon="terminal", color=INK, size=16,
        foot="模型檔要自己下載，這個環境沒有網路")
    s.card(700, 420, 260, [
        "路徑寫 textbook",
        "指令、輸出、會踩的坑都一樣",
        "只有數字不同",
    ], title="不想等下載？", icon="circle-help", color=BROWN, size=16,
        foot="先把流程走一遍，省掉很多來回")
    return s


def figr5_cn():
    """C/N 這個實驗室語言，怎麼翻譯成模型裡的吸收速率。"""
    s = Svg(WR5, 786, "圖 5-2　C/N 怎麼變成模型看得懂的數字")
    s.text(40, 78, "實驗室說「C/N 要 40」，模型只認得「每小時吸收幾毫莫耳」。中間差一個換算。",
           size=17, color=MUTED)

    s.box(64, 136, 400, 150, "", color=BROWN, fill=tint(BROWN, 0.94))
    s.text(84, 174, "實驗室的語言", size=20, weight=700, color=BROWN)
    s.text(84, 210, "40 公克葡萄糖", size=18)
    s.text(84, 240, "2.2 公克硫酸銨", size=18)
    s.text(84, 270, "C/N（莫耳）＝ 40", size=17, weight=700, color=BROWN)

    s.arrow([(480, 211), (552, 211)], color=INK, width=2.6)

    s.box(568, 136, 368, 150, "", color=BLUE, fill=tint(BLUE, 0.94))
    s.text(588, 174, "模型的語言", size=20, weight=700, color=BLUE)
    s.text(588, 210, "葡萄糖吸收 10 mmol/gDW/h", size=18)
    s.text(588, 240, "銨吸收 1.5 mmol/gDW/h", size=18)
    s.text(588, 270, "（上限，不是實際值）", size=15, color=MUTED)

    s.text(40, 352, "換算公式（可以自己驗算）", size=20, weight=700)
    s.box(64, 376, 872, 76, "", color=TEAL, fill=tint(TEAL, 0.94))
    s.text(500, 408, "氮吸收速率 ＝ 6 × 葡萄糖吸收速率 ÷ (C/N)", size=22, weight=700,
           anchor="middle", color=TEAL)
    s.text(500, 436, "葡萄糖一個分子 6 個碳，銨一個分子 1 個氮——就只是這樣", size=15,
           anchor="middle", color=MUTED)

    rows = [(10, 6.0, "氮充足：菌專心長"), (40, 1.5, "中間"), (120, 0.5, "限氮：生長被壓住")]
    s.text(40, 510, "三個 C/N 實際設下去的值（葡萄糖固定 10）", size=20, weight=700)
    hy = 538
    s.raw(f'<rect x="64" y="{hy}" width="872" height="44" rx="8" fill="{C["hairline"]}"/>')
    for x, lab in ((120, "C/N"), (300, "銨吸收上限"), (560, "這一瓶在問什麼")):
        s.text(x, hy + 29, lab, size=17, weight=700, color=MUTED)
    for i, (cn, n, why) in enumerate(rows):
        ry = hy + 44 + i * 50
        if i % 2 == 0:
            s.raw(f'<rect x="64" y="{ry}" width="872" height="50" fill="#fafafa"/>')
        col = (TEAL, ORANGE, RED)[i]
        s.text(120, ry + 32, str(cn), size=19, weight=700, color=col)
        s.text(300, ry + 32, f"{n:.1f} mmol/gDW/h", size=18)
        s.text(560, ry + 32, why, size=17, color=MUTED)
    s.text(64, 740, "※ 這三個就是第 19 章那三瓶。模型先算一次，實驗再做一次，兩邊才對得起來。",
           size=15, color=MUTED)
    return s


def figr5_limits():
    """rhto-GEM 算得出什麼、算不出什麼，以及接回第 19 章的哪一步。"""
    s = Svg(WR5, 830, "圖 5-3　跑完之後：算得出什麼、算不出什麼")
    s.text(40, 78, "模型最危險的地方不是算錯，是**算得出來但你以為它算的是別的東西**。",
           size=17, color=MUTED)

    h = s.card(40, 128, 450, [
        "理論上最多能做多少（碳的上限）",
        "調降 ERG9，產物會不會上升",
        "哪幾個改動值得花三個月試",
        "哪些反應你的菌沒有對應基因",
        "在某個 C/N 下，生長的上限是多少",
    ], title="算得出來", icon="circle-check", color=GREEN, size=16,
        foot="共通點：都是「上限」和「排序」")
    s.card(510, 128, 450, [
        "實際會做多少（差一個數量級）",
        "**限氮會不會累積油脂**——FBA 裡限氮只是把生長壓低",
        "基因有沒有在表現（11 個拷貝都在，不代表在工作）",
        "改完要多久看到效果",
        "溫度、pH 的影響",
    ], title="算不出來", icon="circle-alert", color=RED, size=16,
        foot="這些只能用實驗量，或用 dFBA 另外算", min_h=h)

    y = 128 + h + 34
    s.text(40, y, "算出來之後，接回第 19 章的第 ⑤ 和第 ③ 步", size=21, weight=700, color=INK)
    y += 24
    items = [
        ("生產包絡線", "告訴你「還要不要再改菌株」", "→ 第 19 章第 ⑤ 步：挑條件", PURPLE),
        ("C/N 掃描", "給你一個先驗的預期，實驗去推翻它", "→ 第 19 章第 ⑥ 步：那三瓶", ORANGE),
        ("生長速率 μ", "**還不能填進介面**——那要實驗擬合出來的參數", "→ 第 19 章第 ③ 步卡在這", RED),
    ]
    for i, (what, why, to, col) in enumerate(items):
        yy = y + 20 + i * 96
        s.box(40, yy, 920, 80, "", color=col, fill=tint(col, 0.96))
        s.text(64, yy + 32, what, size=19, weight=700, color=col)
        s.text(64, yy + 62, why, size=16)
        s.text(936, yy + 48, to, size=16, weight=700, anchor="end", color=col)
    return s



# ── 第 21 章：核對別人做的模型 ──────────────────────────────────────────

WR6 = 1000


def _afs():
    return json.loads((CODE / "rhto_afs.json").read_text("utf-8"))


def figr6_audit():
    """核對清單：七項自己重算，對上了幾項。"""
    d = _afs()
    v, e = d["verify"], d["envelope_default"]
    s = Svg(WR6, 1032, "圖 6-1　別人給的模型，我自己重算一次")
    s.text(40, 78, "**不是重述它的說法，是把每個數字自己再跑一次。** "
                   "七項裡六項完全對上，一項要加註解。", size=17, color=MUTED)

    rows = [
        ("模型規模", f'{d["model"]["reactions"]} 反應、{d["model"]["metabolites"]} 代謝物、'
                     f'{d["model"]["genes"]} 基因', "對上", GREEN),
        ("AFS 反應配平", "質量與電荷都平衡，沒有偷加質子", "對上", GREEN),
        ("關掉 AFS", f'產物 ＝ {v["afs_off_product"]:.0f}', "對上", GREEN),
        ("漏洞檢查",
         f'關掉 {v["carbon_inputs_closed"]} 個含碳輸入後產物 ＝ {v["no_carbon_product"]:.0f}',
         "對上", GREEN),
        ("最大生長", f'μ ＝ {e["mu_max"]:.8f} /h（小數點後八位一樣）', "對上", GREEN),
        ("生產包絡線", "六個點逐一重算，全部相同", "對上", GREEN),
        ("碳產率",
         f'模型 {max(r["carbon_yield"] for r in e["rows"])*100:.1f}%　'
         f'教科書 MVA 上限 {d["textbook_carbon_yield"]*100:.1f}%',
         "要加註解", ORANGE),
    ]
    y = 150
    for name, detail, verdict, col in rows:
        s.box(40, y, 920, 76, "", color=col, fill=tint(col, 0.96))
        s.icon("circle-check" if col is GREEN else "circle-alert", 64, y + 26, 22, col, 2.1)
        s.text(100, y + 32, name, size=19, weight=700, color=col)
        s.text(100, y + 60, detail, size=16)
        s.text(936, y + 44, verdict, size=17, weight=700, anchor="end", color=col)
        y += 92

    c = d["carbon_route"]
    s.card(40, y + 14, 920, [
        f'模型走的是**磷酸酮醇酶**（通量 {c["phosphoketolase"]}），不是丙酮酸脫氫酶'
        f'（{c["pyruvate_dehydrogenase"]}）',
        "那條路不會在丙酮酸那一步掉一個 CO₂，所以碳效率比教科書的 MVA 算法高",
        "**數字沒錯，但它預設了這條捷徑在你的菌裡真的在跑**——那件事沒有人驗過",
    ], title="為什麼碳產率比教科書高", icon="git-branch", color=ORANGE, size=16,
        foot="誠實的講法：55.6%（經典路線）到 60.8%（含捷徑）之間")
    return s


def figr6_glucose():
    """葡萄糖吸收上限：模型預設太低，調高又變成長太快。"""
    d = _afs()["glucose_scan"]
    s = Svg(WR6, 870, "圖 6-2　那個 μ ＝ 0.074 不是你的菌長得慢")
    s.text(40, 78, "模型的生長速率**完全由你給的糖吸收上限決定**。"
                   "預設值 1.0 太低，調到 10 又變成兩倍快得離譜。", size=17, color=MUTED)

    X0, X1, Y, H = 90, 700, 170, 380
    mus = [r["mu_max"] for r in d]
    lo, hi = 0, max(mus) * 1.12
    sy = lambda v: Y + H - (v - lo) / (hi - lo) * H   # noqa: E731
    s.arrow([(X0, Y + H), (X1 + 20, Y + H)], color=INK, width=2.2)
    s.arrow([(X0, Y + H), (X0, Y - 16)], color=INK, width=2.2)
    s.text(40, Y - 28, "μmax（每小時）", size=16, weight=700, color=MUTED)
    s.text(X1 + 30, Y + H + 6, "糖吸收上限", size=16, weight=700, color=MUTED)

    # 真實的紅酵母大概落在 0.2–0.35
    s.raw(f'<rect x="{X0}" y="{sy(0.35):.1f}" width="{X1 - X0 + 20}" '
          f'height="{sy(0.20) - sy(0.35):.1f}" fill="{tint(GREEN, 0.85)}"/>')
    s.text(X1 + 30, (sy(0.35) + sy(0.20)) / 2 + 6, "文獻上紅酵母", size=15, weight=700, color=GREEN)
    s.text(X1 + 30, (sy(0.35) + sy(0.20)) / 2 + 28, "大概在這一帶", size=15, weight=700, color=GREEN)

    bw = (X1 - X0) / (len(d) + 0.6)
    for i, r in enumerate(d):
        x = X0 + 20 + i * bw
        col = GREEN if 0.20 <= r["mu_max"] <= 0.35 else (RED if r["mu_max"] > 0.5 else BLUE)
        s.raw(f'<rect x="{x:.1f}" y="{sy(r["mu_max"]):.1f}" width="{bw * 0.62:.1f}" '
              f'height="{Y + H - sy(r["mu_max"]):.1f}" rx="4" fill="{col}"/>')
        s.text(x + bw * 0.31, sy(r["mu_max"]) - 10, f'{r["mu_max"]:.2f}', size=15,
               weight=700, anchor="middle", color=col)
        s.text(x + bw * 0.31, Y + H + 26, str(r["glucose_uptake"]), size=17, anchor="middle")
        s.text(x + bw * 0.31, Y + H + 50, f'{r["doubling_h"]:.1f} h', size=14,
               anchor="middle", color=MUTED)
    s.text(X0 + 20 + 0.31 * bw, Y + H + 76, "↑ 模型預設", size=15, weight=700,
           anchor="middle", color=BLUE)

    s.card(40, 650, 920, [
        "**模型沒有「酵素做得多快」這個限制**，所以糖給越多就長越快，沒有上限",
        "真實的細胞有上限——那個上限只能從你自己的生長曲線量出來（第 11 章）",
        "所以這張圖不是在問「哪一格是對的」，是在說**這個參數現在是空的**",
    ], title="為什麼會這樣", icon="circle-help", color=BLUE, size=16,
        foot="這正好就是第 19 章第 ③ 步卡住的那個參數")
    return s


def figr6_erg9():
    """ERG9 調降：兩種比法給出完全相反的結論。"""
    d = _afs()["erg9_scan"]
    s = Svg(WR6, 900, "圖 6-3　調降 ERG9 到底有沒有用：兩種比法，相反的答案")
    s.text(40, 78, "ERG9 和 AFS 搶同一桶 FPP，所以「把它調小」聽起來很合理。"
                   "**但怎麼比，決定你得到什麼答案。**", size=17, color=MUTED)

    rows = [r for r in d["rows"] if r["afs_at_half_own_growth"] is not None]
    cols = [("保留比例", lambda r: f'{r["erg9_fraction"]*100:.0f}%', INK),
            ("μmax", lambda r: f'{r["mu_max"]:.3f}', MUTED),
            ("產物（各自一半生長）", lambda r: f'{r["afs_at_half_own_growth"]:.3f}', ORANGE),
            ("產物（固定同一個生長）", lambda r: f'{r["afs_at_fixed_growth"]:.3f}', TEAL)]
    xs = [110, 280, 520, 800]
    hy = 150
    s.raw(f'<rect x="40" y="{hy}" width="920" height="48" rx="8" fill="{C["hairline"]}"/>')
    for x, (lab, _, col) in zip(xs, cols):
        s.text(x, hy + 31, lab, size=16, weight=700, anchor="middle", color=col)
    for i, r in enumerate(rows):
        ry = hy + 48 + i * 52
        if i % 2 == 0:
            s.raw(f'<rect x="40" y="{ry}" width="920" height="52" fill="#fafafa"/>')
        for x, (_, fn, col) in zip(xs, cols):
            s.text(x, ry + 34, fn(r), size=18, weight=700 if col is not MUTED else 400,
                   anchor="middle", color=col)
    by = hy + 48 + len(rows) * 52 + 24

    h = s.card(40, by, 450, [
        "**多 81%**：ERG9 調到 10%，產物 1.38 升到 2.50",
        "看起來值得做一個菌株",
    ], title="用「各自一半生長」比", icon="triangle-alert", color=ORANGE, size=16,
        foot="但每一列的生長速率都不一樣，不能這樣比")
    s.card(510, by, 450, [
        "把生長固定在同一個數字再比",
        "**產物完全沒變，每一格都是 2.383**",
    ], title="用「固定生長」比", icon="circle-check", color=TEAL, size=16,
        foot="ERG9 根本不是瓶頸", min_h=h)

    s.card(40, by + h + 24, 920, [
        f'ERG9 在最大生長時的實際通量只有 **{d["erg9_flux_at_max_growth"]} mmol/gDW/h**，'
        f'而它的上限是 1000——**差六萬倍**',
        "前面那個「多 81%」，全部來自「生長變慢了，碳有剩」，和搶 FPP 無關",
        "**而要讓生長變慢，限氮就做得到，不用做菌株**",
    ], title="為什麼", icon="search", color=RED, size=16,
        foot="模型說的是「化學計量上 ERG9 不是瓶頸」；它沒有排除動力學上的競爭")
    return s


def figr6_cn():
    """C/N 掃描：模型給的先驗預期。"""
    d = _afs()["cn_scan"]
    s = Svg(WR6, 836, "圖 6-4　模型對那三瓶的預期")
    s.text(40, 78, "C/N 越高，菌長得越慢、但碳剩得越多。"
                   "**這是模型的預期，不是預測——實驗就是去推翻它的。**", size=17, color=MUTED)

    X0, X1, Y, H = 110, 660, 160, 360
    mu_hi = max(r["mu_max"] for r in d) * 1.15
    af_hi = max(r["afs_at_half_growth"] for r in d) * 1.15
    sx = lambda i: X0 + (X1 - X0) * i / (len(d) - 1)        # noqa: E731
    syl = lambda v: Y + H - v / mu_hi * H                    # noqa: E731
    syr = lambda v: Y + H - v / af_hi * H                    # noqa: E731
    s.arrow([(X0, Y + H), (X1 + 24, Y + H)], color=INK, width=2.2)
    s.text(X0 - 20, Y - 24, "生長 μmax", size=16, weight=700, color=BLUE)
    s.text(X1 - 60, Y - 24, "產物上限", size=16, weight=700, color=PURPLE)
    s.arrow([(sx(i), syl(d[i]["mu_max"])) for i in range(len(d))], color=BLUE, width=3)
    s.arrow([(sx(i), syr(d[i]["afs_at_half_growth"])) for i in range(len(d))],
            color=PURPLE, width=3)
    for i, r in enumerate(d):
        s.raw(f'<circle cx="{sx(i):.1f}" cy="{syl(r["mu_max"]):.1f}" r="6" fill="{BLUE}"/>')
        s.raw(f'<circle cx="{sx(i):.1f}" cy="{syr(r["afs_at_half_growth"]):.1f}" r="6" '
              f'fill="{PURPLE}"/>')
        s.text(sx(i), Y + H + 28, str(int(r["c_n_molar"])), size=17, weight=700, anchor="middle")
        s.text(sx(i), syl(r["mu_max"]) - 14, f'{r["mu_max"]:.2f}', size=14,
               anchor="middle", color=BLUE)
        s.text(sx(i), syr(r["afs_at_half_growth"]) - 14, f'{r["afs_at_half_growth"]:.2f}',
               size=14, anchor="middle", color=PURPLE)
    s.text((X0 + X1) / 2, Y + H + 56, "C/N（莫耳比）", size=16, weight=700,
           anchor="middle", color=MUTED)

    s.card(700, 160, 260, [
        "低 C/N：長得快、產物低",
        "高 C/N：長得慢、產物高",
        "**沒有轉折點**，是單調的",
    ], title="模型說", icon="chart-line", color=INK, size=15,
        foot="因為 FBA 裡限氮只是把生長壓低")
    s.card(40, 590, 920, [
        "17.9 推論「限氮對 farnesene 不利」（限氮催油脂、油脂搶乙醯輔酶A）",
        "這張圖說「限氮對 farnesene 有利」（碳沒被拿去長菌）",
        "**兩個都成立，因為講的是不同的機制**——模型只算化學計量，完全不管調控",
    ], title="這和第 17 章打架嗎？沒有", icon="scan-search", color=BROWN, size=16,
        foot="誰贏？第 19 章那三瓶做完就知道了。這正是那三瓶值錢的地方")
    return s



def figr5_bounds():
    """上下限是什麼：它是圍欄，不是實際速度。"""
    s = Svg(WR5, 940, "圖 5-4　「上下限」是什麼意思")
    s.text(40, 78, "每條反應在模型裡都有一個速度。**上下限是你給它的圍欄**——"
                   "算出來的速度只能落在圍欄裡面。", size=17, color=MUTED)

    rows = [
        ("最低 0、最高 1000", "只能往前跑，最快 1000",
         "**1000 是模型的「無限大」。寫 1000 等於沒有限制。**", GREY),
        ("最低 −1000、最高 1000", "往前往後都可以", "可逆反應", BLUE),
        ("最低 0、最高 0", "這條路被關掉了", "**剔除基因就是把它設成這樣**", RED),
        ("最低 −10", "交換反應：負號代表「從外面進到細胞裡」",
         "這條是「最多吸收 10」", TEAL),
    ]
    y = 142
    for b, what, why, col in rows:
        s.box(40, y, 920, 86, "", color=col, fill=tint(col, 0.96))
        for k, ln in enumerate(wrap(b, 18, 240)):
            s.text(64, y + 34 + k * 24, ln, size=18, weight=700, color=col)
        s.text(330, y + 32, what, size=17)
        for k, ln in enumerate(wrap(why, 15, 600)):
            s.text(330, y + 58 + k * 20, ln, size=15, color=MUTED)
        y += 100

    y += 20
    s.text(40, y, "最高 1000 不是「這個酵素跑得了這麼快」", size=21, weight=700, color=INK)
    s.text(40, y + 28, "是「我們沒有去限制它」。這兩件事差很多。", size=17, color=MUTED)

    BY = y + 62
    X0, X1 = 64, 690
    s.text(X0, BY - 8, "ERG9 這條反應", size=16, weight=700, color=MUTED)
    s.raw(f'<rect x="{X0}" y="{BY + 6}" width="{X1 - X0}" height="40" rx="8" '
          f'fill="{tint(GREY, 0.9)}" stroke="{GREY}" stroke-width="1.6"/>')
    s.text(X0 + 14, BY + 32, "容許上限 1000", size=17, weight=700, color=GREY)
    w = max(3, (X1 - X0) * 0.016364 / 1000)
    s.raw(f'<rect x="{X0}" y="{BY + 58}" width="{w:.1f}" height="28" rx="4" fill="{RED}"/>')
    s.arrow([(X0 + 150, BY + 116), (X0 + 10, BY + 90)], color=RED, width=2.2)
    s.text(X0 + 160, BY + 120, "實際只跑 0.016　← 就是左邊那一小條", size=17,
           weight=700, color=RED)

    s.card(714, BY - 18, 246, [
        "把上限從 1000 改成 100",
        "還是比 0.016 大六千倍",
        "**等於沒碰到它**",
    ], title="所以", icon="circle-alert", color=ORANGE, size=15,
        foot="第 21.3 節第一版就是這樣錯的")

    s.text(40, BY + 168, "要真的壓住一條反應，上限要設成**它實際跑多快**的幾分之幾，"
                         "不是容許上限的幾分之幾。", size=17, weight=700, color=INK)
    return s



def figr6_compare():
    """WT 和 A13 到底差在哪：基因體差很多，模型只差一條。"""
    a = json.loads((CODE / "annotation.json").read_text("utf-8"))
    d = a["delta"]
    s = Svg(WR6, 1040, "圖 6-5　野生株和 A13 到底差在哪")
    s.text(40, 78, "三個層次看同一件事。**往下走，差別越來越小**——"
                   "不是因為菌變像了，是因為每一層看得到的東西不一樣。", size=17, color=MUTED)

    LEV = [
        ("① 基因體（定序逐字比對）", "差很多", RED, [
            "多了一段 **76,217 bp** 的外來 DNA（Contig3 943,094–1,019,311）",
            "AFS 完整拷貝 **11 份**；野生株 **0 份**",
            "插入時鏟掉 **59 bp**，但全部落在兩個基因中間的空地上",
            "**單一位點、沒有重排**",
        ]),
        ("② 功能註解（定序廠自己跑的）", "差得出來", ORANGE, [
            f'萜類合成酶：A13 **{d["terpene_synthase"]["wt"]}** 個、野生株 **{d["terpene_synthase"]["mut"]}** 個',
            f'GNAT 乙醯轉移酶（篩選標記）：**{d["gnat"]["wt"]}** vs **{d["gnat"]["mut"]}**，多 {d["gnat"]["delta"]} 個',
            f'質體骨架（RepA／Resolvase／ParA）：各 **{d["rep_initiator"]["wt"]}** vs **0**',
            "預測蛋白總數 8,421 vs 8,386",
        ]),
        ("③ 代謝模型", "**只差一條反應**", TEAL, [
            "A13 多了一條 AFS 反應、一條產物運輸、一條產物出口——**就這三條**",
            "其餘 2,723 條反應、2,277 個代謝物**完全一樣**",
            "兩株的最大生長速率**一模一樣**（0.07398512）",
        ]),
    ]
    y = 140
    for title, verdict, col, items in LEV:
        h = 54 + len(items) * 26 + 18
        s.box(40, y, 920, h, "", color=col, fill=tint(col, 0.96))
        s.text(64, y + 34, title, size=19, weight=700, color=col)
        s.text(936, y + 34, verdict, size=18, weight=700, anchor="end", color=col)
        yy = y + 62
        for it in items:
            for ln in wrap("・" + it, 16, 850):
                s.text(64, yy, ln, size=16)
                yy += 24
            yy += 2
        y += h + 20

    ch = s.card(40, y + 10, 920, [
        "**模型只差一條，不是因為兩株菌真的只差這麼多。**",
        "是因為這個模型就是「拿野生株的模型、加一條反應」做出來的——"
        "**差別是手動放進去的，不是算出來的**。",
        "所以**不能**用「兩株模型算出一樣的生長速率」去說「基改沒有造成負擔」。"
        "那個結論模型根本沒資格講。",
    ], title="最重要的一句", icon="circle-alert", color=RED, size=16,
        foot="要知道有沒有負擔，只有一個辦法：把兩株的生長曲線放在一起比")

    s.text(40, y + ch + 38, "※ 同一個酵素在兩株有不同的基因編號（定序廠分別給的流水號）。"
                            "那是編號問題，不是生物差異。", size=15, color=MUTED)
    return s



def figr0_roadmap():
    """新分區的導覽圖：七章串起來在回答什麼。"""
    s = Svg(1000, 1040, "圖 0-1　這個分區在回答什麼")
    s.text(40, 78, "一株基改紅酵母，從定序檔一路做到「下一批實驗該怎麼做」。"
                   "**七章，每一章解決一個卡住的地方。**", size=17, color=MUTED)

    steps = [
        ("1", "換成酵母菌", "細菌的工具鏈全部不適用。先換掉註解流程和模型來源", BROWN),
        ("2", "基改菌株", "插進去的基因怎麼變成模型裡的一條反應；生產包絡線怎麼看", PURPLE),
        ("3", "案例：定序比對", "76 kb 串聯陣列、11 份拷貝、插入點在哪、鄰居是什麼", RED),
        ("4", "文獻精讀", "同一株菌八年從 261 mg/L 到 20.8 g/L，三步怎麼走的", ORANGE),
        ("5", "完整流程", "七個步驟串成一條路，最後落在一份可執行的操作單", BLUE),
        ("6", "把模型跑起來", "rhto-GEM 從下載到第一條生產包絡線，六個指令", TEAL),
        ("7", "核對別人的模型", "拿到別人交回來的東西怎麼驗收；調降 ERG9 為什麼沒用", GREEN),
    ]
    X, BW, y = 64, 640, 150
    for no, title, what, col in steps:
        s.box(X, y, BW, 92, "", color=col, fill=tint(col, 0.95))
        s.raw(f'<circle cx="{X + 34}" cy="{y + 46}" r="19" fill="{col}"/>')
        s.text(X + 34, y + 53, no, size=20, weight=700, anchor="middle", color="#ffffff")
        s.text(X + 70, y + 38, title, size=20, weight=700, color=col)
        for i, ln in enumerate(wrap(what, 16, BW - 100)):
            s.text(X + 70, y + 66 + i * 21, ln, size=16, color=MUTED)
        if no != "7":
            s.arrow([(X + BW / 2, y + 92), (X + BW / 2, y + 122)], color=MUTED, width=2.2)
        y += 122

    s.card(730, 150, 230, [
        "紅酵母 **IFO 8766**",
        "蘋果的 α-farnesene 合成酶",
        "農桿菌隨機嵌入",
        "**11 份完整拷貝**",
    ], title="這株菌", icon="dna", color=INK, size=15,
        foot="定序比對已經確定，不用重跑")
    s.card(730, 420, 230, [
        "產物到底有多少",
        "11 份拷貝有沒有在表現",
        "限氮催不催產物",
    ], title="還沒解決", icon="circle-help", color=RED, size=15,
        foot="三件都只能靠實驗")
    s.card(730, 700, 230, [
        "rhto.py　跑模型",
        "rhto\\_afs.py　驗收",
        "線上看板（第 7 章）",
    ], title="工具", icon="terminal", color=BLUE, size=15,
        foot="都在 code/ 底下")
    return s


def figr4_flow():
    """整條流程的標準流程圖：膠囊＝起訖、方框＝步驟、菱形＝判斷。"""
    s = Svg(WR4, 1580, "圖 4-1　整條流程")
    s.text(40, 78, "中間是主流程，左邊是「不通過要做什麼」，右邊是「這一步產出什麼」。",
           size=T_BODY, color=MUTED)

    CX, BW = 500, 460          # 主流程置中
    X = CX - BW / 2
    y = 118

    def note(side, yy, txt, col):
        """左右兩側的註記。左邊 = 不通過的出口，右邊 = 產出。"""
        if side == "L":
            s.arrow([(X + 20, yy), (X - 26, yy)], color=col, width=2.2)
            lines = wrap(txt, T_NOTE, 200)
            for i, ln in enumerate(lines):
                s.text(X - 36, yy - 6 - (len(lines) - 1) * 10 + i * 21, ln,
                       size=T_NOTE, color=col, anchor="end", weight=700)
        else:
            s.arrow([(X + BW + 4, yy), (X + BW + 40, yy)], color=col, width=2.2)
            for i, ln in enumerate(wrap(txt, T_NOTE, 180)):
                s.text(X + BW + 50, yy - 6 + i * 21, ln, size=T_NOTE, color=MUTED)

    def down(y0, y1, label=""):
        s.arrow([(CX, y0), (CX, y1)], color=GREY, width=2.6)
        if label:
            s.text(CX + 14, (y0 + y1) / 2 + 5, label, size=T_NOTE, weight=700, color=GREEN)

    s.stadium(X, y, BW, 70, "開始：定序檔 ＋ 構築序列", color=INK, size=T_H)
    y += 70

    steps = [
        ("① 確認菌是什麼", BROWN, "菌種、倍體性、參考基因體"),
        ("② 確認基改進去了沒", PURPLE, "拷貝數、位置、壞掉的拷貝"),
    ]
    for name, col, out in steps:
        down(y, y + 34)
        y += 34
        s.box(X, y, BW, 88, name, color=col, size=T_H)
        note("R", y + 44, out, col)
        y += 88

    down(y, y + 34)
    y += 34
    s.diamond(CX, y + 55, 420, 110, "兩管的標籤對嗎？", color=RED, size=T_H)
    note("L", y + 55, "送樣時貼反了（見 17.2）", RED)
    s.text(CX - 150, y + 48, "否", size=T_NOTE, weight=700, color=RED)
    y += 110

    down(y, y + 34, "是")
    y += 34
    s.box(X, y, BW, 88, "③ 註解與修正", color=BLUE, size=T_H)
    note("R", y + 44, "基因位置檔、鄰居身分", BLUE)
    y += 88

    y4 = None
    for name, col, out in (("④ 建代謝模型", TEAL, "可以跑 FBA 的模型"),
                           ("⑤ 用模型挑條件", ORANGE, "一張很短的條件清單")):
        down(y, y + 34)
        y += 34
        s.box(X, y, BW, 88, name, color=col, size=T_H)
        note("R", y + 44, out, col)
        if y4 is None:
            y4 = y + 44
        y += 88

    down(y, y + 34)
    y += 34
    s.box(X, y, BW, 108, "⑥ 做實驗", color=GREEN, size=24,
          sub="整條流程唯一產生真實數字的一步", sub_size=T_NOTE)
    s.raw(f'<rect x="{X - 6}" y="{y - 6}" width="{BW + 12}" height="120" rx="14" '
          f'fill="none" stroke="{GREEN}" stroke-width="2.5" stroke-dasharray="8 5"/>')
    note("R", y + 54, "生長曲線、產物、表現量", GREEN)
    y += 108

    down(y, y + 34)
    y += 34
    s.box(X, y, BW, 88, "⑦ 把數據餵回模型", color=PURPLE, size=T_H)
    note("R", y + 44, "修正過的參數", PURPLE)
    y += 88

    down(y, y + 34)
    y += 34
    dy = y + 55
    s.diamond(CX, dy, 420, 110, "產量夠了嗎？", color=ORANGE, size=T_H)
    s.text(CX - 150, dy - 7, "否", size=T_NOTE, weight=700, color=ORANGE)
    y += 110

    down(y, y + 34, "是")
    y += 34
    s.stadium(X, y, BW, 70, "放大，或進下一輪改菌株", color=GREEN, size=T_H)

    # 回饋迴圈：產量不夠 → 回到 ④
    s.arrow([(CX - 210, dy), (150, dy), (150, y4), (X - 4, y4)],
            color=ORANGE, width=2.6, dash=True)
    s.text(162, y4 - 16, "回到 ④ 重挑條件", size=T_NOTE, weight=700, color=ORANGE)

    # 圖例（跟著最後一個膠囊走，不要寫死，不然會壓到它）
    ly = y + 70 + 58
    s.line(40, ly - 28, 960, ly - 28, color=C["hairline"])
    s.stadium(40, ly, 150, 48, "起訖", color=GREY, size=T_NOTE)
    s.box(226, ly, 150, 48, "步驟", color=GREY, size=T_NOTE)
    s.diamond(487, ly + 24, 150, 48, "判斷", color=GREY, size=T_NOTE)
    s.text(600, ly + 30, "虛線＝不滿意就回頭再做一輪", size=T_NOTE, color=MUTED)
    return s



def figr4_model_is():
    """代謝模型聽起來很抽象，其實就是一張很長的表。"""
    s = Svg(WR4, 880, "圖 4-2　代謝模型其實就是一張表")
    s.text(40, 78, "「建模型」聽起來很抽象。打開來看，它就是**一張很長的反應表**，"
                   "一列一個反應。", size=T_BODY, color=MUTED)

    X, W = 40, 920
    cols = [(0, 150, "這個反應在做什麼"), (150, 420, "方程式"),
            (570, 170, "哪個基因做的"), (740, 180, "最多能跑多快")]
    HY = 128
    s.raw(f'<rect x="{X}" y="{HY}" width="{W}" height="46" rx="8" fill="{tint(BLUE, 0.86)}"/>')
    for dx, cw, name in cols:
        s.text(X + dx + 14, HY + 31, name, size=T_BODY, weight=700, color=BLUE)

    rows = [("糖進到細胞裡", "葡萄糖（外） → 葡萄糖（內）", "HXT 家族", "10"),
            ("糖解第一步", "葡萄糖 ＋ ATP → G6P ＋ ADP", "HXK1", "不限"),
            ("⋯⋯", "⋯⋯", "⋯⋯", "⋯"),
            ("做出 FPP", "C5 ＋ C10 → FPP（C15）", "ERG20", "不限"),
            ("做麥角固醇", "2 × FPP → 角鯊烯", "ERG9", "不限"),
            ("**你轉進去的那一列**", "**FPP → α-farnesene ＋ PPi**", "**AFS（蘋果來的）**", "不限"),
            ("長菌（生物量）", "胺基酸 ＋ 核苷酸 ＋ 膜脂 ＋ ATP → 1 g 菌", "（不是單一基因）", "不限")]
    y = HY + 46
    for i, (what, eq, gene, ub) in enumerate(rows):
        hi = "AFS" in gene
        h = 44
        s.raw(f'<rect x="{X}" y="{y}" width="{W}" height="{h}" '
              f'fill="{tint(TEAL, 0.88) if hi else ("#ffffff" if i % 2 else "#f7f8fa")}" '
              f'stroke="{TEAL if hi else C["hairline"]}" stroke-width="{2.2 if hi else 1}"/>')
        for (dx, cw, _), val in zip(cols, (what, eq, gene, ub)):
            s.text(X + dx + 14, y + 29, val, size=T_BODY if hi else 16,
                   color=TEAL if hi else INK)
        y += h

    s.text(X, y + 34, "這種列，整個模型有幾千條——把細胞已知的代謝全部寫進去。",
           size=T_BODY, weight=700)
    s.text(X, y + 62, "確切幾條打開來數就知道：len(model.reactions)。", size=T_NOTE,
           color=MUTED)

    s.card(40, y + 90, 450, [
        "每個代謝物**進來的量 ＝ 出去的量**（質量守恆）",
        "每條反應有速度上限（酵素就那麼多）",
        "輸入固定（你餵多少糖、給多少氧）",
    ], title="模型只用三條規則", icon="ruler", color=BLUE, size=T_BODY,
        foot="就這三條。沒有動力學、沒有時間")

    s.card(520, y + 90, 440, [
        "**基因 → 酵素 → 反應**，這張表把三者連起來",
        "所以「剔除某個基因」＝「把那一列關掉」",
        "你轉進去的 AFS，就是多加一列",
    ], title="為什麼它和基因有關", icon="dna", color=TEAL, size=T_BODY,
        foot="第 16 章在做的就是「多加一列」這件事")
    return s


def figr4_fba():
    """FBA 在算什麼：四條反應的小例子，算術自己看得懂。"""
    s = Svg(WR4, 1046, "圖 4-3　FBA 在算什麼")
    s.text(40, 78, "用四條反應就能說完。看懂這張，幾千條的版本只是同一件事放大。",
           size=T_BODY, color=MUTED)

    # 小網路
    s.box(40, 176, 180, 72, "糖", color=BROWN, size=T_H, sub="你餵進去的", sub_size=T_NOTE)
    s.box(330, 176, 180, 72, "中間物 A", color=BLUE, size=T_H)
    s.box(620, 110, 180, 72, "長菌", color=GREEN, size=T_H)
    s.box(620, 248, 180, 72, "產物", color=TEAL, size=T_H)
    s.arrow([(222, 212), (328, 212)], color=GREY, width=3, label="v₁ ＝ 10", label_dy=-14,
            size=T_BODY, label_color=INK)
    s.arrow([(512, 196), (570, 196), (570, 146), (618, 146)], color=GREEN, width=3)
    s.text(584, 136, "v₂", size=T_BODY, weight=700, color=GREEN)
    s.arrow([(512, 228), (570, 228), (570, 284), (618, 284)], color=TEAL, width=3)
    s.text(584, 304, "v₃", size=T_BODY, weight=700, color=TEAL)

    s.box(830, 176, 150, 72, "", color=BLUE, fill=tint(BLUE, 0.9))
    s.text(905, 204, "A 要平衡", size=T_NOTE, weight=700, anchor="middle", color=BLUE)
    s.text(905, 230, "v₁ ＝ v₂ ＋ v₃", size=T_BODY, weight=700, anchor="middle")

    s.text(40, 376, "問題來了：滿足「v₂ ＋ v₃ ＝ 10」的組合有無限多種", size=T_H, weight=700)

    X, W = 40, 920
    head = [(0, 220, "一種可能的分配"), (220, 180, "v₂（長菌）"), (400, 180, "v₃（產物）"),
            (580, 340, "")]
    s.raw(f'<rect x="{X}" y="406" width="{W}" height="44" rx="8" fill="{tint(GREY, 0.9)}"/>')
    for dx, cw, name in head:
        if name:
            s.text(X + dx + 14, 436, name, size=T_BODY, weight=700)
    opts = [("全部拿去長菌", "10", "0", "產物 0，這台細胞不幫你做東西"),
            ("全部拿去做產物", "0", "10", "菌不長，一下就死光"),
            ("一半一半", "5", "5", "都可以，但哪一個才是真的？"),
            ("⋯ 還有無限多組", "⋯", "⋯", "")]
    y = 450
    for i, (name, v2, v3, note) in enumerate(opts):
        s.raw(f'<rect x="{X}" y="{y}" width="{W}" height="44" '
              f'fill="{"#ffffff" if i % 2 else "#f7f8fa"}" stroke="{C["hairline"]}"/>')
        s.text(X + 14, y + 29, name, size=16)
        s.text(X + 234, y + 29, v2, size=T_BODY, weight=700, color=GREEN)
        s.text(X + 414, y + 29, v3, size=T_BODY, weight=700, color=TEAL)
        s.text(X + 594, y + 29, note, size=15, color=MUTED)
        y += 44

    s.box(40, y + 30, 920, 96, "", color=ORANGE, fill=tint(ORANGE, 0.92))
    s.icon("lightbulb", 70, y + 56, 26, ORANGE, 2.2)
    s.text(112, y + 78, "FBA 就是多問一句話：「哪一組讓某個東西最大？」", size=T_H,
           weight=700, color=ORANGE)
    s.text(70, y + 110, "平衡方程式本身不會給你答案。加上一個目標，答案就唯一了。",
           size=T_BODY)

    yy = y + 158
    s.card(40, yy, 450, [
        "**目標：讓生長最大** → v₂ ＝ 10、v₃ ＝ 0",
        "這是野生菌的預設行為",
        "模型預測的生長速率，可以拿實驗曲線去對",
    ], title="問法一", icon="chart-line", color=GREEN, size=T_BODY,
        foot="對得起來，代表模型大致可信")

    s.card(520, yy, 440, [
        "**目標：生長至少 3，再讓產物最大**", "→ v₂ ＝ 3、v₃ ＝ 7",
        "換一個生長下限，就換一組答案",
        "把所有下限掃過一遍，連成一條線",
    ], title="問法二", icon="target", color=TEAL, size=T_BODY,
        foot="那條線就是第 16 章的「生產包絡線」")
    return s



def figr4_to_ui():
    """有了 rhto-GEM，能不能直接丟進模擬器？——不能，中間還有五步。"""
    s = Svg(WR4, 1180, "圖 4-4　有了模型，能直接放進介面嗎？")
    s.text(40, 78, "**不能。** 介面讀的不是模型，是**事先算好的查表**。中間還有五件事要做。",
           size=T_BODY, color=MUTED)

    s.para(40, 118, 400, 64, "rhto-GEM.xml", color=TEAL, size=T_H)
    s.text(470, 158, "你下載回來的模型檔", size=T_NOTE, color=MUTED)

    steps = [
        (GREEN, "容易", "① 改一行：讀你的模型",
         "gem.py 的 load() 改成 read\\_sbml\\_model('rhto.xml')", "五分鐘"),
        (ORANGE, "要花時間", "② 換四個常數",
         "gem.py 的 BIOMASS、EXCHANGE、MAP\\_RXNS、CARBON\\_SOURCES——"
         "要去查 rhto-GEM 自己的反應編號", "半天"),
        (RED, "卡住的就是這裡", "③ 填你自己的參數",
         "dfba.py 的吸收速率、耗氧上限、溫度與 pH 基點。"
         "現在填的是大腸桿菌的示範值，**這些只能用實驗量**", "要先做實驗"),
        (GREEN, "容易", "④ 重算查表",
         "dfba.py 在 1,394 個格點上重解一次 pFBA → tables.json", "一個指令、半分鐘"),
        (ORANGE, "可以先跳過", "⑤ 重畫代謝圖版面",
         "map\\_layout.json 現在畫的是大腸桿菌的中心碳代謝（21 個節點、23 條邊）", "一天"),
    ]
    y = 206
    for col, tag, name, what, cost in steps:
        s.arrow([(240, y - 24), (240, y)], color=GREY, width=2.6)
        h = 110 if len(what) > 46 else 92
        s.box(40, y, 920, h, "", color=col, fill=tint(col, 0.96))
        s.raw(f'<rect x="40" y="{y}" width="8" height="{h}" rx="4" fill="{col}"/>')
        s.text(72, y + 36, name, size=T_H, weight=700, color=col)
        s.chip(700, y + 18, tag, col, size=T_NOTE)
        for i, ln in enumerate(wrap(what, 16, 600)):
            s.text(72, y + 66 + i * 23, ln, size=16)
        s.text(940, y + h - 20, cost, size=T_NOTE, color=MUTED, anchor="end", weight=700)
        y += h + 24

    s.arrow([(240, y - 24), (240, y)], color=GREY, width=2.6)
    s.para(40, y, 400, 64, "index.html（可以拉滑桿了）", color=GREEN, size=T_H)
    s.text(470, y + 40, "simulator/build.py 產生", size=T_NOTE, color=MUTED)
    y += 92

    s.box(40, y, 920, 104, "", color=RED, fill=tint(RED, 0.94))
    s.icon("circle-alert", 72, y + 28, 26, RED, 2.2)
    s.text(114, y + 50, "所以答案是：不能直接放", size=22, weight=700, color=RED)
    s.text(72, y + 84, "但卡住的不是程式，是**第 ③ 步**——你還沒有自己的參數。"
                       "而那正好就是第一批實驗要產生的東西。", size=T_BODY)
    return s




def _flask(s, cx, by, h=96, w=84, overlay=False, col=TEAL, empty=False):
    """畫一個小搖瓶：梯形瓶身＋瓶頸，有覆蓋層就在液面上多畫一層。"""
    nw, nh = 22, 26
    body = (f"M{cx - nw / 2},{by - h} L{cx - nw / 2},{by - h + nh} "
            f"L{cx - w / 2},{by - 16} Q{cx - w / 2},{by} {cx - w / 2 + 14},{by} "
            f"L{cx + w / 2 - 14},{by} Q{cx + w / 2},{by} {cx + w / 2},{by - 16} "
            f"L{cx + nw / 2},{by - h + nh} L{cx + nw / 2},{by - h} Z")
    cid = f"fk{abs(hash((cx, by, overlay))) % 100000}"
    s.raw(f'<defs><clipPath id="{cid}"><path d="{body}"/></clipPath></defs>')
    s.raw(f'<path d="{body}" fill="#ffffff" stroke="#5b6475" stroke-width="2.6" '
          f'stroke-linejoin="round"/>')
    if not empty:
        s.raw(f'<rect x="{cx - w / 2}" y="{by - 36}" width="{w}" height="36" '
              f'fill="{tint(col, 0.55)}" clip-path="url(#{cid})"/>')
    if overlay:
        s.raw(f'<rect x="{cx - w / 2}" y="{by - 50}" width="{w}" height="14" '
              f'fill="{tint(ORANGE, 0.45)}" clip-path="url(#{cid})"/>')


def figr4_design():
    """第一批實驗的配置：3 個 C/N × 有沒有覆蓋層 ＋ 3 組對照。"""
    d = _wf()["design"]
    v = d["vessel"]
    s = Svg(WR4, 900, "圖 4-5　第一批實驗怎麼擺")
    s.text(40, 78, f'{v["flask_mL"]:.0f} mL 搖瓶裝 {v["work_mL"]:.0f} mL、200 rpm、'
                   f'每個條件 3 重複、遮光。', size=T_BODY, color=MUTED)

    X0, DX = 150, 200
    cns = [(c["medium"]["c_n_molar"], (TEAL, ORANGE, RED)[i])
           for i, c in enumerate([c for c in d["conditions"] if c["overlay"]])]
    for row, has_dod in enumerate((True, False)):
        y = 300 + row * 230
        s.text(40, y - 140, "有十二烷覆蓋" if has_dod else "沒有覆蓋（做一次就好）",
               size=T_H, weight=700, color=ORANGE if has_dod else GREY)
        for i, (cn, col) in enumerate(cns):
            cx = X0 + i * DX
            _flask(s, cx, y, h=100, w=86, overlay=has_dod, col=col)
            s.text(cx, y + 36, f"C/N {cn}", size=22, weight=700, anchor="middle")
            s.text(cx, y + 62, ("氮充足", "中", "限氮")[i], size=T_BODY,
                   anchor="middle", color=MUTED)

    s.text(40, 742, "三組對照", size=T_H, weight=700, color=PURPLE)
    for i, c in enumerate(d["controls"]):
        x = 40 + i * 310
        s.box(x, 764, 290, 108, "", color=PURPLE, fill=tint(PURPLE, 0.96))
        for j, ln in enumerate(wrap(c["label"], T_BODY, 250)):
            s.text(x + 20, 796 + j * 24, ln, size=T_BODY, weight=700, color=PURPLE)
        for j, ln in enumerate(wrap(c["why"].replace("**", ""), 15, 250)):
            s.text(x + 20, 844 + j * 20, ln, size=15, color=MUTED)

    s.card(640, 150, 320, ["低：菌專心長，競爭最小嗎？", "中：轉折點在哪裡？",
                           "高：產物真的被壓下去嗎？"],
           title="三個 C/N 在問什麼", icon="circle-help", color=BLUE, size=16,
           foot="文獻沒人掃過（見 18.9）")
    s.card(640, 420, 320, ["有／無的差距就是你原本漏掉的產量",
                           "差不多 → 先懷疑取樣方法，不要先懷疑菌"],
           title="為什麼要做「沒有覆蓋」", icon="droplet", color=ORANGE, size=16,
           foot="做一次就好")
    return s


def figr4_timeline():
    """96 小時的取樣節奏。"""
    d = _wf()["design"]
    s = Svg(WR4, 700, "圖 4-6　96 小時：什麼時候量什麼")
    s.text(40, 78, "取樣密度不平均：**中段盯「氮什麼時候歸零」**，那是開關被按下的時刻。",
           size=T_BODY, color=MUTED)

    X0, X1, T = 90, 940, 96.0
    AX = 300
    sx = lambda h: X0 + (X1 - X0) * h / T  # noqa: E731
    for a, b, col, name in ((0, 12, GREY, "長起來了沒"), (12, 36, BLUE, "等氮歸零"),
                            (36, 72, ORANGE, "產物累積"), (72, 96, GREEN, "有沒有平台")):
        s.raw(f'<rect x="{sx(a):.0f}" y="168" width="{sx(b) - sx(a):.0f}" height="86" '
              f'rx="8" fill="{tint(col, 0.9)}" stroke="{col}" stroke-width="2"/>')
        s.text((sx(a) + sx(b)) / 2, 202, name, size=T_BODY, weight=700, anchor="middle",
               color=col)
        s.text((sx(a) + sx(b)) / 2, 230, f"{a}–{b} h", size=15, anchor="middle", color=MUTED)

    s.arrow([(X0 - 40, AX), (X1 + 16, AX)], color=INK, width=2.6)
    for h in (0, 24, 48, 72, 96):
        s.line(sx(h), AX - 9, sx(h), AX + 9, color=INK, width=2)
        s.text(sx(h), AX + 34, f"{h} h", size=T_BODY, anchor="middle")
    for seg in d["sampling"]:
        for h in seg["times"]:
            if h <= T:
                s.raw(f'<circle cx="{sx(h):.0f}" cy="{AX}" r="8" fill="{TEAL}"/>')
    s.text(X0 - 40, AX - 26, "取樣點", size=T_BODY, weight=700, color=TEAL)
    for a, b in ((126, 162), (262, AX - 18)):
        s.raw(f'<line x1="{sx(24):.0f}" y1="{a}" x2="{sx(24):.0f}" y2="{b}" '
              f'stroke="{RED}" stroke-width="3" stroke-dasharray="7 5"/>')
    s.raw(f'<circle cx="{sx(24):.0f}" cy="{AX}" r="13" fill="none" stroke="{RED}" '
          f'stroke-width="3"/>')
    s.text(sx(24), 118, "氮歸零 ← 實際落在哪要自己量", size=T_BODY, weight=700,
           anchor="middle", color=RED)

    rows = [(TEAL, "每次", "OD600、殘糖、**殘氮**"),
            (BROWN, "每天", "乾重（OD 只是代理）"),
            (ORANGE, "36 h 起", "油脂、類胡蘿蔔素"),
            (GREEN, "36 h 起", "十二烷相 GC-MS"),
            (PURPLE, "三個點", "AFS 轉錄量 RT-qPCR")]
    for i, (col, when, what) in enumerate(rows):
        y = 396 + i * 54
        s.raw(f'<rect x="40" y="{y}" width="920" height="46" rx="8" '
              f'fill="{tint(col, 0.96)}" stroke="{col}" stroke-width="1.6"/>')
        s.chip(62, y + 11, when, col, size=15)
        s.text(240, y + 30, what, size=T_H)
    return s


def figr4_decide():
    """數據回來之後，照順序問三題。"""
    s = Svg(WR4, 1030, "圖 4-7　數據回來了，照順序問三題")
    s.text(40, 78, "前一題沒過就看後一題，等於在最適化一個假訊號。", size=T_BODY, color=MUTED)

    CX, DW, DH = 620, 440, 120
    LX = CX - DW / 2                      # 菱形的左頂點
    qs = [(150, "菌長得起來嗎？", RED,
           ["先看有沒有十二烷的差別：", "有覆蓋就長得好 → 產物毒性"]),
          (338, "量得到產物嗎？", ORANGE,
           ["RT-qPCR 看有沒有在轉錄；", "11 個拷貝都在，「沒表現」", "比「沒有基因」可能得多"]),
          (526, "比對照株明顯高嗎？", PURPLE,
           ["差不多 → 先懷疑取樣方法", "或基因沒在表現（標籤已排除）"])]
    for y, q, col, no in qs:
        cy = y + DH / 2
        s.diamond(CX, cy, DW, DH, q, color=col, size=T_H)
        # 「否」往左出去：箭頭 → 標籤在箭頭上方 → 說明再往左
        s.arrow([(LX - 4, cy), (LX - 34, cy)], color=col, width=2.4)
        s.text(LX - 19, cy - 12, "否", size=15, weight=700, color=col, anchor="middle")
        for i, ln in enumerate(no):
            s.text(LX - 48, cy - (len(no) - 1) * 12 + i * 24, ln, size=15, color=col,
                   anchor="end", weight=700)
        s.arrow([(CX, y + DH), (CX, y + DH + 38)], color=GREEN, width=2.6)
        s.text(CX + 14, y + DH + 26, "是", size=15, weight=700, color=GREEN)

    s.box(140, 700, 820, 112, "", color=GREEN, fill=tint(GREEN, 0.92))
    s.icon("circle-check", 172, 728, 28, GREEN, 2.2)
    s.text(218, 750, "三題都「是」＝你有一個可信的產量數字了", size=22, weight=700,
           color=GREEN)
    s.text(172, 786, "下一步按第 18 章的優先順序：補整條 MVA → 削弱油脂 → 調降 ERG9。",
           size=T_BODY)

    s.box(40, 844, 920, 132, "", color=BLUE, fill=tint(BLUE, 0.95))
    s.icon("chart-column", 72, 872, 26, BLUE, 2.1)
    s.text(114, 894, "另外看一件事：產物隨 C/N 怎麼變", size=T_H, weight=700, color=BLUE)
    for i, ln in enumerate([
            "低 C/N 最高 → 和 17.9 的推論一致，兩階段策略要改成「一直餵氮」",
            "高 C/N 最高 → 推論被推翻，很可能是開關受氮調控",
            "三個差不多 → C/N 不是主要變因，省下時間直接做基因層次的手段"]):
        s.text(72, 926 + i * 24, ln, size=15.5)
    return s


FIGS = {"fig0-1-roadmap": fig0, "fig1-1-dna-limits": fig1, "fig2-1-annotation": fig2, "fig2-2-clues": fig2_clues, "fig3-1-gem-build": fig3,
        "fd4-5-flux-maps": flux_maps, "fig5-2-phase-indicators": fig5, "fig6-4-stage-decisions": fig6,
        "fig7-2-doe-funnel": fig7, "fig8-3-bo-loop": fig8, "fig12-1-roadmap": fig10,
        "figr0-1-roadmap": figr0_roadmap, "figr1-1-compare": figr1_compare, "figr1-2-annotate": figr1_annotate,
        "figr1-3-yeasts": figr1_culture, "figr2-1-gene-to-reaction": figr2_gene_to_reaction,
        "figr2-2-fpp": figr2_fpp,
        "figr3-1-overview": figr3_overview, "figr3-2-construct": figr3_construct,
        "figr3-3-array": figr3_array, "figr3-5-junction": figr3_junction,
        "figr3-6-pathway": figr3_pathway,
        "figr3-8-states": figr3_states,
        "figr3-10-independent": figr3_independent,
        "figr3-11-site": figr3_site, "figr3-13-blast": figr3_blast, "figr4-1-flow": figr4_flow, "figr4-2-model-is": figr4_model_is,
        "figr4-3-fba": figr4_fba, "figr4-4-to-ui": figr4_to_ui, "figr4-5-design": figr4_design,
        "figr4-6-timeline": figr4_timeline, "figr4-7-decide": figr4_decide, "figr5-1-run": figr5_run, "figr6-1-audit": figr6_audit, "figr6-2-glucose": figr6_glucose, "figr6-3-erg9": figr6_erg9, "figr6-4-cn": figr6_cn, "figr6-5-compare": figr6_compare, "figr5-2-cn": figr5_cn, "figr5-3-limits": figr5_limits, "figr5-4-bounds": figr5_bounds, "figr3-12-fpp-users": figr3_fpp_users,
        "figr7-2-strategy": figr7_strategy,
        "figr3-9-overlay": figr3_overlay, "figr1-4-cell": figr1_cell,
        "fig10-4-vessels": fig10_vessels,
        "fig13-1-resources": fig13_resources}

if __name__ == "__main__":
    want = sys.argv[1:] or list(FIGS)
    render({k: FIGS[k]() for k in want if k in FIGS}, OUT)
