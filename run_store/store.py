"""File-backed store for RunRecord payloads.

One JSON file per run under `<root>/<run_id>.json`. No database: the only access
patterns today are get-by-run_id and list-all. A metadata index is added when a real
query need appears, not before (Evidence Store carries a SQLite index because evidence
is queried by trace_id / test_asset_id).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from artifact_validator import validate_artifact

from run_store.errors import RunNotFoundError, RunStoreError

DEFAULT_ROOT = Path(".veridia/store/runs")
RECORD_SUFFIX = ".json"
RUN_ID_FIELD = "run_id"


@dataclass(frozen=True)
class RunStore:
    """Save and load RunRecord payloads as JSON files."""

    root: Path

    @classmethod
    def open(cls, root: str | Path = DEFAULT_ROOT) -> RunStore:
        root_path = Path(root)
        root_path.mkdir(parents=True, exist_ok=True)
        return cls(root=root_path)

    def save(self, record: Mapping[str, Any]) -> Path:
        """Validate and persist one run record. Returns the written path.

        Raises:
            ArtifactValidationError: the record does not satisfy the RunRecord contract.
            RunStoreError: the run_id is unusable as a filename, or the write failed.
        """
        validate_artifact(record)
        run_id = str(record[RUN_ID_FIELD])
        path = self._path_for(run_id)
        try:
            path.write_text(
                json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise RunStoreError(f"failed to write run record {run_id}: {exc}") from exc
        return path

    def get(self, run_id: str) -> dict[str, Any]:
        """Load one run record by run_id.

        Raises:
            RunNotFoundError: no record exists for run_id.
            RunStoreError: the stored file is unreadable or not a JSON object.
        """
        path = self._path_for(run_id)
        if not path.is_file():
            raise RunNotFoundError(f"run record not found: {run_id}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise RunStoreError(f"failed to read run record {run_id}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RunStoreError(f"failed to parse run record {run_id}: {exc}") from exc
        if not isinstance(payload, dict):
            raise RunStoreError(f"run record must be a JSON object: {run_id}")
        return payload

    def run_ids(self) -> tuple[str, ...]:
        """Return every stored run_id, sorted."""
        return tuple(sorted(path.stem for path in self.root.glob(f"*{RECORD_SUFFIX}")))

    def _path_for(self, run_id: str) -> Path:
        """Resolve `run_id` to a file directly under root, rejecting traversal."""
        if not run_id:
            raise RunStoreError("run_id must not be empty")
        candidate = (self.root / f"{run_id}{RECORD_SUFFIX}").resolve()
        if candidate.parent != self.root.resolve():
            raise RunStoreError(f"run_id must not contain path separators: {run_id!r}")
        return candidate
