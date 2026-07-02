"""epic ID → 表示ラベルのマッピングをTOML設定から読む。

設定の実体は epic_labels.toml。source of truth は計画§3(AGENTS.md変更ルール3)。
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_CONFIG = Path(__file__).with_name("epic_labels.toml")


class EpicConfigError(ValueError):
    """epic設定の読み込み・整合性エラー。"""


@dataclass(frozen=True)
class EpicLabel:
    """1 epicの表示定義。順序は list 内の位置で表す(immutable)。"""

    epic_id: str
    label: str


def load_epic_labels(config_path: Path | None = None) -> tuple[EpicLabel, ...]:
    """TOMLからepic表示定義を順序付きで読む。

    Raises:
        EpicConfigError: ファイル欠落、必須キー欠落、id重複時。
    """
    path = config_path or _DEFAULT_CONFIG
    if not path.exists():
        raise EpicConfigError(f"epic設定ファイルが存在しない: {path}")

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    entries = data.get("epic")
    if not isinstance(entries, list) or not entries:
        raise EpicConfigError(f"{path}: [[epic]] エントリが1件も無い")

    labels: list[EpicLabel] = []
    seen: set[str] = set()
    for i, entry in enumerate(entries):
        epic_id = entry.get("id")
        label = entry.get("label")
        if not epic_id or not label:
            raise EpicConfigError(f"{path}: epic[{i}] に id または label が無い")
        if epic_id in seen:
            raise EpicConfigError(f"{path}: epic id が重複: {epic_id}")
        seen.add(epic_id)
        labels.append(EpicLabel(epic_id=epic_id, label=label))
    return tuple(labels)
