"""_index再生成のオーケストレーション。

タスクディレクトリを読み、全 T-*.md をパースし、task_id昇順で _index.md を組む。
--check で既存との一致だけ検証し、書き込まない(CI用)。
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from .epic_labels import EpicConfigError, load_epic_labels
from .frontmatter import parse_task_file
from .models import TaskEntry, TaskParseError
from .render import render_index

_INDEX_FILENAME = "_index.md"
# 集計対象のタスクファイル名パターン。_index.md や _template.md は除外する。
_TASK_FILE_RE = re.compile(r"^T-\d{3,}-.*\.md$")


def _collect_task_files(tasks_dir: Path) -> list[Path]:
    """タスクディレクトリから T-*.md を集める(名前順で決定的に)。"""
    if not tasks_dir.is_dir():
        raise FileNotFoundError(f"タスクディレクトリが存在しない: {tasks_dir}")
    return sorted(p for p in tasks_dir.iterdir() if _TASK_FILE_RE.match(p.name))


def build_entries(tasks_dir: Path) -> tuple[TaskEntry, ...]:
    """タスクディレクトリ内の全タスクを TaskEntry にして task_id昇順で返す。

    Raises:
        FileNotFoundError: ディレクトリ欠落・タスク0件。
        TaskParseError: いずれかのファイルがパース不能。
    """
    files = _collect_task_files(tasks_dir)
    if not files:
        raise FileNotFoundError(f"タスクファイル(T-*.md)が1件も無い: {tasks_dir}")
    entries = [
        parse_task_file(str(path.name), path.name, path.read_text(encoding="utf-8"))
        for path in files
    ]
    return tuple(sorted(entries, key=lambda e: e.task_id))


def generate_index_text(tasks_dir: Path, generated_on: str) -> str:
    """タスクディレクトリから _index.md の全文を組み立てる。"""
    entries = build_entries(tasks_dir)
    epic_labels = load_epic_labels()
    return render_index(entries, epic_labels, generated_on)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="regen_task_index",
        description="docs/tasks/<phase>/_index.md をタスクfrontmatterから再生成する",
    )
    parser.add_argument(
        "tasks_dir",
        type=Path,
        help="タスクディレクトリ(例: docs/tasks/phase-0)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="書き込まず、既存 _index.md と一致するか検証する(不一致で終了コード1)",
    )
    parser.add_argument(
        "--generated-on",
        default=date.today().isoformat(),
        help="生成日(YYYY-MM-DD)。既定は実行日。",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLIエントリ。終了コード: 0成功 / 1不一致 / 2エラー。"""
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        rendered = generate_index_text(args.tasks_dir, args.generated_on)
    except (FileNotFoundError, TaskParseError, EpicConfigError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    index_path = args.tasks_dir / _INDEX_FILENAME
    if args.check:
        current = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
        if current == rendered:
            print(f"ok: {index_path} は最新")
            return 0
        print(f"drift: {index_path} が再生成結果と不一致(再生成が必要)", file=sys.stderr)
        return 1

    index_path.write_text(rendered, encoding="utf-8")
    print(f"wrote: {index_path}")
    return 0
