"""CLIのend-to-endテスト。fixtureディレクトリからの生成と --check の挙動を検証する。"""

from __future__ import annotations

from pathlib import Path

from task_index.cli import generate_index_text, main

_TASK_TMPL = """\
---
task_id: {task_id}
epic: {epic}
plan_ref: phase-0-foundation.md#2
status: {status}
owner:
blocked_by:{blocked}
---

# {task_id}: {title}

## 目的
"""


def _write_task(
    d: Path, task_id: str, epic: str, status: str, title: str, blocked: str = ""
) -> None:
    body = _TASK_TMPL.format(
        task_id=task_id, epic=epic, status=status, title=title, blocked=blocked
    )
    (d / f"{task_id}-{title[:6]}.md").write_text(body, encoding="utf-8")


def _seed(d: Path) -> None:
    _write_task(d, "T-002", "artifact-schema", "not_started", "beta", blocked=" [T-001]")
    _write_task(d, "T-001", "artifact-schema", "done", "alpha")
    _write_task(d, "T-003", "sandbox", "not_started", "gamma")
    # _index.md / _template.md はタスクとして集計しない(除外確認用)。
    (d / "_template.md").write_text("---\ntask_id: T-XXX\n---\n# T-XXX: t\n", encoding="utf-8")


def test_generate_sorts_by_task_id_and_counts_epics(tmp_path: Path) -> None:
    _seed(tmp_path)
    text = generate_index_text(tmp_path, "2026-07-02")
    # task_id昇順(T-001が先)。
    assert text.index("T-001") < text.index("T-002") < text.index("T-003")
    # 内訳: not_started 2 / done 1。
    assert "全3タスク(not_started: 2 / done: 1)" in text
    # epic別内訳。
    assert "| artifact-schema(WS-A) | 2 |" in text
    assert "| sandbox(WS-D) | 1 |" in text


def test_check_mode_detects_match_and_drift(tmp_path: Path) -> None:
    _seed(tmp_path)
    (tmp_path / "_index.md").write_text(
        generate_index_text(tmp_path, "2026-07-02"), encoding="utf-8"
    )
    assert main([str(tmp_path), "--check", "--generated-on", "2026-07-02"]) == 0
    # タスクを1件書き換えるとdrift。
    _write_task(tmp_path, "T-003", "sandbox", "done", "gamma")
    assert main([str(tmp_path), "--check", "--generated-on", "2026-07-02"]) == 1


def test_missing_dir_returns_error_code(tmp_path: Path) -> None:
    assert main([str(tmp_path / "nope"), "--generated-on", "2026-07-02"]) == 2


def test_empty_dir_returns_error_code(tmp_path: Path) -> None:
    # タスクファイルが1件も無い空ディレクトリでも黙って壊れず、コード2で終了する。
    assert main([str(tmp_path), "--generated-on", "2026-07-02"]) == 2
