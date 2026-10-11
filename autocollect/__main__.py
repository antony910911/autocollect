"""生質能週報

兩種用法：
- 免 API 金鑰（Claude Code 排程分析）：
    python -m autocollect collect          # 收集資料，產生分析包 data/packs/<週次>.md
    python -m autocollect build --analysis data/analysis/<週次>.md   # 驗證引用並組成報告
- 使用 Anthropic API 一次完成：
    python -m autocollect run
- 把報告寫進 Folio 筆記本（需要環境變數 FOLIO_SYNC_TOKEN）：
    python -m autocollect folio
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from . import analyze, folio, report, sources, store, topics

ROOT = Path(__file__).resolve().parent.parent


def week_id(d: date) -> str:
    iso = d.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def previous_report(reports_dir: Path, week: str) -> str | None:
    """取上一期報告的分析本文（去掉統計、參考來源與附錄），供趨勢比較。"""
    older = sorted(p for p in reports_dir.glob("20*-W*.md") if p.stem < week)
    if not older:
        return None
    text = older[-1].read_text("utf-8")
    return text.split("\n## 本週資料概況")[0][:40000]


def write_index(reports_dir: Path, title: str) -> None:
    rows = [f"- [{p.stem}]({p.name})" for p in sorted(reports_dir.glob("20*-W*.md"), reverse=True)]
    (reports_dir / "README.md").write_text(f"# {title}列表\n\n" + "\n".join(rows) + "\n", "utf-8")


def get_topic(args) -> topics.Topic:
    return topics.get_topic(ROOT, getattr(args, "topic", None) or topics.DEFAULT_TOPIC)


def collect(topic: topics.Topic, cfg: dict, today: date) -> dict:
    """收集、去重、排除先前週報已出現者、挑選並編號，存成 <資料夾>/raw/<週次>.json。"""
    week = week_id(today)
    history = store.History(topic.data / "history.json")
    items, status = sources.collect_all(cfg, mailto=os.environ.get("OPENALEX_MAILTO", ""))
    unique = store.dedupe(items)
    new_items = history.filter_new(unique, week)
    print(f"收集 {len(items)} 筆，去重後 {len(unique)} 筆，排除先前週報已出現者後 {len(new_items)} 筆")
    selected = store.select_for_analysis(new_items, cfg.get("max_items_for_analysis", 360),
                                          cfg.get("quotas"))
    start = today - timedelta(days=cfg.get("news_lookback_days", 7))
    bundle = {
        "week": week,
        "date_range": f"{start.isoformat()} ～ {today.isoformat()}（論文回溯 {cfg.get('papers_lookback_days', 21)} 天）",
        "status": status,
        "stats": store.compute_stats(selected),
        "items": selected,
    }
    path = topic.raw_path(week)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, ensure_ascii=False, indent=1), "utf-8")
    history.mark(new_items, week)
    history.save()
    return bundle


def load_bundle(topic: topics.Topic, week: str) -> dict:
    path = topic.raw_path(week)
    if not path.exists():
        raise SystemExit(f"找不到 {path}，請先執行 collect")
    return json.loads(path.read_text("utf-8"))


def analysis_inputs(topic: topics.Topic, cfg: dict, bundle: dict) -> tuple[str, str]:
    """回傳 (系統指示, 使用者訊息)，API 模式與分析包共用同一份內容。"""
    system = (topic.root / topic.prompt).read_text("utf-8")
    user = analyze.build_user_message(bundle["items"], bundle["stats"], bundle["week"],
                                      cfg.get("researcher_profile", ""),
                                      previous_report(topic.reports, bundle["week"]))
    return system, user


def write_pack(topic: topics.Topic, cfg: dict, bundle: dict) -> Path:
    """分析包：給 Claude（例如 Claude Code 排程任務）閱讀的完整分析指示與資料。"""
    system, user = analysis_inputs(topic, cfg, bundle)
    path = topic.pack_path(bundle["week"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{system}\n\n---\n\n{user}\n", "utf-8")
    return path


def build(topic: topics.Topic, bundle: dict, analysis_text: str | None, info: dict | None,
          note: str | None) -> dict:
    reports_dir = topic.reports
    reports_dir.mkdir(parents=True, exist_ok=True)
    if not bundle["items"]:
        note = "本週沒有收集到任何新資料，請檢查「品質檢查」中的來源狀態。"
    md, qa = report.assemble(bundle["week"], bundle["date_range"], analysis_text, bundle["items"],
                             bundle["stats"], bundle["status"], info, note, title=topic.title)
    out_path = reports_dir / f"{bundle['week']}.md"
    out_path.write_text(md, "utf-8")
    write_index(reports_dir, topic.title)
    print(f"報告已寫入 {out_path}")
    if analysis_text:
        print(f"引用 {qa['cited']} 個來源；無效編號 {len(qa['invalid'])}；未附來源條列 {len(qa['uncited'])}")
        for line in qa["uncited"]:
            print(f"  未附來源：{line[:100]}")
        if qa["invalid"]:
            print(f"  無效編號：{', '.join(sorted(set(qa['invalid'])))}")
    if note:
        print(f"注意：{note}", file=sys.stderr)
    return qa


def target_date(args) -> date:
    return date.fromisoformat(args.date) if args.date else date.today()


def cmd_collect(args) -> int:
    topic = get_topic(args)
    week = week_id(target_date(args))
    if topic.analysis_path(week).exists() and not args.force:
        # 已有分析的週次不能重新收集：重新收集會改變來源編號，讓既有分析的引用全部對錯
        print(f"[{topic.name}] {week} 已有分析（{topic.analysis_path(week).relative_to(ROOT)}），不重新收集")
        return 0
    cfg = topic.load_config()
    bundle = collect(topic, cfg, target_date(args))
    pack = write_pack(topic, cfg, bundle)
    print(f"[{topic.name}] 分析包已寫入 {pack}（{len(bundle['items'])} 筆資料）")
    return 0 if bundle["items"] else 2


def cmd_build(args) -> int:
    topic = get_topic(args)
    week = args.week or week_id(target_date(args))
    bundle = load_bundle(topic, week)
    analysis = ROOT / args.analysis if args.analysis else topic.analysis_path(week)
    if args.analysis or analysis.exists():
        # 沒指定 --analysis 但這週已有分析時也用它，避免把完整報告蓋回資料整理版
        text = analysis.read_text("utf-8").strip()
        qa = build(topic, bundle, text, {"model": args.model}, None)
        return 1 if qa["invalid"] else 0
    build(topic, bundle, None, None, "尚未產生 AI 分析，以下只有資料整理。")
    return 0


def cmd_run(args) -> int:
    topic = get_topic(args)
    cfg = topic.load_config()
    week = week_id(target_date(args))
    if args.reuse_raw and topic.raw_path(week).exists():
        bundle = load_bundle(topic, week)
        print(f"使用已收集的資料 {topic.raw_path(week)}（{len(bundle['items'])} 筆）")
    else:
        bundle = collect(topic, cfg, target_date(args))

    analysis_text, info, note, exit_code = None, None, None, 0
    has_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not bundle["items"]:
        exit_code = 2
    elif args.no_ai:
        note = "以 --no-ai 執行，只輸出資料整理。"
    elif not has_key:
        note = "未設定 ANTHROPIC_API_KEY，只輸出資料整理，沒有 AI 分析。"
    else:
        system, user = analysis_inputs(topic, cfg, bundle)
        try:
            analysis_text, info = analyze.run_analysis(system, user)
        except analyze.AnalysisError as exc:
            note = f"AI 分析失敗：{exc}。以下只有資料整理。"
            exit_code = 2
    build(topic, bundle, analysis_text, info, note)
    return exit_code


def cmd_folio(args) -> int:
    topic = get_topic(args)
    reports = sorted(topic.reports.glob("20*-W*.md"))
    path = topic.reports / f"{args.week}.md" if args.week else (reports[-1] if reports else None)
    if not path or not path.exists():
        print(f"[{topic.name}] 還沒有任何報告，略過")
        return 0 if not args.week else 1
    text = path.read_text("utf-8")
    if "## 一、" not in text and not args.force:
        print(f"[{topic.name}] {path.name} 還沒有 AI 分析，先不上傳（要上傳資料整理版請加 --force）")
        return 0
    token = os.environ.get("FOLIO_SYNC_TOKEN", "")
    if not token:
        print("未設定 FOLIO_SYNC_TOKEN", file=sys.stderr)
        return 1
    url = os.environ.get("FOLIO_URL") or folio.DEFAULT_URL
    result = folio.publish(url, token, folio.build_records(path.stem, text, topic.folio))
    print(f"[{topic.name}] 已上傳 {path.stem} 到 Folio「{topic.folio['notebook_name']}」"
          f"（伺服器接受 {result.get('accepted')} 筆紀錄）")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="autocollect", description="國內外新知週報（可多個主題）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--topic", default=topics.DEFAULT_TOPIC,
                       help="週報主題（列在 config/topics.yaml），預設 bioenergy")
        p.add_argument("--date", help="以指定日期（YYYY-MM-DD）當作執行日，預設今天")

    p = sub.add_parser("collect", help="收集資料並產生分析包（不需 API 金鑰）")
    common(p)
    p.add_argument("--force", action="store_true", help="即使這週已有分析也重新收集（會讓既有分析的引用失效）")
    p.set_defaults(func=cmd_collect)

    p = sub.add_parser("build", help="把分析文字與本週資料組成報告，並驗證引用")
    common(p)
    p.add_argument("--week", help="週次，例如 2026-W41，預設本週")
    p.add_argument("--analysis", help="分析文字檔（Markdown）；省略則只輸出資料整理")
    p.add_argument("--model", default="Claude（Claude Code 排程）", help="報告中標示的分析者")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("run", help="收集 + 用 Anthropic API 分析 + 組成報告")
    common(p)
    p.add_argument("--no-ai", action="store_true", help="不呼叫 Claude，只輸出資料整理")
    p.add_argument("--reuse-raw", action="store_true",
                   help="不重新收集，直接用 data/raw/ 中本週已收集的資料重跑分析")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("folio", help="把週報寫進 Folio 筆記本")
    p.add_argument("--topic", default=topics.DEFAULT_TOPIC)
    p.add_argument("--week", help="週次，預設最新一期")
    p.add_argument("--force", action="store_true", help="還沒有 AI 分析也上傳")
    p.set_defaults(func=cmd_folio)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
