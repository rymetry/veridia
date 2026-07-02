"""T-012 trace/run/span ID generation contract tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tests.test_artifact_base_schema import make_valid_artifact

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "artifact-base.schema.json"
FIXED_NOW = datetime(2026, 7, 3, 12, 34, 56, 789012, tzinfo=UTC)


class CountingTokenHex:
    """Deterministic `secrets.token_hex` replacement for ID generation tests."""

    def __init__(self) -> None:
        self._counter = 0

    def __call__(self, nbytes: int) -> str:
        self._counter += 1
        return f"{self._counter:0{nbytes * 2}x}"[-nbytes * 2 :]


def test_generated_ids_match_documented_formats() -> None:
    from trace_ids import RUN_ID_RE, SPAN_ID_RE, TRACE_ID_RE, IdFactory

    factory = IdFactory(clock=lambda: FIXED_NOW, token_hex=CountingTokenHex())

    assert RUN_ID_RE.fullmatch(factory.new_run_id())
    assert TRACE_ID_RE.fullmatch(factory.new_trace_id())
    assert SPAN_ID_RE.fullmatch(factory.new_span_id())


def test_generated_ids_are_unique_across_many_calls() -> None:
    from trace_ids import IdFactory

    factory = IdFactory(clock=lambda: FIXED_NOW, token_hex=CountingTokenHex())

    run_ids = {factory.new_run_id() for _ in range(1_000)}
    trace_ids = {factory.new_trace_id() for _ in range(1_000)}
    span_ids = {factory.new_span_id() for _ in range(1_000)}

    assert len(run_ids) == 1_000
    assert len(trace_ids) == 1_000
    assert len(span_ids) == 1_000


def test_generated_trace_id_passes_artifact_base_schema_validation() -> None:
    from trace_ids import IdFactory

    factory = IdFactory(clock=lambda: FIXED_NOW, token_hex=CountingTokenHex())
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    validator.validate({**make_valid_artifact(), "trace_id": factory.new_trace_id()})


def test_trace_context_propagates_run_trace_and_parent_span() -> None:
    from trace_ids import IdFactory

    factory = IdFactory(clock=lambda: FIXED_NOW, token_hex=CountingTokenHex())

    root = factory.new_trace_context()
    child = factory.new_child_context(root)

    assert child.run_id == root.run_id
    assert child.trace_id == root.trace_id
    assert child.parent_span_id == root.span_id
    assert child.span_id != root.span_id
    assert root.artifact_fields() == {"trace_id": root.trace_id}
    assert child.trace_record_fields() == {
        "run_id": root.run_id,
        "trace_id": root.trace_id,
        "span_id": child.span_id,
        "parent_span_id": root.span_id,
    }


def test_clock_must_return_timezone_aware_datetime() -> None:
    from trace_ids import IdFactory

    factory = IdFactory(
        clock=lambda: datetime(2026, 7, 3, 12, 34, 56),
        token_hex=CountingTokenHex(),
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        factory.new_run_id()
