"""Source Connector tests (T-026: 対象repoのcommit rangeからdiffと変更ファイルを取得する)。

意図的に厚く書いている領域:

- **設定差し替えで別repoへ向くこと。** 対象固有の接続情報がコードへ漏れていないことは、
  「別のrepoを指したら実際に別のrepoが読まれる」でしか実証できない。第2のrepoには
  `vendor/sqk-core`(実在するローカルgit repo)を使う。
- **repo外・repo未満のpathを拒否すること。** 防御コードは正常系テストでは発火しない
  (learning-log 2026-07-03)。
- **git失敗を握り潰さないこと。** 存在しないrevisionは空diffではなく文脈付き例外にする。
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from source_connector import (
    ChangeSet,
    DiffParseError,
    GitCommandError,
    RepositoryNotFoundError,
    RevisionRangeError,
    SourceConnector,
    TargetRepository,
)

REPO_ROOT = Path(__file__).parent.parent
SQK_CORE_ROOT = REPO_ROOT / "vendor" / "sqk-core"

REPO_PATH_ENV = "VERIDIA_TARGET_REPO_PATH"
REPO_LABEL_ENV = "VERIDIA_TARGET_REPO_LABEL"


def make_git_repo(root: Path) -> Path:
    """Build a tiny real repository so tests exercise git, not a mock of git."""
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "--initial-branch", "main")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "commit.gpgsign", "false")
    (root / "kept.txt").write_text("base\n", encoding="utf-8")
    (root / "removed.txt").write_text("gone soon\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "base")

    (root / "kept.txt").write_text("base\nadded\n", encoding="utf-8")
    (root / "added.txt").write_text("new file\n", encoding="utf-8")
    (root / "removed.txt").unlink()
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "change")
    return root


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


@pytest.fixture
def target_repo(tmp_path: Path) -> Path:
    return make_git_repo(tmp_path / "target")


@pytest.fixture
def connector(target_repo: Path) -> SourceConnector:
    return SourceConnector(repository=TargetRepository(path=target_repo, label="target"))


class TestTargetRepository:
    def test_reads_configuration_from_the_environment(
        self, target_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(REPO_PATH_ENV, str(target_repo))
        monkeypatch.setenv(REPO_LABEL_ENV, "from-env")

        repository = TargetRepository.from_env()

        assert repository.path == target_repo.resolve()
        assert repository.label == "from-env"

    def test_label_defaults_to_the_directory_name(
        self, target_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(REPO_PATH_ENV, str(target_repo))
        monkeypatch.delenv(REPO_LABEL_ENV, raising=False)

        assert TargetRepository.from_env().label == target_repo.name

    def test_missing_configuration_raises_with_the_variable_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv(REPO_PATH_ENV, raising=False)

        with pytest.raises(RepositoryNotFoundError, match=REPO_PATH_ENV):
            TargetRepository.from_env()

    def test_path_that_is_not_a_git_repository_is_rejected(self, tmp_path: Path) -> None:
        plain = tmp_path / "not-a-repo"
        plain.mkdir()

        with pytest.raises(RepositoryNotFoundError, match="not a git repository"):
            TargetRepository(path=plain, label="plain").resolved_path()

    def test_absent_path_is_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(RepositoryNotFoundError, match="does not exist"):
            TargetRepository(path=tmp_path / "absent", label="absent").resolved_path()


class TestFetchChange:
    def test_returns_every_changed_file_with_its_change_type(
        self, connector: SourceConnector
    ) -> None:
        change = connector.fetch_change("HEAD~1", "HEAD")

        by_path = {file.path: file for file in change.changed_files}
        assert by_path["kept.txt"].change_type == "modified"
        assert by_path["added.txt"].change_type == "added"
        assert by_path["removed.txt"].change_type == "deleted"

    def test_counts_added_and_deleted_lines(self, connector: SourceConnector) -> None:
        change = connector.fetch_change("HEAD~1", "HEAD")

        kept = next(file for file in change.changed_files if file.path == "kept.txt")
        assert (kept.lines_added, kept.lines_deleted) == (1, 0)

    def test_carries_the_raw_diff_for_downstream_prompts(self, connector: SourceConnector) -> None:
        change = connector.fetch_change("HEAD~1", "HEAD")

        assert change.diff_text.startswith("diff --git ")
        assert "added.txt" in change.diff_text

    def test_resolves_refs_to_full_shas_so_the_range_is_reproducible(
        self, connector: SourceConnector, target_repo: Path
    ) -> None:
        change = connector.fetch_change("HEAD~1", "HEAD")

        assert change.base_sha == _git(target_repo, "rev-parse", "HEAD~1")
        assert change.head_sha == _git(target_repo, "rev-parse", "HEAD")
        assert len(change.head_sha) == 40

    def test_source_refs_identify_the_repository_and_the_range(
        self, connector: SourceConnector
    ) -> None:
        change = connector.fetch_change("HEAD~1", "HEAD")

        assert change.source_refs
        assert all(ref.startswith("git://target/") for ref in change.source_refs)
        assert any(change.head_sha in ref for ref in change.source_refs)

    def test_source_refs_are_non_empty_so_the_grounding_gate_can_pass(
        self, connector: SourceConnector
    ) -> None:
        # source_grounding gate(T-057)がこの値を判定する。空を出す経路を作らない
        from gate_evaluator import OUTCOME_PASS, evaluate_source_grounding

        change = connector.fetch_change("HEAD~1", "HEAD")

        assert evaluate_source_grounding({"source_refs": list(change.source_refs)}).outcome == (
            OUTCOME_PASS
        )

    def test_an_explicit_change_ref_is_carried_into_source_refs(
        self, connector: SourceConnector
    ) -> None:
        # PR URL等、呼び出し側しか知らない恒久refを添えられること
        change = connector.fetch_change(
            "HEAD~1", "HEAD", change_ref="https://github.com/rymetry/veridia/pull/10"
        )

        assert "https://github.com/rymetry/veridia/pull/10" in change.source_refs

    def test_empty_range_yields_no_files_but_still_identifies_the_range(
        self, connector: SourceConnector
    ) -> None:
        change = connector.fetch_change("HEAD", "HEAD")

        assert change.changed_files == ()
        assert change.diff_text == ""
        assert change.source_refs


class TestFailuresAreNotSwallowed:
    def test_unknown_revision_raises_instead_of_returning_an_empty_diff(
        self, connector: SourceConnector
    ) -> None:
        with pytest.raises(RevisionRangeError, match="no-such-ref"):
            connector.fetch_change("no-such-ref", "HEAD")

    def test_revision_that_looks_like_an_option_is_rejected(
        self, connector: SourceConnector
    ) -> None:
        # argv固定でもrevision文字列が "--output=..." 等に化けるとgitの解釈が変わる
        with pytest.raises(RevisionRangeError, match="must not start with"):
            connector.fetch_change("--upload-pack=touch /tmp/pwn", "HEAD")

    @pytest.mark.parametrize("revision", ["", "   "])
    def test_blank_revision_is_rejected(self, connector: SourceConnector, revision: str) -> None:
        with pytest.raises(RevisionRangeError, match="must not be empty"):
            connector.fetch_change(revision, "HEAD")

    def test_git_failure_surfaces_stderr(self, connector: SourceConnector) -> None:
        with pytest.raises(GitCommandError) as excinfo:
            connector.run_git("cat-file", "-p", "0" * 40)

        assert "cat-file" in str(excinfo.value)

    def test_unparsable_diff_output_raises_instead_of_reporting_no_changes(
        self, connector: SourceConnector, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # 空rangeを許すために空文字を短絡させているので、「中身はあるが読めない」を
        # 変更なしへ退化させないことを別途固定する
        import source_connector.connector as connector_module

        monkeypatch.setattr(
            connector_module,
            "run_git",
            lambda *_args, **_kwargs: "something that is not a unified diff\n",
        )

        with pytest.raises(DiffParseError, match="could not parse the diff"):
            connector.fetch_change("HEAD~1", "HEAD")


class TestConfigurationIsSwappable:
    """対象固有の接続情報がコードに埋まっていないことの実証(T-026 DoD)。"""

    @pytest.mark.skipif(not SQK_CORE_ROOT.exists(), reason="submodule vendor/sqk-core が未取得")
    def test_the_same_code_reads_a_second_repository(self, target_repo: Path) -> None:
        first = SourceConnector(repository=TargetRepository(path=target_repo, label="target"))
        second = SourceConnector(repository=TargetRepository(path=SQK_CORE_ROOT, label="sqk-core"))

        first_change = first.fetch_change("HEAD~1", "HEAD")
        second_change = second.fetch_change("HEAD~1", "HEAD")

        assert first_change.head_sha != second_change.head_sha
        assert first_change.source_refs[0].startswith("git://target/")
        assert second_change.source_refs[0].startswith("git://sqk-core/")

    def test_veridia_itself_is_readable_as_the_phase_1_target(self) -> None:
        # OQ-2の決定(対象=veridia自身)がこのconnectorで実際に成立すること
        connector = SourceConnector(repository=TargetRepository(path=REPO_ROOT, label="veridia"))

        change = connector.fetch_change("HEAD~1", "HEAD")

        assert len(change.head_sha) == 40
        assert change.source_refs


class TestNoCredentialsAreHandled:
    def test_the_module_reads_no_credential_environment_variables(self) -> None:
        # 認証情報を扱わない設計そのものを固定する(ADR-0005と同じ原則)。
        # localのgit repositoryのみを読むため、veridiaは資格情報に触れる必要がない
        import source_connector

        sources = "".join(
            (Path(source_connector.__file__).parent / name).read_text(encoding="utf-8")
            for name in (
                "connector.py",
                "settings.py",
                "git_repository.py",
                "cli.py",
                "errors.py",
            )
        )
        for forbidden in ("TOKEN", "PASSWORD", "SECRET", "API_KEY", "GH_TOKEN"):
            assert forbidden not in sources, forbidden


class TestChangeSetIsImmutable:
    def test_change_set_cannot_be_mutated(self, connector: SourceConnector) -> None:
        change = connector.fetch_change("HEAD~1", "HEAD")

        assert isinstance(change, ChangeSet)
        with pytest.raises(AttributeError):
            change.head_sha = "0" * 40  # type: ignore[misc]


class TestCli:
    def test_writes_a_change_set_as_json(self, target_repo: Path, tmp_path: Path) -> None:
        import json

        from source_connector.cli import main

        output = tmp_path / "change.json"
        exit_code = main(
            [
                "--repo",
                str(target_repo),
                "--label",
                "target",
                "--base",
                "HEAD~1",
                "--head",
                "HEAD",
                "--output",
                str(output),
            ]
        )

        assert exit_code == 0
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert {file["path"] for file in payload["changed_files"]} == {
            "kept.txt",
            "added.txt",
            "removed.txt",
        }
        assert payload["source_refs"]

    def test_unknown_revision_exits_with_an_input_error(
        self, target_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from source_connector.cli import main

        exit_code = main(
            [
                "--repo",
                str(target_repo),
                "--base",
                "no-such-ref",
                "--head",
                "HEAD",
                "--output",
                str(tmp_path / "unused.json"),
            ]
        )

        assert exit_code == 2
        assert "no-such-ref" in capsys.readouterr().err
        assert not (tmp_path / "unused.json").exists()
