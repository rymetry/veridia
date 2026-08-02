"""Run Store: sqk-core skill実行の監査ラッパー生成と保存(ADR-0007)。

sqk-core契約に依存するため、submodule未取得時はskipする(CIは VERIDIA_REQUIRE_SQK=1 で
このskip自体を失敗に変える。tests/test_sqk_schema_validation.py 参照)。
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from artifact_validator import ArtifactValidationError, SqkSchemaError, validate_artifact
from artifact_validator.sqk_schema_store import SQK_SCHEMAS_DIR, available_schema_refs
from run_store import RunNotFoundError, RunStore, RunStoreError, build_run_record

pytestmark = pytest.mark.skipif(
    not available_schema_refs(),
    reason="vendor/sqk-core submodule not checked out",
)

FIXTURES_DIR = SQK_SCHEMAS_DIR / "tests" / "fixtures"
PINNED_SHA = "54e78cc7f5b5bb1fcd63a72495a530929538f3f8"
RUN_ARGS = {
    "run_id": "run-20260802-0001",
    "trace_id": "trace-20260802-0001",
    "agent": "claude-code",
    "model": "claude-opus-5",
    "source_refs": ["internal://github/rymetry/veridia/pull/5"],
    "sqk_core_commit": PINNED_SHA,
    "created_at": datetime(2026, 8, 2, 9, 0, tzinfo=UTC),
}


def make_tad_envelope() -> dict[str, Any]:
    """sqk-coreのper-item fixtureから組んだ、契約に適合するTAD出力エンベロープ。"""
    matrix = json.loads(
        next((FIXTURES_DIR / "condition-assignment-matrix" / "valid").glob("*.json")).read_text(
            encoding="utf-8"
        )
    )
    return {
        "source_skill": "test-architecture-design",
        "phase": "TAD",
        "artifacts": [
            {
                "type": "ConditionAssignmentMatrix",
                "schema_ref": "schemas/condition-assignment-matrix.schema.json",
                "content": matrix,
            }
        ],
        "trace_ids": ["DTC-001", "TAE-001"],
        "assumptions": [],
        "open_questions": [],
        "gate_status": "passed",
    }


class TestBuildRunRecord:
    def test_wraps_envelope_verbatim(self) -> None:
        envelope = make_tad_envelope()

        record = build_run_record(envelope, **RUN_ARGS)

        assert record["envelope"] == envelope, "envelopeは書き換えずそのまま格納する"
        assert record["artifact_type"] == "run_record"
        assert record["status"] == "draft", "producerは常にdraftを出す(レビューは後続の更新)"
        assert record["requires_human_review"] is True, "Phase 1は候補生成+人間レビュー必須(計画§7)"

    def test_result_satisfies_the_run_record_contract(self) -> None:
        validate_artifact(build_run_record(make_tad_envelope(), **RUN_ARGS))

    def test_records_the_sqk_core_commit(self) -> None:
        # どのSHAの契約を満たすrecordかが残らないと、後から解釈できない
        record = build_run_record(make_tad_envelope(), **RUN_ARGS)
        assert record["sqk_core"]["commit"] == PINNED_SHA

    def test_skill_name_is_only_in_the_envelope(self) -> None:
        record = build_run_record(make_tad_envelope(), **RUN_ARGS)
        assert record["envelope"]["source_skill"] == "test-architecture-design"
        assert "skill" not in record["created_by"]

    def test_invalid_payload_never_becomes_a_record(self) -> None:
        # envelopeが宣言した schema_ref を満たさない実行は監査記録にしない
        envelope = make_tad_envelope()
        envelope["artifacts"][0]["content"] = {"assignments": "not-an-array"}

        with pytest.raises(ArtifactValidationError):
            build_run_record(envelope, **RUN_ARGS)

    def test_unresolvable_schema_ref_is_a_contract_error_not_a_validation_error(self) -> None:
        envelope = make_tad_envelope()
        envelope["artifacts"][0]["schema_ref"] = "schemas/does-not-exist.schema.json"

        with pytest.raises(SqkSchemaError):
            build_run_record(envelope, **RUN_ARGS)

    def test_naive_created_at_is_rejected(self) -> None:
        args = {**RUN_ARGS, "created_at": datetime(2026, 8, 2, 9, 0)}  # noqa: DTZ001 - 意図的
        with pytest.raises(ValueError, match="timezone-aware"):
            build_run_record(make_tad_envelope(), **args)

    def test_non_utc_created_at_is_normalised_to_utc(self) -> None:
        args = {
            **RUN_ARGS,
            "created_at": datetime(2026, 8, 2, 18, 0, tzinfo=timezone(timedelta(hours=9))),
        }

        record = build_run_record(make_tad_envelope(), **args)

        assert record["created_at"] == "2026-08-02T09:00:00Z"

    def test_empty_source_refs_is_rejected(self) -> None:
        with pytest.raises(ArtifactValidationError):
            build_run_record(make_tad_envelope(), **{**RUN_ARGS, "source_refs": []})


class TestRunStore:
    def test_save_then_get_round_trips(self, tmp_path: Path) -> None:
        store = RunStore.open(tmp_path / "runs")
        record = build_run_record(make_tad_envelope(), **RUN_ARGS)

        store.save(record)

        assert store.get(RUN_ARGS["run_id"]) == record

    def test_saved_file_is_readable_json(self, tmp_path: Path) -> None:
        store = RunStore.open(tmp_path / "runs")
        record = build_run_record(make_tad_envelope(), **RUN_ARGS)

        path = store.save(record)

        assert json.loads(path.read_text(encoding="utf-8")) == record

    def test_save_rejects_a_record_that_breaks_the_contract(self, tmp_path: Path) -> None:
        store = RunStore.open(tmp_path / "runs")
        record = build_run_record(make_tad_envelope(), **RUN_ARGS)
        del record["trace_id"]

        with pytest.raises(ArtifactValidationError):
            store.save(record)
        assert store.run_ids() == (), "検証に落ちたrecordはファイルを残さない"

    def test_get_missing_run_raises_not_found(self, tmp_path: Path) -> None:
        store = RunStore.open(tmp_path / "runs")
        with pytest.raises(RunNotFoundError):
            store.get("run-does-not-exist")

    def test_run_ids_are_sorted(self, tmp_path: Path) -> None:
        store = RunStore.open(tmp_path / "runs")
        for run_id in ("run-b", "run-a", "run-c"):
            store.save(build_run_record(make_tad_envelope(), **{**RUN_ARGS, "run_id": run_id}))

        assert store.run_ids() == ("run-a", "run-b", "run-c")

    @pytest.mark.parametrize("run_id", ["../escape", "nested/run", ""])
    def test_run_id_cannot_escape_the_store_root(self, tmp_path: Path, run_id: str) -> None:
        store = RunStore.open(tmp_path / "runs")
        with pytest.raises(RunStoreError):
            store.get(run_id)

    def test_corrupt_file_is_reported_with_context(self, tmp_path: Path) -> None:
        store = RunStore.open(tmp_path / "runs")
        (tmp_path / "runs" / "run-broken.json").write_text("{not json", encoding="utf-8")

        with pytest.raises(RunStoreError, match="failed to parse run record run-broken"):
            store.get("run-broken")

    def test_non_object_file_is_rejected(self, tmp_path: Path) -> None:
        store = RunStore.open(tmp_path / "runs")
        (tmp_path / "runs" / "run-array.json").write_text("[]", encoding="utf-8")

        with pytest.raises(RunStoreError, match="must be a JSON object"):
            store.get("run-array")
