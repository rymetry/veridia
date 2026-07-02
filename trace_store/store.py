"""High-level Trace Store API for redacted trace records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trace_ids import TraceContext

from trace_store.records import TraceRecord
from trace_store.repository import SqliteTraceRecordRepository

DEFAULT_ROOT = Path(".veridia/store/trace")
TraceIdentity = TraceContext | Mapping[str, str | None]


@dataclass(frozen=True)
class TraceStore:
    """Save and query redacted Phase 0 trace records."""

    record_repository: SqliteTraceRecordRepository

    @classmethod
    def open(cls, root: str | Path = DEFAULT_ROOT) -> TraceStore:
        return cls(record_repository=SqliteTraceRecordRepository.under_root(Path(root)))

    def save_record(
        self,
        context: TraceIdentity,
        *,
        sequence: int,
        event_type: str,
        name: str,
        status: str,
        started_at: str,
        ended_at: str | None = None,
        latency_ms: int | None = None,
        redacted_args: Mapping[str, Any] | None = None,
        result_summary: str | None = None,
        error_summary: str | None = None,
    ) -> TraceRecord:
        """Save one redacted trace record and return the persisted record."""
        identity = _identity_fields(context)
        record = TraceRecord(
            run_id=_required_str(identity, "run_id"),
            trace_id=_required_str(identity, "trace_id"),
            span_id=_required_str(identity, "span_id"),
            parent_span_id=_optional_str(identity, "parent_span_id"),
            sequence=sequence,
            event_type=event_type,
            name=name,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            latency_ms=latency_ms,
            redacted_args=redacted_args or {},
            result_summary=result_summary,
            error_summary=error_summary,
        )
        self.record_repository.save(record)
        return record

    def find_by_trace_id(self, trace_id: str) -> tuple[TraceRecord, ...]:
        return self.record_repository.find_by_trace_id(trace_id)

    def find_by_run_id(self, run_id: str) -> tuple[TraceRecord, ...]:
        return self.record_repository.find_by_run_id(run_id)


def _identity_fields(context: TraceIdentity) -> Mapping[str, str | None]:
    if isinstance(context, TraceContext):
        return context.trace_record_fields()
    return context


def _required_str(fields: Mapping[str, str | None], field_name: str) -> str:
    value = fields[field_name]
    if not isinstance(value, str) or not value:
        raise TypeError(f"{field_name} must be a non-empty string")
    return value


def _optional_str(fields: Mapping[str, str | None], field_name: str) -> str | None:
    value = fields.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise TypeError(f"{field_name} must be a non-empty string or None")
    return value
