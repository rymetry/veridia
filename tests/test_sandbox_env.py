"""T-018 sandbox ephemeral env lifecycle tests."""

from __future__ import annotations

from pathlib import Path

from sandbox_env import create, destroy, reset, state_hash
from sandbox_env.cli import main


def test_create_destroy_and_recreate(tmp_path: Path) -> None:
    sandbox_root = tmp_path / "sandbox"

    created = create(sandbox_root)
    assert created.root == sandbox_root
    assert (sandbox_root / "workspace").is_dir()
    assert (sandbox_root / "manifest.json").is_file()

    destroy(sandbox_root)
    assert not sandbox_root.exists()

    recreated = create(sandbox_root)
    assert recreated.root == sandbox_root
    assert (sandbox_root / "workspace").is_dir()


def test_two_consecutive_creates_have_same_initial_state_hash(tmp_path: Path) -> None:
    sandbox_root = tmp_path / "sandbox"

    create(sandbox_root)
    first_hash = state_hash(sandbox_root)
    destroy(sandbox_root)

    create(sandbox_root)
    second_hash = state_hash(sandbox_root)

    assert first_hash == second_hash


def test_reset_recreates_initial_state_after_mutation(tmp_path: Path) -> None:
    sandbox_root = tmp_path / "sandbox"

    create(sandbox_root)
    initial_hash = state_hash(sandbox_root)
    (sandbox_root / "workspace" / "scratch.txt").write_text("changed\n", encoding="utf-8")

    reset(sandbox_root)

    assert state_hash(sandbox_root) == initial_hash
    assert not (sandbox_root / "workspace" / "scratch.txt").exists()


def test_cli_create_hash_reset_and_destroy(tmp_path: Path, capsys) -> None:
    sandbox_root = tmp_path / "sandbox"

    assert main(["create", str(sandbox_root)]) == 0
    assert main(["state-hash", str(sandbox_root)]) == 0
    first_hash = capsys.readouterr().out.strip().splitlines()[-1]

    (sandbox_root / "workspace" / "scratch.txt").write_text("changed\n", encoding="utf-8")

    assert main(["reset", str(sandbox_root)]) == 0
    assert main(["state-hash", str(sandbox_root)]) == 0
    second_hash = capsys.readouterr().out.strip().splitlines()[-1]

    assert first_hash == second_hash

    assert main(["destroy", str(sandbox_root)]) == 0
    assert not sandbox_root.exists()
