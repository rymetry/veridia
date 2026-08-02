"""Run Store error types."""

from __future__ import annotations


class RunStoreError(RuntimeError):
    """Raised when a run record cannot be saved or loaded."""


class RunNotFoundError(RunStoreError):
    """Raised when no run record exists for the requested run_id."""
