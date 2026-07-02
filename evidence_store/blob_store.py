"""Local filesystem blob adapter with S3-style logical references."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from evidence_store.errors import EvidenceStoreError

LOGICAL_REF_SCHEME = "object-storage"
DEFAULT_STORE_NAME = "evidence"


@dataclass(frozen=True)
class LocalBlobStore:
    """Store blobs under a local root while exposing object-storage:// refs."""

    root: Path
    store_name: str = DEFAULT_STORE_NAME

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root))
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, run_id: str, object_name: str, data: bytes) -> str:
        """Put one blob and return its S3-style logical ref."""
        key = _object_key(run_id, object_name)
        path = self._path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return self._ref_for_key(key)

    def get(self, logical_ref: str) -> bytes:
        """Read one blob by logical ref."""
        path = self._path_for_ref(logical_ref)
        try:
            return path.read_bytes()
        except OSError as exc:
            raise EvidenceStoreError(f"failed to read blob {logical_ref}: {exc}") from exc

    def list(self, run_id: str) -> tuple[str, ...]:
        """List logical refs under one run_id prefix."""
        _validate_run_id(run_id)
        run_root = self.root / run_id
        if not run_root.exists():
            return ()
        refs = []
        for path in sorted(run_root.rglob("*")):
            if path.is_file():
                object_name = path.relative_to(run_root).as_posix()
                refs.append(self._ref_for_key(_object_key(run_id, object_name)))
        return tuple(refs)

    def _path_for_ref(self, logical_ref: str) -> Path:
        return self._path_for_key(self._key_for_ref(logical_ref))

    def _path_for_key(self, key: PurePosixPath) -> Path:
        return self.root.joinpath(*key.parts)

    def _ref_for_key(self, key: PurePosixPath) -> str:
        return f"{LOGICAL_REF_SCHEME}://{self.store_name}/{key.as_posix()}"

    def _key_for_ref(self, logical_ref: str) -> PurePosixPath:
        parsed = urlparse(logical_ref)
        if parsed.scheme != LOGICAL_REF_SCHEME or parsed.netloc != self.store_name:
            raise EvidenceStoreError(f"unsupported blob logical ref: {logical_ref}")
        path = parsed.path.removeprefix("/")
        parts = PurePosixPath(path).parts
        if len(parts) < 2:
            raise EvidenceStoreError(
                f"blob logical ref must include run_id and object name: {logical_ref}"
            )
        return _object_key(parts[0], "/".join(parts[1:]))


def _object_key(run_id: str, object_name: str) -> PurePosixPath:
    _validate_run_id(run_id)
    object_path = PurePosixPath(object_name)
    if object_path.is_absolute() or not object_path.parts:
        raise EvidenceStoreError(f"invalid object name: {object_name!r}")
    if any(part in {"", ".", ".."} for part in object_path.parts):
        raise EvidenceStoreError(f"object name must be a relative object key: {object_name!r}")
    return PurePosixPath(run_id, *object_path.parts)


def _validate_run_id(run_id: str) -> None:
    if not run_id or "/" in run_id or run_id in {".", ".."}:
        raise EvidenceStoreError(f"invalid run_id for blob key: {run_id!r}")
