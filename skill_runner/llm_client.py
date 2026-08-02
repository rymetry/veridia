"""LLM invocation boundary (ADR-0005 Decision 3).

This is a boundary *parallel to* Tool Gateway, not a tool on it: the model is the
agent's inference engine, not something the agent chooses to call. Keeping them
separate preserves the meaning of Tool Gateway's allowlist and keeps token/cost
metrics out of `tool_call` trace records.

The client knows nothing about artifacts. Prompt assembly, schema selection and
artifact construction belong to the runner.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from skill_runner.errors import LLMInvocationError

CLAUDE_CLI = "claude_cli"
CODEX_CLI = "codex_cli"


@dataclass(frozen=True)
class Prompt:
    """One rendered prompt, split so the audit record can treat the halves differently.

    `instructions` is recorded in full; `data` is recorded by reference only
    (ADR-0005 Decision 7 / North Star §15.4). Splitting them is also the structural
    part of instruction/data separation required by §16.4: everything in `data` is
    untrusted input.
    """

    instructions: str
    data: str
    data_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class LLMResponse:
    """A schema-constrained model response plus what the backend reported about the run."""

    output: dict[str, Any]
    model: str
    backend: str
    usage: Mapping[str, Any] = field(default_factory=dict)
    reference_cost_usd: float | None = None


class LLMClient(Protocol):
    """Structural type for a backend. Implementations hide all CLI-specific detail."""

    backend: str

    def verify_available(self) -> None:
        """Fail fast when the backend cannot be used.

        Raises:
            BackendUnavailableError: CLI missing, version not allowlisted, not
                authenticated, or the capability probe failed.
        """
        ...

    def complete(self, prompt: Prompt, *, output_schema: Mapping[str, Any]) -> LLMResponse:
        """Run one isolated, schema-constrained completion.

        Raises:
            LLMInvocationError: the backend returned no usable schema-conforming output.
        """
        ...


@dataclass
class FakeLLMClient:
    """Deterministic client for tests.

    Never selectable from the environment: the runner resolves backends by explicit
    injection only, so a configuration mistake cannot silently produce fake artifacts
    (ADR-0005 Decision 3, fail closed).
    """

    responses: list[dict[str, Any]]
    backend: str = "fake"
    model: str = "fake-model"
    calls: list[tuple[Prompt, Mapping[str, Any]]] = field(default_factory=list)

    def verify_available(self) -> None:
        return None

    def complete(self, prompt: Prompt, *, output_schema: Mapping[str, Any]) -> LLMResponse:
        self.calls.append((prompt, output_schema))
        if not self.responses:
            raise LLMInvocationError("FakeLLMClient has no queued response left")
        return LLMResponse(
            output=self.responses.pop(0),
            model=self.model,
            backend=self.backend,
            usage={"input_tokens": 0, "output_tokens": 0},
        )
