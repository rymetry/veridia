"""T-019 sandbox fixture seed and deterministic clock tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sandbox_env import SandboxEnvError, apply_seed, create, reset, state_hash
from sandbox_env.cli import main
from sandbox_env.clock import FIXED_NOW_ENV_VAR, now, parse_fixed_now

FIXED_NOW_TEXT = "2026-07-03T12:34:56.789012Z"


def write_seed_manifest(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "version": "sandbox-fixture-seed.v1",
                "directories": ["workspace/data"],
                "files": [
                    {
                        "path": "workspace/data/orders.json",
                        "content": ('[{"id":"order-fixture-001","status":"paid","amount":1200}]\n'),
                    },
                    {
                        "path": "workspace/config.json",
                        "content": '{"feature_flags":{"checkout_v2":true}}\n',
                    },
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_seed_manifest_materializes_declared_fixture_files(tmp_path: Path) -> None:
    sandbox_root = tmp_path / "sandbox"
    seed_path = write_seed_manifest(tmp_path / "seed.json")

    create(sandbox_root)
    result = apply_seed(sandbox_root, seed_path)

    assert result.root == sandbox_root
    assert result.seed_path == seed_path
    assert result.directory_count == 1
    assert result.file_count == 2
    assert (sandbox_root / "workspace" / "data").is_dir()
    assert (sandbox_root / "workspace" / "data" / "orders.json").read_text(
        encoding="utf-8"
    ) == '[{"id":"order-fixture-001","status":"paid","amount":1200}]\n'
    assert (sandbox_root / "workspace" / "config.json").read_text(encoding="utf-8") == (
        '{"feature_flags":{"checkout_v2":true}}\n'
    )


def test_reset_then_reseed_produces_the_same_seeded_state_hash(tmp_path: Path) -> None:
    sandbox_root = tmp_path / "sandbox"
    seed_path = write_seed_manifest(tmp_path / "seed.json")

    create(sandbox_root)
    initial_hash = state_hash(sandbox_root)
    apply_seed(sandbox_root, seed_path)
    first_seeded_hash = state_hash(sandbox_root)

    assert first_seeded_hash != initial_hash

    reset(sandbox_root)
    assert state_hash(sandbox_root) == initial_hash
    apply_seed(sandbox_root, seed_path)
    second_seeded_hash = state_hash(sandbox_root)

    assert second_seeded_hash == first_seeded_hash


def test_cli_seed_applies_fixture_and_prints_execution_log(tmp_path: Path, capsys) -> None:
    sandbox_root = tmp_path / "sandbox"
    seed_path = write_seed_manifest(tmp_path / "seed.json")

    assert main(["create", str(sandbox_root)]) == 0
    assert main(["seed", str(sandbox_root), str(seed_path)]) == 0

    output = capsys.readouterr().out
    assert f"seeded: {sandbox_root}" in output
    assert f"seed: {seed_path}" in output
    assert "directories: 1" in output
    assert "files: 2" in output
    assert (sandbox_root / "workspace" / "data" / "orders.json").is_file()


def test_fixed_clock_returns_same_utc_time_in_repeated_sandbox_subprocesses(
    tmp_path: Path,
) -> None:
    sandbox_root = tmp_path / "sandbox"
    create(sandbox_root)
    env = {
        **os.environ,
        FIXED_NOW_ENV_VAR: FIXED_NOW_TEXT,
        "PYTHONPATH": str(Path(__file__).parent.parent),
    }
    command = [
        sys.executable,
        "-c",
        "from sandbox_env.clock import now; print(now().isoformat())",
    ]

    first = subprocess.run(
        command,
        cwd=sandbox_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    second = subprocess.run(
        command,
        cwd=sandbox_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert first.stdout == "2026-07-03T12:34:56.789012+00:00\n"
    assert second.stdout == first.stdout


def test_clock_rejects_invalid_fixed_now_with_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FIXED_NOW_ENV_VAR, "2026-07-03T12:34:56")

    with pytest.raises(SandboxEnvError, match=FIXED_NOW_ENV_VAR):
        now()


@pytest.mark.parametrize(
    "value",
    [
        "not-a-date",
        "2026-07-03T12:34:56+09:00",
    ],
)
def test_parse_fixed_now_rejects_invalid_or_non_utc_values(value: str) -> None:
    with pytest.raises(SandboxEnvError, match=FIXED_NOW_ENV_VAR):
        parse_fixed_now(value)


@pytest.mark.parametrize(
    "manifest_payload",
    [
        {"version": "sandbox-fixture-seed.v1", "directories": ["../escape"], "files": []},
        {"version": "sandbox-fixture-seed.v1", "directories": ["/absolute"], "files": []},
        {
            "version": "sandbox-fixture-seed.v1",
            "directories": [],
            "files": [{"path": "../escape.txt", "content": "x"}],
        },
        {
            "version": "sandbox-fixture-seed.v1",
            "directories": [],
            "files": [{"path": "/absolute.txt", "content": "x"}],
        },
    ],
)
def test_seed_manifest_rejects_paths_that_escape_sandbox(
    tmp_path: Path,
    manifest_payload: dict[str, object],
) -> None:
    sandbox_root = tmp_path / "sandbox"
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(manifest_payload), encoding="utf-8")
    create(sandbox_root)

    with pytest.raises(SandboxEnvError, match="relative sandbox path"):
        apply_seed(sandbox_root, seed_path)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("[]", "JSON object"),
        (json.dumps({"version": "wrong", "directories": [], "files": []}), "unsupported"),
        (
            json.dumps({"version": "sandbox-fixture-seed.v1", "directories": {}, "files": []}),
            "directories",
        ),
        (
            json.dumps({"version": "sandbox-fixture-seed.v1", "directories": [1], "files": []}),
            "directory at index 0",
        ),
        (
            json.dumps({"version": "sandbox-fixture-seed.v1", "directories": [], "files": {}}),
            "files",
        ),
        (
            json.dumps({"version": "sandbox-fixture-seed.v1", "directories": [], "files": [1]}),
            "file at index 0",
        ),
        (
            json.dumps({"version": "sandbox-fixture-seed.v1", "directories": [], "files": [{}]}),
            "missing string path",
        ),
        (
            json.dumps(
                {
                    "version": "sandbox-fixture-seed.v1",
                    "directories": [],
                    "files": [{"path": "workspace/file.txt"}],
                }
            ),
            "missing string content",
        ),
    ],
)
def test_seed_manifest_validation_errors_include_context(
    tmp_path: Path,
    payload: str,
    message: str,
) -> None:
    sandbox_root = tmp_path / "sandbox"
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(payload, encoding="utf-8")
    create(sandbox_root)

    with pytest.raises(SandboxEnvError, match=message):
        apply_seed(sandbox_root, seed_path)


def test_apply_seed_requires_existing_sandbox_root(tmp_path: Path) -> None:
    seed_path = write_seed_manifest(tmp_path / "seed.json")

    with pytest.raises(SandboxEnvError, match="sandbox root"):
        apply_seed(tmp_path / "missing-sandbox", seed_path)
