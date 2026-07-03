"""Deterministic filesystem state diff for sandbox roots."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    for path in sorted(
        sandbox_root.rglob("*"), key=lambda item: item.relative_to(sandbox_root).as_posix()
    ):
        relative_path = path.relative_to(sandbox_root).as_posix()
        entries[relative_path] = _entry_for(path, relative_path)
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


def _entry_for(path: Path, relative_path: str) -> StateEntry:
    if path.is_symlink():
        return StateEntry(path=relative_path, type="symlink", target=path.readlink().as_posix())
    if path.is_file():
        return StateEntry(path=relative_path, type="file", sha256=_sha256(path))
    if path.is_dir():
        return StateEntry(path=relative_path, type="dir")
    raise SandboxRunnerError(f"unsupported filesystem entry in sandbox state: {path}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
