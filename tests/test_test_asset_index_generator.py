"""T-009 TestAssetIndex generatorの契約テスト。"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from artifact_validator import ArtifactValidationError, validate_artifact
from test_asset_index_generator.generator import generate_test_asset_index
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


class TestRepositoryNameDerivation:
    """`scope.repository` はディレクトリ名ではなくgitリポジトリ名を記録する。

    worktree はリポジトリ名ではなく worktree 名のディレクトリに置かれるため、basename を
    そのまま使うと artifact に誤ったリポジトリ名が入る。
    """

    def _init_repo(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        (root / "tests").mkdir()
        (root / "tests" / "test_sample.py").write_text("def test_x() -> None: ...\n")
        for args in (
            ["init", "-q"],
            ["-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "init"],
        ):
            if args[0] == "init":
                subprocess.run(["git", "-C", str(root), *args], check=True)
                continue
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(root), *args], check=True)

    def test_worktree_records_the_repository_name_not_the_worktree_name(
        self, tmp_path: Path
    ) -> None:
        main_repo = tmp_path / "my-repo"
        self._init_repo(main_repo)
        worktree = tmp_path / "wt" / "feature-branch-slug"
        subprocess.run(
            ["git", "-C", str(main_repo), "worktree", "add", "-q", "-b", "wt1", str(worktree)],
            check=True,
        )

        artifact = generate_test_asset_index(worktree)

        assert artifact["scope"]["repository"] == "my-repo"

    def test_plain_checkout_records_the_repository_name(self, tmp_path: Path) -> None:
        repo = tmp_path / "plain-repo"
        self._init_repo(repo)

        assert generate_test_asset_index(repo)["scope"]["repository"] == "plain-repo"

    def test_non_git_directory_falls_back_to_the_directory_name(self, tmp_path: Path) -> None:
        plain = tmp_path / "not-a-repo"
        (plain / "tests").mkdir(parents=True)
        (plain / "tests" / "test_sample.py").write_text("def test_x() -> None: ...\n")

        assert generate_test_asset_index(plain)["scope"]["repository"] == "not-a-repo"

    def test_explicit_repository_name_wins(self, tmp_path: Path) -> None:
        repo = tmp_path / "plain-repo"
        self._init_repo(repo)

        artifact = generate_test_asset_index(repo, repository_name="explicit-name")

        assert artifact["scope"]["repository"] == "explicit-name"
