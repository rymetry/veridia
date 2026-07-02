"""High-level Evidence Store API for ExecutionEvidence artifacts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from artifact_validator import validate_artifact

from evidence_store.blob_store import LocalBlobStore
from evidence_store.errors import EvidenceNotFoundError
from evidence_store.metadata import EvidenceMetadata, SqliteEvidenceMetadataRepository

DEFAULT_ROOT = Path(".veridia/store/evidence")
PAYLOAD_OBJECT_NAME = "execution-evidence.json"
TEST_RESULT_OBJECT_NAME = "test-result.json"
STATE_DIFF_OBJECT_NAME = "state-diff.json"


@dataclass(frozen=True)
class StoredEvidence:
    """ExecutionEvidence payload and blobs loaded through logical refs."""

    metadata: EvidenceMetadata
    payload: dict[str, Any]
    test_result: Any
    state_diff: Any
    logs: dict[str, bytes]


@dataclass(frozen=True)
class EvidenceStore:
    """Save and load ExecutionEvidence plus its local blobs."""

    metadata_repository: SqliteEvidenceMetadataRepository
    blob_store: LocalBlobStore

    @classmethod
    def open(cls, root: str | Path = DEFAULT_ROOT) -> EvidenceStore:
        root_path = Path(root)
        return cls(
            metadata_repository=SqliteEvidenceMetadataRepository.under_root(root_path),
            blob_store=LocalBlobStore(root_path / "objects"),
        )

    def save_execution_evidence(
        self,
        artifact: Mapping[str, Any],
        *,
        test_result: Any,
        state_diff: Any,
        logs: Mapping[str, bytes] | None = None,
    ) -> StoredEvidence:
        """Validate, persist blobs, save metadata, and return the stored evidence."""
        payload = dict(artifact)
        validate_artifact(payload)

        run_id = _required_str(payload, "run_id")
        test_result_ref = self.blob_store.put(
            run_id,
            TEST_RESULT_OBJECT_NAME,
            _json_bytes(test_result),
        )
        state_diff_ref = self.blob_store.put(
            run_id,
            STATE_DIFF_OBJECT_NAME,
            _json_bytes(state_diff),
        )
        log_refs_by_name = self._put_logs(run_id, logs or {})

        payload = _payload_with_refs(
            payload,
            test_result_ref=test_result_ref,
            state_diff_ref=state_diff_ref,
            log_refs_by_name=log_refs_by_name,
        )
        validate_artifact(payload)

        payload_ref = self.blob_store.put(
            run_id,
            PAYLOAD_OBJECT_NAME,
            _json_bytes(payload),
        )
        metadata = EvidenceMetadata(
            artifact_id=_required_str(payload, "artifact_id"),
            trace_id=_required_str(payload, "trace_id"),
            run_id=run_id,
            test_asset_id=_required_str(payload, "test_asset_id"),
            verdict=_required_str(payload, "verdict"),
            created_at=_required_str(payload, "created_at"),
            schema_version=_required_str(payload, "version"),
            payload_ref=payload_ref,
            state_diff_ref=state_diff_ref,
            log_refs=tuple(log_refs_by_name.values()),
        )
        self.metadata_repository.save(metadata)
        return self._stored_from_metadata(metadata)

    def get_by_artifact_id(self, artifact_id: str) -> StoredEvidence:
        metadata = self.metadata_repository.get_by_artifact_id(artifact_id)
        if metadata is None:
            raise EvidenceNotFoundError(f"evidence artifact not found: {artifact_id}")
        return self._stored_from_metadata(metadata)

    def find_by_trace_id(self, trace_id: str) -> tuple[StoredEvidence, ...]:
        return tuple(
            self._stored_from_metadata(metadata)
            for metadata in self.metadata_repository.find_by_trace_id(trace_id)
        )

    def find_by_run_id(self, run_id: str) -> tuple[StoredEvidence, ...]:
        return tuple(
            self._stored_from_metadata(metadata)
            for metadata in self.metadata_repository.find_by_run_id(run_id)
        )

    def find_by_test_asset_id(self, test_asset_id: str) -> tuple[StoredEvidence, ...]:
        return tuple(
            self._stored_from_metadata(metadata)
            for metadata in self.metadata_repository.find_by_test_asset_id(test_asset_id)
        )

    def _put_logs(self, run_id: str, logs: Mapping[str, bytes]) -> dict[str, str]:
        refs: dict[str, str] = {}
        for object_name, data in sorted(logs.items()):
            refs[object_name] = self.blob_store.put(run_id, f"logs/{object_name}", data)
        return refs

    def _stored_from_metadata(self, metadata: EvidenceMetadata) -> StoredEvidence:
        payload = json.loads(self.blob_store.get(metadata.payload_ref).decode("utf-8"))
        test_result_ref = _required_str(payload["outputs"], "test_result_ref")
        test_result = json.loads(self.blob_store.get(test_result_ref).decode("utf-8"))
        state_diff = json.loads(self.blob_store.get(metadata.state_diff_ref).decode("utf-8"))
        logs = {
            ref.removeprefix(
                f"object-storage://evidence/{metadata.run_id}/logs/"
            ): self.blob_store.get(ref)
            for ref in metadata.log_refs
        }
        return StoredEvidence(
            metadata=metadata,
            payload=payload,
            test_result=test_result,
            state_diff=state_diff,
            logs=logs,
        )


def _payload_with_refs(
    payload: dict[str, Any],
    *,
    test_result_ref: str,
    state_diff_ref: str,
    log_refs_by_name: Mapping[str, str],
) -> dict[str, Any]:
    updated = dict(payload)
    updated["outputs"] = {**_mapping_value(payload, "outputs"), "test_result_ref": test_result_ref}
    updated["state_diff"] = {**_mapping_value(payload, "state_diff"), "ref": state_diff_ref}
    if log_refs_by_name:
        updated["logs"] = [{"ref": ref, "kind": "test_runner"} for ref in log_refs_by_name.values()]
    return updated


def _mapping_value(payload: Mapping[str, Any], field_name: str) -> dict[str, Any]:
    value = payload.get(field_name)
    if not isinstance(value, Mapping):
        return {}
    return dict(value)


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")


def _required_str(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload[field_name]
    if not isinstance(value, str) or not value:
        raise TypeError(f"{field_name} must be a non-empty string")
    return value
