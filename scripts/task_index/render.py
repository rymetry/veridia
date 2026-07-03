"""TaskEntry の並びから _index.md の全文を組み立てる。

列仕様は docs/tasks/README.md 準拠。出力は現行 _index.md とバイト一致する形。
固定文言は定数化する(coding-style: ハードコード値は定数化)。
"""

from __future__ import annotations

from collections import Counter

from .epic_labels import EpicLabel
from .models import VALID_STATUSES, TaskEntry

# --- 固定文言(_index.md のテンプレート要素) ---
_TITLE_TEMPLATE = "# {phase_title} タスク一覧(集約ビュー)"
_INTRO = (
    "frontmatterから再生成する集約ビュー。**手で編集しない**"
    "(statusの正本は各タスクファイル。`docs/tasks/README.md` 参照)。"
)
_TABLE_HEADER = "| task_id | epic | status | blocked_by | タイトル |"
_TABLE_SEP = "|---|---|---|---|---|"
_EPIC_TABLE_HEADER = "| epic(計画§3) | タスク数 |"
_EPIC_TABLE_SEP = "|---|---:|"
_EPIC_SECTION_HEADING = "## epic別内訳"
_FOOTER = (
    "全タスクdone後もPhase完了とは判定しない"
    "(計画mdの完了条件チェックリストが正、AGENTS.md変更ルール6)。"
)
_EMPTY_BLOCKED = "-"


def phase_title(directory_name: str) -> str:
    """Derive a human-readable phase title from a task directory name."""
    parts = directory_name.split("-")
    if len(parts) >= 2 and parts[0] == "phase" and parts[1].isdigit():
        suffix = " ".join(part.upper() for part in parts[2:])
        title = f"Phase {int(parts[1])}"
        return f"{title} {suffix}" if suffix else title
    return directory_name


def _status_summary(entries: tuple[TaskEntry, ...]) -> str:
    """`not_started: N / done: M` 形式の内訳文字列を作る。

    VALID_STATUSES の正準順で、件数>0のstatusのみを列挙する。
    """
    counts = Counter(entry.status for entry in entries)
    parts = [f"{status}: {counts[status]}" for status in VALID_STATUSES if counts[status] > 0]
    return " / ".join(parts)


def _header_line(entries: tuple[TaskEntry, ...], generated_on: str) -> str:
    """`生成日: <日付> / 全Nタスク(<内訳>)` 行を作る。"""
    return f"生成日: {generated_on} / 全{len(entries)}タスク({_status_summary(entries)})"


def _task_row(entry: TaskEntry) -> str:
    """タスク1件のテーブル行を作る。"""
    blocked = ", ".join(entry.blocked_by) if entry.blocked_by else _EMPTY_BLOCKED
    link = f"[{entry.task_id}]({entry.filename})"
    return f"| {link} | {entry.epic} | {entry.status} | {blocked} | {entry.title} |"


def _epic_breakdown_rows(
    entries: tuple[TaskEntry, ...],
    epic_labels: tuple[EpicLabel, ...],
) -> list[str]:
    """epic別内訳テーブルの行を作る。未知epicは黙殺せずValueError。"""
    counts = Counter(entry.epic for entry in entries)
    known = {label.epic_id for label in epic_labels}
    unknown = set(counts) - known
    if unknown:
        raise ValueError(
            f"epic_labels.toml に定義の無いepicが使われている: {', '.join(sorted(unknown))}"
        )
    return [f"| {label.label} | {counts[label.epic_id]} |" for label in epic_labels]


def render_index(
    entries: tuple[TaskEntry, ...],
    epic_labels: tuple[EpicLabel, ...],
    generated_on: str,
    phase_dir_name: str = "phase-0",
) -> str:
    """_index.md の全文(末尾改行込み)を返す。

    Args:
        entries: task_id昇順で渡す(呼び出し側でソート済みを前提)。
        epic_labels: 表示順を持つepicラベル定義。
        generated_on: `生成日` に出す日付文字列(YYYY-MM-DD)。
    """
    lines: list[str] = [
        _TITLE_TEMPLATE.format(phase_title=phase_title(phase_dir_name)),
        "",
        _INTRO,
        "",
        _header_line(entries, generated_on),
        "",
        _TABLE_HEADER,
        _TABLE_SEP,
    ]
    lines.extend(_task_row(entry) for entry in entries)
    lines.extend(
        [
            "",
            _EPIC_SECTION_HEADING,
            "",
            _EPIC_TABLE_HEADER,
            _EPIC_TABLE_SEP,
        ]
    )
    lines.extend(_epic_breakdown_rows(entries, epic_labels))
    lines.extend(["", _FOOTER])
    # 末尾は改行1つで終える(現行 _index.md と一致)。
    return "\n".join(lines) + "\n"
