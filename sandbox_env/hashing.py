"""Normalized state hashing for Phase 0 sandbox roots."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from sandbox_env.errors import SandboxEnvError

CHUNK_SIZE = 1024 * 1024
HASH_VERSION = "sandbox-state-hash-v2"


@dataclass(frozen=True)
class NormalizedStateEntry:
    """Normalized filesystem entry shared by state hashing and diffing."""

    path: str
    type: str
    sha256: str | None = None
    target: str | None = None


def state_hash(root: Path | str) -> str:
    """Return a deterministic hash of relative path, file type, and content.

    Absolute path, mtime, inode, owner, and permission bits are intentionally excluded.
    """

    sandbox_root = Path(root)
    if not sandbox_root.is_dir():
        raise SandboxEnvError(f"sandbox root does not exist or is not a directory: {sandbox_root}")

    digest = hashlib.sha256()
    _update_frame(digest, HASH_VERSION.encode("utf-8"))

    for entry in iter_normalized_entries(sandbox_root):
        _update_frame(digest, entry.path.encode("utf-8"))
        _update_frame(digest, entry.type.encode("ascii"))
        _update_frame(digest, (entry.sha256 or "").encode("ascii"))
        _update_frame(digest, (entry.target or "").encode("utf-8"))

    return digest.hexdigest()


def iter_normalized_entries(root: Path | str) -> tuple[NormalizedStateEntry, ...]:
    """Return normalized entries for deterministic hashing and diffing."""
    sandbox_root = Path(root)
    if not sandbox_root.is_dir():
        raise SandboxEnvError(f"sandbox root does not exist or is not a directory: {sandbox_root}")

    entries: list[NormalizedStateEntry] = []
    for path in sorted(sandbox_root.rglob("*"), key=_relative_posix(sandbox_root)):
        relative_path = path.relative_to(sandbox_root).as_posix()
        entries.append(_entry_for(path, relative_path))
    return tuple(entries)


def _relative_posix(root: Path):
    def key(path: Path) -> str:
        return path.relative_to(root).as_posix()

    return key


def _entry_for(path: Path, relative_path: str) -> NormalizedStateEntry:
    file_type = _file_type(path)
    if file_type == "file":
        return NormalizedStateEntry(path=relative_path, type=file_type, sha256=file_sha256(path))
    if file_type == "symlink":
        return NormalizedStateEntry(
            path=relative_path,
            type=file_type,
            target=path.readlink().as_posix(),
        )
    return NormalizedStateEntry(path=relative_path, type=file_type)


def _file_type(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_file():
        return "file"
    if path.is_dir():
        return "dir"
    raise SandboxEnvError(f"unsupported filesystem entry in sandbox state: {path}")


def file_sha256(path: Path) -> str:
    """Return a streaming SHA-256 digest for one file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _update_frame(digest: hashlib._Hash, value: bytes) -> None:
    digest.update(str(len(value)).encode("ascii"))
    digest.update(b":")
    digest.update(value)
