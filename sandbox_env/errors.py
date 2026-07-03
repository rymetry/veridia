"""Errors raised by the Phase 0 sandbox environment."""

from __future__ import annotations


class SandboxEnvError(RuntimeError):
    """Base error for sandbox lifecycle and hashing failures."""
