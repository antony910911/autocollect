"""產生第 9 章用的模擬器截圖。執行：python screenshots.py（需要 Playwright 與 Chromium）"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "figures"
SKELETON = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>body{margin:0}</style></head><body>{}</body></html>')


def main():
    page_file = HERE / "_preview.html"
    page_file.write_text(SKELETON.replace("{}", (HERE / "index.html").read_text("utf-8")), "utf-8")
    exe = os.environ.get("CHROMIUM", "/opt/pw-browsers/chromium")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe if Path(exe).exists() else None)
        pg = b.new_page(viewport={"width": 1300, "height": 1000}, device_scale_factor=1.5)
        pg.goto(page_file.as_uri())
        pg.wait_for_timeout(800)
        # 1 兩階段情境：整體畫面
        pg.screenshot(path=str(OUT / "fd9-1-simulator.png"), clip={"x": 0, "y": 0, "width": 1300, "height": 1370})
        # 2 代謝圖：拉到第 3 小時（好氧）
        pg.fill("#scrub", "3")
        pg.dispatch_event("#scrub", "input")
        pg.locator("section.two").screenshot(path=str(OUT / "fd9-2-simulator-map.png"))
        # 3 比較：先把搖瓶好氧設為基準，再換成供氧不足
        pg.click("[data-preset=flask]")
        pg.click("#pin")
        pg.click("[data-preset=poor]")
        pg.wait_for_timeout(300)
        pg.evaluate("window.scrollTo(0, 0)")
        box = pg.locator("main").bounding_box()
        pg.screenshot(path=str(OUT / "fd9-3-simulator-compare.png"), full_page=True,
                      clip={"x": box["x"], "y": box["y"], "width": box["width"], "height": 760})
        # 4 掃描與敏感度：兩階段情境
        pg.click("#unpin")
        pg.click("[data-preset=two]")
        pg.wait_for_timeout(300)
        pg.locator("section.tools").screenshot(path=str(OUT / "fd9-4-simulator-tools.png"))
        b.close()
    page_file.unlink()
    print("寫入 fd9-1 ~ fd9-4")


if __name__ == "__main__":
    main()
