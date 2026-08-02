"""Run skills through an isolated LLM backend and persist auditable records.

Boundaries (ADR-0005):

- `LLMClient` — model inference. Parallel to Tool Gateway, never on it.
- `SkillSource` — where skills are read from. Two families, neither privileged
  (ADR-0010): `SqkSkillSource` reads the pinned sqk-core submodule, `QaSkillSource`
  reads veridia's own `qa-skills/` packages.
- `SkillRunner` — orchestrates load → prompt → invoke → validate → store → metrics.

Backends are injected, never resolved from the environment: a configuration mistake
must not silently produce fake artifacts.

Values whose authority is not the model (`trust_level`) are passed to `SkillRunner.run`
as `authoritative_fields` and written over the output before validation
(ADR-0009 Decision 2).
"""

from skill_runner.claude_cli import ClaudeCliLLMClient
from skill_runner.errors import (
    BackendUnavailableError,
    IsolationError,
    LLMInvocationError,
    SkillNotFoundError,
    SkillRunnerError,
    SkillSourceError,
)
from skill_runner.llm_client import FakeLLMClient, LLMClient, LLMResponse, Prompt
from skill_runner.qa_skill_source import QA_SKILLS_DIR, QaSkillSource
from skill_runner.runner import SkillRunner, SkillRunResult
from skill_runner.skill_source import SkillDefinition, SkillSource, SqkSkillSource

__all__ = [
    "QA_SKILLS_DIR",
    "BackendUnavailableError",
    "ClaudeCliLLMClient",
    "FakeLLMClient",
    "IsolationError",
    "LLMClient",
    "LLMInvocationError",
    "LLMResponse",
    "Prompt",
    "QaSkillSource",
    "SkillDefinition",
    "SkillNotFoundError",
    "SkillRunResult",
    "SkillRunner",
    "SkillRunnerError",
    "SkillSource",
    "SkillSourceError",
    "SqkSkillSource",
]
