"""Normalized state hashing for Phase 0 sandbox roots."""

from __future__ import annotations

import hashlib
from pathlib import Path

from sandbox_env.errors import SandboxEnvError

_HASH_VERSION = "sandbox-state-hash-v1"


def state_hash(root: Path | str) -> str:
    """Return a deterministic hash of relative path, file type, and content.

    Absolute path, mtime, inode, owner, and permission bits are intentionally excluded.
    """

    sandbox_root = Path(root)
    if not sandbox_root.is_dir():
        raise SandboxEnvError(f"sandbox root does not exist or is not a directory: {sandbox_root}")

    digest = hashlib.sha256()
    digest.update(_HASH_VERSION.encode("utf-8"))
    digest.update(b"\0")

    for path in sorted(sandbox_root.rglob("*"), key=_relative_posix(sandbox_root)):
        relative_path = path.relative_to(sandbox_root).as_posix()
        file_type = _file_type(path)
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_type.encode("ascii"))
        digest.update(b"\0")
        if file_type == "file":
            digest.update(path.read_bytes())
        elif file_type == "symlink":
            digest.update(path.readlink().as_posix().encode("utf-8"))
        digest.update(b"\0")

    return digest.hexdigest()


def _relative_posix(root: Path):
    def key(path: Path) -> str:
        return path.relative_to(root).as_posix()

    return key


def _file_type(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_file():
        return "file"
    if path.is_dir():
        return "dir"
    raise SandboxEnvError(f"unsupported filesystem entry in sandbox state: {path}")
