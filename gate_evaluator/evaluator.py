"""Evaluate one stored run against the GatePolicy and produce a GateDecision.

    run record → per-gate results (policy stages) → aggregate → validated GateDecision

The evaluator never mutates the subject and never trusts it. Producing a decision
requires only one thing of the subject: that it says which run it is. Everything else
a gate finds missing is a gate outcome, not an error.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from artifact_validator import validate_artifact

from gate_evaluator.errors import GateBlockedError, GateEvaluationError
from gate_evaluator.policy import GatePolicy
from gate_evaluator.results import (
    DECISION_BLOCK,
    OUTCOME_INCONCLUSIVE,
    GateResult,
    aggregate,
)
from gate_evaluator.rules import GATE_RULES, unimplemented_reason

ARTIFACT_TYPE = "gate_decision"
SCHEMA_VERSION = "0.1.0"
GATE_ID_PREFIX = "GATE-"

RUN_ID_FIELD = "run_id"
ENVELOPE_FIELD = "envelope"
DECLARED_STATUS_FIELD = "gate_status"
DECLARED_STATUS_VALUES = frozenset({"passed", "passed-with-risks", "blocked"})

DECISION_FIELD = "decision"
GATE_ID_FIELD = "gate_id"
BLOCKING_REASONS_FIELD = "blocking_reasons"


@dataclass(frozen=True)
class GateEvaluator:
    """Apply every gate in a GatePolicy to one subject."""

    policy: GatePolicy

    def evaluate(
        self,
        run_record: Mapping[str, Any],
        *,
        created_at: datetime,
        release_candidate: str | None = None,
    ) -> dict[str, Any]:
        """Judge one run and return a validated GateDecision payload.

        Raises:
            GateEvaluationError: the subject does not identify the run it describes.
            ValueError: `created_at` is naive (the audit contract requires a timezone).
            ArtifactValidationError: the produced decision breaks its own contract.
        """
        run_id = _run_id(run_record)
        results = tuple(
            self._evaluate_gate(gate_id, stage, run_record)
            for gate_id, stage in sorted(self.policy.stages.items())
        )
        declared_status = _declared_status(run_record)
        verdict = aggregate(results, declared_status)

        decision = {
            "artifact_type": ARTIFACT_TYPE,
            "version": SCHEMA_VERSION,
            GATE_ID_FIELD: f"{GATE_ID_PREFIX}{run_id}",
            "created_at": _format_utc(created_at),
            "policy_version": self.policy.policy_version,
            "release_candidate": release_candidate,
            "subject_declared_status": declared_status,
            DECISION_FIELD: verdict.decision,
            "gate_results": [result.as_dict() for result in results],
            BLOCKING_REASONS_FIELD: list(verdict.blocking_reasons),
            "warning_reasons": list(verdict.warning_reasons),
            "evidence_refs": [run_id],
        }
        validate_artifact(decision)
        return decision

    def _evaluate_gate(
        self,
        gate_id: str,
        stage: str,
        subject: Mapping[str, Any],
    ) -> GateResult:
        rule = GATE_RULES.get(gate_id)
        if rule is None:
            return GateResult(
                gate=gate_id,
                stage=stage,
                outcome=OUTCOME_INCONCLUSIVE,
                reason=unimplemented_reason(gate_id),
            )
        result = rule(subject)
        return GateResult(gate=gate_id, stage=stage, outcome=result.outcome, reason=result.reason)


def enforce(decision: Mapping[str, Any]) -> None:
    """Stop the caller when the decision blocks. No-op for warn and pass.

    Recording a block and acting on it are separate steps on purpose: the decision is
    always stored, and only a caller that wants to halt calls this.

    Raises:
        GateBlockedError: `decision` blocks.
    """
    if decision.get(DECISION_FIELD) != DECISION_BLOCK:
        return
    reasons = decision.get(BLOCKING_REASONS_FIELD) or ("no reason recorded",)
    raise GateBlockedError(
        f"gate decision {decision.get(GATE_ID_FIELD)} blocks: {'; '.join(reasons)}"
    )


def _run_id(subject: Mapping[str, Any]) -> str:
    """The subject must identify itself: a decision about an unnamed run is unusable."""
    run_id = subject.get(RUN_ID_FIELD)
    if not isinstance(run_id, str) or not run_id.strip():
        raise GateEvaluationError(
            f"cannot evaluate a subject without a usable {RUN_ID_FIELD}: {run_id!r}"
        )
    return run_id


def _declared_status(subject: Mapping[str, Any]) -> str | None:
    """Read the subject's self-declared gate status, or None when it declares none.

    None means "no declaration was readable" and is recorded as such. It is not the
    same as `passed`, and the caller must not read it as one.
    """
    envelope = subject.get(ENVELOPE_FIELD)
    if not isinstance(envelope, Mapping):
        return None
    status = envelope.get(DECLARED_STATUS_FIELD)
    return status if status in DECLARED_STATUS_VALUES else None


def _format_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("created_at must be timezone-aware (RFC 3339 with offset)")
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
