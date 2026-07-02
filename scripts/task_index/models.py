"""ドメインモデルと例外定義。

すべてのモデルはfrozen(イミュータブル)。パース失敗は黙殺せず例外で表す
(AGENTS.md実装規約 / coding-style: エラーは黙殺しない)。
"""

from __future__ import annotations

from dataclasses import dataclass

# docs/tasks/README.md で定義されたstatus値。ここが唯一の許容集合。
VALID_STATUSES: tuple[str, ...] = ("not_started", "in_progress", "blocked", "done")

# frontmatterに必須のキー。欠落は TaskParseError にする。
REQUIRED_FRONTMATTER_KEYS: tuple[str, ...] = ("task_id", "epic", "status")


class TaskParseError(ValueError):
    """タスクファイルのパース失敗。どのファイル・何が問題かを必ず含める。"""

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"{path}: {reason}")


@dataclass(frozen=True)
class TaskEntry:
    """1タスクファイルから抽出した_index表示用の値。

    Attributes:
        task_id: frontmatterの task_id(例: T-002)。
        epic: frontmatterの epic ID(計画§3のepic ID)。
        status: docs/tasks/README.md のstatus値のいずれか。
        blocked_by: 依存タスクIDの並び(空可)。
        title: H1見出しから "T-NNN: " プレフィックスを除いた表示タイトル。
        filename: タスクファイルのbasename(_indexのリンク先)。
    """

    task_id: str
    epic: str
    status: str
    blocked_by: tuple[str, ...]
    title: str
    filename: str
