"""Quality gate evaluation: GatePolicy in, GateDecision out (North Star §6.24 / §17).

    GatePolicy.load() → GateEvaluator.evaluate(run_record) → GateDecisionStore.save()
                                                           → enforce()  # raises on block

Two properties are load-bearing and are pinned by tests:

- a gate with no evaluator is `inconclusive`, never `pass`. 15 of the 16 gates have no
  evaluator yet, so silently passing them would make the whole decision meaningless
- the subject's self-declared `gate_status` can only make the decision stricter. A
  trust label the subject writes about itself must not be able to open the gate
"""

from gate_evaluator.errors import (
    GateBlockedError,
    GateDecisionNotFoundError,
    GateDecisionStoreError,
    GateEvaluationError,
    GateEvaluatorError,
    GatePolicyError,
)
from gate_evaluator.evaluator import ARTIFACT_TYPE, SCHEMA_VERSION, GateEvaluator, enforce
from gate_evaluator.policy import DEFAULT_POLICY_PATH, GatePolicy
from gate_evaluator.results import (
    DECISION_BLOCK,
    DECISION_PASS,
    DECISION_WARN,
    OUTCOME_FAIL,
    OUTCOME_INCONCLUSIVE,
    OUTCOME_PASS,
    STAGE_BLOCK,
    STAGE_SHADOW,
    STAGE_WARN,
    GateResult,
    Verdict,
    aggregate,
)
from gate_evaluator.rules import SOURCE_GROUNDING_GATE, RuleOutcome, evaluate_source_grounding
from gate_evaluator.store import GateDecisionStore

__all__ = [
    "ARTIFACT_TYPE",
    "DECISION_BLOCK",
    "DECISION_PASS",
    "DECISION_WARN",
    "DEFAULT_POLICY_PATH",
    "OUTCOME_FAIL",
    "OUTCOME_INCONCLUSIVE",
    "OUTCOME_PASS",
    "SCHEMA_VERSION",
    "SOURCE_GROUNDING_GATE",
    "STAGE_BLOCK",
    "STAGE_SHADOW",
    "STAGE_WARN",
    "GateBlockedError",
    "GateDecisionNotFoundError",
    "GateDecisionStore",
    "GateDecisionStoreError",
    "GateEvaluationError",
    "GateEvaluator",
    "GateEvaluatorError",
    "GatePolicy",
    "GatePolicyError",
    "GateResult",
    "RuleOutcome",
    "Verdict",
    "aggregate",
    "enforce",
    "evaluate_source_grounding",
]
