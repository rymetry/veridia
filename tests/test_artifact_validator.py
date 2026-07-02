"""T-008 artifact validator(lib + CLI)の契約テスト。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.test_core_spec_schemas import SPEC_CASES, make_valid_instance
from tests.test_execution_evidence_schema import (
    make_valid_instance as make_execution_evidence_instance,
)
from tests.test_reporting_schemas import (
    make_quality_analytics_snapshot_instance,
    make_release_readiness_report_instance,
)
from tests.test_test_asset_impact_schemas import (
    make_change_impact_spec_instance,
    make_test_asset_index_instance,
)


def all_valid_artifacts() -> list[dict[str, Any]]:
    """T-004〜T-007の7 artifact種の有効サンプル。"""
    return [
        *(make_valid_instance(case) for case in SPEC_CASES),
        make_execution_evidence_instance(),
        make_test_asset_index_instance(),
        make_change_impact_spec_instance(),
        make_quality_analytics_snapshot_instance(),
        make_release_readiness_report_instance(),
    ]


@pytest.mark.parametrize(
    "artifact",
    all_valid_artifacts(),
    ids=lambda artifact: artifact["artifact_type"],
)
def test_validator_accepts_all_phase_0_artifact_samples(artifact: dict[str, Any]) -> None:
    from artifact_validator import validate_artifact

    validate_artifact(artifact)


@pytest.mark.parametrize("source_refs", [[], None])
def test_validator_rejects_empty_or_missing_source_refs(source_refs: list[str] | None) -> None:
    from artifact_validator import ArtifactValidationError, validate_artifact

    artifact = make_test_asset_index_instance()
    if source_refs is None:
        del artifact["source_refs"]
    else:
        artifact["source_refs"] = source_refs

    with pytest.raises(ArtifactValidationError) as exc_info:
        validate_artifact(artifact)

    assert exc_info.value.errors
    assert {issue.field_path for issue in exc_info.value.errors} == {"$.source_refs"}


def test_validator_rejects_naive_created_at_with_machine_readable_field_path() -> None:
    from artifact_validator import ArtifactValidationError, validate_artifact

    artifact = make_test_asset_index_instance()
    artifact["created_at"] = "2026-07-02T10:00:00"

    with pytest.raises(ArtifactValidationError) as exc_info:
        validate_artifact(artifact)

    assert any(
        issue.field_path == "$.created_at" and issue.validator == "format"
        for issue in exc_info.value.errors
    )


@pytest.mark.parametrize("artifact_type", ["unknown_type", None])
def test_validator_rejects_unknown_or_missing_artifact_type(
    artifact_type: str | None,
) -> None:
    from artifact_validator import ArtifactValidationError, validate_artifact

    artifact = make_test_asset_index_instance()
    if artifact_type is None:
        del artifact["artifact_type"]
    else:
        artifact["artifact_type"] = artifact_type

    with pytest.raises(ArtifactValidationError) as exc_info:
        validate_artifact(artifact)

    assert exc_info.value.errors
    assert {issue.field_path for issue in exc_info.value.errors} == {"$.artifact_type"}


def test_validation_error_exposes_serializable_details() -> None:
    from artifact_validator import ArtifactValidationError, validate_artifact

    artifact = make_release_readiness_report_instance()
    del artifact["evidence_refs"]

    with pytest.raises(ArtifactValidationError) as exc_info:
        validate_artifact(artifact)

    assert exc_info.value.to_dict() == {
        "errors": [
            {
                "field_path": "$.evidence_refs",
                "message": "'evidence_refs' is a required property",
                "schema_path": "$.required",
                "validator": "required",
            }
        ]
    }


def test_cli_accepts_valid_artifact_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from artifact_validator.cli import main

    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(make_test_asset_index_instance()), encoding="utf-8")

    assert main([str(path)]) == 0
    assert capsys.readouterr().out == f"valid: {path}\n"


def test_cli_reports_field_path_for_invalid_artifact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from artifact_validator.cli import main

    artifact = make_test_asset_index_instance()
    artifact["source_refs"] = []
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    assert main([str(path)]) == 1
    captured = capsys.readouterr()
    assert "$.source_refs" in captured.err
    assert "[] should be non-empty" in captured.err
