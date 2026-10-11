"""教材的設計系統：顏色、字級、間距、圓角、圖示對應，全部集中在這裡。

為什麼要有這個檔：第 11 章講「設計決定要有一個名字、放一個地方」，但這個 repo 自己
以前把色碼散在 svgkit、mplstyle 和每一支 diagrams.py 裡——改一個顏色要翻三個檔案。
這份檔案就是把那些決定收攏起來。

命名規則：**講用途，不要講長相**。`danger` 而不是 `red`；`surface` 而不是 `light-grey`。
每個 token 都要有 `usage`，寫清楚什麼時候用——沒有用途說明的 token 很快就會被亂用。

用法：
    from tokens import C, ICON, SPACE, RADIUS, TYPE
    s.box(x, y, w, h, color=C["accent"])
"""

from __future__ import annotations

# ── 色彩 ───────────────────────────────────────────────────────────
# 教材的圖是印在白底上的，所以這裡只有一組值（沒有深色模式）。
# 每個顏色對白底的對比度都 ≥3:1（當線條與大字用），主要文字另外用 ink。
_TOKENS = [
    ("ink",      "#1d2330", "主要文字、箭頭、方塊外框的預設色。"),
    ("muted",    "#5b6475", "次要文字：說明、註腳、座標軸標籤。"),
    ("hairline", "#e3e6ec", "格線、分隔線；純裝飾，不承載意義。"),
    ("axis",     "#8a93a3", "座標軸、淡框線。"),
    ("surface",  "#fbfbfd", "中性區塊的底色。"),

    ("blue",     "#2f6fb3", "流程的第一順位、輸入、量測值。"),
    ("orange",   "#d9821e", "第二順位、競爭者、要注意但不是錯誤的事。"),
    ("teal",     "#1b8a8f", "產物、結果、正向的量。"),
    ("purple",   "#7b4bb3", "模型、計算、推論。"),
    ("green",    "#2f9e6e", "通過、完成、建議這樣做。"),
    ("red",      "#c23b3b", "錯誤、警告、不要這樣做。"),
    ("brown",    "#8a6d3b", "實體與硬體：容器、儀器、染色體。"),
    ("grey",     "#6b7280", "沒有語意的第四、第五類。"),

    # 語意別名——畫圖時優先用這些，而不是上面的顏色名
    ("accent",   "#1b8a8f", "一張圖的主角。"),
    ("danger",   "#c23b3b", "錯誤、禁止、失效。"),
    ("ok",       "#2f9e6e", "通過、正確。"),
    ("warn",     "#d9821e", "要注意。"),
    ("model",    "#7b4bb3", "模型與推論。"),
    ("data",     "#2f6fb3", "實測資料。"),
    ("hw",       "#8a6d3b", "實體設備。"),

    # 氨氮教材的固定對應（章節之間要看得出同一個東西）
    ("nh4", "#2f6fb3", "氨氮。"), ("no2", "#d9821e", "亞硝酸鹽。"),
    ("no3", "#c23b3b", "硝酸鹽。"), ("n2", "#2f9e6e", "氮氣。"),
    ("org", "#8a6d3b", "有機氮。"), ("amx", "#7b4bb3", "厭氧氨氧化。"),
    ("gas", "#6b7280", "其他氣體。"),
]
C = {name: value for name, value, _ in _TOKENS}
USAGE = {name: usage for name, _, usage in _TOKENS}

# 分類資料的預設順序：相鄰兩色在明度與色相都分得開（灰階印出來也分得出）
CYCLE = [C["blue"], C["orange"], C["teal"], C["purple"], C["green"], C["red"], C["brown"]]

# ── 字級 ───────────────────────────────────────────────────────────
# 一張圖最多用到四級就夠；超過代表層次沒想清楚。
TYPE = {
    "title":   {"size": 24, "weight": 700, "usage": "圖的標題，每張圖只有一個。"},
    "section": {"size": 19, "weight": 700, "usage": "區塊標題、卡片抬頭。"},
    "body":    {"size": 15, "weight": 400, "usage": "一般說明、條列。"},
    "label":   {"size": 14, "weight": 400, "usage": "圖上的標籤、座標說明。"},
    "note":    {"size": 13, "weight": 400, "usage": "註腳、來源、限制說明。"},
    "stat":    {"size": 26, "weight": 700, "usage": "要被一眼看到的數字。"},
}

# ── 間距與圓角 ─────────────────────────────────────────────────────
SPACE = {"1": 6, "2": 12, "3": 18, "4": 24, "6": 36, "8": 48}
RADIUS = {"sm": 6, "md": 10, "lg": 14, "pill": 999}
STROKE = {"hair": 1.2, "line": 2.0, "bold": 3.0, "arrow": 2.5}

# ── 圖示對應 ───────────────────────────────────────────────────────
# 同一個概念在不同章節要用同一個圖示，讀者才會建立連結。
ICON = {
    "file": "file-text", "folder": "folder-open", "code": "file-code",
    "repo": "git-branch", "github": "github", "terminal": "terminal",
    "database": "database", "server": "server", "cloud": "server",
    "model": "cpu", "ai": "bot", "skill": "wand-sparkles", "plugin": "puzzle",
    "schedule": "clock", "calendar": "calendar-days", "alert": "triangle-alert",
    "ok": "circle-check", "no": "circle-x", "idea": "lightbulb", "book": "book-open",
    "search": "scan-search", "web": "globe", "link": "link", "chart": "chart-line",
    "settings": "settings", "shield": "shield", "lock": "lock", "key": "key",
    "lab": "flask-conical", "tube": "test-tube", "dna": "dna", "scope": "microscope",
    "drop": "droplet", "temp": "thermometer", "atom": "atom", "leaf": "leaf",
    "layers": "layers", "flow": "workflow", "target": "target", "people": "users",
    "palette": "palette", "type": "type", "ruler": "ruler", "time": "history",
    "fast": "zap", "up": "rocket", "gauge": "gauge", "check-list": "list-checks",
}


def icon(name: str) -> str:
    """語意名稱 → Lucide 圖示名。沒對應就當成已經是 Lucide 名稱。"""
    return ICON.get(name, name)
