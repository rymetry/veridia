"""T-013 Evidence Store integration tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from artifact_validator import ArtifactValidationError

from tests.test_execution_evidence_schema import make_valid_instance


def make_execution_evidence() -> dict[str, Any]:
    artifact = make_valid_instance()
    return {
        **artifact,
        "artifact_id": "ART-EVIDENCE-T013-001",
        "run_id": "run-20260703T123456789012Z-000000000001",
        "trace_id": "trace-20260703-00000000000000a2",
        "test_asset_id": "TEST-T013-EVIDENCE-STORE",
        "created_at": "2026-07-03T12:34:56Z",
    }


def test_save_and_read_execution_evidence_by_artifact_id_and_trace_id(tmp_path: Path) -> None:
    from evidence_store import EvidenceStore

    artifact = make_execution_evidence()
    test_result = {
        "command": "uv run pytest tests/test_sample.py",
        "summary": {"passed": 3, "failed": 0},
    }
    state_diff = {
        "tables": [{"name": "orders", "rows_changed": 1}],
        "events": [{"type": "order_cancelled", "count": 1}],
    }
    store = EvidenceStore.open(tmp_path / "evidence")

    saved = store.save_execution_evidence(
        artifact,
        test_result=test_result,
        state_diff=state_diff,
        logs={"test-runner.log": b"3 passed\n"},
    )

    by_artifact_id = store.get_by_artifact_id(artifact["artifact_id"])
    by_trace_id = store.find_by_trace_id(artifact["trace_id"])
    by_run_id = store.find_by_run_id(artifact["run_id"])
    by_test_asset_id = store.find_by_test_asset_id(artifact["test_asset_id"])

    assert saved.metadata.artifact_id == artifact["artifact_id"]
    assert by_artifact_id.metadata == saved.metadata
    assert tuple(record.metadata.artifact_id for record in by_trace_id) == (
        artifact["artifact_id"],
    )
    assert tuple(record.metadata.artifact_id for record in by_run_id) == (artifact["artifact_id"],)
    assert tuple(record.metadata.artifact_id for record in by_test_asset_id) == (
        artifact["artifact_id"],
    )
    assert by_artifact_id.payload["artifact_id"] == artifact["artifact_id"]
    assert by_artifact_id.payload["outputs"]["test_result_ref"].startswith(
        f"object-storage://evidence/{artifact['run_id']}/"
    )
    assert by_artifact_id.test_result == test_result
    assert by_artifact_id.state_diff == state_diff
    assert by_artifact_id.logs == {"test-runner.log": b"3 passed\n"}


def test_save_rejects_invalid_execution_evidence_before_writing_blobs(tmp_path: Path) -> None:
    from evidence_store import EvidenceStore

    artifact = make_execution_evidence()
    artifact["source_refs"] = []
    store = EvidenceStore.open(tmp_path / "evidence")

    with pytest.raises(ArtifactValidationError):
        store.save_execution_evidence(
            artifact,
            test_result={"summary": {"passed": 1}},
            state_diff={"tables": []},
        )

    assert list((tmp_path / "evidence" / "objects").rglob("*")) == []


def test_local_blob_store_uses_s3_style_logical_refs(tmp_path: Path) -> None:
    from evidence_store import LocalBlobStore

    run_id = "run-20260703T123456789012Z-000000000001"
    blob_store = LocalBlobStore(tmp_path / "objects")

    ref = blob_store.put(run_id, "state-diff.json", b'{"changed": true}')

    assert ref == f"object-storage://evidence/{run_id}/state-diff.json"
    assert blob_store.get(ref) == b'{"changed": true}'
    assert blob_store.list(run_id) == (ref,)
