"""Audit wrapper and storage for one sqk-core skill run (ADR-0007).

`build_run_record` wraps a sqk-core handoff envelope with the audit fields the
envelope cannot carry (when, who, against what, which sqk-core commit). `RunStore`
persists the result. Both entry points validate before they return or write.
"""

from run_store.errors import RunNotFoundError, RunStoreError
from run_store.record import ARTIFACT_TYPE, SCHEMA_VERSION, build_run_record
from run_store.store import RunStore

__all__ = [
    "ARTIFACT_TYPE",
    "SCHEMA_VERSION",
    "RunNotFoundError",
    "RunStore",
    "RunStoreError",
    "build_run_record",
]
