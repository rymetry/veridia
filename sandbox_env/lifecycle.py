"""Lifecycle operations for temporary-directory based sandbox environments."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from sandbox_env.errors import SandboxEnvError
from sandbox_env.manifest import DEFAULT_MANIFEST, SandboxManifest, materialize_manifest

DEFAULT_RUNS_ROOT = Path(".veridia/sandbox/runs")


@dataclass(frozen=True)
class SandboxEnv:
    """A created Phase 0 sandbox environment."""

    root: Path


def create(
    root: Path | str | None = None,
    *,
    manifest: SandboxManifest = DEFAULT_MANIFEST,
) -> SandboxEnv:
    """Create a new sandbox root from the deterministic manifest."""

    sandbox_root = _resolve_root(root)
    if sandbox_root.exists():
        raise SandboxEnvError(f"sandbox root already exists: {sandbox_root}")

    try:
        sandbox_root.mkdir(parents=True, exist_ok=False)
        materialize_manifest(sandbox_root, manifest)
    except OSError as exc:
        raise SandboxEnvError(f"failed to create sandbox root {sandbox_root}: {exc}") from exc

    return SandboxEnv(root=sandbox_root)


def destroy(root: Path | str) -> None:
    """Recursively delete a sandbox root if it exists."""

    sandbox_root = Path(root)
    if not sandbox_root.exists():
        return
    if not sandbox_root.is_dir() or sandbox_root.is_symlink():
        raise SandboxEnvError(f"refusing to destroy non-directory sandbox root: {sandbox_root}")

    try:
        shutil.rmtree(sandbox_root)
    except OSError as exc:
        raise SandboxEnvError(f"failed to destroy sandbox root {sandbox_root}: {exc}") from exc


def reset(
    root: Path | str,
    *,
    manifest: SandboxManifest = DEFAULT_MANIFEST,
) -> SandboxEnv:
    """Delete and recreate a sandbox root from the deterministic manifest."""

    destroy(root)
    return create(root, manifest=manifest)


def _resolve_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root)

    DEFAULT_RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="run-", dir=DEFAULT_RUNS_ROOT))
