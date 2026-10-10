"""資料收集：Google News RSS、產業 RSS、OpenAlex 論文。

每個收集器回傳統一格式的 item dict：
    kind, title, url, source, published (YYYY-MM-DD), lang, summary, query, meta
任何單一來源失敗都不會中斷整體流程，錯誤會記錄在 status 裡，最後寫進報告。
"""

from __future__ import annotations

import html
import re
import time
from datetime import date, timedelta
from urllib.parse import quote_plus

import feedparser
import requests

USER_AGENT = "autocollect-bioenergy-weekly/1.0 (+https://github.com/antony910911/autocollect)"
TIMEOUT = 30

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def clean_text(text: str | None, limit: int = 600) -> str:
    if not text:
        return ""
    text = html.unescape(_TAG_RE.sub(" ", text))
    text = _WS_RE.sub(" ", text).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def _entry_date(entry) -> str | None:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            return date(parsed.tm_year, parsed.tm_mon, parsed.tm_mday).isoformat()
    return None


def _get(url: str, **kwargs) -> requests.Response:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, **kwargs)
    resp.raise_for_status()
    return resp


def parse_feed_entries(feed, *, kind: str, source_name: str, lang: str, query: str,
                       since: date, limit: int | None = None) -> list[dict]:
    items = []
    for entry in feed.entries:
        published = _entry_date(entry)
        if published and published < since.isoformat():
            continue
        title = clean_text(entry.get("title"), 300)
        source = source_name
        # Google News 的標題格式為「標題 - 媒體名稱」，並附 <source> 欄位
        src = entry.get("source")
        if src and src.get("title"):
            source = src["title"]
            suffix = f" - {source}"
            if title.endswith(suffix):
                title = title[: -len(suffix)]
        items.append({
            "kind": kind,
            "title": title,
            "url": entry.get("link", ""),
            "source": source,
            "published": published,
            "lang": lang,
            "summary": clean_text(entry.get("summary")),
            "query": query,
            "meta": {},
        })
        if limit and len(items) >= limit:
            break
    return items


def google_news(group: dict, query: str, days: int) -> list[dict]:
    q = quote_plus(f"{query} when:{days}d")
    url = (f"https://news.google.com/rss/search?q={q}"
           f"&hl={group['hl']}&gl={group['gl']}&ceid={quote_plus(group['ceid'])}")
    feed = feedparser.parse(_get(url).content)
    since = date.today() - timedelta(days=days)
    return parse_feed_entries(feed, kind="news", source_name="Google News", lang=group["lang"],
                              query=query, since=since, limit=group.get("max_per_query", 20))


def rss(feed_cfg: dict, days: int) -> list[dict]:
    feed = feedparser.parse(_get(feed_cfg["url"]).content)
    since = date.today() - timedelta(days=days)
    return parse_feed_entries(feed, kind="industry", source_name=feed_cfg["name"],
                              lang=feed_cfg.get("lang", "en"), query=feed_cfg["name"], since=since)


def _openalex_abstract(inverted: dict | None) -> str:
    if not inverted:
        return ""
    positions = [(pos, word) for word, poss in inverted.items() for pos in poss]
    return " ".join(word for _, word in sorted(positions))


def parse_openalex_work(work: dict, query: str) -> dict:
    loc = work.get("primary_location") or {}
    venue = (loc.get("source") or {}).get("display_name") or "OpenAlex"
    institutions, countries = [], []
    for au in work.get("authorships", []):
        for inst in au.get("institutions", []):
            name = inst.get("display_name")
            if name and name not in institutions:
                institutions.append(name)
        for c in au.get("countries", []):
            if c and c not in countries:
                countries.append(c)
    doi = work.get("doi")
    return {
        "kind": "paper",
        "title": clean_text(work.get("title") or work.get("display_name"), 300),
        "url": doi or loc.get("landing_page_url") or work.get("id", ""),
        "source": venue,
        "published": work.get("publication_date"),
        "lang": work.get("language") or "en",
        "summary": clean_text(_openalex_abstract(work.get("abstract_inverted_index")), 700),
        "query": query,
        "meta": {
            "institutions": institutions[:6],
            "countries": countries,
            "cited_by": work.get("cited_by_count", 0),
            "openalex_id": work.get("id"),
        },
    }


def openalex(query: str, days: int, per_page: int, mailto: str = "") -> list[dict]:
    since = (date.today() - timedelta(days=days)).isoformat()
    params = {
        "search": query,
        "filter": f"from_publication_date:{since},type:article|review",
        "sort": "relevance_score:desc",
        "per_page": per_page,
    }
    if mailto:
        params["mailto"] = mailto
    data = _get("https://api.openalex.org/works", params=params).json()
    return [parse_openalex_work(w, query) for w in data.get("results", [])]


def collect_all(cfg: dict, mailto: str = "") -> tuple[list[dict], list[dict]]:
    """執行所有收集器，回傳 (items, status)。"""
    items: list[dict] = []
    status: list[dict] = []
    news_days = cfg.get("news_lookback_days", 7)
    paper_days = cfg.get("papers_lookback_days", 21)

    jobs = []
    for group in cfg.get("google_news", []):
        for q in group.get("queries", []):
            jobs.append((f"Google News [{group['lang']}] {q}", lambda g=group, q=q: google_news(g, q, news_days)))
    for feed_cfg in cfg.get("rss_feeds", []):
        jobs.append((f"RSS {feed_cfg['name']}", lambda f=feed_cfg: rss(f, news_days)))
    oa = cfg.get("openalex") or {}
    for q in oa.get("queries", []):
        jobs.append((f"OpenAlex {q}", lambda q=q: openalex(q, paper_days, oa.get("max_per_query", 25),
                                                         mailto or oa.get("mailto", ""))))

    for name, fn in jobs:
        try:
            got = fn()
            items.extend(got)
            status.append({"source": name, "ok": True, "count": len(got)})
        except Exception as exc:  # 單一來源失敗不影響其他來源
            status.append({"source": name, "ok": False, "count": 0, "error": f"{type(exc).__name__}: {exc}"[:200]})
        time.sleep(0.5)
    return items, status

