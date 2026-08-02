"""File-backed store for GateDecision payloads.

One JSON file per decision under `<root>/<gate_id>.json`, mirroring `RunStore`. The
gate_id is derived from the run, so re-evaluating a run replaces its previous decision
rather than accumulating versions — Phase 1 evaluates each run once.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from artifact_validator import validate_artifact

from gate_evaluator.errors import GateDecisionNotFoundError, GateDecisionStoreError

DEFAULT_ROOT = Path(".veridia/store/gates")
DECISION_SUFFIX = ".json"
GATE_ID_FIELD = "gate_id"


@dataclass(frozen=True)
class GateDecisionStore:
    """Save and load GateDecision payloads as JSON files."""

    root: Path

    @classmethod
    def open(cls, root: str | Path = DEFAULT_ROOT) -> GateDecisionStore:
        root_path = Path(root)
        root_path.mkdir(parents=True, exist_ok=True)
        return cls(root=root_path)

    def save(self, decision: Mapping[str, Any]) -> Path:
        """Validate and persist one gate decision. Returns the written path.

        Raises:
            ArtifactValidationError: the payload does not satisfy the GateDecision contract.
            GateDecisionStoreError: the gate_id is unusable as a filename, or the write failed.
        """
        validate_artifact(decision)
        gate_id = str(decision[GATE_ID_FIELD])
        path = self._path_for(gate_id)
        try:
            path.write_text(
                json.dumps(decision, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise GateDecisionStoreError(f"failed to write gate decision {gate_id}: {exc}") from exc
        return path

    def get(self, gate_id: str) -> dict[str, Any]:
        """Load one gate decision by gate_id.

        Raises:
            GateDecisionNotFoundError: no decision exists for gate_id.
            GateDecisionStoreError: the stored file is unreadable or not a JSON object.
        """
        path = self._path_for(gate_id)
        if not path.is_file():
            raise GateDecisionNotFoundError(f"gate decision not found: {gate_id}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise GateDecisionStoreError(f"failed to read gate decision {gate_id}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise GateDecisionStoreError(f"failed to parse gate decision {gate_id}: {exc}") from exc
        if not isinstance(payload, dict):
            raise GateDecisionStoreError(f"gate decision must be a JSON object: {gate_id}")
        return payload

    def gate_ids(self) -> tuple[str, ...]:
        """Return every stored gate_id, sorted."""
        return tuple(sorted(path.stem for path in self.root.glob(f"*{DECISION_SUFFIX}")))

    def _path_for(self, gate_id: str) -> Path:
        """Resolve `gate_id` to a file directly under root, rejecting traversal."""
        if not gate_id:
            raise GateDecisionStoreError("gate_id must not be empty")
        candidate = (self.root / f"{gate_id}{DECISION_SUFFIX}").resolve()
        if candidate.parent != self.root.resolve():
            raise GateDecisionStoreError(f"gate_id must not contain path separators: {gate_id!r}")
        return candidate
