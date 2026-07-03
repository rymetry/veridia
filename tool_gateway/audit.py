"""Audit-log wrapper for Tool Gateway executions."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from itertools import count
from typing import Any

from trace_ids import IdFactory, TraceContext
from trace_store import TOOL_CALL_EVENT, TraceStore

from tool_gateway.gateway import ToolGateway
from tool_gateway.redaction import redact_tool_args, sensitive_values

SUCCESS_STATUS = "success"
ERROR_STATUS = "error"
SUMMARY_MAX_CHARS = 240


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class AuditedToolGateway:
    """Wrap `ToolGateway.execute` and persist redacted tool-call audit records."""

    gateway: ToolGateway
    trace_store: TraceStore
    parent_context: TraceContext
    id_factory: IdFactory = field(default_factory=IdFactory)
    clock: Callable[[], datetime] = _utc_now
    _sequence: Iterator[int] = field(default_factory=lambda: count(1), repr=False, compare=False)

    def execute(self, tool_name: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """Run one tool call and save a Trace Store audit record."""
        context = self.id_factory.new_child_context(self.parent_context)
        sequence = next(self._sequence)
        started_at = _format_utc(self.clock())
        start_ns = time.perf_counter_ns()
        redacted_args = redact_tool_args(payload)

        try:
            result = self.gateway.execute(tool_name, payload)
        except Exception as exc:
            ended_at = _format_utc(self.clock())
            self.trace_store.save_record(
                context,
                sequence=sequence,
                event_type=TOOL_CALL_EVENT,
                name=tool_name,
                status=ERROR_STATUS,
                started_at=started_at,
                ended_at=ended_at,
                latency_ms=_latency_ms(start_ns),
                redacted_args=redacted_args,
                error_summary=_summarize_error(exc, payload),
            )
            raise

        ended_at = _format_utc(self.clock())
        self.trace_store.save_record(
            context,
            sequence=sequence,
            event_type=TOOL_CALL_EVENT,
            name=tool_name,
            status=SUCCESS_STATUS,
            started_at=started_at,
            ended_at=ended_at,
            latency_ms=_latency_ms(start_ns),
            redacted_args=redacted_args,
            result_summary=_summarize_result(result),
        )
        return result


def _latency_ms(start_ns: int) -> int:
    return max(0, round((time.perf_counter_ns() - start_ns) / 1_000_000))


def _format_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("audit clock must return a timezone-aware datetime")
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _summarize_result(result: Mapping[str, Any]) -> str:
    keys = ", ".join(sorted(str(key) for key in result))
    return _truncate(f"object keys=[{keys}] field_count={len(result)}")


def _summarize_error(exc: Exception, payload: Mapping[str, Any]) -> str:
    message = str(exc)
    for value in sensitive_values(payload):
        message = message.replace(value, "<redacted>")
    return _truncate(f"{exc.__class__.__name__}: {message}")


def _truncate(value: str) -> str:
    if len(value) <= SUMMARY_MAX_CHARS:
        return value
    return f"{value[: SUMMARY_MAX_CHARS - 3]}..."
