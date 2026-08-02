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

from artifact_validator import (
    declares_sqk_core_contract,
    validate_artifact,
    validate_handoff_envelope,
)

from run_store.errors import RunStoreError

ARTIFACT_TYPE = "run_record"
SCHEMA_VERSION = "0.3.0"
ARTIFACTS_FIELD = "artifacts"
INITIAL_STATUS = "draft"
# Phase 1のLLM出力は「候補生成 + 人間レビュー必須」から始める(phase-1計画 §7)。
# producerが真実として供給できる値なので必須fieldにできる(confidenceとの違い)。
INITIAL_REQUIRES_HUMAN_REVIEW = True


def build_run_record(
    envelope: Mapping[str, Any],
    *,
    run_id: str,
    trace_id: str,
    agent: str,
    model: str,
    source_refs: Sequence[str],
    created_at: datetime,
    sqk_core_commit: str | None = None,
) -> dict[str, Any]:
    """Wrap a handoff envelope into a validated RunRecord payload.

    Both contracts are checked: the envelope against the schemas its `schema_ref`s
    name, and the wrapper against `schemas/run-record.schema.json`. A run whose
    envelope does not satisfy the contract it declares must not become an audit record.

    `sqk_core_commit` is conditional (ADR-0010 Decision 3): required when the envelope
    declares any sqk-core contract, rejected when it declares none. "Optional" would
    let an unrelated SHA sit on a veridia-native run with nothing to catch it.

    Raises:
        ArtifactValidationError: the envelope or the resulting RunRecord is invalid.
        SqkSchemaError: a `schema_ref` declared by the envelope is unavailable.
        RunStoreError: `sqk_core_commit` does not match what the envelope declares.
        ValueError: `created_at` is naive (the audit contract requires a timezone).
    """
    validate_handoff_envelope(envelope)
    _check_sqk_core_commit(envelope, sqk_core_commit)

    record: dict[str, Any] = {
        "artifact_type": ARTIFACT_TYPE,
        "version": SCHEMA_VERSION,
        "run_id": run_id,
        "trace_id": trace_id,
        "created_at": _format_utc(created_at),
        "created_by": {"agent": agent, "model": model},
        "source_refs": list(source_refs),
        "status": INITIAL_STATUS,
        "requires_human_review": INITIAL_REQUIRES_HUMAN_REVIEW,
        "envelope": dict(envelope),
    }
    if sqk_core_commit is not None:
        record["sqk_core"] = {"commit": sqk_core_commit}
    validate_artifact(record)
    return record


def _check_sqk_core_commit(envelope: Mapping[str, Any], sqk_core_commit: str | None) -> None:
    """Require the sqk-core pin exactly when the envelope declares a sqk-core contract."""
    declares_sqk_core = declares_sqk_core_contract(envelope.get(ARTIFACTS_FIELD))
    if declares_sqk_core and sqk_core_commit is None:
        raise RunStoreError(
            "sqk_core_commit is required: the envelope declares a sqk-core contract, and "
            "a record that does not pin the contract SHA cannot be interpreted later "
            "(ADR-0006)"
        )
    if not declares_sqk_core and sqk_core_commit is not None:
        raise RunStoreError(
            "sqk_core_commit must not be set: the envelope declares no sqk-core contract, "
            "so the pin would describe a contract this run never used (ADR-0010)"
        )


def _format_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("created_at must be timezone-aware (RFC 3339 with offset)")
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
