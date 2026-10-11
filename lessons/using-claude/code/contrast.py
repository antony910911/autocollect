"""第 11 章：驗算一個設計系統的色彩對比度。

輸入是 `beamup-tokens.json`——使用者自己的 Beamup 設計系統的 token 檔，
在 2026-10-11 從設計系統 artifact 抄下來的快照（活的版本在 artifact 上，
這裡只是為了讓教材的數字可以重跑）。

這支程式做兩件事：
1. 把每個 token 的色碼算出相對亮度，再算文字／底色配對的對比度（WCAG 2.x 公式）。
2. 和 README 裡聲稱的數字對照——**聲稱的要驗，不要照抄**。

WCAG 門檻：一般文字 4.5:1、大字（24px 以上或 18.66px 粗體）3:1、
非文字（框線、焦點環、圖示）3:1。

執行：python contrast.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = {"artifact": "Beamup 設計系統（使用者自己的）",
       "snapshot": "2026-10-11",
       "built_from": "github:antony910911/thought_task_entry @ f5f021f"}

# 要檢查的配對：(前景 token, 背景 token, 用途, 門檻)
PAIRS = [
    ("ink", "surface-page", "主要文字在頁面底上", 4.5),
    ("ink", "surface-card", "主要文字在卡片上", 4.5),
    ("ink", "surface-fill", "主要文字在填色控制項上", 4.5),
    ("ink-2", "surface-page", "次要文字在頁面底上", 4.5),
    ("ink-2", "surface-card", "次要文字在卡片上", 4.5),
    ("ink-3", "surface-page", "placeholder 在頁面底上", 4.5),
    ("ink-3", "surface-card", "placeholder 在卡片上", 4.5),
    ("blip", "surface-page", "品牌色當連結在頁面底上", 4.5),
    ("blip", "surface-card", "品牌色當連結在卡片上", 4.5),
    ("on-blip", "blip", "主要按鈕的字", 4.5),
    ("note", "surface-card", "筆記代表色當文字", 4.5),
    ("event", "surface-card", "行程代表色當文字", 4.5),
    ("danger", "surface-card", "錯誤訊息", 4.5),
    ("line", "surface-page", "需要看見的框線（非文字）", 3.0),
    ("line", "surface-card", "未勾選 checkbox 的框（非文字）", 3.0),
    ("blip", "surface-card", "焦點環（非文字）", 3.0),
]


def hex_to_rgb(s: str) -> tuple[float, float, float]:
    s = s.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return tuple(int(s[i:i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(rgb) -> float:
    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = luminance(hex_to_rgb(a)), luminance(hex_to_rgb(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def resolve(tokens: dict, name: str, theme: str) -> str | None:
    """取出 token 在某個主題下的色碼，處理 {alias} 參照。"""
    seen = set()
    while True:
        tok = tokens.get(name)
        if tok is None or name in seen:
            return None
        seen.add(name)
        val = tok["value"]
        v = val.get(theme, val.get("light")) if isinstance(val, dict) else val
        m = re.fullmatch(r"\{([^}]+)\}", str(v).strip())
        if not m:
            return v if str(v).startswith("#") else None
        name = m.group(1)


def main():
    raw = json.loads((HERE / "beamup-tokens.json").read_text("utf-8"))
    tokens = {t["name"]: t for t in raw["color"]["tokens"]}
    themes = [t["id"] for t in raw["color"]["themes"]]

    rows = []
    for fg, bg, what, need in PAIRS:
        row = {"fg": fg, "bg": bg, "what": what, "need": need, "by_theme": {}}
        for th in themes:
            a, b = resolve(tokens, fg, th), resolve(tokens, bg, th)
            if a and b:
                r = contrast(a, b)
                row["by_theme"][th] = {"fg_hex": a, "bg_hex": b,
                                       "ratio": round(r, 2), "pass": r >= need}
        rows.append(row)

    fails = [(r, th) for r in rows for th, v in r["by_theme"].items() if not v["pass"]]
    swatches = [{"name": n, "light": resolve(tokens, n, "light"),
                 "dark": resolve(tokens, n, "dark"),
                 "usage": tokens[n]["usage"].split("。")[0] + "。"}
                for n in tokens]

    out = {"source": SRC, "themes": raw["color"]["themes"], "pairs": rows,
           "swatches": swatches, "n_fail": len(fails),
           "counts": {"colors": len(tokens),
                      "text_styles": sum(len(g["styles"]) for g in raw["type"]["groups"]),
                      "spacing": len(raw["spacing"]["tokens"]),
                      "radius": len(raw["radius"]["tokens"]),
                      "shadow": len(raw.get("shadow", {}).get("tokens", []))}}
    (HERE / "contrast.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")

    print(f'Beamup 設計系統：{out["counts"]["colors"]} 個顏色、'
          f'{out["counts"]["text_styles"]} 種文字樣式、'
          f'{out["counts"]["spacing"]} 個間距、{out["counts"]["radius"]} 個圓角\n')
    print(f'{"配對":34s}{"門檻":>5s}  ' + "  ".join(f'{t["name"]:>10s}' for t in raw["color"]["themes"]))
    for r in rows:
        cells = "  ".join(
            f'{r["by_theme"][th]["ratio"]:7.2f} {"✓" if r["by_theme"][th]["pass"] else "✗"}'
            if th in r["by_theme"] else f'{"—":>9s}' for th in themes)
        print(f'{r["fg"] + " on " + r["bg"]:34s}{r["need"]:5.1f}  {cells}')
    print(f'\n不合格 {len(fails)} 項' + ("" if fails else "——全部通過"))
    for r, th in fails:
        print(f'  ✗ {r["fg"]} on {r["bg"]}（{th}）：'
              f'{r["by_theme"][th]["ratio"]:.2f}:1，需要 {r["need"]}:1　{r["what"]}')
    print("\n寫入 contrast.json")


if __name__ == "__main__":
    main()
