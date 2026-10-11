import json
from datetime import date
from pathlib import Path

import feedparser
import pytest

from autocollect import __main__ as cli
from autocollect import analyze, report, sources, store

FIX = Path(__file__).parent / "fixtures"


def make(sid, kind="news", **kw):
    it = {"sid": sid, "kind": kind, "title": f"title {sid}", "url": f"https://e.com/{sid}",
          "source": "Src", "published": "2026-10-08", "lang": "en", "summary": "", "queries": ["q"], "meta": {}}
    it.update(kw)
    return it


def test_google_news_parsing_strips_publisher_and_old_items():
    feed = feedparser.parse((FIX / "google_news.xml").read_bytes())
    items = sources.parse_feed_entries(feed, kind="news", source_name="Google News", lang="zh-TW",
                                       query="生質能", since=date(2026, 10, 1))
    assert [it["title"] for it in items] == ["台糖沼氣發電廠擴建 年發電量倍增", "能源署公布生質能躉購費率草案"]
    assert items[0]["source"] == "經濟日報"
    assert items[0]["published"] == "2026-10-08"


def test_openalex_parsing_rebuilds_abstract_and_affiliations():
    work = json.loads((FIX / "openalex.json").read_text())["results"][0]
    it = sources.parse_openalex_work(work, "biomass pyrolysis")
    assert it["summary"] == "Bio-oil was upgraded over zeolite."
    assert it["url"] == "https://doi.org/10.1000/abc"
    assert it["meta"]["countries"] == ["TW", "US"]
    assert "NREL" in it["meta"]["institutions"]


def test_dedupe_merges_queries_by_url_and_title():
    a = {"kind": "news", "title": "SAF plant opens", "url": "https://x.com/a?utm_source=1", "query": "saf", "source": "X"}
    b = {"kind": "news", "title": "SAF plant opens", "url": "https://x.com/a", "query": "biofuel", "source": "X"}
    c = {"kind": "news", "title": "SAF Plant Opens!", "url": "https://y.com/z", "query": "jet", "source": "Y"}
    out = store.dedupe([a, b, c])
    assert len(out) == 1 and out[0]["queries"] == ["saf", "biofuel", "jet"]


def test_history_excludes_items_from_earlier_weeks(tmp_path):
    h = store.History(tmp_path / "h.json")
    it = {"title": "A", "url": "https://a.com/1"}
    h.mark([it], "2026-W40")
    h.save()
    h2 = store.History(tmp_path / "h.json")
    assert h2.filter_new([it], "2026-W41") == []
    assert h2.filter_new([it], "2026-W40") == [it]  # 同一週重跑仍保留


def test_select_orders_and_numbers():
    items = [make(None, "paper", published="2026-10-01"), make(None, "news", published="2026-10-02"),
             make(None, "industry", published="2026-10-03"), make(None, "news", published="2026-10-05")]
    out = store.select_for_analysis(items, 3)
    assert [it["sid"] for it in out] == ["S1", "S2", "S3"]
    assert [it["kind"] for it in out] == ["industry", "news", "news"]
    assert out[1]["published"] == "2026-10-05"


def test_validate_citations_flags_unknown_ids():
    text = "A happened [S1]. B [S2, S9]. C [S9]."
    fixed, cited, invalid = report.validate_citations(text, {"S1", "S2"})
    assert fixed == "A happened [S1]. B [S2][⚠️來源編號不存在]. C [⚠️來源編號不存在]."
    assert cited == ["S1", "S2"] and invalid == ["S9", "S9"]


def test_uncited_claims_skips_idea_section_and_table_header():
    text = "\n".join([
        "## 二、國際技術與產業動態",
        "- 某公司宣布建置一座年產十萬噸的 SAF 工廠於鹿特丹港區",
        "- 另一家公司完成示範運轉並取得認證，已有來源 [S1]",
        "| 技術路徑 | 本週代表案例 | 發展階段 | 訊號強度 | 來源 |",
        "|---|---|---|---|---|",
        "| HEFA | 某某公司新廠完工並開始供應航空公司 | 商轉 | 強 | [S1] |",
        "## 六、可開發的新題目建議",
        "- 這是一個推論性的題目構想，沒有來源也沒有關係的一段文字",
    ])
    assert report.uncited_claims(text) == ["- 某公司宣布建置一座年產十萬噸的 SAF 工廠於鹿特丹港區"]


def test_build_user_message_contains_items_and_previous_report():
    items = [make("S1", summary="hello", meta={"institutions": ["NTU"], "countries": ["TW"]})]
    stats = store.compute_stats(items)
    msg = analyze.build_user_message(items, stats, "2026-W41", "profile text", "上期內容")
    assert "[S1] (新聞｜en｜2026-10-08｜Src) title S1" in msg
    assert "機構：NTU" in msg and "<previous_report>" in msg and "profile text" in msg


def test_full_run_offline(tmp_path, monkeypatch):
    """模擬收集與 Claude 回應，確認整個流程能產出報告並更新歷史紀錄。"""
    root = tmp_path
    (root / "config").mkdir()
    (root / "prompts").mkdir()
    (root / "config" / "sources.yaml").write_text("news_lookback_days: 7\nresearcher_profile: test\n", "utf-8")
    (root / "prompts" / "weekly_analysis.md").write_text("system", "utf-8")
    monkeypatch.setattr(cli, "ROOT", root)

    fake = [{"kind": "news", "title": f"消息 {i}", "url": f"https://n.com/{i}", "source": "媒體",
             "published": "2026-10-08", "lang": "zh-TW", "summary": "", "query": "生質能", "meta": {}}
            for i in range(3)]
    monkeypatch.setattr(sources, "collect_all", lambda cfg, mailto="": (fake, [{"source": "x", "ok": True, "count": 3}]))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    seen = {}

    def fake_analysis(system, user):
        seen["n"] = user.count("\n[S")
        return ("## 一、本週重點摘要\n- 台灣某廠擴建沼氣發電設備，預計明年完工 [S1]\n- 錯誤引用的一條長長的敘述內容 [S99]\n",
                {"model": "m", "stop_reason": "end_turn", "input_tokens": 10, "output_tokens": 5})
    monkeypatch.setattr(analyze, "run_analysis", fake_analysis)

    assert cli.main(["run", "--date", "2026-10-10"]) == 0
    md = (root / "reports" / "2026-W41.md").read_text("utf-8")
    assert seen["n"] == 3
    assert "## 參考來源（本週報告引用）" in md and "[消息 0](https://n.com/0)" in md
    assert "不存在的來源編號：1" in md
    assert "2026-W41" in (root / "reports" / "README.md").read_text("utf-8")

    # 下一週同樣的消息不應再出現
    assert cli.main(["run", "--date", "2026-10-17", "--no-ai"]) == 2
    md2 = (root / "reports" / "2026-W42.md").read_text("utf-8")
    assert "沒有收集到任何新資料" in md2


def test_collect_then_build_without_api(tmp_path, monkeypatch):
    """免 API 流程：collect 產生分析包，build 驗證外部寫好的分析。"""
    root = tmp_path
    (root / "config").mkdir()
    (root / "prompts").mkdir()
    (root / "config" / "sources.yaml").write_text("researcher_profile: 熱裂解專長\n", "utf-8")
    (root / "prompts" / "weekly_analysis.md").write_text("系統指示", "utf-8")
    monkeypatch.setattr(cli, "ROOT", root)
    fake = [{"kind": "paper", "title": "Bio-oil study", "url": "https://doi.org/1", "source": "Fuel",
             "published": "2026-10-01", "lang": "en", "summary": "abs", "query": "pyrolysis",
             "meta": {"institutions": ["NTU"], "countries": ["TW"]}}]
    monkeypatch.setattr(sources, "collect_all", lambda cfg, mailto="": (fake, [{"source": "x", "ok": True, "count": 1}]))

    assert cli.main(["collect", "--date", "2026-10-10"]) == 0
    pack = (root / "data" / "packs" / "2026-W41.md").read_text("utf-8")
    assert pack.startswith("系統指示") and "[S1] (論文" in pack and "熱裂解專長" in pack

    (root / "data" / "analysis").mkdir()
    good = root / "data" / "analysis" / "2026-W41.md"
    good.write_text("## 一、本週重點摘要\n- 台大團隊發表熱裂解生質油升級研究成果 [S1]\n", "utf-8")
    assert cli.main(["build", "--week", "2026-W41", "--analysis", "data/analysis/2026-W41.md"]) == 0
    md = (root / "reports" / "2026-W41.md").read_text("utf-8")
    assert "Claude（Claude Code 排程）" in md and "[Bio-oil study](https://doi.org/1)" in md

    good.write_text("## 一、本週重點摘要\n- 不存在的引用造成驗證失敗的一段敘述 [S7]\n", "utf-8")
    assert cli.main(["build", "--week", "2026-W41", "--analysis", "data/analysis/2026-W41.md"]) == 1


def test_crossref_parsing():
    work = {"DOI": "10.1/x", "title": ["PHA from <i>swine</i> manure"], "container-title": ["Bioresour. Technol."],
            "published-online": {"date-parts": [[2026, 10, 2]]}, "abstract": "<jats:p>VFA to PHA.</jats:p>",
            "author": [{"affiliation": [{"name": "ITRI"}]}], "is-referenced-by-count": 1}
    it = sources.parse_crossref_work(work, "pha")
    assert it["title"] == "PHA from swine manure" and it["url"] == "https://doi.org/10.1/x"
    assert it["published"] == "2026-10-02" and it["summary"] == "VFA to PHA."
    assert it["meta"]["institutions"] == ["ITRI"]


def test_papers_fall_back_to_crossref(monkeypatch):
    import requests as rq

    def boom(*a, **k):
        raise rq.HTTPError("429")
    monkeypatch.setattr(sources, "openalex", boom)
    monkeypatch.setattr(sources, "crossref", lambda q, d, r, m="": [{"kind": "paper", "title": "t", "url": "u", "query": q}])
    monkeypatch.setattr(sources.time, "sleep", lambda s: None)
    items, status = sources.collect_all({"openalex": {"queries": ["pha"]}})
    assert len(items) == 1
    assert status[0]["ok"] and "Crossref" in status[-1]["source"]
    out = report.status_section(status)
    assert "成功 1 / 1" in out and "↪️" in out


def test_rss_without_entries_is_reported_as_failure(monkeypatch):
    class R:
        content = b"<html>blocked</html>"
    monkeypatch.setattr(sources, "_get", lambda *a, **k: R())
    with pytest.raises(ValueError):
        sources.rss({"name": "X", "url": "https://x"}, 7)


def test_selection_keeps_paper_quota_and_spreads_across_queries():
    news = [make(None, "news", url=f"https://n/{i}", published="2026-10-08") for i in range(50)]
    papers = [make(None, "paper", url=f"https://p/{q}{r}", queries=[q], rank=r, published="2026-10-01")
              for q in "abc" for r in range(10)]
    out = store.select_for_analysis(news + papers, 20, {"industry": 0, "news": 14, "paper": 6})
    picked = [it for it in out if it["kind"] == "paper"]
    assert len(out) == 20 and len(picked) == 6
    assert sorted(it["rank"] for it in picked) == [0, 0, 0, 1, 1, 1]  # 每個關鍵字取前兩名

    # 論文不夠用時，多的名額給新聞
    out = store.select_for_analysis(news + papers[:2], 20, {"industry": 0, "news": 14, "paper": 6})
    assert len(out) == 20 and sum(it["kind"] == "news" for it in out) == 18


def test_second_topic_uses_its_own_folders(tmp_path, monkeypatch):
    """新主題的資料、報告與歷史紀錄都放在自己的資料夾，不影響生質能週報。"""
    root = tmp_path
    (root / "config").mkdir()
    (root / "prompts").mkdir()
    (root / "config" / "topics.yaml").write_text(
        "topics:\n  farnesene:\n    title: 法尼烯週報\n    config: config/f.yaml\n    prompt: prompts/f.md\n"
        "    data_dir: data/farnesene\n    reports_dir: reports/farnesene\n    folio: {}\n", "utf-8")
    (root / "config" / "f.yaml").write_text("researcher_profile: 酵母\n", "utf-8")
    (root / "prompts" / "f.md").write_text("法尼烯指示", "utf-8")
    monkeypatch.setattr(cli, "ROOT", root)
    fake = [{"kind": "news", "title": "β-farnesene plant", "url": "https://f/1", "source": "X",
             "published": "2026-10-08", "lang": "en", "summary": "", "query": "farnesene", "meta": {}}]
    monkeypatch.setattr(sources, "collect_all", lambda cfg, mailto="": (fake, [{"source": "x", "ok": True, "count": 1}]))

    assert cli.main(["collect", "--topic", "farnesene", "--date", "2026-10-10"]) == 0
    assert (root / "data" / "farnesene" / "packs" / "2026-W41.md").read_text("utf-8").startswith("法尼烯指示")
    assert (root / "data" / "farnesene" / "history.json").exists()
    assert not (root / "data" / "history.json").exists()

    analysis = root / "data" / "farnesene" / "analysis" / "2026-W41.md"
    analysis.parent.mkdir(parents=True)
    analysis.write_text("## 一、本週重點摘要\n- 某公司宣布建置 β-法尼烯示範工廠並開始試產 [S1]\n", "utf-8")
    assert cli.main(["build", "--topic", "farnesene", "--week", "2026-W41",
                     "--analysis", "data/farnesene/analysis/2026-W41.md"]) == 0
    md = (root / "reports" / "farnesene" / "2026-W41.md").read_text("utf-8")
    assert md.startswith("# 法尼烯週報 2026-W41")
    assert not (root / "reports" / "2026-W41.md").exists()


def test_repo_topics_are_valid():
    """實際的 config/topics.yaml：每個主題的設定檔與分析指示都存在，Folio id 不重複。"""
    from pathlib import Path
    from autocollect import topics
    root = Path(__file__).resolve().parent.parent
    reg = topics.all_topics(root)
    assert {"bioenergy", "farnesene"} <= set(reg)
    ids = set()
    for name in reg:
        t = topics.get_topic(root, name)
        assert (root / t.prompt).exists() and t.load_config()["openalex"]["queries"]
        for key in ("notebook_id", "section_id", "page_prefix", "item_prefix"):
            assert t.folio[key] not in ids
            ids.add(t.folio[key])
    # 生質能週報既有的 Folio id 不能變，否則會在 Folio 產生重複的筆記本
    assert reg["bioenergy"]["folio"]["notebook_id"] == "nb_autocollect_bio"
