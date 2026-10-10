"""呼叫 Claude 產生週報分析。"""

from __future__ import annotations

import os
import anthropic

DEFAULT_MODEL = "claude-opus-5-5"
KIND_LABEL = {"industry": "產業媒體", "news": "新聞", "paper": "論文"}


class AnalysisError(RuntimeError):
    pass


def format_item(it: dict) -> str:
    head = (f"[{it['sid']}] ({KIND_LABEL.get(it['kind'], it['kind'])}｜{it.get('lang') or '?'}｜"
            f"{it.get('published') or '日期不明'}｜{it['source']}) {it['title']}")
    lines = [head]
    if it.get("summary"):
        lines.append(f"    摘要：{it['summary']}")
    meta = it.get("meta") or {}
    if meta.get("institutions"):
        lines.append(f"    機構：{'; '.join(meta['institutions'])}")
    if meta.get("countries"):
        lines.append(f"    國家：{', '.join(meta['countries'])}")
    return "\n".join(lines)


def format_stats(stats: dict) -> str:
    def pairs(rows):
        return "、".join(f"{k}({v})" for k, v in rows) or "無"
    return "\n".join([
        f"- 資料總數：{stats['total']}，類型：{stats['by_kind']}，語言：{stats['by_lang']}",
        f"- 命中最多的關鍵字：{pairs(stats['top_queries'])}",
        f"- 論文作者國家分布：{pairs(stats['paper_countries'])}",
        f"- 論文主要機構：{pairs(stats['paper_institutions'])}",
        f"- 主要媒體來源：{pairs(stats['top_media'])}",
    ])


def build_user_message(items: list[dict], stats: dict, week: str, profile: str,
                       previous_report: str | None) -> str:
    parts = [f"# 週次：{week}", "", "# 讀者背景", profile.strip() or "（未提供）", "",
             "# 本週資料統計（程式計算）", format_stats(stats), ""]
    if previous_report:
        parts += ["# 上一期週報（僅供比較趨勢延續或轉變；上一期的內容不可當作本週來源引用）",
                  "<previous_report>", previous_report, "</previous_report>", ""]
    parts += ["# 本週資料", "", "\n".join(format_item(it) for it in items), "",
              "請依系統指示撰寫本週分析。"]
    return "\n".join(parts)


def run_analysis(system: str, user: str) -> tuple[str, dict]:
    """回傳 (markdown, info)。info 包含實際使用的模型與 token 用量。"""
    model = os.environ.get("AUTOCOLLECT_MODEL") or DEFAULT_MODEL
    effort = os.environ.get("AUTOCOLLECT_EFFORT") or "high"
    client = anthropic.Anthropic()

    try:
        with client.beta.messages.stream(
            model=model,
            max_tokens=64000,
            system=system,
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
            # 若主模型因安全分類拒答，由伺服器自動改用建議的備援模型重跑
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": user}],
        ) as stream:
            message = stream.get_final_message()
    except anthropic.AuthenticationError as exc:
        raise AnalysisError("ANTHROPIC_API_KEY 無效或未設定") from exc
    except anthropic.RateLimitError as exc:
        raise AnalysisError(f"API 速率限制：{exc.message}") from exc
    except anthropic.APIStatusError as exc:
        raise AnalysisError(f"API 錯誤 {exc.status_code}：{exc.message}") from exc
    except anthropic.APIConnectionError as exc:
        raise AnalysisError("無法連線到 Anthropic API") from exc

    if message.stop_reason == "refusal":
        raise AnalysisError("模型拒絕產生內容（refusal）")
    text = "".join(b.text for b in message.content if b.type == "text").strip()
    if not text:
        raise AnalysisError(f"模型沒有回傳文字（stop_reason={message.stop_reason}）")
    info = {
        "model": message.model,
        "stop_reason": message.stop_reason,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
    }
    return text, info
