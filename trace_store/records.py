"""Trace Store record types and validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from trace_store.errors import InvalidTraceEventTypeError, TraceStoreError

TOOL_CALL_EVENT = "tool_call"
ERROR_EVENT = "error"
RUN_METRICS_EVENT = "run_metrics"
ALLOWED_EVENT_TYPES = frozenset({TOOL_CALL_EVENT, ERROR_EVENT, RUN_METRICS_EVENT})


@dataclass(frozen=True)
class TraceRecord:
    """Redacted trace record saved by the Phase 0 Trace Store."""

    run_id: str
    trace_id: str
    span_id: str
    parent_span_id: str | None
    sequence: int
    event_type: str
    name: str
    status: str
    started_at: str
    ended_at: str | None
    latency_ms: int | None
    redacted_args: Mapping[str, Any]
    result_summary: str | None
    error_summary: str | None

    def __post_init__(self) -> None:
        _require_non_empty_str(self.run_id, "run_id")
        _require_non_empty_str(self.trace_id, "trace_id")
        _require_non_empty_str(self.span_id, "span_id")
        if self.parent_span_id is not None:
            _require_non_empty_str(self.parent_span_id, "parent_span_id")
        if self.sequence < 0:
            raise TraceStoreError("sequence must be greater than or equal to 0")
        if self.event_type not in ALLOWED_EVENT_TYPES:
            raise InvalidTraceEventTypeError(
                f"unsupported trace event_type for Phase 0: {self.event_type!r}"
            )
        _require_non_empty_str(self.name, "name")
        _require_non_empty_str(self.status, "status")
        _require_non_empty_str(self.started_at, "started_at")
        if self.ended_at is not None:
            _require_non_empty_str(self.ended_at, "ended_at")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise TraceStoreError("latency_ms must be greater than or equal to 0")


def _require_non_empty_str(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise TraceStoreError(f"{field_name} must be a non-empty string")
