"""レンダラの単体テスト。status内訳の一般化とepic未定義の検出を重点確認する。"""

from __future__ import annotations

import pytest

import task_index.render as render
from task_index.epic_labels import EpicLabel
from task_index.models import TaskEntry
from task_index.render import render_index

_LABELS = (
    EpicLabel(epic_id="artifact-schema", label="artifact-schema(WS-A)"),
    EpicLabel(epic_id="sandbox", label="sandbox(WS-D)"),
)


def _entry(task_id: str, status: str, epic: str = "artifact-schema") -> TaskEntry:
    return TaskEntry(
        task_id=task_id,
        epic=epic,
        status=status,
        blocked_by=(),
        title=f"タイトル{task_id}",
        filename=f"{task_id}-x.md",
    )


def test_status_summary_only_lists_nonzero_in_canonical_order() -> None:
    entries = (
        _entry("T-001", "done"),
        _entry("T-002", "not_started"),
        _entry("T-003", "not_started"),
    )
    text = render_index(entries, _LABELS, "2026-07-02")
    # 正準順は not_started が先、done が後。in_progress/blockedは0件なので出ない。
    assert "全3タスク(not_started: 2 / done: 1)" in text


def test_output_ends_with_single_newline() -> None:
    text = render_index((_entry("T-001", "done"),), _LABELS, "2026-07-02")
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_blocked_by_rendered_as_dash_when_empty() -> None:
    text = render_index((_entry("T-001", "done"),), _LABELS, "2026-07-02")
    assert "| done | - |" in text


def test_unknown_epic_raises() -> None:
    entries = (_entry("T-001", "done", epic="mystery-epic"),)
    with pytest.raises(ValueError, match="定義の無いepic"):
        render_index(entries, _LABELS, "2026-07-02")


@pytest.mark.parametrize(
    ("directory_name", "expected"),
    [
        ("phase-0", "Phase 0"),
        ("phase-1-crud-mvp", "Phase 1 CRUD MVP"),
    ],
)
def test_phase_title_is_derived_from_task_directory_name(
    directory_name: str,
    expected: str,
) -> None:
    assert hasattr(render, "phase_title")
    assert render.phase_title(directory_name) == expected


def test_phase_zero_default_title_preserves_existing_output() -> None:
    text = render_index((_entry("T-001", "done"),), _LABELS, "2026-07-02")
    assert text.startswith("# Phase 0 タスク一覧(集約ビュー)\n")
