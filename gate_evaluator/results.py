"""Per-gate results and how they aggregate into one decision (§17.0).

The aggregation rule is deliberately asymmetric:

- only a gate that ran at `block` stage and **failed** can block
- an `inconclusive` gate never blocks, but it can never be reported as a pass either

Blocking on inconclusive would be the safer-looking choice and the wrong one: 16 of
the 17 gates have no evaluator yet, so every run would block on day one. §17.0 says
that outcome (blanket blocking, then routine override) is how a gate becomes
ceremonial. Warning keeps the gap visible without spending the trust.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

OUTCOME_PASS = "pass"
OUTCOME_FAIL = "fail"
OUTCOME_INCONCLUSIVE = "inconclusive"

STAGE_SHADOW = "shadow"
STAGE_WARN = "warn"
STAGE_BLOCK = "block"
ENFORCING_STAGES = frozenset({STAGE_WARN, STAGE_BLOCK})

DECISION_PASS = "pass"
DECISION_WARN = "warn"
DECISION_BLOCK = "block"

DECLARED_BLOCKED = "blocked"
DECLARED_PASSED_WITH_RISKS = "passed-with-risks"


@dataclass(frozen=True)
class GateResult:
    """One gate's verdict, with the stage it was judged at."""

    gate: str
    stage: str
    outcome: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "gate": self.gate,
            "stage": self.stage,
            "outcome": self.outcome,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class Verdict:
    """The aggregate decision and the human-readable reasons behind it."""

    decision: str
    blocking_reasons: tuple[str, ...]
    warning_reasons: tuple[str, ...]


def aggregate(results: Iterable[GateResult], declared_status: str | None) -> Verdict:
    """Fold gate results and the subject's self-declared status into one decision.

    `declared_status` moves the decision only towards stricter outcomes. A subject
    claiming `passed` earns nothing: a self-reported trust label that can grant
    passage is a gate the subject can walk around (learning-log 2026-08-02).
    """
    blocking: list[str] = []
    warning: list[str] = []

    for result in results:
        reason = _reason_for(result)
        if reason is None:
            continue
        if result.stage == STAGE_BLOCK and result.outcome == OUTCOME_FAIL:
            blocking.append(reason)
        else:
            warning.append(reason)

    if declared_status == DECLARED_BLOCKED:
        blocking.append(f"the evaluated subject declared gate_status {DECLARED_BLOCKED!r}")
    elif declared_status == DECLARED_PASSED_WITH_RISKS:
        warning.append(f"the evaluated subject declared gate_status {DECLARED_PASSED_WITH_RISKS!r}")

    return Verdict(
        decision=_decision_for(blocking, warning),
        blocking_reasons=tuple(blocking),
        warning_reasons=tuple(warning),
    )


def _reason_for(result: GateResult) -> str | None:
    """Render the reason a result contributes, or None when it contributes nothing.

    Shadow-stage results are recorded in the decision but never surface here: §17.0
    defines shadow as measured and invisible to developers.
    """
    if result.stage not in ENFORCING_STAGES:
        return None
    if result.outcome == OUTCOME_FAIL:
        return f"gate {result.gate!r} (stage {result.stage}) failed: {result.reason}"
    if result.outcome == OUTCOME_INCONCLUSIVE:
        return f"gate {result.gate!r} (stage {result.stage}) is inconclusive: {result.reason}"
    return None


def _decision_for(blocking: Sequence[str], warning: Sequence[str]) -> str:
    if blocking:
        return DECISION_BLOCK
    if warning:
        return DECISION_WARN
    return DECISION_PASS
