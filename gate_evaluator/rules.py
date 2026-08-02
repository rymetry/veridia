"""The gate rules veridia can actually evaluate today.

One rule is implemented: `source_grounding`. Every other gate in `gate-policy.yaml`
has no evaluator and no input, and is reported as inconclusive rather than pass.

A rule receives the subject **as stored**, not as a validated object. That is the
point of the gate: `RunRecord` already requires `minItems: 1` on `source_refs`, so a
rule that trusted the contract could never fire. Gates are the second, independent
check for payloads the contract never gated — hand-written records, records from a
future producer, a file edited in place.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from gate_evaluator.results import OUTCOME_FAIL, OUTCOME_PASS

SOURCE_GROUNDING_GATE = "source_grounding"
SOURCE_REFS_FIELD = "source_refs"


@dataclass(frozen=True)
class RuleOutcome:
    """What a rule concluded, and why."""

    outcome: str
    reason: str


GateRule = Callable[[Mapping[str, Any]], RuleOutcome]


def evaluate_source_grounding(subject: Mapping[str, Any]) -> RuleOutcome:
    """§17.1 source grounding gate: the subject must name what it was derived from.

    Phase 1 evaluates the run wrapper's own `source_refs`. Grounding of the individual
    produced artifacts needs RequirementSpec producers that do not exist yet (T-029),
    so this is the narrow form of the gate, not the §17.4 P0/P1 scoped form.
    """
    if SOURCE_REFS_FIELD not in subject:
        return RuleOutcome(OUTCOME_FAIL, f"{SOURCE_REFS_FIELD} is absent")

    refs = subject[SOURCE_REFS_FIELD]
    if not isinstance(refs, list):
        return RuleOutcome(
            OUTCOME_FAIL,
            f"{SOURCE_REFS_FIELD} must be a list of references, got {type(refs).__name__}",
        )

    grounded = [ref for ref in refs if isinstance(ref, str) and ref.strip()]
    if not grounded:
        return RuleOutcome(OUTCOME_FAIL, f"{SOURCE_REFS_FIELD} declares no usable reference")
    return RuleOutcome(OUTCOME_PASS, f"{SOURCE_REFS_FIELD} declares {len(grounded)} reference(s)")


GATE_RULES: Mapping[str, GateRule] = MappingProxyType(
    {SOURCE_GROUNDING_GATE: evaluate_source_grounding}
)


def unimplemented_reason(gate: str) -> str:
    return f"no evaluator implemented for gate {gate!r}"
