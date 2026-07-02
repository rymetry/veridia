"""Evidence Store error types."""

from __future__ import annotations


class EvidenceStoreError(ValueError):
    """Raised when Evidence Store data cannot be saved or read."""


class EvidenceNotFoundError(LookupError):
    """Raised when requested evidence metadata does not exist."""
