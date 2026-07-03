"""Deterministic filesystem state diff for sandbox roots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sandbox_env.errors import SandboxEnvError
from sandbox_env.hashing import iter_normalized_entries

from sandbox_runner.errors import SandboxRunnerError


@dataclass(frozen=True)
class StateEntry:
    """Normalized filesystem entry used for deterministic state comparison."""

    path: str
    type: str
    sha256: str | None = None
    target: str | None = None

    def to_json(self) -> dict[str, str]:
        payload = {"path": self.path, "type": self.type}
        if self.sha256 is not None:
            payload["sha256"] = self.sha256
        if self.target is not None:
            payload["target"] = self.target
        return payload


def snapshot(root: Path | str) -> dict[str, StateEntry]:
    """Return a path-keyed normalized snapshot of a sandbox root."""

    sandbox_root = Path(root)
    if not sandbox_root.is_dir():
        raise SandboxRunnerError(f"sandbox root does not exist: {sandbox_root}")

    entries: dict[str, StateEntry] = {}
    try:
        normalized_entries = iter_normalized_entries(sandbox_root)
    except SandboxEnvError as exc:
        raise SandboxRunnerError(str(exc)) from exc

    for entry in normalized_entries:
        entries[entry.path] = StateEntry(
            path=entry.path,
            type=entry.type,
            sha256=entry.sha256,
            target=entry.target,
        )
    return entries


def diff(before: dict[str, StateEntry], after: dict[str, StateEntry]) -> dict[str, Any]:
    """Return deterministic added/modified/deleted changes between snapshots."""

    before_paths = set(before)
    after_paths = set(after)
    added_paths = sorted(after_paths - before_paths)
    deleted_paths = sorted(before_paths - after_paths)
    common_paths = sorted(before_paths & after_paths)
    modified_paths = [path for path in common_paths if before[path] != after[path]]

    return {
        "version": "sandbox-state-diff.v1",
        "added": [after[path].to_json() for path in added_paths],
        "modified": [
            {"before": before[path].to_json(), "after": after[path].to_json()}
            for path in modified_paths
        ],
        "deleted": [before[path].to_json() for path in deleted_paths],
        "summary": {
            "added": len(added_paths),
            "modified": len(modified_paths),
            "deleted": len(deleted_paths),
        },
    }
