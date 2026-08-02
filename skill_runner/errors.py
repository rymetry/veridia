"""Skill runner error types.

Separated by cause so callers can tell "the environment is not usable" from
"the model produced something that does not satisfy the contract".
"""

from __future__ import annotations


class SkillRunnerError(RuntimeError):
    """Base for every skill runner failure."""


class BackendUnavailableError(SkillRunnerError):
    """Raised when the configured LLM backend cannot be used.

    Covers a missing CLI, a version outside the allowlist, missing authentication,
    and a failed capability probe (ADR-0005 Decision 1 / 4).
    """


class IsolationError(SkillRunnerError):
    """Raised when the hermetic execution preconditions do not hold (ADR-0005 Decision 5)."""


class SkillNotFoundError(SkillRunnerError):
    """Raised when the requested skill does not exist in the configured source."""


class SkillSourceError(SkillRunnerError):
    """Raised when a skill definition cannot be parsed."""


class LLMInvocationError(SkillRunnerError):
    """Raised when the backend failed to return a usable response."""
