"""報告組裝：驗證引用、產生參考來源、品質檢查、附錄。"""

from __future__ import annotations

import re
from collections import defaultdict

from .analyze import KIND_LABEL

CITE_GROUP = re.compile(r"\[(S\d+(?:\s*[,，、;；]\s*S\d+)*)\]")
SID = re.compile(r"S\d+")
# 這些章節允許推論或不需逐句引用，不列入引用覆蓋率檢查
EXEMPT_SECTIONS = ("新題目", "追蹤")


def validate_citations(text: str, valid_ids: set[str]) -> tuple[str, list[str], list[str]]:
    """把不存在的來源編號標記出來。回傳 (修正後文字, 有效引用編號依出現順序, 無效編號)。"""
    cited: list[str] = []
    invalid: list[str] = []

    def repl(m: re.Match) -> str:
        ids = SID.findall(m.group(1))
        good = [i for i in ids if i in valid_ids]
        bad = [i for i in ids if i not in valid_ids]
        for i in good:
            if i not in cited:
                cited.append(i)
        invalid.extend(bad)
        out = f"[{', '.join(good)}]" if good else ""
        if bad:
            out += "[⚠️來源編號不存在]"
        return out

    return CITE_GROUP.sub(repl, text), cited, invalid


def uncited_claims(text: str) -> list[str]:
    """找出應有來源卻沒有引用的條列項目或表格列。"""
    separator = re.compile(r"^\|[\s:|-]+\|$")
    lines = [line.strip() for line in text.splitlines()]
    missing, section = [], ""
    for idx, s in enumerate(lines):
        if s.startswith("## "):
            section = s
            continue
        if any(k in section for k in EXEMPT_SECTIONS):
            continue
        is_bullet = re.match(r"^([-*]|\d+[.)、])\s+\S", s)
        is_header = idx + 1 < len(lines) and separator.match(lines[idx + 1])
        is_row = s.startswith("|") and not separator.match(s) and not is_header
        if (is_bullet or is_row) and not CITE_GROUP.search(s) and "背景知識" not in s and len(s) > 25:
            missing.append(s)
    return missing


def _link(it: dict) -> str:
    title = it["title"].replace("[", "［").replace("]", "］")
    return f"[{title}]({it['url']})"


def reference_line(it: dict) -> str:
    extra = ""
    inst = (it.get("meta") or {}).get("institutions")
    if inst:
        extra = f"｜{'; '.join(inst[:3])}"
    return (f"- **[{it['sid']}]** {_link(it)} — {it['source']}，{it.get('published') or '日期不明'}"
            f"（{KIND_LABEL.get(it['kind'], it['kind'])}{extra}）")


def stats_section(stats: dict) -> str:
    def pairs(rows):
        return "、".join(f"{k} ({v})" for k, v in rows) or "—"
    kinds = "、".join(f"{KIND_LABEL.get(k, k)} {v}" for k, v in stats["by_kind"].items())
    return "\n".join([
        "## 本週資料概況（程式統計）", "",
        f"- 納入分析的資料：{stats['total']} 筆（{kinds}）",
        f"- 命中最多的關鍵字：{pairs(stats['top_queries'][:10])}",
        f"- 論文作者國家：{pairs(stats['paper_countries'][:10])}",
        f"- 論文主要機構：{pairs(stats['paper_institutions'][:8])}",
        f"- 主要媒體：{pairs(stats['top_media'][:8])}",
    ])


def status_section(status: list[dict]) -> str:
    failed = [s for s in status if not s["ok"]]
    ok = sum(1 for s in status if s["ok"])
    lines = [f"- 成功 {ok} / {len(status)} 個查詢"]
    for s in failed:
        lines.append(f"- ❌ {s['source']}：{s.get('error', '')}")
    return "\n".join(lines)


def appendix(items: list[dict]) -> str:
    groups = defaultdict(list)
    for it in items:
        groups[it["kind"]].append(it)
    out = ["## 附錄：本週收集的全部資料", ""]
    for kind in ("industry", "news", "paper"):
        if not groups.get(kind):
            continue
        out += [f"<details><summary>{KIND_LABEL[kind]}（{len(groups[kind])} 筆）</summary>", ""]
        out += [reference_line(it) for it in groups[kind]]
        out += ["", "</details>", ""]
    return "\n".join(out)


def assemble(week: str, date_range: str, analysis: str | None, items: list[dict], stats: dict,
             status: list[dict], info: dict | None, note: str | None = None) -> tuple[str, dict]:
    by_id = {it["sid"]: it for it in items}
    qa = {"cited": 0, "invalid": [], "uncited": []}
    out = [f"# 生質能國內外新知週報 {week}", "", f"> 資料期間：{date_range}　｜　產生方式："
           + (f"自動收集 + {info['model']} 分析" if info else "自動收集（未進行 AI 分析）"), ""]
    if note:
        out += [f"> ⚠️ {note}", ""]

    if analysis:
        analysis, cited, invalid = validate_citations(analysis, set(by_id))
        qa.update(cited=len(cited), invalid=invalid, uncited=uncited_claims(analysis))
        out += [analysis, "", stats_section(stats), "", "## 參考來源（本週報告引用）", ""]
        out += [reference_line(by_id[i]) for i in sorted(cited, key=lambda s: int(s[1:]))]
    else:
        out += [stats_section(stats)]

    out += ["", "## 品質檢查", ""]
    if analysis:
        out.append(f"- 引用來源數：{qa['cited']} / {len(items)}")
        out.append(f"- 不存在的來源編號：{len(qa['invalid'])}" + (f"（{', '.join(sorted(set(qa['invalid'])))}，已在內文標示⚠️）" if qa["invalid"] else ""))
        out.append(f"- 事實章節中未附來源的條列：{len(qa['uncited'])}")
        for line in qa["uncited"][:10]:
            out.append(f"  - {line[:120]}")
    out.append(status_section(status))
    if info:
        out.append(f"- 模型：{info['model']}；tokens 輸入 {info['input_tokens']:,}／輸出 {info['output_tokens']:,}")
    out += ["", appendix(items)]
    return "\n".join(out).rstrip() + "\n", qa
