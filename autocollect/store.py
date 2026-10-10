"""去重、跨週歷史紀錄、統計與挑選送進分析的資料。"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_TRACKING = re.compile(r"^(utm_|fbclid|gclid|mc_)")
_NON_WORD = re.compile(r"[\W_]+", re.UNICODE)

KIND_PRIORITY = {"industry": 0, "news": 1, "paper": 2}


def normalize_url(url: str) -> str:
    p = urlparse(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(p.query) if not _TRACKING.match(k)])
    return urlunparse((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), "", query, ""))


def title_key(title: str) -> str:
    return _NON_WORD.sub("", title.lower())[:120]


def dedupe(items: list[dict]) -> list[dict]:
    """同一則消息常被多個關鍵字抓到，依網址與標題去重，並合併命中的關鍵字。"""
    seen: dict[str, dict] = {}
    out = []
    for it in items:
        if not it.get("title") or not it.get("url"):
            continue
        keys = [k for k in (normalize_url(it["url"]), title_key(it["title"])) if k]
        hit = next((seen[k] for k in keys if k in seen), None)
        if hit:
            if it["query"] not in hit["queries"]:
                hit["queries"].append(it["query"])
            continue
        it = {**it, "queries": [it["query"]]}
        it.pop("query", None)
        for k in keys:
            seen[k] = it
        out.append(it)
    return out


class History:
    """記錄已出現過的資料，避免同一則新聞或論文每週重複出現。"""

    def __init__(self, path: Path):
        self.path = path
        self.data: dict[str, str] = json.loads(path.read_text("utf-8")) if path.exists() else {}

    def keys(self, it: dict) -> list[str]:
        return [normalize_url(it["url"]), "t:" + title_key(it["title"])]

    def filter_new(self, items: list[dict], week: str) -> list[dict]:
        return [it for it in items
                if not any(self.data.get(k) not in (None, week) for k in self.keys(it))]

    def mark(self, items: list[dict], week: str) -> None:
        for it in items:
            for k in self.keys(it):
                self.data.setdefault(k, week)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=0, sort_keys=True), "utf-8")


def select_for_analysis(items: list[dict], limit: int) -> list[dict]:
    """超過上限時保留：被多個關鍵字命中的、產業媒體、較新的、被引用多的。"""
    def newest_first(it):
        return it.get("published") or ""

    def priority(it):
        return (-len(it.get("queries", [])), KIND_PRIORITY.get(it["kind"], 9),
                -(it.get("meta", {}).get("cited_by") or 0))

    # Python 的排序是穩定的：先依日期，再依優先度，同優先度時較新的在前
    chosen = sorted(items, key=newest_first, reverse=True)
    chosen.sort(key=priority)
    chosen = chosen[:limit]
    # 編號順序：產業媒體 → 新聞 → 論文，各自依日期新到舊
    chosen.sort(key=newest_first, reverse=True)
    chosen.sort(key=lambda it: KIND_PRIORITY.get(it["kind"], 9))
    for i, it in enumerate(chosen, 1):
        it["sid"] = f"S{i}"
    return chosen


def compute_stats(items: list[dict]) -> dict:
    kinds = Counter(it["kind"] for it in items)
    langs = Counter(it.get("lang") or "?" for it in items)
    queries = Counter(q for it in items for q in it.get("queries", []))
    papers = [it for it in items if it["kind"] == "paper"]
    countries = Counter(c for it in papers for c in it.get("meta", {}).get("countries", []))
    institutions = Counter(i for it in papers for i in it.get("meta", {}).get("institutions", []))
    sources = Counter(it["source"] for it in items if it["kind"] != "paper")
    return {
        "total": len(items),
        "by_kind": dict(kinds),
        "by_lang": dict(langs),
        "top_queries": queries.most_common(15),
        "paper_countries": countries.most_common(12),
        "paper_institutions": institutions.most_common(12),
        "top_media": sources.most_common(12),
    }
