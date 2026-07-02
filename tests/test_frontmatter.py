"""frontmatterパースの単体テスト。正常系と、黙殺してはいけない異常系を検証する。"""

from __future__ import annotations

import pytest

from task_index.frontmatter import parse_task_file
from task_index.models import TaskParseError

_VALID = """\
---
task_id: T-042
epic: artifact-schema
plan_ref: phase-0-foundation.md#2
status: not_started
owner:
blocked_by: [T-001, T-002]
---

# T-042: サンプルタスク(かっこ付き)

## 目的
"""


def test_parses_valid_task() -> None:
    entry = parse_task_file("T-042.md", "T-042-sample.md", _VALID)
    assert entry.task_id == "T-042"
    assert entry.epic == "artifact-schema"
    assert entry.status == "not_started"
    assert entry.blocked_by == ("T-001", "T-002")
    assert entry.title == "サンプルタスク(かっこ付き)"
    assert entry.filename == "T-042-sample.md"


def test_empty_blocked_by_becomes_empty_tuple() -> None:
    text = _VALID.replace("blocked_by: [T-001, T-002]", "blocked_by:")
    entry = parse_task_file("T-042.md", "T-042-sample.md", text)
    assert entry.blocked_by == ()


def test_missing_fence_raises() -> None:
    with pytest.raises(TaskParseError, match="fence"):
        parse_task_file("bad.md", "bad.md", "no frontmatter here\n# T-001: x")


def test_missing_required_key_raises() -> None:
    text = _VALID.replace("status: not_started\n", "")
    with pytest.raises(TaskParseError, match="status"):
        parse_task_file("T-042.md", "T-042.md", text)


def test_invalid_status_raises() -> None:
    text = _VALID.replace("status: not_started", "status: wip")
    with pytest.raises(TaskParseError, match="不正なstatus"):
        parse_task_file("T-042.md", "T-042.md", text)


def test_missing_h1_raises() -> None:
    text = _VALID.replace("# T-042: サンプルタスク(かっこ付き)", "本文だけ")
    with pytest.raises(TaskParseError, match="H1"):
        parse_task_file("T-042.md", "T-042.md", text)


def test_h1_task_id_mismatch_raises() -> None:
    text = _VALID.replace("# T-042:", "# T-999:")
    with pytest.raises(TaskParseError, match="不一致"):
        parse_task_file("T-042.md", "T-042.md", text)
