"""Build RunRecord payloads that wrap a sqk-core handoff envelope.

A RunRecord is the veridia audit wrapper around one sqk-core skill run (ADR-0007).
The envelope is stored verbatim; veridia adds only what the envelope cannot carry:
when the run happened, who ran it, what it ran against, and which sqk-core commit
defines the contracts the envelope claims to satisfy.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from artifact_validator import validate_artifact, validate_handoff_envelope

ARTIFACT_TYPE = "run_record"
SCHEMA_VERSION = "0.1.0"
INITIAL_STATUS = "draft"


def build_run_record(
    envelope: Mapping[str, Any],
    *,
    run_id: str,
    trace_id: str,
    agent: str,
    model: str,
    source_refs: Sequence[str],
    sqk_core_commit: str,
    created_at: datetime,
) -> dict[str, Any]:
    """Wrap a sqk-core handoff envelope into a validated RunRecord payload.

    Both contracts are checked: the envelope against sqk-core's schemas, and the
    wrapper against `schemas/run-record.schema.json`. A run whose envelope does not
    satisfy the contract it declares must not become an audit record.

    Raises:
        ArtifactValidationError: the envelope or the resulting RunRecord is invalid.
        SqkSchemaError: a `schema_ref` declared by the envelope is unavailable.
        ValueError: `created_at` is naive (the audit contract requires a timezone).
    """
    validate_handoff_envelope(envelope)

    record = {
        "artifact_type": ARTIFACT_TYPE,
        "version": SCHEMA_VERSION,
        "run_id": run_id,
        "trace_id": trace_id,
        "created_at": _format_utc(created_at),
        "created_by": {"agent": agent, "model": model},
        "source_refs": list(source_refs),
        "sqk_core": {"commit": sqk_core_commit},
        "status": INITIAL_STATUS,
        "envelope": dict(envelope),
    }
    validate_artifact(record)
    return record


def _format_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("created_at must be timezone-aware (RFC 3339 with offset)")
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
