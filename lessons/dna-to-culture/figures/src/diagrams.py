"""「從 DNA 到最適培養」的概念圖與代謝流量圖。執行：python lessons/dna-to-culture/figures/src/diagrams.py [圖名 ...]"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_tools"))
from svgkit import INK, MUTED, Svg, render, tint, wrap  # noqa: E402

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
    s = Svg(1200, 450, "圖 4-5　同一個代謝網路，三種供氧條件下的流量分布（線越粗流量越大，mmol/gDW/h）")
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
    s = Svg(1200, 640, "圖 5-2　培養的每個階段：看什麼指標、可以調什麼")
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
    s = Svg(1200, 600, "圖 6-4　分階段調參數的決策流程：每一階段要調什麼、怎麼知道")
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
    s = Svg(1200, 520, "圖 7-2　實驗設計的漏斗：從很多個可能的參數，到最適條件")
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
def fig15_compare():
    s = Svg(1200, 790, "圖 15-1　前面 14 章，換成酵母菌要改哪些？")
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


def fig15_annotate():
    s = Svg(1200, 660, "圖 15-2　酵母菌的註解流程：和細菌版（圖 2-1）哪裡不一樣")
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


def fig15_culture():
    s = Svg(1240, 720, "圖 15-3　酵母菌之間差很多：釀酒酵母的經驗不能直接套到產油酵母")
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


def fig16_gene_to_reaction():
    s = Svg(1200, 640, "圖 16-1　基改菌株：把「插進去的基因」變成模型裡的反應")
    cols = [
        ("① 你知道的", BROWN, "插入了哪個基因\n（名稱、來源生物、序列）\n例：Z. mobilis 的 pdc"),
        ("② 查它催化什麼反應", BLUE, "UniProt／KEGG／BRENDA\n查 EC 編號與反應式\n例：丙酮酸 → 乙醛 + CO₂"),
        ("③ 對應到模型的代謝物", PURPLE, "找出模型裡的 id\n（pyr_c、acald_c、co2_c）\n要確認區隔（細胞質？粒線體？）"),
        ("④ 加進模型", GREEN, "新增反應、設界限\n寫上基因對應規則\n（程式見 engineered.py）"),
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



def fig16_fpp():
    s = Svg(1240, 760, "圖 16-2　你的案例：α-farnesene 在和誰搶原料")
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


def fig17_overview():
    d = _case()
    km, a = d["kmer"], d["assembly"]
    arr = d["array"]
    carrier, host = arr["carrier"], ("mut" if arr["carrier"] == "wt" else "wt")
    names = {"wt": d["provenance"]["wt_file"], "mut": d["provenance"]["mut_file"]}
    n_afs = {t: len(d[t + "_afs_copies"]) for t in ("wt", "mut")}
    s = Svg(1280, 790, "圖 17-1　兩份組裝比對的結論：轉殖基因陣列只在其中一份裡")

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
    for i, (cx, nm, pos, col) in enumerate(small):
        ty = y - 40 - (i % 3) * 30
        s.line(cx, y - 2, cx, ty + 6, color=col, width=1.4)
        s.text(cx, ty, f"{nm}　{pos}", size=12.5, color=col, anchor="middle", weight=700)
    # 座標尺
    step = 1000
    t = ((c0 // step) + 1) * step
    while t < c1:
        tx = x0 + (t - c0) * sc
        s.line(tx, y + 46, tx, y + 56, color=MUTED, width=1.2)
        s.text(tx, y + 72, f"{t // 1000}k", size=11.5, color=MUTED, anchor="middle")
        t += step


def fig17_construct():
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


def fig17_array():
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


def fig17_junction():
    d = _case()
    carrier = d["array"]["carrier"]
    bad = [c for c in d[carrier + "_afs_copies"] if not c["intact"]]
    s = Svg(1280, 760, "圖 17-5　12 個拷貝裡壞掉的那一個：不是突變，是陣列的接合點")
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


def fig17_pathway():
    d = json.loads((CODE / "farnesene_path.json").read_text("utf-8"))
    f = d["per_farnesene"]
    gy = d["yield"]["glucose"]
    s = Svg(1480, 950, "圖 17-6　轉進去一個基因，代謝上改變了什麼")
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


def fig17_states():
    d = json.loads((CODE / "farnesene_path.json").read_text("utf-8"))
    s = Svg(1460, 880, "圖 17-8　四種狀態：什麼時候產油、什麼時候產色素、什麼時候產 farnesene")
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


def fig18_strategy():
    d = json.loads((CODE / "literature_terpenes.json").read_text("utf-8"))
    steps = d["steps"]
    s = Svg(1480, 860, "圖 18-2　八年三步：別人是怎麼從 680 mg/L 走到 20 g/L 的")
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


def fig17_overlay():
    s = Svg(1420, 900, "圖 17-9　為什麼沒有有機相覆蓋，你量到的產量是假的")
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


def fig15_cell():
    s = Svg(1440, 900, "圖 15-4　為什麼細菌的工具鏈不能用在酵母菌上")
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
    s.line(bx - 226, by - 54, bx - 108, by + 4, color=PURPLE, width=1.4)
    s.text(bx - 232, by - 60, "DNA 散在細胞質裡", size=13.5, color=PURPLE, anchor="end")
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


FIGS = {"fig0-1-roadmap": fig0, "fig1-1-dna-limits": fig1, "fig2-1-annotation": fig2, "fig2-2-clues": fig2_clues, "fig3-1-gem-build": fig3,
        "fd4-5-flux-maps": flux_maps, "fig5-2-phase-indicators": fig5, "fig6-4-stage-decisions": fig6,
        "fig7-2-doe-funnel": fig7, "fig8-3-bo-loop": fig8, "fig12-1-roadmap": fig10,
        "fig15-1-compare": fig15_compare, "fig15-2-annotate": fig15_annotate,
        "fig15-3-yeasts": fig15_culture, "fig16-1-gene-to-reaction": fig16_gene_to_reaction,
        "fig16-2-fpp": fig16_fpp,
        "fig17-1-overview": fig17_overview, "fig17-2-construct": fig17_construct,
        "fig17-3-array": fig17_array, "fig17-5-junction": fig17_junction,
        "fig17-6-pathway": fig17_pathway,
        "fig17-8-states": fig17_states,
        "fig18-2-strategy": fig18_strategy,
        "fig17-9-overlay": fig17_overlay, "fig15-4-cell": fig15_cell,
        "fig10-4-vessels": fig10_vessels,
        "fig13-1-resources": fig13_resources}

if __name__ == "__main__":
    want = sys.argv[1:] or list(FIGS)
    render({k: FIGS[k]() for k in want if k in FIGS}, OUT)
