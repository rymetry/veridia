"""Gate evaluator error types."""

from __future__ import annotations


class GateEvaluatorError(RuntimeError):
    """Base class for every gate evaluation failure."""


class GatePolicyError(GateEvaluatorError):
    """Raised when the GatePolicy config cannot be read, parsed, or trusted."""


class GateEvaluationError(GateEvaluatorError):
    """Raised when a subject cannot be evaluated at all.

    Distinct from a gate failing: a failing gate produces a GateDecision that blocks,
    while this means no auditable decision could be produced (for example the subject
    does not say which run it is).
    """


class GateBlockedError(GateEvaluatorError):
    """Raised by `enforce` when a GateDecision blocks.

    This is the mechanism that actually stops a caller. It carries a result, not a
    malfunction, so callers that want to record-and-continue simply do not call
    `enforce`.
    """


class GateDecisionStoreError(GateEvaluatorError):
    """Raised when a gate decision cannot be saved or loaded."""


class GateDecisionNotFoundError(GateDecisionStoreError):
    """Raised when no gate decision exists for the requested gate_id."""
