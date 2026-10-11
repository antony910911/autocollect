"""週報主題：每個主題有自己的設定檔、分析指示、資料夾、報告資料夾與 Folio 筆記本。

主題列在 config/topics.yaml。沒有這個檔案時只有預設的「生質能」主題。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_TOPIC = "bioenergy"

BUILTIN = {
    "bioenergy": {
        "title": "生質能國內外新知週報",
        "config": "config/sources.yaml",
        "prompt": "prompts/weekly_analysis.md",
        "data_dir": "data",
        "reports_dir": "reports",
        "folio": {
            "notebook_id": "nb_autocollect_bio",
            "notebook_name": "生質能週報",
            "section_id": "sc_autocollect_weekly",
            "section_name": "每週週報",
            "page_prefix": "pg_autocollect_",
            "item_prefix": "t_autocollect_",
        },
    },
}


@dataclass
class Topic:
    name: str
    root: Path
    title: str
    config: str
    prompt: str
    data_dir: str
    reports_dir: str
    folio: dict = field(default_factory=dict)

    @property
    def data(self) -> Path:
        return self.root / self.data_dir

    @property
    def reports(self) -> Path:
        return self.root / self.reports_dir

    def raw_path(self, week: str) -> Path:
        return self.data / "raw" / f"{week}.json"

    def pack_path(self, week: str) -> Path:
        return self.data / "packs" / f"{week}.md"

    def analysis_path(self, week: str) -> Path:
        return self.data / "analysis" / f"{week}.md"

    def load_config(self) -> dict:
        return yaml.safe_load((self.root / self.config).read_text("utf-8"))


def all_topics(root: Path) -> dict[str, dict]:
    registry = dict(BUILTIN)
    path = root / "config" / "topics.yaml"
    if path.exists():
        registry.update((yaml.safe_load(path.read_text("utf-8")) or {}).get("topics", {}))
    return registry


def get_topic(root: Path, name: str = DEFAULT_TOPIC) -> Topic:
    registry = all_topics(root)
    if name not in registry:
        raise SystemExit(f"沒有這個主題：{name}（可用：{', '.join(registry)}）")
    return Topic(name=name, root=root, **registry[name])
