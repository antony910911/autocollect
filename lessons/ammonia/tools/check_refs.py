"""核對教材參考文獻：每個 DOI 到 Crossref 查詢，確認存在、標題與年份和文中寫的一致。

用法：python lessons/ammonia/tools/check_refs.py [教材資料夾]
有任何一筆查不到或對不上時以代碼 1 結束，GitHub Actions 會標示失敗。
"""

from __future__ import annotations

import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests
from requests.utils import quote

DOI = re.compile(r"https://doi\.org/(10\.\S+)")
YEAR = re.compile(r"\((\d{4})\)")


def norm_words(s: str) -> list[str]:
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"<[^>]+>", " ", s)  # Crossref 標題可能含 <i> 等標籤
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.findall(r"[a-z0-9]+", s.lower())


def references(md: str) -> list[str]:
    part = md.split("## 參考文獻", 1)
    if len(part) < 2:
        return []
    return [line.strip() for line in part[1].splitlines() if re.match(r"\s*\d+\.\s", line)]


def lookup(doi: str, mailto: str) -> dict | None:
    url = "https://api.crossref.org/works/" + quote(doi, safe="/")
    headers = {"User-Agent": f"autocollect-lessons/1.0 (mailto:{mailto})" if mailto else "autocollect-lessons/1.0"}
    for attempt in range(4):
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 404:
            return None
        if r.status_code == 200:
            return r.json()["message"]
        time.sleep(2 ** attempt)
    r.raise_for_status()
    return None


def extract_doi(line: str) -> str | None:
    m = DOI.search(line)
    if not m:
        return None
    doi = m.group(1).rstrip("。，,）")
    while doi.endswith(")") and doi.count("(") < doi.count(")"):  # 句尾的括號不是 DOI 的一部分
        doi = doi[:-1]
    return doi


def check_line(line: str, mailto: str) -> tuple[bool, str]:
    doi = extract_doi(line)
    if not doi:
        return True, "（無 DOI，略過）"
    meta = lookup(doi, mailto)
    if meta is None:
        return False, f"Crossref 查無此 DOI：{doi}"
    title = " ".join(meta.get("title") or [""])
    # Crossref 有時把註腳併進標題，只比對前 15 個字
    words = set(norm_words(title)[:15]) - {"a", "an", "the", "of", "and", "in", "by", "for", "to", "on", "with"}
    line_words = set(norm_words(line))
    hit = len(words & line_words) / max(1, len(words))
    year_cr = None
    for key in ("published-print", "published-online", "issued"):
        parts = (meta.get(key) or {}).get("date-parts") or [[None]]
        if parts[0][0]:
            year_cr = parts[0][0]
            break
    y = YEAR.search(line)
    year_ok = not y or not year_cr or abs(int(y.group(1)) - int(year_cr)) <= 1  # 線上先行與正式出版常差一年
    ok = hit >= 0.75 and year_ok
    note = f"標題吻合 {hit:.0%}，Crossref 年份 {year_cr}｜{title[:90]}"
    return ok, note


def main(argv: list[str]) -> int:
    folder = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent
    mailto = os.environ.get("OPENALEX_MAILTO", "")
    bad = 0
    total = 0
    for md in sorted(folder.glob("*.md")):
        for line in references(md.read_text("utf-8")):
            ok, note = check_line(line, mailto)
            if "略過" in note:
                continue
            total += 1
            mark = "OK " if ok else "NG "
            print(f"{mark} {md.name}: {line[:70]}…\n     {note}")
            bad += not ok
            time.sleep(0.2)
    print(f"\n共核對 {total} 筆 DOI，{bad} 筆有問題")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
