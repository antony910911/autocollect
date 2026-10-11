"""把查表、代謝圖版面與計算核心內嵌進模擬器頁面。執行：python build.py → index.html"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = HERE.parent / "code"


def main():
    tables = json.loads((CODE / "tables.json").read_text("utf-8"))
    layout = json.loads((CODE / "map_layout.json").read_text("utf-8"))
    layout.pop("_說明", None)
    page = (HERE / "template.html").read_text("utf-8")
    page = page.replace("/*TABLES*/null", json.dumps(tables, separators=(",", ":")))
    page = page.replace("/*LAYOUT*/null", json.dumps(layout, ensure_ascii=False, separators=(",", ":")))
    page = page.replace("/*SIMJS*/", (HERE / "sim.js").read_text("utf-8"))
    (HERE / "index.html").write_text(page, "utf-8")
    print("寫入", HERE / "index.html", f"{len(page) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
