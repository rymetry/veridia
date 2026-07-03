"""T-009 TestAssetIndex generatorの契約テスト。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from artifact_validator import ArtifactValidationError, validate_artifact
from trace_ids import TRACE_ID_RE


def test_cli_generates_valid_test_asset_index_from_veridia_tests(tmp_path: Path) -> None:
    from test_asset_index_generator.cli import main

    repo_root = Path(__file__).resolve().parents[1]
    output_path = tmp_path / "test-asset-index.json"

    assert main([str(repo_root), str(output_path)]) == 0

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    validate_artifact(artifact)
    assert artifact["artifact_type"] == "test_asset_index"
    assert artifact["scope"]["repository"] == "veridia"
    assert artifact["assets"]
    matching_assets = [
        asset for asset in artifact["assets"] if asset["path"] == "tests/test_artifact_validator.py"
    ]
    assert matching_assets
    assert any(
        asset["path"] == "tests/test_artifact_validator.py" and asset["test_type"] == "unit"
        for asset in artifact["assets"]
    )


def test_generator_is_deterministic_for_same_input() -> None:
    from test_asset_index_generator import generate_test_asset_index

    repo_root = Path(__file__).resolve().parents[1]

    first = generate_test_asset_index(repo_root)
    second = generate_test_asset_index(repo_root)

    assert first == second
    assert first["created_at"] == "1970-01-01T00:00:00Z"
    assert first["indexed_at"] == "1970-01-01T00:00:00Z"
    assert TRACE_ID_RE.fullmatch(first["trace_id"])


def test_phase_0_uncollected_fields_are_explicitly_marked() -> None:
    from test_asset_index_generator import generate_test_asset_index

    repo_root = Path(__file__).resolve().parents[1]

    artifact = generate_test_asset_index(repo_root)

    assert artifact["assets"]
    for asset in artifact["assets"]:
        assert asset["covered_requirements"] == []
        assert asset["covered_risks"] == []
        assert asset["oracle_refs"] == []
        assert asset["stability"]["flake_rate"] is None


def test_cli_returns_validation_error_when_generated_artifact_is_invalid(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import test_asset_index_generator.cli as cli

    def reject(_artifact: object) -> None:
        raise ArtifactValidationError(())

    monkeypatch.setattr(cli, "validate_artifact", reject)

    assert cli.main([str(Path(__file__).resolve().parents[1]), str(tmp_path / "out.json")]) == 1
    assert "invalid generated artifact" in capsys.readouterr().err


def test_cli_still_returns_input_error_for_missing_repository_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from test_asset_index_generator.cli import main

    assert main([str(tmp_path / "missing-repo"), str(tmp_path / "out.json")]) == 2
    assert "error:" in capsys.readouterr().err
