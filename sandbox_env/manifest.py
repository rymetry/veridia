"""Deterministic initial state for Phase 0 sandbox environments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

MANIFEST_FILENAME = "manifest.json"
MANIFEST_VERSION = "sandbox-env.v1"

_INITIAL_DIRECTORIES: tuple[str, ...] = (
    "artifacts",
    "tmp",
    "workspace",
)
_INITIAL_FILES: tuple[tuple[str, str], ...] = (
    (
        "workspace/README.md",
        "# Veridia sandbox workspace\n\n"
        "This directory is recreated from a deterministic Phase 0 manifest.\n",
    ),
)


@dataclass(frozen=True)
class ManifestFile:
    """A file entry in the deterministic sandbox manifest."""

    relative_path: str
    content: str


@dataclass(frozen=True)
class SandboxManifest:
    """Initial directories and files used to recreate a sandbox root."""

    version: str
    directories: tuple[str, ...]
    files: tuple[ManifestFile, ...]

    def to_json_bytes(self) -> bytes:
        payload = {
            "version": self.version,
            "directories": list(self.directories),
            "files": [{"path": file.relative_path, "content": file.content} for file in self.files],
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        return text.encode("utf-8")


DEFAULT_MANIFEST = SandboxManifest(
    version=MANIFEST_VERSION,
    directories=_INITIAL_DIRECTORIES,
    files=tuple(ManifestFile(path, content) for path, content in _INITIAL_FILES),
)


def materialize_manifest(root: Path, manifest: SandboxManifest = DEFAULT_MANIFEST) -> None:
    """Create deterministic directories, files, and manifest metadata under root."""

    for relative_dir in manifest.directories:
        (root / relative_dir).mkdir(parents=True, exist_ok=False)

    for file in manifest.files:
        output_path = root / file.relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(file.content, encoding="utf-8")

    (root / MANIFEST_FILENAME).write_bytes(manifest.to_json_bytes())
