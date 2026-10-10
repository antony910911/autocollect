"""生質能週報：python -m autocollect run"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

from . import analyze, report, sources, store

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


def write_index(reports_dir: Path) -> None:
    rows = [f"- [{p.stem}]({p.name})" for p in sorted(reports_dir.glob("20*-W*.md"), reverse=True)]
    (reports_dir / "README.md").write_text("# 生質能週報列表\n\n" + "\n".join(rows) + "\n", "utf-8")


def cmd_run(args) -> int:
    cfg = yaml.safe_load((ROOT / args.config).read_text("utf-8"))
    today = date.fromisoformat(args.date) if args.date else date.today()
    week = week_id(today)
    raw_path = ROOT / "data" / "raw" / f"{week}.json"
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    history = store.History(ROOT / "data" / "history.json")

    if args.reuse_raw and raw_path.exists():
        raw = json.loads(raw_path.read_text("utf-8"))
        new_items, status = raw["items"], raw["status"]
        print(f"使用已收集的資料 {raw_path}（{len(new_items)} 筆）")
    else:
        items, status = sources.collect_all(cfg, mailto=os.environ.get("OPENALEX_MAILTO", ""))
        unique = store.dedupe(items)
        new_items = history.filter_new(unique, week)
        print(f"收集 {len(items)} 筆，去重後 {len(unique)} 筆，排除先前週報已出現者後 {len(new_items)} 筆")
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(json.dumps({"week": week, "status": status, "items": new_items},
                                       ensure_ascii=False, indent=1), "utf-8")

    selected = store.select_for_analysis(new_items, cfg.get("max_items_for_analysis", 260))
    stats = store.compute_stats(selected)
    start = today - timedelta(days=cfg.get("news_lookback_days", 7))
    date_range = f"{start.isoformat()} ～ {today.isoformat()}（論文回溯 {cfg.get('papers_lookback_days', 21)} 天）"

    analysis_text, info, note, exit_code = None, None, None, 0
    has_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not selected:
        note = "本週沒有收集到任何新資料，請檢查「品質檢查」中的來源狀態。"
        exit_code = 2
    elif args.no_ai:
        note = "以 --no-ai 執行，只輸出資料整理。"
    elif not has_key:
        note = "未設定 ANTHROPIC_API_KEY，只輸出資料整理，沒有 AI 分析。"
    else:
        try:
            analysis_text, info = analyze.run_analysis(
                selected, stats, week, cfg.get("researcher_profile", ""),
                previous_report(reports_dir, week), ROOT / "prompts" / "weekly_analysis.md")
        except analyze.AnalysisError as exc:
            note = f"AI 分析失敗：{exc}。以下只有資料整理。"
            exit_code = 2

    md, qa = report.assemble(week, date_range, analysis_text, selected, stats, status, info, note)
    out_path = reports_dir / f"{week}.md"
    out_path.write_text(md, "utf-8")
    write_index(reports_dir)
    history.mark(new_items, week)
    history.save()
    print(f"報告已寫入 {out_path}")
    if analysis_text:
        print(f"引用 {qa['cited']} 個來源；無效編號 {len(qa['invalid'])}；未附來源條列 {len(qa['uncited'])}")
    if note:
        print(f"注意：{note}", file=sys.stderr)
    return exit_code


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="autocollect", description="生質能國內外新知週報")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="收集資料並產生本週報告")
    run.add_argument("--config", default="config/sources.yaml")
    run.add_argument("--date", help="以指定日期（YYYY-MM-DD）當作執行日，預設今天")
    run.add_argument("--no-ai", action="store_true", help="不呼叫 Claude，只輸出資料整理")
    run.add_argument("--reuse-raw", action="store_true",
                     help="不重新收集，直接用 data/raw/ 中本週已收集的資料重跑分析")
    args = parser.parse_args(argv)
    return cmd_run(args)


if __name__ == "__main__":
    sys.exit(main())
