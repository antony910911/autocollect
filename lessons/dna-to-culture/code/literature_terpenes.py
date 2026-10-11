"""第 18 章：紅酵母做萜類的文獻數據表。

這一章和其他章不同——數字不是算出來的，是**從論文抄下來的**。所以這份表的每一筆
都帶 `source`（哪一篇）與 `verified`（我是怎麼確認的）兩個欄位，第 18 章的圖直接
讀它，讀者可以逐筆回去查原文。

`verified` 的意義：
  "abstract"  摘要或結論裡明確寫出的數字
  "secondary" 來自回顧性文章或資料庫摘要的轉述，**沒有核對過原文**
這個執行環境連不上期刊網站（只有搜尋工具可用），所以沒有任何一筆是「我讀過全文」。
要引用到正式文件裡之前，請自己開全文核對一次。

執行：python literature_terpenes.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

SOURCES = {
    "yaegashi2017": {
        "cite": "Yaegashi et al. (2017) Biotechnol Biofuels 10:241",
        "doi": "10.1186/s13068-017-0927-5"},
    "kirby2021": {
        "cite": "Kirby et al. (2021) Biotechnol Biofuels 14:101",
        "doi": "10.1186/s13068-021-01950-w"},
    "geiselman2020": {
        "cite": "Geiselman et al. (2020) Microb Cell Fact 19:24",
        "doi": "10.1186/s12934-020-1293-8"},
    "liu2021": {
        "cite": "Liu et al. (2021) Biotechnol Biofuels 14",
        "doi": "10.1186/s13068-021-02094-7"},
    "adamczyk2025": {
        "cite": "Adamczyk et al. (2025) Metab Eng 90:92–105",
        "doi": "10.1016/j.ymben.2025.02.014"},
}

# product, titer (mg/L), year, 規模與條件, 來源, 驗證程度
TITERS = [
    ("α-bisabolene", 261, 2017, "搖瓶／離子液體前處理玉米稈水解液", "yaegashi2017", "abstract"),
    ("α-bisabolene", 521, 2017, "高糖饋料批次發酵槽／純葡萄糖對照", "yaegashi2017", "secondary"),
    ("α-bisabolene", 680, 2017, "高糖饋料批次發酵槽／鹼法前處理玉米稈水解液", "yaegashi2017", "abstract"),
    ("α-bisabolene", 2200, 2021, "2 L 發酵槽／木質纖維素水解液", "kirby2021", "abstract"),
    ("α-bisabolene", 2600, 2021, "玉米稈水解液（結論段的最高值）", "kirby2021", "abstract"),
    ("α-bisabolene", 19300, 2025, "2 L 發酵槽／葡萄糖最小培養基", "adamczyk2025", "abstract"),
    ("α-bisabolene", 20800, 2025, "微量盤／玉米稈水解液，總糖 300 g/L", "adamczyk2025", "abstract"),
    ("1,8-cineole", 1400, 2021, "玉米稈水解液", "kirby2021", "abstract"),
    ("ent-kaurene", 1440, 2020, "木質纖維素水解液", "geiselman2020", "abstract"),
    ("limonene", 393.5, 2021, "工程菌株（另有資料寫 383.5，兩個來源不一致）", "liu2021", "secondary"),
]

# 每一篇「做了什麼」的重點，用於策略演進圖
STEPS = [
    {"year": 2017, "key": "yaegashi2017", "title": "建立平台",
     "what": ["把 bisabolene 合成酶放進 R. toruloides",
              "證明它能直接長在玉米稈水解液上",
              "700 mL 批次 ＋ 150 mL 十二烷覆蓋層（約 21% v/v），"
              "內標 1 g/L pentadecane 用來校正揮發"],
     "best": 680},
    {"year": 2021, "key": "kirby2021", "title": "拷貝數",
     "what": ["合成酶卡匣拷貝數與產量相關 R²＝0.93（20 株）",
              "第一個卡匣用原生 GAPDH 啟動子，再加第二個用 ANT 啟動子",
              "水解液 ＋ 最少的營養補充就能到 g/L 等級"],
     "best": 2600},
    {"year": 2025, "key": "adamczyk2025", "title": "補 MVA ＋ 削弱油脂",
     "what": ["把釀酒酵母完整的 MVA 路徑疊到多拷貝合成酶母株上",
              "**削弱往油脂的通量 → 產量提高 6–7 倍**",
              "2 L 葡萄糖最小培養基 19.3 g/L，生產力 0.11 g/L/h"],
     "best": 20800},
]


def main():
    rows = [{"product": p, "titer_mg_L": v, "year": y, "condition": c,
             "source": s, "cite": SOURCES[s]["cite"], "doi": SOURCES[s]["doi"],
             "verified": ver}
            for p, v, y, c, s, ver in TITERS]
    bis = [r for r in rows if r["product"] == "α-bisabolene"]
    lo, hi = min(r["titer_mg_L"] for r in bis), max(r["titer_mg_L"] for r in bis)
    out = {"sources": SOURCES, "titers": rows, "steps": STEPS,
           "bisabolene_span": {"low": lo, "high": hi, "fold": round(hi / lo, 1),
                               "years": [min(r["year"] for r in bis),
                                         max(r["year"] for r in bis)]}}
    (HERE / "literature_terpenes.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
    print(f'α-bisabolene：{lo:,} → {hi:,} mg/L，'
          f'{out["bisabolene_span"]["years"][0]}–{out["bisabolene_span"]["years"][1]} 年間成長 '
          f'{out["bisabolene_span"]["fold"]} 倍')
    for r in rows:
        print(f'  {r["product"]:14s}{r["titer_mg_L"]:>9,.1f} mg/L  {r["year"]}  '
              f'{r["verified"]:9s} {r["condition"]}')
    print("\n寫入 literature_terpenes.json")


if __name__ == "__main__":
    main()
