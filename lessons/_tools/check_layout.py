"""檢查教材頁面的版面：文字框與圖片會不會在 Folio 上疊在一起。

Folio 的頁面是絕對定位的，每個區塊有自己的 y 座標與高度。文字高度是用
`lessons.estimate_height()` 估的，估得不準就會疊圖。推送前跑一次這支程式，
比上傳之後才發現省事很多。

用法：
  python lessons/_tools/check_layout.py                      # 檢查所有教材
  python lessons/_tools/check_layout.py lessons/using-claude # 只檢查一門

有重疊時以代碼 1 結束。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from autocollect import lessons  # noqa: E402


def check(lesson_dir: Path) -> int:
    records, _ = lessons.build_all(lesson_dir, now_ms=1000)
    pages: dict[str, list] = {}
    for r in records:
        if r["key"].startswith("it:") and not r["deleted"]:
            pages.setdefault(r["key"].split(":")[1], []).append(r["data"])
    bad = 0
    for pid, items in sorted(pages.items()):
        items.sort(key=lambda i: i["y"])
        for a, b in zip(items, items[1:]):
            bottom = a["y"] + (a["h"] if a["type"] == "image"
                               else lessons.estimate_height(a["html"]))
            if bottom >= b["y"]:
                bad += 1
                print(f"  ⚠ 重疊 {pid}：{a['type']} 底部 {bottom} ≥ 下一塊頂部 {b['y']}")
    print(f"{lesson_dir.name}：{len(pages)} 頁，重疊 {bad} 處")
    return bad


def main(argv=None):
    args = (argv if argv is not None else sys.argv[1:])
    dirs = [Path(a) for a in args] if args else sorted(
        p.parent for p in (ROOT / "lessons").glob("*/course.yaml"))
    total = sum(check(d) for d in dirs)
    if total:
        print(f"\n共 {total} 處重疊——修好再推。")
        return 1
    print("\n全部沒有重疊。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
