"""Errors raised by the Phase 0 sandbox runner."""

from __future__ import annotations


class SandboxRunnerError(RuntimeError):
    """Raised when the sandbox runner cannot prepare, execute, or persist a run."""
