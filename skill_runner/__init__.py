"""Run sqk-core skills through an isolated LLM backend and persist auditable records.

Boundaries (ADR-0005):

- `LLMClient` — model inference. Parallel to Tool Gateway, never on it.
- `SqkSkillSource` — reads SKILL.md from the pinned sqk-core submodule.
- `SkillRunner` — orchestrates load → prompt → invoke → validate → store → metrics.

Backends are injected, never resolved from the environment: a configuration mistake
must not silently produce fake artifacts.
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
from skill_runner.runner import SkillRunner, SkillRunResult
from skill_runner.skill_source import SkillDefinition, SqkSkillSource

__all__ = [
    "BackendUnavailableError",
    "ClaudeCliLLMClient",
    "FakeLLMClient",
    "IsolationError",
    "LLMClient",
    "LLMInvocationError",
    "LLMResponse",
    "Prompt",
    "SkillDefinition",
    "SkillNotFoundError",
    "SkillRunResult",
    "SkillRunner",
    "SkillRunnerError",
    "SkillSourceError",
    "SqkSkillSource",
]
