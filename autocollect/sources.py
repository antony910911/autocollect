"""資料收集：Google News RSS、產業 RSS、OpenAlex 論文。

每個收集器回傳統一格式的 item dict：
    kind, title, url, source, published (YYYY-MM-DD), lang, summary, query, meta
任何單一來源失敗都不會中斷整體流程，錯誤會記錄在 status 裡，最後寫進報告。
"""

from __future__ import annotations

import html
import os
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


def _get(url: str, retries: int = 0, **kwargs) -> requests.Response:
    """GET；遇到 429（請求過多）或 5xx 時依 Retry-After 或指數退避重試。"""
    for attempt in range(retries + 1):
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, **kwargs)
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < retries:
            wait = resp.headers.get("Retry-After", "")
            time.sleep(min(float(wait) if wait.isdigit() else 5 * 2 ** attempt, 60))
            continue
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
    feed = feedparser.parse(_get(feed_cfg["url"], retries=1).content)
    if not feed.entries:
        # 回傳的不是 RSS（常見於網站改版或被防爬機制擋下，回了一般網頁）
        raise ValueError(f"沒有讀到任何 RSS 項目（{feed.get('bozo_exception') or '格式不符'}）")
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


def openalex(query: str, days: int, per_page: int, mailto: str = "", api_key: str = "") -> list[dict]:
    since = (date.today() - timedelta(days=days)).isoformat()
    params = {
        "search": query,
        "filter": f"from_publication_date:{since},type:article|review",
        "sort": "relevance_score:desc",
        "per_page": per_page,
    }
    if mailto:
        params["mailto"] = mailto
    if api_key:
        params["api_key"] = api_key
    data = _get("https://api.openalex.org/works", retries=3, params=params).json()
    return [parse_openalex_work(w, query) for w in data.get("results", [])]


def _crossref_date(work: dict) -> str | None:
    for key in ("published-online", "published-print", "published", "issued", "created"):
        parts = (work.get(key) or {}).get("date-parts") or [[]]
        p = parts[0]
        if p and p[0]:
            return date(p[0], (p[1] if len(p) > 1 else 1), (p[2] if len(p) > 2 else 1)).isoformat()
    return None


def parse_crossref_work(work: dict, query: str) -> dict:
    institutions = []
    for au in work.get("author", []):
        for aff in au.get("affiliation", []):
            name = aff.get("name")
            if name and name not in institutions:
                institutions.append(name)
    doi = work.get("DOI")
    return {
        "kind": "paper",
        "title": clean_text((work.get("title") or [""])[0], 300),
        "url": f"https://doi.org/{doi}" if doi else work.get("URL", ""),
        "source": (work.get("container-title") or ["Crossref"])[0],
        "published": _crossref_date(work),
        "lang": work.get("language") or "en",
        "summary": clean_text(work.get("abstract"), 700),
        "query": query,
        "meta": {"institutions": institutions[:6], "countries": [],
                 "cited_by": work.get("is-referenced-by-count", 0), "via": "crossref"},
    }


def crossref(query: str, days: int, rows: int, mailto: str = "") -> list[dict]:
    """OpenAlex 失敗時的備援論文來源（Crossref 不需金鑰；沒有作者國家資訊）。"""
    since = (date.today() - timedelta(days=days)).isoformat()
    params = {"query.bibliographic": query, "filter": f"from-pub-date:{since},type:journal-article",
              "rows": rows, "sort": "relevance"}
    if mailto:
        params["mailto"] = mailto
    data = _get("https://api.crossref.org/works", retries=2, params=params).json()
    works = data.get("message", {}).get("items", [])
    return [it for it in (parse_crossref_work(w, query) for w in works) if it["title"]]


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
    oa_mailto = mailto or oa.get("mailto", "")
    oa_key = os.environ.get("OPENALEX_API_KEY", "")
    per_query = oa.get("max_per_query", 25)

    def papers(q):
        # OpenAlex 連續失敗 3 次後，其餘查詢直接用 Crossref，避免每次都等重試
        if oa_failures[0] < 3:
            try:
                return openalex(q, paper_days, per_query, oa_mailto, oa_key)
            except requests.RequestException as exc:
                oa_failures[0] += 1
                reason = f"{type(exc).__name__}: {exc}"[:80]
        else:
            reason = "先前連續失敗，略過"
        got = crossref(q, paper_days, per_query, oa_mailto)
        fallbacks.append(f"OpenAlex {q}（{reason}）→ 改用 Crossref 取得 {len(got)} 筆")
        return got

    fallbacks: list[str] = []
    oa_failures = [0]
    for q in oa.get("queries", []):
        jobs.append((f"論文 {q}", lambda q=q: papers(q)))

    for name, fn in jobs:
        try:
            got = fn()
            items.extend(got)
            status.append({"source": name, "ok": True, "count": len(got)})
        except Exception as exc:  # 單一來源失敗不影響其他來源
            status.append({"source": name, "ok": False, "count": 0, "error": f"{type(exc).__name__}: {exc}"[:200]})
        time.sleep(0.5)
    for note in fallbacks:
        status.append({"source": note, "ok": True, "count": 0, "note": True})
    return items, status

