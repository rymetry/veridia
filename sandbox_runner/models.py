"""Public data models for the Phase 0 sandbox runner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evidence_store import StoredEvidence


@dataclass(frozen=True)
class CommandSpec:
    """Shell-free command declaration constrained by an executable allowlist."""

    argv: tuple[str, ...]
    allowed_executables: tuple[str, ...]
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class SandboxRunRequest:
    """Inputs needed to prepare a sandbox, run one test command, and save evidence."""

    sandbox_root: Path
    evidence_root: Path
    seed_path: Path
    seed_id: str
    fixed_now: str
    test_asset_id: str
    command: CommandSpec


@dataclass(frozen=True)
class SandboxRunResult:
    """Runner output returned after ExecutionEvidence persistence."""

    artifact: dict[str, Any]
    test_result: dict[str, Any]
    state_diff: dict[str, Any]
    stored_evidence: StoredEvidence
    verdict: str
