"""Trace Store error types."""

from __future__ import annotations


class TraceStoreError(ValueError):
    """Raised when Trace Store data cannot be saved or read."""


class InvalidTraceEventTypeError(TraceStoreError):
    """Raised when a trace event type is outside the Phase 0 subset."""
