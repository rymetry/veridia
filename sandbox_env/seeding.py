"""Fixture seed manifest support for Phase 0 sandbox environments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sandbox_env.errors import SandboxEnvError

SEED_MANIFEST_VERSION = "sandbox-fixture-seed.v1"


@dataclass(frozen=True)
class SeedFile:
    """A fixture file declared by a seed manifest."""

    relative_path: str
    content: str


@dataclass(frozen=True)
class SeedManifest:
    """Deterministic fixture layer applied on top of a created sandbox root."""

    version: str
    directories: tuple[str, ...]
    files: tuple[SeedFile, ...]


@dataclass(frozen=True)
class SeedResult:
    """Summary of a seed operation."""

    root: Path
    seed_path: Path
    directory_count: int
    file_count: int


def apply_seed(root: Path | str, seed_path: Path | str) -> SeedResult:
    """Apply a deterministic fixture seed manifest to an existing sandbox root."""

    sandbox_root = Path(root)
    if not sandbox_root.is_dir():
        raise SandboxEnvError(f"sandbox root does not exist or is not a directory: {sandbox_root}")

    manifest_path = Path(seed_path)
    manifest = load_seed_manifest(manifest_path)
    _materialize_seed(sandbox_root, manifest)

    return SeedResult(
        root=sandbox_root,
        seed_path=manifest_path,
        directory_count=len(manifest.directories),
        file_count=len(manifest.files),
    )


def load_seed_manifest(seed_path: Path | str) -> SeedManifest:
    """Read and validate a fixture seed manifest from JSON."""

    manifest_path = Path(seed_path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SandboxEnvError(f"failed to read seed manifest {manifest_path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SandboxEnvError(f"invalid seed manifest JSON {manifest_path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise SandboxEnvError(f"seed manifest must be a JSON object: {manifest_path}")

    version = payload.get("version")
    if version != SEED_MANIFEST_VERSION:
        raise SandboxEnvError(f"unsupported seed manifest version in {manifest_path}: {version!r}")

    directories = _read_directories(payload.get("directories", ()), manifest_path)
    files = _read_files(payload.get("files", ()), manifest_path)
    return SeedManifest(version=version, directories=directories, files=files)


def _materialize_seed(root: Path, manifest: SeedManifest) -> None:
    try:
        for relative_dir in manifest.directories:
            (root / relative_dir).mkdir(parents=True, exist_ok=True)

        for file in manifest.files:
            output_path = root / file.relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(file.content, encoding="utf-8")
    except OSError as exc:
        raise SandboxEnvError(f"failed to apply fixture seed to {root}: {exc}") from exc


def _read_directories(value: Any, manifest_path: Path) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise SandboxEnvError(f"seed manifest directories must be a list: {manifest_path}")

    directories: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise SandboxEnvError(
                f"seed manifest directory at index {index} must be a string: {manifest_path}"
            )
        directories.append(_validate_relative_path(item, manifest_path))
    return tuple(directories)


def _read_files(value: Any, manifest_path: Path) -> tuple[SeedFile, ...]:
    if not isinstance(value, list):
        raise SandboxEnvError(f"seed manifest files must be a list: {manifest_path}")

    files: list[SeedFile] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise SandboxEnvError(
                f"seed manifest file at index {index} must be an object: {manifest_path}"
            )
        raw_path = item.get("path")
        content = item.get("content")
        if not isinstance(raw_path, str):
            raise SandboxEnvError(
                f"seed manifest file at index {index} is missing string path: {manifest_path}"
            )
        if not isinstance(content, str):
            raise SandboxEnvError(
                f"seed manifest file at index {index} is missing string content: {manifest_path}"
            )
        files.append(SeedFile(_validate_relative_path(raw_path, manifest_path), content))
    return tuple(files)


def _validate_relative_path(value: str, manifest_path: Path) -> str:
    path = Path(value)
    if value == "" or path.is_absolute() or ".." in path.parts:
        raise SandboxEnvError(
            f"seed manifest path must be a relative sandbox path without '..' segments "
            f"in {manifest_path}: {value!r}"
        )
    return path.as_posix()
