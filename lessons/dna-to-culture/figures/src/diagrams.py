"""「從 DNA 到最適培養」的概念圖與代謝流量圖。執行：python lessons/dna-to-culture/figures/src/diagrams.py [圖名 ...]"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_tools"))
from svgkit import INK, MUTED, Svg, render, tint  # noqa: E402

OUT = Path(__file__).resolve().parent.parent
CODE = OUT.parent / "code"
BLUE, ORANGE, RED, GREEN, PURPLE, GREY, BROWN, TEAL = ("#2f6fb3", "#d9821e", "#c23b3b", "#2f9e6e", "#7b4bb3",
                                                       "#6b7280", "#8a6d3b", "#1b8a8f")


def fig0():
    s = Svg(1200, 600, "學習地圖：從一段 DNA 序列，到看得見的最適培養條件")
    steps = [
        ("DNA 序列", "定序、組裝\n品質檢查", BROWN, "2"),
        ("功能註解", "這株菌有\n哪些基因、酵素", ORANGE, "2"),
        ("代謝模型 GEM", "基因 → 反應\n→ 代謝網路", PURPLE, "3"),
        ("FBA", "給定環境\n算出代謝流量", BLUE, "4"),
        ("動態模擬 dFBA", "加上時間：\n生長曲線與階段", TEAL, "5–6"),
        ("最適化", "分階段調參數\n貝氏最適化", GREEN, "6–8"),
        ("視覺化介面", "拉動參數\n立刻看到變化", RED, "9"),
    ]
    x = 24
    for i, (h, b, c, ch) in enumerate(steps):
        s.box(x, 90, 150, 70, h, color=c, size=16)
        s.box(x, 170, 150, 86, "", color=c, fill="#ffffff")
        s.text(x + 75, 213, b, size=14, anchor="middle-v")
        s.pill(x + 75, 284, f"第 {ch} 章", c, size=13)
        if i < len(steps) - 1:
            s.arrow([(x + 152, 125), (x + 170, 125)], color=c)
        x += 168
    s.box(24, 330, 1152, 112, "", color=GREY, fill="#fbfbfd")
    s.text(48, 364, "實驗室資料一路回饋（第 5、7、8、10 章）", size=17, weight=700)
    s.text(48, 396, "生長曲線、基質與產物濃度、溶氧、pH、溫度 → 校正吸收速率、找出溫度與 pH 的最適範圍、檢查模型預測對不對。", size=15)
    s.text(48, 424, "模型負責「縮小範圍、解釋原因」；實驗負責「驗證、提供模型算不出來的參數」。兩者交替，越轉越準。", size=15)
    s.box(24, 470, 370, 100, "第 1 章", color=BROWN, size=15, sub="先回答你的問題：\n能做到什麼、做不到什麼", sub_size=15,
          fill="#ffffff")
    s.box(415, 470, 370, 100, "第 10 章", color=GREEN, size=15, sub="怎麼開始：步驟、分工\n你要收集什麼、AI 能幫什麼", sub_size=15,
          fill="#ffffff")
    s.box(806, 470, 370, 100, "第 11–12 章", color=PURPLE, size=15, sub="國內外文獻與資源\n更創新的做法", sub_size=15,
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
        (906, 320, "8 回饋模型", "把新資料加回模型\n下一輪更準\n（第 8、12 章）", GREY),
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
    s = Svg(1200, 700, "圖 10-1　起步路線圖：你要做的事 vs AI／工具能幫的事")
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


FIGS = {"fig0-1-roadmap": fig0, "fig1-1-dna-limits": fig1, "fig2-1-annotation": fig2, "fig3-1-gem-build": fig3,
        "fd4-5-flux-maps": flux_maps, "fig5-2-phase-indicators": fig5, "fig6-4-stage-decisions": fig6,
        "fig7-2-doe-funnel": fig7, "fig8-3-bo-loop": fig8, "fig10-1-roadmap": fig10}

if __name__ == "__main__":
    want = sys.argv[1:] or list(FIGS)
    render({k: FIGS[k]() for k in want if k in FIGS}, OUT)
