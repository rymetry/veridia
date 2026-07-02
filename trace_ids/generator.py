"""ID factory for run_id, trace_id, and OpenTelemetry-style span IDs."""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

RUN_RANDOM_BYTES = 6
TRACE_RANDOM_BYTES = 8
SPAN_RANDOM_BYTES = 8

RUN_ID_PATTERN = r"^run-\d{8}T\d{6}\d{6}Z-[0-9a-f]{12}$"
TRACE_ID_PATTERN = r"^trace-\d{8}-[0-9a-f]{16}$"
SPAN_ID_PATTERN = r"^[0-9a-f]{16}$"

RUN_ID_RE = re.compile(RUN_ID_PATTERN)
TRACE_ID_RE = re.compile(TRACE_ID_PATTERN)
SPAN_ID_RE = re.compile(SPAN_ID_PATTERN)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _token_hex(nbytes: int) -> str:
    return secrets.token_hex(nbytes)


@dataclass(frozen=True)
class TraceContext:
    """Propagation context shared by trace store records and generated artifacts."""

    run_id: str
    trace_id: str
    span_id: str
    parent_span_id: str | None = None

    def __post_init__(self) -> None:
        _require_match(RUN_ID_RE, self.run_id, "run_id")
        _require_match(TRACE_ID_RE, self.trace_id, "trace_id")
        _require_match(SPAN_ID_RE, self.span_id, "span_id")
        if self.parent_span_id is not None:
            _require_match(SPAN_ID_RE, self.parent_span_id, "parent_span_id")

    def artifact_fields(self) -> dict[str, str]:
        """Return the ArtifactBase fields propagated from this context."""
        return {"trace_id": self.trace_id}

    def trace_record_fields(self) -> dict[str, str | None]:
        """Return the Trace Store identity fields propagated from this context."""
        return {
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
        }


@dataclass(frozen=True)
class IdFactory:
    """Generate sortable run/trace IDs and OpenTelemetry-style span IDs."""

    clock: Callable[[], datetime] = _utc_now
    token_hex: Callable[[int], str] = _token_hex

    def new_run_id(self) -> str:
        now = _aware_utc(self.clock())
        return f"run-{now:%Y%m%dT%H%M%S%fZ}-{self._hex(RUN_RANDOM_BYTES)}"

    def new_trace_id(self) -> str:
        now = _aware_utc(self.clock())
        return f"trace-{now:%Y%m%d}-{self._hex(TRACE_RANDOM_BYTES)}"

    def new_span_id(self) -> str:
        return self._hex(SPAN_RANDOM_BYTES)

    def new_trace_context(self) -> TraceContext:
        return TraceContext(
            run_id=self.new_run_id(),
            trace_id=self.new_trace_id(),
            span_id=self.new_span_id(),
        )

    def new_child_context(self, parent: TraceContext) -> TraceContext:
        return TraceContext(
            run_id=parent.run_id,
            trace_id=parent.trace_id,
            span_id=self.new_span_id(),
            parent_span_id=parent.span_id,
        )

    def _hex(self, nbytes: int) -> str:
        value = self.token_hex(nbytes).lower()
        expected_len = nbytes * 2
        if not re.fullmatch(rf"[0-9a-f]{{{expected_len}}}", value):
            raise ValueError(
                f"token_hex({nbytes}) must return {expected_len} lowercase hex characters"
            )
        return value


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("ID factory clock must return a timezone-aware datetime")
    return value.astimezone(UTC)


def _require_match(pattern: re.Pattern[str], value: str, field_name: str) -> None:
    if not pattern.fullmatch(value):
        raise ValueError(f"invalid {field_name}: {value!r}")
