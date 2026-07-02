"""T-014 Trace Store integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from trace_ids import TraceContext


def make_trace_context(*, span_id: str, parent_span_id: str | None = None) -> TraceContext:
    return TraceContext(
        run_id="run-20260703T123456789012Z-000000000001",
        trace_id="trace-20260703-00000000000000a2",
        span_id=span_id,
        parent_span_id=parent_span_id,
    )


def test_save_tool_call_and_error_records_then_query_in_chronological_order(
    tmp_path: Path,
) -> None:
    from trace_store import TraceStore

    root = make_trace_context(span_id="00000000000000a3")
    child = make_trace_context(
        span_id="00000000000000a4",
        parent_span_id=root.span_id,
    )
    store = TraceStore.open(tmp_path / "trace")

    saved_error = store.save_record(
        child,
        sequence=2,
        event_type="error",
        name="tool.orders.cancel",
        status="error",
        started_at="2026-07-03T12:34:57Z",
        ended_at="2026-07-03T12:34:57Z",
        latency_ms=40,
        redacted_args={"order_id": "<redacted>"},
        error_summary="tool rejected the request with validation_error",
    )
    saved_tool_call = store.save_record(
        root,
        sequence=1,
        event_type="tool_call",
        name="tool.orders.cancel",
        status="ok",
        started_at="2026-07-03T12:34:56Z",
        ended_at="2026-07-03T12:34:56Z",
        latency_ms=25,
        redacted_args={"order_id": "<redacted>"},
        result_summary="cancelled one synthetic order fixture",
    )

    by_trace_id = store.find_by_trace_id(root.trace_id)
    by_run_id = store.find_by_run_id(root.run_id)

    assert saved_error.event_type == "error"
    assert saved_tool_call.event_type == "tool_call"
    assert tuple(record.sequence for record in by_trace_id) == (1, 2)
    assert tuple(record.sequence for record in by_run_id) == (1, 2)
    assert tuple(record.span_id for record in by_trace_id) == (root.span_id, child.span_id)
    assert by_trace_id[1].parent_span_id == root.span_id
    assert by_trace_id[0].redacted_args == {"order_id": "<redacted>"}
    assert by_trace_id[0].result_summary == "cancelled one synthetic order fixture"
    assert by_trace_id[1].error_summary == "tool rejected the request with validation_error"
    assert (tmp_path / "trace" / "trace.sqlite3").exists()
    assert not (tmp_path / "trace" / "evidence.sqlite3").exists()


def test_rejects_event_types_outside_phase_0_subset(tmp_path: Path) -> None:
    from trace_store import InvalidTraceEventTypeError, TraceStore

    context = make_trace_context(span_id="00000000000000a3")
    store = TraceStore.open(tmp_path / "trace")

    with pytest.raises(InvalidTraceEventTypeError, match="handoff"):
        store.save_record(
            context,
            sequence=1,
            event_type="handoff",
            name="agent-router",
            status="ok",
            started_at="2026-07-03T12:34:56Z",
            redacted_args={},
            result_summary="handoff skipped in Phase 0",
        )

    assert store.find_by_trace_id(context.trace_id) == ()
